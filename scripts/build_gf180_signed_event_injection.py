"""Build bipolar pulse-duration injection interface with continuously biased sources and idle parking."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_signed_event_injection_v1';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={}
 state='gf180_source_nf05_l1_compact';cmp='gf180_fixed_body_tg_quarter_shorttracks';pf='gf180_source_pf05_l1_compact'
 for name in [state,cmp,pf]:
  d=flow.BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback'];children[name]=(d,q)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;assert sha(f)==h,n;files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 ports=['STATE','PARK','PPROGRAM','NPROGRAM','PCAS','NCAS','POS','POSB','NEG','NEGB','VDD','VSS'];nets=ports+['PI','NI','POUT','NOUT'];tracks={n:12000+480*i for i,n in enumerate(nets)};layers={};uses=[]
 instances=[('psource',pf,0,{'D':'PI','G':'PPROGRAM','S':'VDD','VDD':'VDD'}),('pcas',pf,4000,{'D':'POUT','G':'PCAS','S':'PI','VDD':'VDD'}),('nsource',state,10000,{'D':'NI','G':'NPROGRAM','S':'VSS','VSS':'VSS'}),('ncas',state,14000,{'D':'NOUT','G':'NCAS','S':'NI','VSS':'VSS'})]
 for inst,dx,source,enable,enableb,outnet in [('pevent',20000,'POUT','POS','POSB','STATE'),('pidle',29000,'POUT','POSB','POS','PARK'),('nevent',38000,'NOUT','NEG','NEGB','STATE'),('nidle',47000,'NOUT','NEGB','NEG','PARK')]:instances.append((inst,cmp,dx,{'A':source,'B':outnet,'EN':enable,'ENB':enableb,'VSS':'VSS','VDD':'VDD'}))
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:rect(layer,(x-40,y-40,x+40,y+40))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 0','box '+' '.join(map(str,bbox))]
  text=(children[name][0]/(name+'.mag')).read_text()
  labels=re.findall(r'^rlabel metal3 s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',text,re.M)
  assert set(mapping)=={r[-1] for r in labels}
  for i,(x1,y1,x2,y2,pin) in enumerate(labels):
   x=dx-1400+400*i;y=(int(y1)+int(y2))//2;dest=tracks[mapping[pin]]
   via('metal3','metal4','via3',x,y);rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest)
 for net,y in tracks.items():rect('metal5',(-1600,y-60,60000,y+60))
 # Ground guards between adjacent global clock/current tracks and local vertical escapes.
 rect('metal4',(-2040,11960,-1960,21000));rect('metal5',(-2040,tracks['VSS']-60,-1500,tracks['VSS']+60));via('metal4','metal5','via4',-2000,tracks['VSS'])
 for i in range(len(nets)-1):
  y=12000+480*i+240;rect('metal5',(-2040,y-44,60000,y+44));via('metal4','metal5','via4',-2000,y)
 for inst,name,dx,mapping in instances:
  for i in range(len(mapping)-1):
   x=dx-1200+400*i;rect('metal4',(x-40,-1000,x+40,21000));via('metal4','metal5','via4',x,tracks['VSS'])
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
 for name in [state,cmp,pf]:visit(name)
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
 q={'cell':cell,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':12,'native_mim_count':0,'target_float_channel':None,'scope':'Reusable signed event injection interface: continuously biased PF source/cascode and NF sink/cascode, two event and two idle parking quarterTG paths.12MOS,noMIM. Twelve real external ports, four internal nets. POS and NEG externally supplied nonoverlapping weight-duration pulses; analog program/cascode references and PARK external. No quantized weights, no model-frequency change, no autonomous weight-to-time conversion or local weight memory claim. Full DRC/LVS/GDS/cap extraction; actual signed charge, clock injection and hold must be measured. Characterization geometry, not completePLIF/model accuracy/service/full-chip acceptance','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':12},indent=2))
if __name__=='__main__':main()
