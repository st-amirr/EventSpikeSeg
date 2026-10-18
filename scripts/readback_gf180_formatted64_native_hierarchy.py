"""Read back full64 formatter GDS for independent device-only hierarchy checks."""
import probe_gf180_mos_gate_cap as f
import re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 cell='gf180_formatted_energy64_v3';d=f.BASE/'layout'/cell;out=f.BASE/'verification/gds_roundtrip'/cell;assert not out.exists();out.mkdir(parents=True);f.OUT=out;tcl='gds read /workspace/'+(d/(cell+'.gds')).relative_to(ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract no capacitance\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n';(out/'readback.tcl').write_text(tcl);log=f.magic(tcl);(out/'readback.log').write_text(log);count=re.search(r'Total DRC errors found:\s*(\d+)',log);print(json.dumps({'gds_readback_completed':True,'drc':int(count[1]) if count else None,'feedback':(out/'roundtrip.feedback').read_text()}))
if __name__=='__main__':main()
