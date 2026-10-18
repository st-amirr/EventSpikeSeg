"""Method review: replace top-rim access with external left VCM escape."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def main():
 p=R/'scripts/build_gf180_compact_memory_bank2x2_v2.py';s=p.read_text().replace('bank2x2_v2','bank2x2_v3')
 old="rect('metal4',(440+dx,1400+dy,760+dx,1640+dy));via('metal3','metal4','via3',600,1600);h('metal3',-1000,600,1600)"
 new="rect('metal4',(-340+dx,840+dy,-100+dx,960+dy));rect('metal4',(-340+dx,900+dy,-180+dx,1640+dy));via('metal3','metal4','via3',-260,1600);h('metal3',-1000,-260,1600)"
 assert old in s;s=s.replace(old,new).replace('Focused spacing repair2x2','External left-rim VCM access2x2')
 dest=p.with_name('build_gf180_compact_memory_bank2x2_v3.py');assert not dest.exists();dest.write_text(s)
 out=R/'artifacts/analog_asic/results/gf180_compact_memory_bank2x2_method_review_v1.json';assert not out.exists()
 out.write_text(json.dumps(dict(baseline=p.relative_to(R).as_posix(),baseline_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),diagnosis='After one focused repair, all16 remaining errors are MIM bottom plate to unrelated metal at the existing STATE M4/via3 pads. Extending the VCM plate upward reduced their clearance. No netlist error; independent LVS unique in both attempts.',selected_method='Move the VCM plate extension entirely to the left external rim; access via above and left of the active capacitor. Keep original top STATE clearance and all devices/wordlines unchanged.',alternatives='More top-plate spacing would enlarge cell row pitch; moving STATE would modify the qualified child. External-rim escape isolates the access geometry without those changes.',scope='Fresh native parent checks required; no qualification inferred from review.'),indent=2)+'\n')
if __name__=='__main__':main()
