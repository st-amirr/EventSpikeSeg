"""Physically route five qualified analog neuron modules into a characterization parent."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_neuron_five_module_parent_v1';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={};cache_changes=[]
 state='gf180_state_threshold_output_clamp_v2';park='gf180_tracking_autozero_parking_v1';reset='gf180_reset_current_steering_shielded_v2';inject='gf180_signed_event_injection_v1';decision='gf180_sampled_decision_hold_v2';names=[state,park,reset,inject,decision]
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
 ports=['STATE','AUX','DATA','WRITE','WRITEB','AUXRESET','BETA','AUXREF','VCM','VSS','VDD','SENSE_REF','SENSE_BIAS','SENSE_COMP','OUTPUT_HOLD','OUTPUT_HOLDB','PARK_AZ','PARK_AZB','PARK_BIAS','RESET_PROGRAM','NCAS','RESET','INJ_PPROGRAM','INJ_NPROGRAM','PCAS','POS','POSB','NEG','NEGB','SAMPLE','SAMPLEB','SPIKE','SPIKEB'];nets=ports+['SENSE_OUT','PARK'];tracks={n:100000+640*i for i,n in enumerate(nets)};layers={};uses=[]
 instances=[('state',state,0,{'STATE':'STATE','AUX':'AUX','DATA':'DATA','WRITE':'WRITE','WRITEB':'WRITEB','AUXRESET':'AUXRESET','BETA':'BETA','AUXREF':'AUXREF','VCM':'VCM','VSS':'VSS','VDD':'VDD','SENSE_REF':'SENSE_REF','SENSE_OUT':'SENSE_OUT','BIAS':'SENSE_BIAS','SENSE_COMP':'SENSE_COMP','LATCHED_SPIKE':'SPIKE','OUTPUT_HOLD':'OUTPUT_HOLD','OUTPUT_HOLDB':'OUTPUT_HOLDB'}),('tracking',park,80000,{'STATE':'STATE','PARK':'PARK','VCM':'VCM','AZ':'PARK_AZ','AZB':'PARK_AZB','VDD':'VDD','VSS':'VSS','BIAS':'PARK_BIAS'}),('reset',reset,320000,{'STATE':'STATE','PARK':'PARK','PROGRAM':'RESET_PROGRAM','CASCODE':'NCAS','RESET':'RESET','SPIKE':'SPIKE','VDD':'VDD','VSS':'VSS'}),('inject',inject,400000,{'STATE':'STATE','PARK':'PARK','PPROGRAM':'INJ_PPROGRAM','NPROGRAM':'INJ_NPROGRAM','PCAS':'PCAS','NCAS':'NCAS','POS':'POS','POSB':'POSB','NEG':'NEG','NEGB':'NEGB','VDD':'VDD','VSS':'VSS'}),('decision',decision,500000,{'IN':'SENSE_OUT','SAMPLE':'SAMPLE','SAMPLEB':'SAMPLEB','SPIKE':'SPIKE','SPIKEB':'SPIKEB','VDD':'VDD','VSS':'VSS'})]
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:rect(layer,(x-120,y-120,x+120,y+120))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 0','box '+' '.join(map(str,bbox))]
  text=(children[name][0]/(name+'.mag')).read_text()
  labels=re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',text,re.M)
  assert set(mapping)=={r[-1] for r in labels}
  for i,(layer,x1,y1,x2,y2,pin) in enumerate(labels):
   assert layer=='metal5', (name,pin,layer)
   px=dx+(int(x1)+int(x2))//2;y=(int(y1)+int(y2))//2;x=dx-5000-400*i;dest=tracks[mapping[pin]]
   rect('metal5',(x-60,y-60,px+60,y+60));via('metal4','metal5','via4',x,y)
   rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest)
 for net,y in tracks.items():rect('metal5',(-22000,y-60,550000,y+60))
 rect('metal4',(-22440,99960,-22360,122200));rect('metal5',(-22440,tracks['VSS']-60,-21900,tracks['VSS']+60));via('metal4','metal5','via4',-22400,tracks['VSS'])
 for i in range(len(nets)-1):
  y=100000+640*i+320;rect('metal5',(-22440,y-44,550000,y+44));via('metal4','metal5','via4',-22400,y)
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 pins={}
 for net in ports:
  y=tracks[net];layer,b='metal5',(-21140,y-20,-21100,y+20);rect(layer,b);pins[net]=(layer,b)
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
 ref=''
 for name,(d,q) in children.items():
  fqpath=d/'flat_cap_qualification.json';fq=json.loads(fqpath.read_text());assert fq['flat_extraction_completed'] and fq['flat_lvs_unique'];files.add(fqpath)
  p=d/(fq['flat_subcircuit']+'.spice');files.add(p);txt=p.read_text();ref+=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(fq['flat_subcircuit'])+r'(?![A-Za-z0-9_])',name,txt)+'\n'
 ref+='.subckt reference '+' '.join(ports)+'\n'
 for inst,name,dx,mapping in instances:
  d=children[name][0];fq=json.loads((d/'flat_cap_qualification.json').read_text());txt=(d/(fq['flat_subcircuit']+'.spice')).read_text().replace('\n+',' ');order=re.search(r'(?m)^\.subckt\s+'+fq['flat_subcircuit']+r'\s+([^\n]+)',txt)[1].split();ref+='X'+inst+' '+' '.join(mapping[p] for p in order)+' '+name+'\n'
 ref+='.ends\n';(out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-3000:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'generated_cache_changes':cache_changes,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':56,'native_mim_count':41,'target_float_channel':None,'scope':'Physically routed characterization parent of five actual modules: state/beta/detector/clamp, tracking/autozero parking, current-steered reset, bipolar event injection and sampled decision.56MOS41nativeMIM plus186.5um2 auxiliary M4/M5 plate. Thirty-three real external ports; STATE, detector decision, SPIKE and PARK connections are actual parent metal. External comparator autozero/reference fixture, analog biases, phases and float-weight-duration generation remain unfinished infrastructure. Spacious characterization geometry; do not replicate its footprint as dense resident-state area. Full DRC/LVS/GDS/flat-extraction and new parent simulation required; child transfer precision does not transfer. No completePLIF/adaptation/inhibition/readout, original-float accuracy,5ms population service or full-chip acceptance','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':56,'native_mim_count':41},indent=2))
if __name__=='__main__':main()
