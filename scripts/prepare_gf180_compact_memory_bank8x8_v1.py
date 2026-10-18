"""Scale the qualified2x2 storage routing pattern to one actual8x8 bank."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def main():
 p=R/'scripts/build_gf180_compact_memory_bank2x2_v4.py';s=p.read_text()
 s=s.replace('bank2x2_v4','bank8x8_v1').replace('range(2)','range(8)').replace('5400','27000').replace('5600','27200').replace('5300','21500')
 s=s.replace('2700+y','18900+y').replace('mos_count=16,native_mim_count=4','mos_count=256,native_mim_count=64').replace('2x2','8x8').replace('16 nativeMOS+4','256 nativeMOS+64')
 d=p.with_name('build_gf180_compact_memory_bank8x8_v1.py');assert not d.exists();d.write_text(s)
 out=R/'artifacts/analog_asic/results/gf180_memory_bank8x8_layout_expansion_v1.json';assert not out.exists();out.write_text(json.dumps(dict(source=p.relative_to(R).as_posix(),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),method='One actual8x8 storage bank using measured2x2 geometry: same18um column/13.5um row pitch, shared buses extended for8rows8columns. Fresh native parent source/GDS/flat DRC and LVS, followed by one selective write/hold/read sequence. No parameter sweep or compute-sharing assumption.',fullcapacity_layout_complete=False),indent=2)+'\n')
if __name__=='__main__':main()
