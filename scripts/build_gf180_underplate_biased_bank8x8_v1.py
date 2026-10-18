"""Actual shared row/column 3T memory with transistors below MIM plates."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_underplate_biased_bank8x8_v1';out=f.BASE/'layout'/cell;assert not out.exists();out.mkdir();f.OUT=out
 child='gf180_shared_underplate_3t_v2';d=f.BASE/'layout'/child;src=d/(child+'.mag');q=json.loads((d/'qualification.json').read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and sha(src)==q['sha256'][src.name]
 shape=rectangles(src,0);layers={};pins={};ref=[];dx=dy=0
 def rect(l,b):layers.setdefault(l,[]).append(tuple(b))
 def h(l,a,b,y,p=40):rect(l,(min(a,b)+dx-p,y+dy-p,max(a,b)+dx+p,y+dy+p))
 def v(l,x,a,b,p=40):rect(l,(x+dx-p,min(a,b)+dy-p,x+dx+p,max(a,b)+dy+p))
 def via(lo,hi,cut,x,y):
  p,c=(38,26) if cut=='via1' else (40,28)
  for l in [lo,hi]:
   a=44 if l=='metal5' else p;rect(l,(x+dx-a,y+dy-a,x+dx+a,y+dy+a))
  rect(cut,(x+dx-c,y+dy-c,x+dx+c,y+dy+c))
 def pin(n,l,x,y):pins[n]=(l,(x+dx-20,y+dy-20,x+dx+20,y+dy+20))
 for row in range(8):
  for col in range(8):
   dx=2200*col;dy=2240*row
   for l,boxes in shape.items():
    for a,b,c,e in boxes:rect(l,(a+dx,b+dy,c+dx,e+dy))
   pin(f'STATE{row}{col}','metal3',480,1100)
   h('metal3',-420,-300,-500);h('metal3',1500,1620,-500)
   for x in [-420,1620]:via('metal3','metal4','via3',x,-500)
   v('metal2',0,600,1340);via('metal2','metal3','via2',0,1340);via('metal3','metal4','via3',0,1340);via('metal4','metal5','via4',0,1340)
   h('metal2',1300,1400,600);v('metal2',1300,600,1540);via('metal2','metal3','via2',1300,1540);via('metal3','metal4','via3',1300,1540);via('metal4','metal5','via4',1300,1540)
   rect('metal4',(1000+dx,753+dy,1120+dx,1040+dy));via('metal3','metal4','via3',1060,1000);via('metal2','metal3','via2',1060,1000);via('metal1','metal2','via1',1060,1000)
   ref +=[f'Xw{row}{col} STATE{row}{col} WRITE{row} DATA{col} VSS nfet_03v3 w=.25u l=.28u',f'Xf{row}{col} VDD STATE{row}{col} sense{row}{col} VSS nfet_03v3 w=.5u l=1u',f'Xr{row}{col} sense{row}{col} READ{row} READOUT{col} VSS nfet_03v3 w=.25u l=.28u',f'Xc{row}{col} STATE{row}{col} VCM cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u']
 # One physical diode master and eight native column sinks, shared by64membranes.
 p=next(p for p in (f.BASE/'layout/gf180_shared_analog_memory_3t_v2').glob('nfet_03v3_*.mag') if 'string parameters w 0.5 l 1.0 ' in p.read_text());sink=rectangles(p,0)
 for col in range(9):
  dx=1620+2200*col if col<8 else 18400;dy=-2000
  for l,boxes in sink.items():
   for a,b,c,e in boxes:rect(l,(a+dx,b+dy,c+dx,e+dy))
  via('metal1','metal2','via1',-152,-46);v('metal2',-152,-46,-400);via('metal1','metal2','via1',-152,-400)
  v('metal1',0,104,204,38);via('metal1','metal2','via1',0,204);v('metal2',0,204,400)
  via('metal1','metal2','via1',152,-46)
  if col<8:
   v('metal2',152,-46,150);via('metal2','metal3','via2',152,150);h('metal3',0,152,150);via('metal3','metal4','via3',0,150);v('metal4',0,150,1350)
   ref +=[f'Xsink{col} READOUT{col} BIAS VSS VSS nfet_03v3 w=.5u l=1u']
  else:
   v('metal2',152,-46,400);ref +=['Xmaster BIAS BIAS VSS VSS nfet_03v3 w=.5u l=1u']
 dx=dy=0;h('metal2',1620,18552,-1600);h('metal1',-800,18552,-2400,38);v('metal2',-800,-2400,-350);via('metal1','metal2','via1',-800,-2400);pin('BIAS','metal2',18400,-1600)
 for row in range(8):
  dx=0;dy=2240*row
  for n,y in [('WRITE',1340),('READ',1540)]:h('metal5',-1400,17200,y,44);pin(n+str(row),'metal5',-1400,y)
  for n,y,x in [('VSS',-350,-800),('VDD',850,-1000),('VCM',1000,-1200)]:h('metal1',x,17200,y,38);via('metal1','metal2','via1',x,y)
 dx=dy=0
 for col in range(8):
  for n,x in [('DATA',-420),('READOUT',1620)]:v('metal4',x+2200*col,-650,17500);pin(n+str(col),'metal4',x+2200*col,17500)
 for n,x,y in [('VSS',-800,-350),('VDD',-1000,850),('VCM',-1200,1000)]:v('metal2',x,y,15680+y);pin(n,'metal2',x,y)
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(n,(l,b)) in enumerate(pins.items(),1):lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {n}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines));(out/'build_source.py').write_bytes(Path(__file__).read_bytes());(out/'reference.spice').write_text('.subckt reference '+' '.join(pins)+'\n'+'\n'.join(ref)+'\n.ends\n')
 log=f.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl)
 files=[Path(__file__),src,d/'qualification.json',out/(cell+'.mag'),out/(cell+'.spice'),out/(cell+'.gds'),out/'reference.spice',out/'netgen.log',out/'extraction.log']
 result=dict(cell=cell,magic_drc_count=count,lvs_unique='Circuits match uniquely' in nl,source_layout_completed=True,mos_count=201,native_mim_count=64,bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=list(pins),dense_array_qualified=False,scope='Actual64-state3T gain-cell bank,11um column and11.2um row pitch,50fF MIM over local transistor/lower-metal routing. Shared8 DATA/READOUT columns,8 WRITE/READ row pairs and supply/reference rails.64local STATE diagnostic ports. Native flat painted geometry and independent reference. Native9MOS shared column-current mirror included; external master current, row controls and analog DATA fixtures. No physical decoder, write-driver/calibration or complete compute/fullchip claim.',sha256={p.relative_to(R).as_posix():sha(p) for p in files})
 (out/'initial_physical_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['ports','sha256']},indent=2));assert count==0 and result['lvs_unique']
if __name__=='__main__':main()
