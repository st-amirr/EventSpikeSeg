"""Audit passive restoreAZ mechanism and preserve uncalibrated gain/area boundaries."""
import hashlib,json,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_charge_sample_autozero_boundary.json';assert not out.exists();files={Path(__file__)};cases=[];blocks=[]
 names=['gf180_charge_sample_autozero_seed29_srcfece8b6be183','gf180_charge_sample_restoreAZ4_seed29_src58b8f13a8d8b','gf180_charge_sample_restoreAZ4_seed0_src58b8f13a8d8b']
 for name in names:
  p=BASE/(name+'.json');d=json.loads(p.read_text());files.add(p);assert d['simulation_completed'] and d['simulator_returncode']==0 and len(d['measurements'])==54
  for n,h in d['sha256'].items():
   f=ROOT/n;assert sha(f)==h,n;files.add(f)
  rows=np.loadtxt(p.with_suffix('.dat'),skiprows=1);assert rows.shape[1]==28 and np.isfinite(rows).all() and rows[-1,0]>=315e-6-1e-12
  dump=BASE/(name+'_instances.txt');b=re.findall(r'BSIM4v5:.*?(?=\n\s*\n|\Z)',dump.read_text(),re.S);assert b and all('?????????' not in v for v in b);blocks.append(b)
  summary={}
  for i,tag in enumerate(['low','mid','high']):
   at=lambda t,c:float(np.interp(t*1e-6,rows[:,0],rows[:,c]));col=1+9*i
   reader_offset=lambda t:at(t,col+6)-at(t,col+2)
   restore_offset=lambda t:at(t,col+8)-at(t,col+7)
   summary[tag]={'reader_AZ_release_change_v':reader_offset(50.1)-reader_offset(49.9),'restore_AZ_release_change_v':restore_offset(59.92)-restore_offset(59.8),'restore_offset_change_release_to_read_v':restore_offset(84.5)-restore_offset(59.92),'first_access_error_v':at(114,col)-at(59,col),'third_cycle_drift_v':at(314,col)-at(59,col)}
  cases.append({'report':p.relative_to(ROOT).as_posix(),'settings':d['settings'],'phase_results':summary,'max_donor_measure_difference_v':d['maximum_donor_measure_difference_v']})
 assert cases[0]['max_donor_measure_difference_v']==0 and blocks[0]==blocks[1]
 budget=BASE/'gf180_charge_interface_service_budget.json';bd=json.loads(budget.read_text());assert bd['status']=='conditional_current_charge_interface_budget';files.add(budget)
 m=json.loads((BASE/(names[2]+'.json')).read_text())['measurements'];x0=m['low_c0_held'];x1=m['high_c0_held'];y0=m['low_c0_restored'];y1=m['high_c0_restored'];slope=(y1-y0)/(x1-x0)
 report={'status':'three_native_autozero_cases_and_conditional_budget_audited','cases':cases,'native_instance_comparison':'Baseline seed29 and restoreAZ4seed29 nativeMOS device/model/delvto/mulu0/l/w blocks identical at printed precision; extra passive native capacitance only.','conclusion':'Restore-only4banks reduce measured AZ release shift3.61..3.64mV to0.959..0.969mV. Reader unchanged. Existing coupling/reference calibration no longer applies; raw gain/state error is not accepted. Nominal4bank first-access endpoint slope measured for future calibration, not fitted/forced into state.','nominal4bank_first_access_slope':slope,'service_budget':budget.relative_to(ROOT).as_posix(),'system_decision':'Prioritize storage/access organization before more capacitor growth or combined layout. Current100us access period implies619520conditional lanes and5191.58/6011.20mm2 bare membrane+shared-lane plates for1/4AZbanks, excluding adaptation/periphery. Faster scenarios are unqualified, not physical limits. Examine exact event-free background state sharing and real access pipelining as reversible architecture research; do not substitute digital/quantized state or discard logical identities.','scope':'One mismatch seed; static mismatch is not sampled noise.3cycle100us accelerated access,40/49us holds,no5msretention. All parent/nativefractionalMIM connections schematic using qualified children. No recalibrated4bank accuracy, real references/phase, completePLIF/model/service/fullchip qualification. Area scenarios are architecture-specific plate sums,not general analog lowerbounds.','acceptance':{'readout':False,'original_float_accuracy':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'nominal4bank_first_access_slope':slope,'phase_results':[c['phase_results'] for c in cases]},indent=2))
if __name__=='__main__':main()
