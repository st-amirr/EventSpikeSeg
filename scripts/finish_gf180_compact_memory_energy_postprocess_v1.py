"""Finish energy integration from the completed trace without rerunning SPICE."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=R/'artifacts/analog_asic/results/gf180_compact_analog_memory_4t_v4_three_native_5ms_src4064c8a2cdd0.json'
 r=json.loads(p.read_text());assert r['module_simulation_completed'] and r['postprocess_error']=="module 'numpy' has no attribute 'trapz'"
 for n,h in r['sha256'].items():assert sha(R/n)==h,n
 data=p.with_suffix('.dat');w=np.loadtxt(data,skiprows=1)
 r['VDD_supply_energy_j_excludes_ideal_data_and_control_drivers']=float(np.trapezoid(-3.3*w[:,-1],w[:,0]))
 r['previous_report']=p.relative_to(R).as_posix();r['resolved_postprocess_error']=r.pop('postprocess_error')
 r['sha256'].update({p.relative_to(R).as_posix():sha(p),Path(__file__).relative_to(R).as_posix():sha(Path(__file__))})
 out=p.with_name(p.stem+'_postprocessed_v1.json');assert not out.exists();out.write_text(json.dumps(r,indent=2)+'\n')
 print(out.relative_to(R));print(r['VDD_supply_energy_j_excludes_ideal_data_and_control_drivers'])
if __name__=='__main__':main()
