"""Build a compact one-MIM held scale PFET with routed GF180 hierarchy."""
import hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 cell='gf180_membrane_scale_compact_v22'
 cap='gf180_mim_bank_7x7_n9'; tg='gf180_fixed_body_tg_fullroute_half'; fet='gf180_membrane_scale_pf042_l10_fullroute_v2'
 out=flow.BASE/'layout'/cell; out.mkdir(parents=True,exist_ok=True)
 if (out/'qualification.json').exists(): raise ValueError('preserve existing qualification')
 flow.OUT=out
 names=[cap,tg,fet]; children={}; qs={}; inputs=set()
 for name in names:
  d=flow.BASE/'layout'/name; q=json.loads((d/'qualification.json').read_text())
  assert q['magic_drc_count']==0 and q.get('gds_roundtrip_drc_count',0)==0 and q['lvs_unique'] and q.get('gds_roundtrip_lvs_unique',True)
  for group in ('sha256','input_sha256','gds_roundtrip_sha256'):
   for rel,expected in q.get(group,{}).items():
    p=d/rel if group=='sha256' else flow.ROOT/rel
    if sha(p)!=expected: raise ValueError('qualified child changed: '+str(p))
    inputs.add(p)
  inputs.add(d/'qualification.json'); children[name]=d; qs[name]=q
 deps=['gf180_source_nf05_l1_compact','gf180_source_pf05_l1_compact']
 for name in deps: children[name]=flow.BASE/'layout'/name
 nets=['PROGRAM','WRITE','WRITEB','VCM','SCALE_OUT','VDD','VSS','SCALE_GATE']
 tracks={n:12000+i*900 for i,n in enumerate(nets)}
 layers={}
 def rect(layer,b): layers.setdefault(layer,[]).append(tuple(b))
 def via4(x,y,pad=90):
  rect('metal4',(x-pad,y-pad,x+pad,y+pad)); rect('metal5',(x-pad,y-pad,x+pad,y+pad)); rect('via4',(x-28,y-28,x+28,y+28))
 def stack_to_m4(layer,x,y,pad=90):
  if layer=='metal1':
   rect('metal1',(x-pad,y-pad,x+pad,y+pad));rect('metal2',(x-pad,y-pad,x+pad,y+pad));rect('via1',(x-28,y-28,x+28,y+28))
   rect('metal2',(x-pad,y-pad,x+pad,y+pad));rect('metal3',(x-pad,y-pad,x+pad,y+pad));rect('via2',(x-28,y-28,x+28,y+28))
   rect('metal3',(x-pad,y-pad,x+pad,y+pad));rect('metal4',(x-pad,y-pad,x+pad,y+pad));rect('via3',(x-28,y-28,x+28,y+28))
  elif layer=='metal2':
   rect('metal2',(x-pad,y-pad,x+pad,y+pad));rect('metal3',(x-pad,y-pad,x+pad,y+pad));rect('via2',(x-28,y-28,x+28,y+28))
   rect('metal3',(x-pad,y-pad,x+pad,y+pad));rect('metal4',(x-pad,y-pad,x+pad,y+pad));rect('via3',(x-28,y-28,x+28,y+28))
  elif layer=='metal3':
   rect('metal3',(x-pad,y-pad,x+pad,y+pad));rect('metal4',(x-pad,y-pad,x+pad,y+pad));rect('via3',(x-28,y-28,x+28,y+28))
 cfg=[(cap,'cap',0,0,['SCALE_GATE','VCM','VSS']),
      (tg,'write',30000,0,['PROGRAM','SCALE_GATE','WRITE','WRITEB','VSS','VDD']),
      (fet,'scale',40000,0,['SCALE_OUT','SCALE_GATE','VDD'])]
 uses=[]
 for name,inst,dx,dy,mapping in cfg:
  q=qs[name]; bbox=[round(x/.005) for x in q['bbox_um']]
  uses += [f'use {name} {inst}',f'transform 1 0 {dx} 0 1 {dy}','box '+' '.join(map(str,bbox))]
  mag=(children[name]/f'{name}.mag').read_text(encoding='ascii')
  labs=re.findall(r'(?m)^rlabel (\S+) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)\nport (\d+)',mag)
  labs.sort(key=lambda x:int(x[-1]))
  if len(labs)!=len(mapping): raise ValueError(f'{name} ports {len(labs)} != {len(mapping)}')
  for layer,x1,y1,x2,y2,label,pno in labs:
   net=mapping[int(pno)-1]; x=dx+(int(x1)+int(x2))//2; y=dy+(int(y1)+int(y2))//2
   col=dx+bbox[0]-700-int(pno)*450
   if layer in ('metal1','metal2','metal3'):
    rect(layer,(min(x,col)-45,y-45,max(x,col)+45,y+45))
    stack_to_m4(layer,col,y)
   elif layer in ('metal4','via4'):
    rect('metal4',(min(x,col)-65,y-65,max(x,col)+65,y+65))
   elif layer=='metal5':
    width=120 if name==cap and net=='SCALE_GATE' else 65
    rect('metal5',(min(x,col)-width,y-width,max(x,col)+width,y+width)); via4(col,y)
   elif layer=='mimcapcontact':
    rect('mimcapcontact',(min(x,col)-65,y-65,max(x,col)+65,y+65)); rect('metal4',(col-65,y-65,col+65,y+65)); via4(col,y)
   else: raise ValueError('unknown pin layer '+layer)
   rect('metal4',(col-55,y-55,col+55,tracks[net]+55))
   via4(col,tracks[net])
 left=min(round(x/.005) for q in qs.values() for x in q['bbox_um'][0:1])-3500
 right=max(round(x/.005) for q in qs.values() for x in q['bbox_um'][2:3])+max(dx for _,_,dx,_,_ in cfg)+22000
 for y in tracks.values(): rect('metal5',(left,y-65,right,y+65))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 for layer,boxes in layers.items(): lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,n in enumerate(nets,1):
  y=tracks[n]; lines += [f'rlabel metal5 s {left+140} {y-20} {left+180} {y+20} 4 {n}',f'port {i} nsew']
 lines+=['<< end >>','']; (out/f'{cell}.mag').write_text('\n'.join(lines),encoding='ascii')
 (out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 preload='\n'.join('load /workspace/'+(children[n]/n).relative_to(flow.ROOT).as_posix() for n in deps+names)+'\n'
 log=flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nputs "BBOX [box values]"\nquit -noprompt\n')
 (out/'extraction.log').write_text(log)
 dm=re.search(r'Total DRC errors found:\s*(\d+)',log)
 if not dm or int(dm.group(1)) or (out/'gds_warnings.feedback').read_text(): raise RuntimeError('DRC/GDS failed '+log[-1800:])
 ref=''.join((d/f'{n}.spice').read_text()+'\n' for n,d in children.items())
 ref+=f'.subckt reference '+' '.join(nets)+'\n'
 ref+=f'Xcap SCALE_GATE VCM VSS {cap}\nXwrite PROGRAM SCALE_GATE WRITE WRITEB VSS VDD {tg}\nXscale SCALE_OUT SCALE_GATE VDD {fet}\n.ends\n'
 (out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
 lvs=flow.run(['netgen-lvs','-batch','lvs',f'{cell}.spice {cell}','reference.spice reference',setup,'lvs.out']); (out/'netgen.log').write_text(lvs)
 if 'Circuits match uniquely' not in lvs: raise RuntimeError('LVS failed '+lvs[-2200:])
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n'); (out/'capacitance_extraction.log').write_text(caplog)
 rd=flow.BASE/'verification/gds_roundtrip'/cell; rd.mkdir(parents=True,exist_ok=True); flow.OUT=rd
 read=flow.magic('gds read /workspace/'+(out/f'{cell}.gds').relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n'); (rd/'readback.log').write_text(read)
 drm=re.search(r'Total DRC errors found:\s*(\d+)',read)
 rlvs=flow.run(['netgen-lvs','-batch','lvs',f'roundtrip.spice {cell}','/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs)
 if not drm or int(drm.group(1)) or 'Circuits match uniquely' not in rlvs or (rd/'roundtrip.feedback').read_text(): raise RuntimeError('readback failed '+read[-1400:]+' '+rlvs[-1400:])
 generated=[out/f'{cell}{s}' for s in ('.mag','.spice','_cap.spice','.gds')]+[out/n for n in ('build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback')]
 q={'cell':cell,'ports':nets,'magic_drc_count':0,'lvs_unique':True,'gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],'native_mim_count':1,'native_mos_count':3,'architecture':'one native 7um MIM held by the routed TG; PFET reads the stored gate as bank-scale current','physical_scale_cell_accepted':False,'scope':'Compact per-bank scale-cell prototype only. No current calibration through the exact macro, fan-in multiplier, membrane update, PVT/noise or full-float inference acceptance.','sha256':{p.name:sha(p) for p in generated},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(inputs)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in (rd/n for n in ('readback.log','netgen.log','roundtrip.spice','roundtrip.feedback'))}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'area_mm2':((q['bbox_um'][2]-q['bbox_um'][0])*(q['bbox_um'][3]-q['bbox_um'][1]))/1e6},indent=2))
if __name__=='__main__':main()

