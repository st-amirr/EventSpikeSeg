"""Place gain-cell transistors below the MIM footprint; actual physical qualification."""
from pathlib import Path
import json,hashlib,re
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_shared_underplate_3t_v2';out=f.BASE/'layout'/cell;assert not out.exists();out.mkdir();f.OUT=out
 source=f.BASE/'layout/gf180_shared_analog_memory_3t_v2';layers={};devices={};inputs={Path(__file__)}
 def rect(l,b):layers.setdefault(l,[]).append(tuple(b))
 def h(l,a,b,y,p=40):rect(l,(min(a,b)-p,y-p,max(a,b)+p,y+p))
 def v(l,x,a,b,p=40):rect(l,(x-p,min(a,b)-p,x+p,max(a,b)+p))
 def via(lo,hi,cut,x,y):
  p,c=(38,26) if cut=='via1' else (40,28)
  for l in [lo,hi]:rect(l,(x-p,y-p,x+p,y+p))
  rect(cut,(x-c,y-c,x+c,y+c))
 for n,w,le,dx in [('wn',.25,.28,0),('rf',.5,1.,500),('rs',.25,.28,1100)]:
  p=next(p for p in source.glob('nfet_03v3_*.mag') if f'string parameters w {w} l {le} ' in p.read_text());inputs.add(p);shape=rectangles(p,0);devices[n]=(shape,dx)
  for l,boxes in shape.items():
   for a,b,c,d in boxes:rect(l,(a+dx,b,c+dx,d))
 def diff(n,right):
  shape,dx=devices[n];b=(max if right else min)(shape['ndiffc'],key=lambda b:b[0]);x=(b[0]+b[2])//2+dx;y=(b[1]+b[3])//2;via('metal1','metal2','via1',x,y);return x,y
 def gate(n):
  shape,dx=devices[n];b=shape['polycontact'][0];x=(b[0]+b[2])//2+dx;y=(b[1]+b[3])//2;lift=(y+101)//2*2;v('metal1',x,y,lift,38);via('metal1','metal2','via1',x,lift);return x,lift
 x,y=diff('wn',False);h('metal2',x,-220,y);v('metal2',-220,y,-500);via('metal2','metal3','via2',-220,-500);h('metal3',-300,-220,-500)
 x,y=diff('wn',True);h('metal2',x,200,y);v('metal2',200,y,350)
 x,y=gate('rf');v('metal2',x,y,350);h('metal2',200,x,350);via('metal2','metal3','via2',200,350);v('metal3',200,350,1100);h('metal3',200,480,1100);via('metal3','metal4','via3',480,1100);via('metal4','metal5','via4',480,1100)
 x,y=gate('wn');v('metal2',x,y,600);via('metal2','metal3','via2',x,600);h('metal3',-300,x,600)
 for n,right in [('rf',False),('rs',False)]:
  x,y=diff(n,right);v('metal2',x,y,-160);via('metal2','metal3','via2',x,-160)
 h('metal3',348,1016,-160)
 x,y=diff('rf',True);h('metal2',x,760,y);v('metal2',760,y,850);via('metal1','metal2','via1',760,850);h('metal1',760,1500,850,38)
 x,y=diff('rs',True);h('metal2',x,1320,y);v('metal2',1320,y,-500);via('metal2','metal3','via2',1320,-500);h('metal3',1320,1500,-500)
 x,y=gate('rs');h('metal2',x,1400,y);v('metal2',1400,y,600);via('metal2','metal3','via2',1400,600);h('metal3',1400,1500,600)
 rect('pwell',(420,-550,780,-150));rect('psubdiff',(564,-450,636,-250));rect('psubdiffcont',(577,-437,623,-263));rect('metal1',(562,-448,638,-252));h('metal1',-300,600,-350,38)
 cap=f.BASE/'layout/gf180_mim_5x5_ports_routed/gf180_mim_5x5_ports_routed.mag';inputs.add(cap)
 for l,boxes in rectangles(cap,0).items():
  if l not in ['mimcap','mimcapcontact','metal4','metal5','via4']:continue
  for a,b,c,d in boxes:rect(l,(a+600,b+200,c+600,d+200))
 pins={'STATE':('metal3',(460,1080,500,1120)),'DATA':('metal3',(-320,-520,-280,-480)),'WRITE':('metal3',(-320,580,-280,620)),'READ':('metal3',(1480,580,1520,620)),'READOUT':('metal3',(1480,-520,1520,-480)),'VCM':('metal4',(-100,180,-60,220)),'VDD':('metal1',(1480,830,1520,870)),'VSS':('metal1',(-320,-370,-280,-330))}
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(n,(l,b)) in enumerate(pins.items(),1):lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {n}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines));(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 (out/'reference.spice').write_bytes((source/'reference.spice').read_bytes())
 log=f.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
 nl=f.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl)
 outputs=[out/(cell+s) for s in ['.mag','.spice','.gds']]+[out/'reference.spice',out/'extraction.log',out/'netgen.log']
 q=dict(cell=cell,magic_drc_count=count,lvs_unique='Circuits match uniquely' in nl,source_layout_completed=True,mos_count=3,native_mim_count=1,ports=list(pins),bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],scope='Three native NFETs placed under MIM footprint with lower-metal routing; same single-write/buffered-read gain cell and50fF capacitor. Actual physical overlap must pass native DRC/LVS and fresh extracted simulation. External shared peripherals remain unimplemented here; no fullchip acceptance.',sha256={p.relative_to(R).as_posix():sha(p) for p in inputs|set(outputs)})
 (out/'initial_physical_result.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='sha256'},indent=2));assert count==0 and q['lvs_unique']
if __name__=='__main__':main()
