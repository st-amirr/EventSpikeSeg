"""One focused repair of measured parent bank metal5/MIM access spacing violations."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def main():
 p=R/'scripts/build_gf180_compact_memory_bank2x2_v1.py';s=p.read_text()
 s=s.replace('bank2x2_v1','bank2x2_v2').replace('Initial2x2','Focused spacing repair2x2')
 s=s.replace("for l in [lo,hi]:rect(l,(x+dx-p,y+dy-p,x+dx+p,y+dy+p))","for l in [lo,hi]:\n   a=44 if l=='metal5' else p;rect(l,(x+dx-a,y+dy-a,x+dx+a,y+dy+a))")
 s=s.replace('300,2020','300,2040').replace(',-760,2020',',-760,2040')
 s=s.replace('[(400,1500,2200),(1100,1700,2380)]','[(400,1700,2220),(1100,1880,2400)]')
 s=s.replace("via('metal3','metal4','via3',600,1480);h('metal3',-1000,600,1480);via('metal2','metal3','via2',-1000,1480);v('metal2',-1000,-400,1480)","rect('metal4',(440+dx,1400+dy,760+dx,1640+dy));via('metal3','metal4','via3',600,1600);h('metal3',-1000,600,1600);via('metal2','metal3','via2',-1000,1600);v('metal2',-1000,-400,1600)")
 s=s.replace("[('WRITE',2020),('WRITEB',2200),('READ',2380)]","[('WRITE',2040),('WRITEB',2220),('READ',2400)]").replace("h('metal5',-2000,5400,y)","h('metal5',-2000,5600,y,44)")
 dest=p.with_name('build_gf180_compact_memory_bank2x2_v2.py');assert not dest.exists();dest.write_text(s)
 report=dict(baseline_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),baseline='artifacts/analog_asic/layout/gf180_compact_memory_bank2x2_v1/initial_physical_result.json',diagnosis='Source LVS unique;30 native DRC violations in four rule families: M5 width/spacing, MIM bottom-plate overlap at new access via and unrelated-M4 keepout. Preserve function/device sizes; widen M5 to.44um with.46um gaps, lift VCM via away from MIM edge and move right wordline escape outside MIM keepout.',repair_script=dest.relative_to(R).as_posix())
 out=R/'artifacts/analog_asic/results/gf180_compact_memory_bank2x2_spacing_review_v1.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
