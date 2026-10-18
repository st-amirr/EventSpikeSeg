"""Audit actual5ms cadence from primary extracted-parent waveforms."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_extracted_state_update_5ms_boundary.json';assert not out.exists();files={Path(__file__)};cases=[]
 for seed in [0,29]:
  rp=R/f'gf180_extracted_state_update_5ms_check_seed{seed}_src4cfbdbccb382.json';d=json.loads(rp.read_text());files.add(rp);assert d['simulation_completed'] and d['simulator_returncode']==0
  for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n
  dp=rp.with_suffix('.dat');w=np.loadtxt(dp,skiprows=1);assert w.shape[1]==9 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-.015015)<1e-12
  phases=[]
  for k in range(3):
   phase={label:{tag:{node:float(np.interp((5000*k+t)*1e-6,w[:,0],w[:,1+2*i+j])) for j,node in enumerate(['state','aux'])} for i,tag in enumerate(['low','mid','high'])} for label,t in [('before',19),('sharing',20.45),('after',21.5),('rearmed',31.5),('late',4999.5)]}
   for label,tags in phase.items():
    for tag,nodes in tags.items():
     for node,v in nodes.items():assert abs(v-d['measurements'][f'{tag}_c{k}_{node}_{label}'])<6e-6
   phases.append(phase)
  b=d['comparison_slope'];residuals={tag:[phases[k]['late'][tag]['state']-1.65-b**(k+1)*(phases[0]['before'][tag]['state']-1.65) for k in range(3)] for tag in ['low','mid','high']}
  drift=[phases[k+1]['before'][tag]['state']-phases[k]['rearmed'][tag]['state'] for k in range(2) for tag in ['low','mid','high']]
  cases.append({'report':rp.relative_to(ROOT).as_posix(),'seed':seed,'native_parent':'gf180_nf_state_update_localnodes','primary_measurements_verified':True,'update_period_us':5000,'between_update_hold_us':4987.5,'worst_between_update_hold_drift_v':max(map(abs,drift)),'frozen_aux_reference_v':d['frozen_auxiliary_reference_v'],'frozen_comparison_slope':b,'late_cumulative_residuals_v':residuals,'worst_late_cumulative_residual_v':max(abs(v) for vs in residuals.values() for v in vs)})
 result={'audit_completed':True,'cases':cases,'conclusion':'Extracted combined one-plate parent completes three actual5ms updates using frozen parent-specific common reference. Evaluate realizable trained-beta ratios and integrate complete neuron next. Static-bus/native-model hold is scoped evidence, not measured dielectric retention or population service.','scope':'Two15.015ms simulations at nominal27C, one mismatch seed with global variation disabled; capacitance extraction, ideal reference/data fixtures, external native inverter clocks. No RPEX, native sampled noise, MIM dielectric leakage, PVT/statistical yield, learned-beta inventory, model/fullPLIF/service/chip acceptance.','acceptance':{'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'audit_completed':True,'cases':cases},indent=2))
if __name__=='__main__':main()
