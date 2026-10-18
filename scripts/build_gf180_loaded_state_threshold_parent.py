"""Physically join resized native state/update and shielded comparator, preserving child evidence."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_loaded_state_threshold_parent';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={}
 state='gf180_loaded_beta_detailstem_ch3_overlap146';cmp='gf180_compact_nf_threshold_shielded'
 for name in [state,cmp]:
  d=flow.BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback'];children[name]=(d,q)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;assert sha(f)==h,n;files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 stateports=['STATE','AUX','DATA','WRITE','WRITEB','AUXRESET','BETA','AUXREF','VCM','VSS','VDD'];ports=stateports+['SENSE_REF','SENSE_OUT','BIAS','SENSE_COMP'];tracks={n:13000+240*i for i,n in enumerate(stateports[2:])};layers={};uses=[]
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:rect(layer,(x-40,y-40,x+40,y+40))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx in [('memory',state,0),('detector',cmp,14000)]:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 0','box '+' '.join(map(str,bbox))]
 # STATE leaves its existing localM4 route above prior stateM5 bridge; no isolated long global STATE bar.
 via('metal4','metal5','via4',4600,6500);rect('metal5',(4540,6440,12500,6560));via('metal4','metal5','via4',12440,6500);rect('metal4',(12400,2960,12480,6540));via('metal3','metal4','via3',12440,3000)
 access=[('SENSE_REF',14400,4200,17000),('SENSE_OUT',14800,5400,17400),('VDD',15200,6600,tracks['VDD']),('VSS',15600,7800,tracks['VSS']),('BIAS',16000,9000,17800),('SENSE_COMP',16400,10200,18200)]
 newtracks={}
 for net,x,y,dest in access:
  via('metal3','metal4','via3',x,y);rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest)
  if net in tracks:rect('metal5',(9940,dest-60,x+60,dest+60))
  else:rect('metal5',(-1600,dest-60,36000,dest+60));newtracks[net]=dest
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 # Explicit parent metal at reused child ports; labels alone do not create connectivity.
 pins={}
 for net in ports:
  if net=='STATE':layer,b='metal4',(4580,5900,4620,5940)
  elif net=='AUX':layer,b='metal4',(2780,2400,2820,2440)
  else:
   y=tracks[net] if net in tracks else newtracks[net];layer,b='metal5',(-1540,y-20,-1500,y+20)
  rect(layer,b);pins[net]=(layer,b)
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
 for name in [state,cmp]:visit(name)
 preload=''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in views);flow.OUT=out
 log=flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert drc and int(drc[1])==0 and not (out/'gds_warnings.feedback').read_text() and not re.search(r'\d+ problems occurred',log),log[-5000:]
 ref=''.join((d/(name+'.spice')).read_text()+'\n' for name,(d,q) in children.items());ref+='.subckt reference '+' '.join(ports)+'\nXmemory '+' '.join(stateports)+' '+state+'\nXdetector STATE SENSE_REF SENSE_OUT VDD VSS BIAS SENSE_COMP '+cmp+'\n.ends\n';(out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-3000:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':11,'native_mim_count':1,'target_float_channel':children[state][1]['target_float_channel'],'scope':'Physically joined resized resident state/beta and shielded seven-MOS comparator input; explicit STATE M4/M5 route, shared rails and four real comparator access ports. Full DRC/LVS/GDS readback/cap extraction. Autozero/reference storage, tracking, decision/reset/bias/clocks still external schematic assembly. New physical route adds coupling/load; old separate-child beta/reference/reset results cannot transfer. Characterization fixture, not dense leaf, complete PLIF/model/noise/service/chip acceptance.','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':11},indent=2))
if __name__=='__main__':main()
