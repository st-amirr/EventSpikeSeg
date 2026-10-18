"""Build sampled analog magnitude-to-pulse-duration comparator interface."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_analog_weight_duration_v1';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={};cache_changes=[]
 cmp='gf180_compact_nf_threshold_shielded';select='gf180_reset_select_and_fullroute';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 for name in [cmp,select,inv,tg,mim]:
  d=flow.BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback'];children[name]=(d,q)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;actual=sha(f)
    if actual!=h:
     assert f.suffix=='.ext',n
     cache_changes.append({'path':f.relative_to(flow.ROOT).as_posix(),'qualified_sha256':h,'current_sha256':actual,'reason':'Generated cache rewritten by parent extraction; source geometry and all consumed netlists remain checked.'})
    files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 ports=['MAG_DATA','WRITE','WRITEB','RAMP','ARM','BIAS','VDD','VSS','PULSE','PULSEB','MAG_HOLD','CMP','OUT'];nets=ports+['LOGIC','LOGICB'];tracks={n:20000+480*i for i,n in enumerate(nets)};layers={};uses=[]
 instances=[('compare',cmp,0,{'IP':'MAG_HOLD','IN':'RAMP','OUT':'OUT','VDD':'VDD','VSS':'VSS','BIAS':'BIAS','CMP':'CMP'}),('writer',tg,30000,{'A':'MAG_DATA','B':'MAG_HOLD','EN':'WRITE','ENB':'WRITEB','VSS':'VSS','VDD':'VDD'}),('store',mim,42000,{'P':'MAG_HOLD','M':'VSS','VSS':'VSS'}),('compensation',mim,46000,{'P':'OUT','M':'CMP','VSS':'VSS'}),('invert',inv,52000,{'IN':'OUT','OUT':'LOGICB','VDD':'VDD','VSS':'VSS'}),('buffer',inv,62000,{'IN':'LOGICB','OUT':'LOGIC','VDD':'VDD','VSS':'VSS'}),('gate',select,72000,{'A':'ARM','B':'LOGIC','Y':'PULSE','YB':'PULSEB','VDD':'VDD','VSS':'VSS'})]
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:rect(layer,(x-40,y-40,x+40,y+40))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 0','box '+' '.join(map(str,bbox))]
  text=(children[name][0]/(name+'.mag')).read_text()
  labels=re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',text,re.M)
  assert set(mapping)=={r[-1] for r in labels}
  for i,(layer,x1,y1,x2,y2,pin) in enumerate(labels):
   px=dx+(int(x1)+int(x2))//2;y=(int(y1)+int(y2))//2;dest=tracks[mapping[pin]]
   if layer=='metal3':
    x=dx-1400+400*i;via('metal3','metal4','via3',x,y)
   elif layer=='metal5':
    x=px;via('metal4','metal5','via4',x,y)
   elif layer=='metal4':
    x=dx-1400;rect('metal4',(x-40,y-40,px+40,y+40))
   elif layer=='metal1':
    x=dx-2000;via('metal1','metal2','via1',px,y);via('metal2','metal3','via2',px,y);rect('metal3',(min(x,px)-40,y-40,max(x,px)+40,y+40));via('metal3','metal4','via3',x,y)
   else:raise ValueError(layer)
   rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest)
   if name==mim and pin=='M':rect('metal4',(x-120,dest-120,x+120,dest+120))
 for net,y in tracks.items():rect('metal5',(-2600,y-60,100000,y+60))
 # Ground guards between globals; local mixed-layer MIM escapes remain clear.
 rect('metal4',(-3040,19960,-2960,28000));rect('metal5',(-3040,tracks['VSS']-60,-2500,tracks['VSS']+60));via('metal4','metal5','via4',-3000,tracks['VSS'])
 for i in range(len(nets)-1):
  y=20000+480*i+240;rect('metal5',(-3040,y-44,100000,y+44));via('metal4','metal5','via4',-3000,y)
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 pins={}
 for net in ports:
  y=tracks[net];layer,b='metal5',(-1540,y-20,-1500,y+20);rect(layer,b);pins[net]=(layer,b)
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,net in enumerate(ports,1):layer,b=pins[net];lines +=[f'rlabel {layer} s '+' '.join(map(str,b))+f' 4 {net}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 visited=set();views=[]
 def visit(name):
  if name in visited:return
  assert name in geometry and len(geometry[name])==1,name;p=next(iter(geometry[name]))
  for child in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(child)
  visited.add(name);views.append(p)
 for name in [cmp,select,inv,tg,mim]:visit(name)
 preload=''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in views);flow.OUT=out
 log=flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert drc and int(drc[1])==0 and not (out/'gds_warnings.feedback').read_text() and not re.search(r'\d+ problems occurred',log),log[-5000:]
 ref=''.join((d/(name+'.spice')).read_text()+'\n' for name,(d,q) in children.items());ref+='.subckt reference '+' '.join(ports)+'\n'
 for inst,name,dx,mapping in instances:
  txt=(children[name][0]/(name+'.spice')).read_text().replace('\n+',' ');order=re.search(r'(?m)^\.subckt\s+'+name+r'\s+([^\n]+)',txt)[1].split();ref+='X'+inst+' '+' '.join(mapping[p] for p in order)+' '+name+'\n'
 ref+='.ends\n';(out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-3000:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'generated_cache_changes':cache_changes,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':19,'native_mim_count':2,'target_float_channel':None,'scope':'Analog magnitude-to-duration interface: one native sampled MIM magnitude, seven-MOS differential comparator, minimum MIM compensation, two inverter buffers and phase-AND output.19MOS2MIM,thirteen real ports. PULSE equalsARM while held magnitude exceeds rising RAMP; intended weight-to-duration mechanism, sign selection separate. RAMP,programmer,bias and ARM external; autonomous ramp/event phases, original-float voltage mapping and timing accuracy remain unqualified. Full physical and flat extraction plus three nominal programmed levels required. No QAT/digital membrane or fullPLIF/model/service/fullchip acceptance','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':19,'native_mim_count':2},indent=2))
if __name__=='__main__':main()
