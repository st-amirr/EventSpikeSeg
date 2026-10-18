"""Initial two-row/two-column physical analog-memory bank, shared actual metal buses."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_compact_memory_bank2x2_v4';out=f.BASE/'layout'/cell;assert not out.exists();out.mkdir();f.OUT=out
 child='gf180_compact_analog_memory_4t_v4';d=f.BASE/'layout'/child;q=json.loads((d/'qualification.json').read_text());src=d/(child+'.mag')
 assert q['magic_drc_count']==0 and q['lvs_unique'] and sha(src)==q['sha256'][src.name]
 shape=rectangles(src,0);layers={};pins={};ref=[];dx=dy=0
 def rect(l,b):layers.setdefault(l,[]).append(tuple(b))
 def h(l,x1,x2,y,p=40):rect(l,(min(x1,x2)+dx-p,y+dy-p,max(x1,x2)+dx+p,y+dy+p))
 def v(l,x,y1,y2,p=40):rect(l,(x+dx-p,min(y1,y2)+dy-p,x+dx+p,max(y1,y2)+dy+p))
 def via(lo,hi,cut,x,y):
  p,c=(38,26) if cut=='via1' else (40,28)
  for l in [lo,hi]:
   a=44 if l=='metal5' else p;rect(l,(x+dx-a,y+dy-a,x+dx+a,y+dy+a))
  rect(cut,(x+dx-c,y+dy-c,x+dx+c,y+dy+c))
 def pin(n,l,x,y):pins[n]=(l,(x+dx-20,y+dy-20,x+dx+20,y+dy+20))
 for row in range(2):
  for col in range(2):
   dx=3600*col;dy=2700*row
   for l,boxes in shape.items():
    for a,b,c,e in boxes:rect(l,(a+dx,b+dy,c+dx,e+dy))
   pin(f'STATE{row}{col}','metal3',480,1800)
   # Independent DATA/READOUT column buses on M4 outside the cell's MIM stack.
   for name,y,x in [('DATA',-200,-1200),('READOUT',600,-1400)]:
    h('metal3',x,-860 if name=='READOUT' else -760,y);via('metal3','metal4','via3',x,y)
   # Row wordlines M5; local M4 escapes clear the MIM and held-state metal.
   via('metal2','metal3','via2',-760,300);via('metal3','metal4','via3',-760,300);v('metal4',-760,300,2040);via('metal4','metal5','via4',-760,2040)
   for y,x,track in [(400,1700,2220),(1100,1880,2400)]:
    via('metal2','metal3','via2',1340,y);h('metal3',1340,x,y);via('metal3','metal4','via3',x,y);v('metal4',x,y,track);via('metal4','metal5','via4',x,track)
   # Separate power drops to M1 row rails. VCM escapes from the top MIM rim.
   rect('metal4',(-340+dx,840+dy,-100+dx,1640+dy));via('metal3','metal4','via3',-260,1600);h('metal3',-1000,-260,1600);via('metal2','metal3','via2',-1000,1600);v('metal2',-1000,-400,1600);via('metal1','metal2','via1',-1000,-400)
   v('metal2',1600,-560,1240);via('metal1','metal2','via1',1600,-560)
   via('metal1','metal2','via1',-760,0);v('metal2',-760,-720,0);via('metal1','metal2','via1',-760,-720)
   ref +=[f'Xwn{row}{col} STATE{row}{col} WRITE{row} DATA{col} VSS nfet_03v3 w=.25u l=.28u',
    f'Xwp{row}{col} STATE{row}{col} WRITEB{row} DATA{col} VDD pfet_03v3 w=.5u l=.28u',
    f'Xrf{row}{col} VDD STATE{row}{col} sense{row}{col} VSS nfet_03v3 w=.5u l=1u',
    f'Xrs{row}{col} sense{row}{col} READ{row} READOUT{col} VSS nfet_03v3 w=.25u l=.28u',
    f'Xc{row}{col} STATE{row}{col} VCM cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u']
 for row in range(2):
  dx=0;dy=row*2700
  for n,y in [('WRITE',2040),('WRITEB',2220),('READ',2400)]:h('metal5',-2000,5600,y,44);pin(n+str(row),'metal5',-2000,y)
  for n,y,x in [('VSS',-720,-2400),('VDD',-560,-2200),('VCM',-400,-2600)]:h('metal1',x,5400,y,38);via('metal1','metal2','via1',x,y)
 dx=dy=0
 for col in range(2):
  for n,x in [('DATA',-1200),('READOUT',-1400)]:v('metal4',x+col*3600,-900,5300);pin(n+str(col),'metal4',x+col*3600,5300)
 for n,x,y in [('VSS',-2400,-720),('VDD',-2200,-560),('VCM',-2600,-400)]:v('metal2',x,y,2700+y);pin(n,'metal2',x,y)
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(n,(l,b)) in enumerate(pins.items(),1):lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {n}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines));(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 (out/'reference.spice').write_text('.subckt reference '+' '.join(pins)+'\n'+'\n'.join(ref)+'\n.ends\n')
 log=f.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
 nl=f.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl)
 result=dict(cell=cell,magic_drc_count=count,lvs_unique='Circuits match uniquely' in nl,source_layout_completed=True,mos_count=16,native_mim_count=4,
  bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=list(pins),dense_array_qualified=False,
  scope='External left-rim VCM access2x2 real shared-row/shared-column storage bank,16 nativeMOS+4 minimum50fF MIM. Actual shared DATA/READOUT columns, three categorical wordlines per row and VDD/VSS/VCM row buses with separate spines. Four STATE diagnostic pads remain local. Original compact cell geometry copied flat with fresh parent DRC/reference LVS required. No beta/threshold/weight compute, decoder, bus-driver layout, fullcapacity or fullchip claim.',
  sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),src,d/'qualification.json',out/(cell+'.mag'),out/(cell+'.spice'),out/(cell+'.gds'),out/'reference.spice',out/'netgen.log',out/'extraction.log']})
 (out/'initial_physical_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert count==0 and result['lvs_unique']
if __name__=='__main__':main()
