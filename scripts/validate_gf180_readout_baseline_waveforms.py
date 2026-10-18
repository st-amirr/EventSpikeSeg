"""Validate captured baseline waveform completion with explicit time tolerance."""
import hashlib,json,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=BASE/'results/gf180_readout_loop_waveforms_1a1ea7741a_src1fc0698dbb33.json';d=json.loads(p.read_text());files={p,Path(__file__)}
 for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 data=next(ROOT/n for n in d['sha256'] if n.endswith('.dat'));log=next(ROOT/n for n in d['sha256'] if n.endswith('.log') and 'gf180_readout_loop_waveforms_' in n);a=np.loadtxt(data,skiprows=1);text=log.read_text()
 assert a.shape==(15512,9) and np.isfinite(a).all() and abs(a[-1,0]-.00508)<1e-12 and 'ngspice-47 done' in text and not re.search('timestep too small|simulation\(s\) aborted',text,re.I)
 d={'audit_completed':True,'simulation_completed':True,'raw_report':p.relative_to(ROOT).as_posix(),'actual_end_time_s':float(a[-1,0]),'required_end_time_s':.00508,'completion_time_tolerance_s':1e-12,'rows':len(a),'windows':d['windows'],'scope':'Initial postprocessor rejected endpoint by1.73e-18s floating-point rounding. Original report/source/log/data remain unchanged; immutable source hashes, normal ngspice termination, complete finite waveform dimensions and endpoint tolerance verified. This establishes baseline diagnostic completion, not loop stability or physical acceptance.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 p=BASE/'results/gf180_readout_baseline_waveform_validation.json';assert not p.exists();p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(p),'simulation_completed':True,'actual_end_time_s':d['actual_end_time_s']},indent=2))
if __name__=='__main__':main()
