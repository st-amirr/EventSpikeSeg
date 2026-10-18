"""One focused repair of identified sense/read/state/supply crossing shorts."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'scripts/build_gf180_compact_analog_memory_4t_v1.py'
q=R/'scripts/build_gf180_compact_analog_memory_4t_v2.py';assert not q.exists()
s=p.read_text().replace('gf180_compact_analog_memory_4t_v1','gf180_compact_analog_memory_4t_v2')
s=s.replace("('rs','nfet',.25,.28,350,600)","('rs','nfet',.25,.28,350,900)")
s=s.replace("via('metal1','metal2','via1',x,y);vertical('metal2',x,y,dest_y)\n  return x", "via('metal1','metal2','via1',x,y)\n  if dest_y is None:return x,y\n  vertical('metal2',x,y,dest_y)\n  return x",1)
s=s.replace("horizontal('metal2',enb,1600,400)","horizontal('metal2',enb,1400,400)")
s=s.replace("sense=[diff('rf',False,500),diff('rs',True,500)];horizontal('metal2',min(sense),max(sense),500)","sense=[diff('rf',False,600),diff('rs',True,600)];horizontal('metal2',min(sense),max(sense),600)")
s=s.replace("ro=diff('rs',False,-400);via('metal2','metal3','via2',ro,-400);horizontal('metal3',-800,ro,-400)","ro,ry=diff('rs',False,None);via('metal2','metal3','via2',ro,ry);horizontal('metal3',-900,ro,ry)")
s=s.replace("sg=gate('rf',900);via('metal2','metal3','via2',sg,900);horizontal('metal3',sg,480,900)","sg=gate('rf',1300);via('metal2','metal3','via2',sg,1300);horizontal('metal3',sg,480,1300)")
s=s.replace("rd=diff('rf',True,1300);horizontal('metal2',rd,1600,1300)","rd,rdy=diff('rf',True,None);via('metal2','metal3','via2',rd,rdy);horizontal('metal3',-1000,rd,rdy);vertical('metal3',-1000,-500,rdy);via('metal3','metal4','via3',-1000,-500);horizontal('metal4',-1000,1600,-500)")
s=s.replace("via('metal1','metal2','via1',1600,0);vertical('metal2',1600,0,1300)","via('metal1','metal2','via1',1600,0);via('metal2','metal3','via2',1600,0);vertical('metal3',1600,-500,0);via('metal3','metal4','via3',1600,-500)")
s=s.replace("'WRITEB':('metal2',(1520,380,1560,420))","'WRITEB':('metal2',(1320,380,1360,420))")
s=s.replace("'READOUT':('metal3',(-780,-420,-740,-380))","'READOUT':('metal3',(-880,ry-20,-840,ry+20))")
s=s.replace("'VDD':('metal2',(1580,1240,1620,1280))","'VDD':('metal4',(1520,-520,1560,-480))")
s=s.replace('Compact first4T/50fF-MIM','Focused routing repair of actual v1 net shorts: separate sense/readout from held-state and supply crossings, move read-select active row, keep every transistor and capacitor dimension unchanged. Compact4T/50fF-MIM')
q.write_text(s);print(q)
