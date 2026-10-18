"""One compact4T minimum-MIM write/hold/source-follower-read layout prototype."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_shared_analog_memory_3t_v2';out=f.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);f.OUT=out
 gen=f.magic('dict set gf180mcu::ruleset gate_to_polycont 0.50\nload compact_memory_raw\nmagic::gencell gf180mcu::nfet_03v3 wn -spice w 0.25u l 0.28u nf 1 guard 0 botc 0 topc 1\nmagic::gencell gf180mcu::pfet_03v3 wp -spice w 0.5u l 0.28u nf 1 guard 0 botc 0 topc 1\nmagic::gencell gf180mcu::nfet_03v3 rf -spice w 0.5u l 1u nf 1 guard 0 botc 0 topc 1\nwriteall force\nquit -noprompt\n')
 (out/'generation.log').write_text(gen);files={Path(__file__),R/'scripts/build_gf180_fixed_body_tg.py'}
 layers={};shapes={}
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  pad=38 if cut=='via1' else 40;half=26 if cut=='via1' else 28
  for layer in [lo,hi]:rect(layer,(x-pad,y-pad,x+pad,y+pad))
  rect(cut,(x-half,y-half,x+half,y+half))
 def horizontal(layer,x1,x2,y,pad=40):rect(layer,(min(x1,x2)-pad,y-pad,max(x1,x2)+pad,y+pad))
 def vertical(layer,x,y1,y2,pad=40):rect(layer,(x-pad,min(y1,y2)-pad,x+pad,max(y1,y2)+pad))
 for label,family,w,l,dx,dy in [('wn','nfet',.25,.28,0,0),('rf','nfet',.5,1.,-350,600),('rs','nfet',.25,.28,350,900)]:
  candidates=[p for p in out.glob(family+'_03v3_*.mag') if f'string parameters w {w} l {l} ' in p.read_text() and 'guard 0' in p.read_text()]
  assert candidates,(label,w,l);p=max(candidates,key=lambda p:p.stat().st_mtime);files.add(p)
  shape=rectangles(p,0);shapes[label]=(shape,dx,dy)
  for layer,boxes in shape.items():
   for x1,y1,x2,y2 in boxes:rect(layer,(x1+dx,y1+dy,x2+dx,y2+dy))
 def diff(label,right,dest_y):
  shape,dx,dy=shapes[label];family='pdiffc' if label=='wp' else 'ndiffc'
  b=(max if right else min)(shape[family],key=lambda b:(b[0]+b[2])/2)
  x=(b[0]+b[2])//2+dx;y=(b[1]+b[3])//2+dy
  via('metal1','metal2','via1',x,y)
  if label in ['wn']:column=dx+(260 if right else -260)
  elif label=='rf':column=-100 if right else -700
  else:column=700 if right else 100
  horizontal('metal2',x,column,y,38)
  vertical('metal2',column,y,dest_y)
  return column

 def gate(label,dest_y):
  shape,dx,dy=shapes[label];b=shape['polycontact'][0];x=(b[0]+b[2])//2+dx;y=(b[1]+b[3])//2+dy;lift=(y+101)//2*2
  vertical('metal1',x,y,lift,38);via('metal1','metal2','via1',x,lift);vertical('metal2',x,lift,dest_y)
  return x
 # Write TG data on M3 below the active row; held state on a distinct M3 route.
 ax=[diff(label,False,-200) for label in ['wn']]
 bx=[diff(label,True,200) for label in ['wn']]
 for x in ax:via('metal2','metal3','via2',x,-200)
 for x in bx:via('metal2','metal3','via2',x,200)
 horizontal('metal3',-800,max(ax),-200);horizontal('metal3',min(bx),1100,200)
 vertical('metal3',1100,200,1800);horizontal('metal3',480,1100,1800);via('metal3','metal4','via3',480,1800);via('metal4','metal5','via4',480,1800)
 en=gate('wn',300);horizontal('metal2',-800,en,300)
 # Source follower plus read-select NFET. Read current comes from the external column.
 sense=[diff('rf',False,900),diff('rs',True,900)]
 for x in sense:via('metal2','metal3','via2',x,900)
 horizontal('metal3',min(sense),max(sense),900)
 ro=diff('rs',False,600);via('metal2','metal3','via2',ro,600);horizontal('metal3',-900,ro,600);ry=600
 sg=gate('rf',1300);via('metal2','metal3','via2',sg,1300);horizontal('metal3',sg,1100,1300)
 rg=gate('rs',1100);horizontal('metal2',rg,1400,1100)
 rd=diff('rf',True,1300);horizontal('metal2',rd,1600,1300)

 # Native body contacts, using the same dimensions as the qualified fixed-body TG.
 for tx,kind in [(-440,'p')]:
  rect('pwell' if kind=='p' else 'nwell',(tx-180,-200,tx+180,200))
  rect('psubdiff' if kind=='p' else 'nsubdiff',(tx-36,-100,tx+36,100))
  rect('psubdiffcont' if kind=='p' else 'nsubdiffcont',(tx-23,-87,tx+23,87))
  rect('metal1',(tx-38,-98,tx+38,98))
 horizontal('metal1',-800,-440,0,38);horizontal('metal1',1560,1600,0,38)
 via('metal1','metal2','via1',1600,0);vertical('metal2',1600,0,1300)
 # Reuse only the native MIM stack; the existing NF body contact supplies local substrate.
 cp=f.BASE/'layout/gf180_mim_5x5_ports_routed/gf180_mim_5x5_ports_routed.mag';cq=cp.with_name('qualification.json');q=json.loads(cq.read_text())
 assert q['magic_drc_count']==0 and q['lvs_unique'] and sha(cp)==q['sha256'][cp.name];files.update([cp,cq])
 for layer,boxes in rectangles(cp,0).items():
  if layer not in ['mimcap','mimcapcontact','metal4','via4','metal5']:continue
  for x1,y1,x2,y2 in boxes:rect(layer,(x1+600,y1+900,x2+600,y2+900))
 pins={'STATE':('metal3',(460,1780,500,1820)),'DATA':('metal3',(-780,-220,-740,-180)),
  'WRITE':('metal2',(-780,280,-740,320)),
  'READ':('metal2',(1320,1080,1360,1120)),'READOUT':('metal3',(-880,ry-20,-840,ry+20)),
  'VCM':('metal4',(-100,880,-60,920)),'VDD':('metal2',(1580,1240,1620,1280)),
  'VSS':('metal1',(-780,-20,-740,20))}
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(name,(layer,b)) in enumerate(pins.items(),1):lines+=[f'rlabel {layer} s '+' '.join(map(str,b))+f' 4 {name}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines));(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 ref='.subckt reference '+' '.join(pins)+'\nXwn STATE WRITE DATA VSS nfet_03v3 w=.25u l=.28u\nXrf VDD STATE sense VSS nfet_03v3 w=.5u l=1u\nXrs sense READ READOUT VSS nfet_03v3 w=.25u l=.28u\nXc STATE VCM cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u\n.ends\n'
 (out/'reference.spice').write_text(ref)
 log=f.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 match=re.search(r'Total DRC errors found:\s*(\d+)',log);assert match
 r=dict(cell=cell,magic_drc_count=int(match[1]),source_layout_completed=True,lvs_unique=False,
  bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=list(pins),
  mos_count=3,native_mim_count=1,physical_storage_accepted=False,dense_array_qualified=False,
  scope='3T gain-cell candidate: one native NFET write-access, local source-follower and read-select NFET, one 50fF MIM. Row selection and column bias/read processing are shared. The single NFET is evaluated only in the existing 1.0-1.4V storage window with 3.3V wordline; no rail-to-rail write claim. Local buffered read retained to isolate held state from column charge sharing. Fresh physical and native retention/read checks required; no model, accuracy, full-chip or complete periphery acceptance.')
 if r['magic_drc_count']==0:
  setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
  lvs=f.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);r['lvs_unique']='Circuits match uniquely' in lvs
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files|{out/(cell+'.mag'),out/(cell+'.spice'),out/(cell+'.gds'),out/'reference.spice',out/'extraction.log'}}
 report=out/'initial_physical_result.json';report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['magic_drc_count']==0 and r['lvs_unique']
if __name__=='__main__':main()
