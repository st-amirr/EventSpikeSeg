"""Add native detector-output clamp to checked state/detector layout for article module integration."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_state_threshold_output_clamp_v1';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={}
 state='gf180_loaded_state_threshold_shielded_v6';cmp='gf180_fixed_body_tg_quarter_shorttracks'
 for name in [state,cmp]:
  d=flow.BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback'];children[name]=(d,q)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;assert sha(f)==h,n;files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 stateports=children[state][1]['ports'];ports=stateports+['LATCHED_SPIKE','OUTPUT_HOLD','OUTPUT_HOLDB'];tracks={n:13000+240*i for i,n in enumerate(['DATA','WRITE','WRITEB','AUXRESET','BETA','AUXREF','VCM','VSS','VDD'])};tracks.update({'SENSE_REF':17000,'SENSE_OUT':17400,'BIAS':17800,'SENSE_COMP':18200,'LATCHED_SPIKE':19000,'OUTPUT_HOLD':19240,'OUTPUT_HOLDB':19480});layers={};uses=[]
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:rect(layer,(x-40,y-40,x+40,y+40))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx,dy in [('core',state,0,0),('output_clamp',cmp,42000,14000)]:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 {dy}','box '+' '.join(map(str,bbox))]
 # Six independently escaped clamp terminals. Existing qualified core routes retained.
 for net,x,y,dest in [('SENSE_OUT',42000,16000,17400),('LATCHED_SPIKE',42400,16240,19000),('OUTPUT_HOLD',42800,16480,19240),('OUTPUT_HOLDB',43200,16720,19480),('VSS',43600,16960,tracks['VSS']),('VDD',44000,17200,tracks['VDD'])]:
  via('metal3','metal4','via3',x,y);rect('metal4',(x-40,min(y,dest)-40,x+40,max(y,dest)+40));via('metal4','metal5','via4',x,dest)
  left=35500 if net in ['SENSE_OUT','VSS','VDD'] else -1600
  rect('metal5',(left,dest-60,x+60,dest+60))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 # Explicit parent metal at reused child ports; labels alone do not create connectivity.
 pins={}
 for net in ports:
  if net=='STATE':layer,b='metal4',(4580,5900,4620,5940)
  elif net=='AUX':layer,b='metal4',(2780,2400,2820,2440)
  else:
   y=tracks[net];layer,b='metal5',(-1540,y-20,-1500,y+20)
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
 ref=''.join((d/(name+'.spice')).read_text()+'\n' for name,(d,q) in children.items());ref+='.subckt reference '+' '.join(ports)+'\nXmemory '+' '.join(stateports)+' '+state+'\nXholdout SENSE_OUT LATCHED_SPIKE OUTPUT_HOLD OUTPUT_HOLDB VSS VDD '+cmp+'\n.ends\n';(out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-3000:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':13,'native_mim_count':1,'target_float_channel':children[state][1]['target_float_channel'],'scope':'Physically joined previously qualified v6 resident state/beta/detector core plus one native quarterTG detector-output clamp,13MOS/oneMIM plus auxiliary overlap. Three real external ports carry buffered latched decision and hold phases. Parent OUT/VSS/VDD connections physically routed, full DRC/LVS/GDS readback/cap extraction. Reset/tracking/autozero/reference/decision and phase/bias generation remain external assemblies. Module layout for article research, not dense-array/full-PLIF/accuracy/population-service/chip acceptance. New parent route load requires its own simulation; schematic unclamped/clamped results do not qualify its transfer.','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':13},indent=2))
if __name__=='__main__':main()
