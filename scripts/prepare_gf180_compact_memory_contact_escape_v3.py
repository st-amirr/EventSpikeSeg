"""Method review then one contact-escape routing candidate, without sizing sweeps."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
review=B/'results/gf180_compact_memory_routing_method_review_v1.json';assert not review.exists()
inputs=[B/'layout'/f'gf180_compact_analog_memory_4t_v{i}'/'initial_physical_result.json' for i in [1,2]]
assert all(json.loads(p.read_text())['magic_drc_count']==2 for p in inputs)
review.write_text(json.dumps({'method_review_completed':True,'two_native_layout_attempts_unqualified':True,
 'finding':'The first focused crossing repair did not qualify the layout. Native extraction still identifies WRITEB/STATE merging and a bypassed read follower; identical native M2.2a spacing locations remain. Direct vertical diffusion lifts pass too close to gate-contact lifts. Sense/read supply routing also shares an inadequate M2 corridor.',
 'diagnostic_limit':'Explicit-metal overlap diagnostic finds the original supply/sense/read crossing; it does not reproduce all native implicit-contact shorts, so native extraction remains authoritative.',
 'selected_method':'Use lateral M2 contact escapes before vertical transitions, as in the qualified fixed-body TG. Give SENSE a separate M3 row; route READOUT on a separate M3 row and VDD above them on M2. Same4T sizes and50fF-MIM; one named routing-method candidate, no dimension sweep.',
 'qualified_dense_array_or_model_claim':False,'sha256':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}},indent=2)+'\n')
p=R/'scripts/build_gf180_compact_analog_memory_4t_v2.py';q=R/'scripts/build_gf180_compact_analog_memory_4t_v3.py';assert not q.exists()
s=p.read_text().replace('gf180_compact_analog_memory_4t_v2','gf180_compact_analog_memory_4t_v3')
start=s.index(' def diff(');end=s.index('\n def gate(',start)
s=s[:start]+''' def diff(label,right,dest_y):
  shape,dx,dy=shapes[label];family='pdiffc' if label=='wp' else 'ndiffc'
  b=(max if right else min)(shape[family],key=lambda b:(b[0]+b[2])/2)
  x=(b[0]+b[2])//2+dx;y=(b[1]+b[3])//2+dy
  via('metal1','metal2','via1',x,y)
  if label in ['wn','wp']:column=dx+(260 if right else -260)
  elif label=='rf':column=-100 if right else -700
  else:column=700 if right else 100
  horizontal('metal2',x,column,y,38)
  vertical('metal2',column,y,dest_y)
  return column
''' + s[end:]
start=s.index(' sense=[');end=s.index('\n # Native body contacts',start)
s=s[:start]+''' sense=[diff('rf',False,900),diff('rs',True,900)]
 for x in sense:via('metal2','metal3','via2',x,900)
 horizontal('metal3',min(sense),max(sense),900)
 ro=diff('rs',False,600);via('metal2','metal3','via2',ro,600);horizontal('metal3',-900,ro,600);ry=600
 sg=gate('rf',1300);via('metal2','metal3','via2',sg,1300);horizontal('metal3',sg,480,1300)
 rg=gate('rs',1000);horizontal('metal2',rg,1400,1000)
 rd=diff('rf',True,1300);horizontal('metal2',rd,1600,1300)
''' + s[end:]
s=s.replace("via('metal1','metal2','via1',1600,0);via('metal2','metal3','via2',1600,0);vertical('metal3',1600,-500,0);via('metal3','metal4','via3',1600,-500)","via('metal1','metal2','via1',1600,0);vertical('metal2',1600,0,1300)")
s=s.replace("'VDD':('metal4',(1520,-520,1560,-480))","'VDD':('metal2',(1580,1240,1620,1280))")
s=s.replace('Focused routing repair of actual v1 net shorts: separate sense/readout from held-state and supply crossings, move read-select active row, keep every transistor and capacitor dimension unchanged.', 'Contact-escape method after documented v1/v2 routing review: lateral diffusion escapes before vertical lifts, separate M3 sense/read/state rows and M2 supply, unchanged4T/MIM dimensions.')
q.write_text(s);print(q)
