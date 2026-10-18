"""Repair the diagnosed narrow notch in the external VCM plate extension."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def main():
 p=R/'scripts/build_gf180_compact_memory_bank2x2_v3.py';s=p.read_text().replace('bank2x2_v3','bank2x2_v4')
 old="rect('metal4',(-340+dx,840+dy,-100+dx,960+dy));rect('metal4',(-340+dx,900+dy,-180+dx,1640+dy))"
 new="rect('metal4',(-340+dx,840+dy,-100+dx,1640+dy))"
 assert old in s;s=s.replace(old,new);d=p.with_name('build_gf180_compact_memory_bank2x2_v4.py');assert not d.exists();d.write_text(s)
 out=R/'artifacts/analog_asic/results/gf180_compact_memory_bank2x2_rim_notch_diagnosis_v1.json';assert not out.exists();out.write_text(json.dumps(dict(diagnosis='All12 errors localized to the40unit notch between external VCM vertical metal and existing native bottom-plate rim. Fill that notch continuously so the extension touches the plate along its length; no device/spacing search.',source='artifacts/analog_asic/layout/gf180_compact_memory_bank2x2_v3/extraction.log',repair=d.relative_to(R).as_posix()),indent=2)+'\n')
if __name__=='__main__':main()
