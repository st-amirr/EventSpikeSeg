"""Physically assemble native writer, NF local update and minimum MIM; no neuron acceptance."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_nf_state_update_aux_three_mim';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);flow.OUT=out;files={Path(__file__)};children={}
 tg='gf180_fixed_body_tg_quarter_shorttracks';nf='gf180_fixed_body_nf025_shorttracks';cap='gf180_mim_5x5_ports_routed'
 for name in [tg,nf,cap]:
  directory=flow.BASE/'layout'/name;qp=directory/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback']
  if name!=cap:assert q['gds_roundtrip_lvs_unique'] and q['gds_roundtrip_drc_count']==0
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=directory/n if key=='sha256' else flow.ROOT/n;assert sha(f)==h,n;files.add(f)
  children[name]=(directory,q)
 auditp=flow.BASE/'results/gf180_minimum_mim_routed_gds_integrity.json';audit=json.loads(auditp.read_text());assert audit['audit_completed'] and audit['cases'][0]['physical_layout_accepted'];files.add(auditp)
 for n,h in audit['sha256'].items():assert sha(flow.ROOT/n)==h,n;files.add(flow.ROOT/n)
 ports=['STATE','AUX','DATA','WRITE','WRITEB','AUXRESET','BETA','AUXREF','VCM','VSS','VDD'];globalnets=ports[2:];tracks={n:13000+240*i for i,n in enumerate(globalnets)};layers={};uses=[]
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:rect(layer,(x-40,y-40,x+40,y+40))
  rect(cut,(x-28,y-28,x+28,y+28))
 specs=[('writer',tg,0,8000,['STATE','DATA','WRITE','WRITEB','VSS','VDD'],[4600,-1280,-960,-640,-320,0]),('reset',nf,4000,0,['AUX','AUXREF','AUXRESET','VSS'],[2800,3200,3600,4000]),('share',nf,4000,4000,['STATE','AUX','BETA','VSS'],[4600,2800,4960,5280])]
 for inst,name,dx,dy,mapping,xs in specs:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 {dy}','box '+' '.join(map(str,bbox))]
  for i,(net,x) in enumerate(zip(mapping,xs)):
   y=dy+2000+240*i;via('metal3','metal4','via3',x,y)
   if net in tracks:
    rect('metal4',(x-40,y-40,x+40,tracks[net]+40));via('metal4','metal5','via4',x,tracks[net])
 rect('metal4',(4560,5760,4640,10040));rect('metal4',(2760,1960,2840,6280))
 # STATE/AUX stay local; no long diagnostic global bars.
 via('metal4','metal5','via4',4600,5800);rect('metal5',(4540,5740,7940,5860));rect('metal5',(7820,5740,7940,8060))
 cx,cy=8000,7000
 for layer,boxes in rectangles(children[cap][0]/(cap+'.mag'),0).items():
  for x1,y1,x2,y2 in boxes:rect(layer,(x1+cx,y1+cy,x2+cx,y2+cy))
 mx=cx-700;rect('metal4',(mx-60,cy-60,mx+60,tracks['VCM']+60));via('metal4','metal5','via4',mx,tracks['VCM']);rect('metal4',(mx-108,tracks['VCM']-108,mx+108,tracks['VCM']+108))
 sx=cx+1140
 for lo,hi,cut in [('metal1','metal2','via1'),('metal2','metal3','via2'),('metal3','metal4','via3')]:via(lo,hi,cut,sx,cy)
 rect('metal4',(sx-40,cy-40,sx+40,tracks['VSS']+40));via('metal4','metal5','via4',sx,tracks['VSS'])
 # Coarse low-beta range: three actual50fF auxiliary MIMs in parallel.
 via('metal4','metal5','via4',2800,5000)
 for cx,cy in [(11600,7000),(15200,7000),(18800,7000)]:
  rect('metal5',(2740,4940,cx-60,5060));rect('metal5',(cx-180,4940,cx-60,8060))
  for layer,boxes in rectangles(children[cap][0]/(cap+'.mag'),0).items():
   for x1,y1,x2,y2 in boxes:rect(layer,(x1+cx,y1+cy,x2+cx,y2+cy))
  mx=cx-700;rect('metal4',(mx-60,cy-60,mx+60,tracks['AUXREF']+60));via('metal4','metal5','via4',mx,tracks['AUXREF']);rect('metal4',(mx-108,tracks['AUXREF']-108,mx+108,tracks['AUXREF']+108))
  sx=cx+1140
  for lo,hi,cut in [('metal1','metal2','via1'),('metal2','metal3','via2'),('metal3','metal4','via3')]:via(lo,hi,cut,sx,cy)
  rect('metal4',(sx-40,cy-40,sx+40,tracks['VSS']+40));via('metal4','metal5','via4',sx,tracks['VSS'])
 for y in tracks.values():rect('metal5',(-1600,y-60,20800,y+60))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,net in enumerate(ports,1):
  if net=='STATE':layer,b='metal4',(4580,5900,4620,5940)
  elif net=='AUX':layer,b='metal4',(2780,2400,2820,2440)
  else:layer,b='metal5',(-1540,tracks[net]-20,-1500,tracks[net]+20)
  lines +=[f'rlabel {layer} s '+' '.join(map(str,b))+f' 4 {net}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 preload='\n'.join('load /workspace/'+(directory/name).relative_to(flow.ROOT).as_posix() for name,(directory,q) in children.items())+'\n'
 log=flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
 assert drc and int(drc[1])==0 and not (out/'gds_warnings.feedback').read_text() and not re.search(r'\d+ problems occurred',log),log[-5000:]
 ref=''.join((directory/(name+'.spice')).read_text()+'\n' for name,(directory,q) in children.items());ref +='.subckt reference '+' '.join(ports)+'\n'
 for inst,name,dx,dy,mapping,xs in specs:ref+='X'+inst+' '+' '.join(mapping)+' '+name+'\n'
 ref+='Xstorage STATE VCM cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u\n'+''.join(f'Xauxcap{i} AUX AUXREF cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u\n' for i in range(3))+'.ends\n';(out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-3000:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':4,'native_mim_count':4,'auxiliary_mim_count':3,'scope':'Physically connected native quarterTG writer, NF auxiliary reset, NF beta selector and one state/three auxiliary minimum MIMs; STATE/AUX diagnostics local to physical routes. This is a representative state/update characterization module, not a dense-array leaf or complete PLIF. Full DRC/LVS/GDS readback and cap extraction. Parent routing changes capacitance; old schematic beta/reference/noise/retention cannot transfer. New extracted complete-cycle simulation/calibration required before integration/replication. No RPEX, native noise, learned beta, model/service/complete-neuron or chip acceptance.','physical_storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'gds_roundtrip_lvs_unique':True},indent=2))
if __name__=='__main__':main()
