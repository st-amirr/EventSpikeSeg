"""Audit physical-parent complete-cycle data without claiming learned-beta acceptance."""
from pathlib import Path
import hashlib,json,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_coarse_beta_range_boundary.json';assert not out.exists();files={Path(__file__)};cases=[]
 for variant,source,seeds in [('_aux_three_mim','dcaa6a865525',[0]),('_sixplates','953036e66d84',[0])]:
  for mode,seed in [('baseline',0)]+[('check',x) for x in seeds]:
   rp=R/f'gf180_extracted_state_update{variant}_{mode}_seed{seed}_src{source}.json';d=json.loads(rp.read_text());files.add(rp);assert d['simulation_completed'] and d['simulator_returncode']==0
   for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n
   dp=rp.with_suffix('.dat');w=np.loadtxt(dp,skiprows=1);assert w.shape[1]==9 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-315e-6)<1e-12
   for key,v in d['measurements'].items():
    m=re.fullmatch(r'(low|mid|high)_c([0-2])_(state|aux)_(before|sharing|after|rearmed|late)',key);assert m
    tag,k,node,phase=m.groups();idx=1+2*['low','mid','high'].index(tag)+['state','aux'].index(node);t=100*int(k)+dict(before=19,sharing=20.45,after=21.5,rearmed=31.5,late=99.5)[phase];assert abs(v-np.interp(t*1e-6,w[:,0],w[:,idx]))<6e-6
   cases.append({'report':rp.relative_to(ROOT).as_posix(),'state_plates':6 if variant=='_sixplates' else 1,'auxiliary_MIMs':0 if variant=='_sixplates' else 3,'mode':mode,'seed':seed,'frozen_aux_reference_v':d['frozen_auxiliary_reference_v'],'observed_full_cycle_slope':d['first_complete_cycle_slope'],'frozen_comparator_slope':d['comparison_slope'],'worst_three_cycle_residual_v':d['worst_cumulative_residual_v'],'primary_measurements_verified':True})
 ip=R/'gf180_executed_float_beta_inventory.json';inv=json.loads(ip.read_text());assert inv['measurement_completed'];files.add(ip)
 for n,h in inv['sha256'].items():assert sha(ROOT/n)==h,n
 measured=[c['observed_full_cycle_slope'] for c in cases if c['mode']=='check'];assert min(measured)<inv['beta_min'] and max(measured)>inv['beta_max']
 result={'audit_completed':True,'cases':cases,'trained_beta_range':[inv['beta_min'],inv['beta_max']],'measured_nominal_endpoints_bracket_trained_range':True,'conclusion':'Actual one-state/three-auxMIM and six-state/no-extra-auxMIM parents bracket the full learned-beta range at nominal conditions. Frozen geometry-specific corrections checked at independent targets, residual0.108/0.590mV respectively. This proves two physical endpoint examples, not all1856 learned beta coefficients, interpolation, accuracy tolerance, yield or array service. Combine coarse MIM sizing and previously checked fine intermetal auxiliary increments; calibrate representative trained ratios next.','scope':'Four315us cases,3cycles at100us, extracted-cap parent, native external inverter clocks, ideal reference/data fixtures, nominal only. No resistance extraction, native sampled noise, dielectric leakage/PVT/yield, full PLIF/model/service/chip acceptance.','acceptance':{'learned_beta_coverage':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'audit_completed':True,'cases':cases},indent=2))
if __name__=='__main__':main()
