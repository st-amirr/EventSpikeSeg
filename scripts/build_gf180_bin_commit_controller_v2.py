"""Add pre-reset RMS settle/capture phases to native bin control."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bin_commit_controller_v2';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={};cache_changes=[]
 dff='gf180_control_dff_v1';phase='gf180_nonoverlap_phase_pair_v2';select='gf180_reset_select_and_fullroute';inv='gf180_phase_inverter_fullroute';names=[dff,phase,select,inv]
 for name in names:
  d=flow.BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback'];children[name]=(d,q)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;actual=sha(f)
    if actual!=h:
     assert f.suffix=='.ext',n
     cache_changes.append({'path':f.relative_to(flow.ROOT).as_posix(),'qualified_sha256':h,'current_sha256':actual,'reason':'Generated cache rewritten by parent extraction; source geometry and all consumed netlists remain checked.'})
    files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 ports=['CLK','RESET','BIN_START','COMPLETE','VDD','VSS','READY','AGE','BETA','ACCUM','RMS_SETTLE','RMS_CAPTURE','DETECT','RESET_STATE','INHIBIT','ADAPT','DONE'];nets=ports+['PHIA','PHIAB','PHIB','PHIBB','RESETB','COMPLETEB','R01','R23','R45','R67','R03','R47','R07','R89','IDLE','ACCEPT','KEEP','KEEPB','RAW2','ADV3']+[f'Q{i}' for i in range(10) if i!=2]+[f'QB{i}' for i in range(10)]+[f'D{i}' for i in range(1,10)];tracks={n:70000+640*i for i,n in enumerate(nets)};layers={};uses=[]
 qname=lambda i:'ACCUM' if i==2 else f'Q{i}'
 instances=[('clock',phase,0,{'CMD':'CLK','VDD':'VDD','VSS':'VSS','PHIA':'PHIA','PHIAB':'PHIAB','PHIB':'PHIB','PHIBB':'PHIBB'})]
 for i in range(10):instances.append((f'stage{i}',dff,120000+144000*i,{'D':'ACCEPT' if i==0 else f'D{i}','PHIA':'PHIA','PHIAB':'PHIAB','PHIB':'PHIB','PHIBB':'PHIBB','VDD':'VDD','VSS':'VSS','Q':qname(i),'QB':f'QB{i}'}))
 gates=[('idle01','QB0','QB1','R01'),('idle23','QB2','QB3','R23'),('idle45','QB4','QB5','R45'),('idle67','QB6','QB7','R67'),('idle03','R01','R23','R03'),('idle47','R45','R67','R47'),('idle07','R03','R47','R07'),('idle89','QB8','QB9','R89'),('idle','R07','R89','IDLE'),('ready','IDLE','RESETB','READY'),('accept','BIN_START','READY','ACCEPT'),('wait','ACCUM','COMPLETEB','KEEP'),('exit','ACCUM','COMPLETE','ADV3')]
 for i in range(1,10):gates.append((f'advance{i}','RAW2' if i==2 else 'ADV3' if i==3 else qname(i-1),'RESETB',f'D{i}'))
 outputs=[('AGE',0),('BETA',1),('RMS_SETTLE',3),('RMS_CAPTURE',4),('DETECT',5),('RESET_STATE',6),('INHIBIT',7),('ADAPT',8),('DONE',9)]
 for p,i in outputs:gates.append(('output'+str(i),qname(i),'PHIA',p))
 for i,(inst,a,b,y) in enumerate(gates):instances.append((inst,select,1600000+30000*i,{'A':a,'B':b,'Y':y,'YB':'KEEPB' if inst=='wait' else 'unused_'+inst,'VDD':'VDD','VSS':'VSS'}))
 instances.append(('waitor',select,1600000+30000*len(gates),{'A':'QB1','B':'KEEPB','Y':'unused_waitor','YB':'RAW2','VDD':'VDD','VSS':'VSS'}))
 instances.append(('resetinvert',inv,2700000,{'IN':'RESET','OUT':'RESETB','VDD':'VDD','VSS':'VSS'}))
 instances.append(('completeinvert',inv,2712000,{'IN':'COMPLETE','OUT':'COMPLETEB','VDD':'VDD','VSS':'VSS'}))
 assert len(gates)+1==32
 # Reserve bbox and routing escape envelopes before any geometry mutation.
 intervals=[]
 for inst,name,dx,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];pin_count=len(children[name][1]['ports']);left=dx+bbox[0]-2000-400*(pin_count-1)-120;right=dx+bbox[2]
  assert all(right<lo or left>hi for lo,hi,_ in intervals),(inst,left,right,intervals)
  intervals.append((left,right,inst))
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:
   pad=120 if layer=='metal4' else 40;rect(layer,(x-pad,y-pad,x+pad,y+pad))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 0','box '+' '.join(map(str,bbox))]
  text=(children[name][0]/(name+'.mag')).read_text()
  labels=re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',text,re.M)
  assert set(mapping)=={r[-1] for r in labels}
  for i,(layer,x1,y1,x2,y2,pin) in enumerate(labels):
   assert layer in ['metal3','metal4','metal5'], (name,pin,layer)
   if mapping[pin] not in tracks:continue
   px=dx+(int(x1)+int(x2))//2;y=(int(y1)+int(y2))//2;x=dx+bbox[0]-2000-400*i;dest=tracks[mapping[pin]]
   if layer=='metal3':
    rect('metal3',(min(x,px)-40,y-40,max(x,px)+40,y+40));via('metal3','metal4','via3',x,y)
   if layer=='metal4':via('metal4','metal5','via4',px,y)
   if layer!='metal3':
    rect('metal5',(min(x,px)-60,y-60,max(x,px)+60,y+60));via('metal4','metal5','via4',x,y)
   rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest)
 for net,y in tracks.items():
  xs=[b[0] for b in layers.get('via4',[]) if abs((b[1]+b[3])//2-y)<1]+[b[2] for b in layers.get('via4',[]) if abs((b[1]+b[3])//2-y)<1]
  rect('metal5',(min(xs+([-18000] if net in ports else []))-60,y-60,max(xs)+60,y+60))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 pins={}
 for net in ports:
  y=tracks[net];layer,b='metal5',(-17940,y-20,-17900,y+20);rect(layer,b);pins[net]=(layer,b)
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
 for name in names:visit(name)
 preload=''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in views);flow.OUT=out
 log=flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert drc and int(drc[1])==0 and not (out/'gds_warnings.feedback').read_text() and not re.search(r'\d+ problems occurred',log),log[-5000:]
 ref='';orders={}
 for name,(d,q) in children.items():
  fqpath=d/'flat_cap_qualification.json'
  if fqpath.exists():
   fq=json.loads(fqpath.read_text());assert fq['flat_extraction_completed'] and fq['flat_lvs_unique'];files.add(fqpath);sub=fq['flat_subcircuit'];p=d/(sub+'.spice')
  else:sub=name;p=d/(name+'.spice')
  files.add(p);txt=p.read_text();orders[name]=re.search(r'(?m)^\.subckt\s+'+sub+r'\s+([^\n]+)',txt.replace('\n+',' '))[1].split();ref+=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(sub)+r'(?![A-Za-z0-9_])',name,txt)+'\n'
 ref+='.subckt reference '+' '.join(ports)+'\n'
 for inst,name,dx,mapping in instances:ref+='X'+inst+' '+' '.join(mapping[p] for p in orders[name])+' '+name+'\n'
 ref+='.ends\n';(out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-3000:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'generated_cache_changes':cache_changes,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':sum(children[n][1]['mos_count'] for _,n,_,_ in instances),'native_mim_count':0,'target_float_channel':None,'scope':'Native ten-stage analog bin phase controller. Adds RMS_SETTLE and RMS_CAPTURE after all-upstream-complete accumulation and before DETECT,RESET_STATE,INHIBIT,ADAPT,DONE. Every strobe is gated by native nonoverlapPHIA, so capture releases before state reset/adaptation writes. Trained beta applies once including zero-event bins. Native DFFs/AND gates/inverters and clock nonoverlap reused; original analog numerical state/weights remain analog. This fixed-period physical controller is distinct from the new RTL handshake reference; analog phase duration must be selected from actual connected circuit settling. COMPLETE must already match the current semantic bin. No dense/full population, connected native phase-to-analog timing, model accuracy or5ms acceptance; actual new parent extraction/simulation required','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':sum(children[n][1]['mos_count'] for _,n,_,_ in instances),'native_mim_count':0},indent=2))
if __name__=='__main__':main()
