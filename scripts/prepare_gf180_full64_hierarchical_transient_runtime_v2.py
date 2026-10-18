"""One runtime extension based on measured successful time advancement, no solver change."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=R/'scripts/screen_gf180_full64_rms_frontend_hierarchical_transient_v1.py';old=B/'results/gf180_full64_rms_frontend_v1_three_transient_src6d1880acd997.json';r=json.loads(old.read_text());log=old.with_suffix('.log');times=re.findall(r'Reference value\s*:\s*([0-9.eE+-]+)',log.read_text());last=float(times[-1]);assert r['simulator_returncode']==124 and last>1.9e-6
 out=B/'results/gf180_full64_hierarchical_transient_runtime_review_v1.json';assert not out.exists();out.write_text(json.dumps(dict(initial_report=old.relative_to(R).as_posix(),last_observed_time_s=last,requested_stop_s=6e-6,initial_native_bound_s=180,one_extended_native_bound_s=660,basis='Native job advanced to1.99us of6us before180s wall-time limit, without convergence abort. Linear fulltrace estimate543s plus20percent margin gives652s, rounded660s. Same geometry, all90640C, solver tolerances, initial operating point,6us and three levels; no fit/calibration/stimulus change. Preserve initial timeout; no further unchanged retry if extension fails.',sha256={p.relative_to(R).as_posix():sha(p) for p in [p,old,log]}),indent=2)+'\n')
 s=p.read_text().replace("'180','ngspice'","'660','ngspice'").replace('timeout=195','timeout=675').replace('One180s native bound based on completed actual2304MOS full64 baseline6us transient.','One660s native runtime extension after the180s run reached1.99us of6us without a convergence abort. Measured543s linear estimate plus20percent margin; unchanged actual geometry, solver and three-level stimulus.')
 d=p.with_name('screen_gf180_full64_rms_frontend_hierarchical_transient_v2.py');assert not d.exists();d.write_text(s)
if __name__=='__main__':main()
