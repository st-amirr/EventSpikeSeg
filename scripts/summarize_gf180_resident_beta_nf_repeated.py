"""Audit NF full-cycle repeated update including auxiliary recharge, and predict common reference."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_resident_beta_nf_repeated_boundary.json';assert not out.exists();files={Path(__file__)};cases=[]
 oldp=R/'gf180_resident_beta_nf_terminal_storage_boundary.json';old=json.loads(oldp.read_text());files.add(oldp)
 for seed,n in [(0,1),(29,1),(0,2)]:
  rp=R/f'gf180_resident_beta_nf_repeated3_seed{seed}_plates{n}_srcf1815ab6f841.json';d=json.loads(rp.read_text());files.add(rp);assert d['simulation_completed'] and d['simulator_returncode']==0
  for name,h in d['sha256'].items():assert sha(ROOT/name)==h,name
  donor=R/f'gf180_resident_beta_nf_corrected_seed{seed}_on_plates{n}_src04f3c11b868c.json';don=json.loads(donor.read_text());files.add(donor)
  dp=rp.with_suffix('.dat');files.add(dp);w=np.loadtxt(dp,skiprows=1);assert w.shape[1]==9 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-315e-6)<1e-12
  phases=[]
  for k in range(3):
   ph={label:{tag:{node:float(np.interp((100*k+t)*1e-6,w[:,0],w[:,1+2*i+j])) for j,node in enumerate(['state','aux'])} for i,tag in enumerate(['low','mid','high'])} for label,t in [('before',19),('sharing',20.45),('after',21.5),('rearmed',31.5),('late',99.5)]}
   for label,states in ph.items():
    for tag,nodes in states.items():
     for node,v in nodes.items():
      assert abs(v-d['measurements'][f'{tag}_c{k}_{node}_{label}'])<6e-6
      if k==0 and label in ['before','sharing','after']:assert abs(v-don['measurements'][f'{tag}_{node}_{"held" if label=="before" else label}'])<6e-6
   phases.append(ph)
  x=np.array([phases[0]['before'][t]['state'] for t in ['low','mid','high']]);y=np.array([phases[0]['rearmed'][t]['state'] for t in ['low','mid','high']]);b=float((y[2]-y[0])/(x[2]-x[0]));offset=float(y[0]-1.65-b*(x[0]-1.65));prev=next(c['endpoint_slope'] for c in old['cases'] if c['mode']=='on' and c['state_plates']==n)
  cycles=[]
  for k,ph in enumerate(phases):
   lanes={}
   for i,t in enumerate(['low','mid','high']):
    before=ph['before'][t]['state'];after=ph['after'][t]['state'];rearmed=ph['rearmed'][t]['state'];late=ph['late'][t]['state']
    lanes[t]={'before_v':before,'after_v':after,'rearmed_v':rearmed,'rearm_shift_v':rearmed-after,'full_cycle_residual_v':rearmed-1.65-b*(before-1.65),'cumulative_residual_vs_full_cycle_slope_v':late-1.65-b**(k+1)*(x[i]-1.65),'cumulative_residual_vs_earlier_partial_slope_v':late-1.65-prev**(k+1)*(x[i]-1.65)}
   cycles.append({'cycle':k,'lanes':lanes})
  cases.append({'report':rp.relative_to(ROOT).as_posix(),'seed':seed,'state_plates':n,'first_cycle_donor_measures_match':True,'first_complete_cycle_slope':b,'first_complete_cycle_endpoint_offset_v':offset,'first_complete_cycle_midpoint_nonlinearity_v':float(y[1]-y[0]-b*(x[1]-x[0])),'cycles':cycles,'frozen_aux_reference_v':d['frozen_auxiliary_reference_v']})
 base=cases[0];prediction=base['frozen_aux_reference_v']-base['first_complete_cycle_endpoint_offset_v']/(1-base['first_complete_cycle_slope'])
 result={'audit_completed':True,'cases':cases,'predicted_full_cycle_aux_reference_v':prediction,'reference_prediction_scope':'One common correction from nominal1plate first complete-cycle endpoints, using assumed charge-sharing reference sensitivity1-beta. Not yet independently run; no per-lane or numerical state correction.','conclusion':'Auxiliary recharge has state-dependent backaction and changes effective beta. Single-cycle postrelease errors exclude this required phase. Define commit after recharge, fit full-cycle ratios and test common reference before integrated neuron layout.','scope':'Three accelerated315us cases,3updates at100us period, native qualified child connections schematic. Static buses, external references/clocks, native mismatch seed29 only. No full5ms retention, native noise/dielectric leakage/PVT/yield/model or population service acceptance.','acceptance':{'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'predicted_aux_reference_v':prediction,'cases':[{'seed':c['seed'],'state_plates':c['state_plates'],'full_cycle_beta':c['first_complete_cycle_slope'],'offset_v':c['first_complete_cycle_endpoint_offset_v'],'worst_rearm_shift_v':max(abs(v['rearm_shift_v']) for row in c['cycles'] for v in row['lanes'].values()),'worst_cumulative_error_vs_full_cycle_slope_v':max(abs(v['cumulative_residual_vs_full_cycle_slope_v']) for row in c['cycles'] for v in row['lanes'].values())} for c in cases]},indent=2))
if __name__=='__main__':main()
