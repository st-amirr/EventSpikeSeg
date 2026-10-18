"""Audit native sample isolation, distinguishing disconnect from restore-bus backaction."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_memory_charge_sample_boundary.json';assert not out.exists();files={Path(__file__)};cases=[]
 names=['gf180_memory_charge_sample_always_on_repeated3_seed0_src988c1868703c','gf180_memory_charge_sample_isolate_repeated3_seed0_src988c1868703c','gf180_memory_charge_sample_corrected_independent_isolate_repeated3_seed0_src8f7c9627040a','gf180_memory_charge_sample_corrected_independent_isolate_repeated3_seed29_src8f7c9627040a']
 for name in names:
  p=BASE/(name+'.json');d=json.loads(p.read_text());files.add(p);assert d['simulation_completed'] and d['simulator_returncode']==0 and len(d['measurements'])==54
  for n,h in d['sha256'].items():
   f=ROOT/n;assert sha(f)==h,n;files.add(f)
  wave=p.with_suffix('.dat');assert wave.relative_to(ROOT).as_posix() in d['sha256'];a=np.loadtxt(wave,skiprows=1)
  assert a.shape[1]==19 and np.isfinite(a).all() and a[-1,0]>=315e-6-1e-12 and np.all(np.diff(a[:,0])>=0)
  phases={};hist={}
  for i,tag in enumerate(['low','mid','high']):
   at=lambda t,c:float(np.interp(t*1e-6,a[:,0],a[:,c]));state=1+6*i;restore=state+4
   phases[tag]={'sample_disconnect_window_v':at(85.03,restore)-at(84.5,restore),'restore_bus_actuation_window_v':at(109.5,restore)-at(85.03,restore),'state_release_window_v':at(114,state)-at(109.5,state)}
   hist[tag]=[];initial=at(59,state)
   for k in range(3):
    held=at(100*k+59,state);restored=at(100*k+114,state);assert abs(restored-d['measurements'][f'{tag}_c{k}_restored'])<1e-5
    hist[tag].append({'cycle':k,'held_v':held,'restored_v':restored,'access_error_v':restored-held,'cumulative_change_v':restored-initial})
  cases.append({'report':p.relative_to(ROOT).as_posix(),'settings':d['settings'],'frozen_reference_v':d['frozen_reference_v'],'coupling_units':d['coupling_unit_count'],'histories':hist,'first_cycle_phase_windows':phases,'worst_access_error_v':max(abs(r['access_error_v']) for v in hist.values() for r in v),'worst_three_cycle_drift_v':max(abs(v[-1]['cumulative_change_v']) for v in hist.values())})
 assert cases[0]['frozen_reference_v']==cases[1]['frozen_reference_v'] and cases[0]['coupling_units']==cases[1]['coupling_units']
 assert cases[2]['frozen_reference_v']==cases[3]['frozen_reference_v'] and cases[2]['coupling_units']==cases[3]['coupling_units']
 report={'status':'four_native_three_cycle_cases_audited','cases':cases,'mechanism':'Most prior restore-output movement occurs during restore-bus actuation after85.04us, not directly at reader disconnect85us. Same-device nominal always-on/isolate pair reduces that later shift22.55..34.92mV to1.57..1.66mV, while sampling introduces4.60..4.77mV earlier shift. Existing calibration does not transfer: uncorrected isolate drifts110mV.','calibration':'One common measured endpoint ratio/reference prediction from1.2/2.1V targets. Native corrected circuit uses107full7umMIMs plus one5x5umplate and external1.329442295V reference. New independent1.05/1.65/2.25V levels, no per-lane/state arithmetic correction. Nominal worst1.21mV/access,3.62mV three-cycle drift; seed29 worst4.63mV/access,13.88mV three-cycle drift. Different levels/hierarchy prevent a matched numerical improvement claim over older unsampled reader mismatch.','next_action':'Retain native sample isolation as a candidate; diagnose residual autozero/release offset and representative sampled noise before combined layout or another task replay. Check whether larger native autozero storage reduces lane-dependent offset with one matched mechanism comparison; include ratio/reference response rather than blindly repeating calibration.','scope':'Schematic parent/fractional MIM and external references/bias/clocks, qualified extracted child views,100us access period,40/49us hold, no5ms retention or population service. One selected mismatch seed,notyield/noise. Prior nominal model replay belongs to earlier circuit and cannot qualify this changed interface.','acceptance':{'readout':False,'original_float_accuracy':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'case_worst_access_and_drift_v':[(c['worst_access_error_v'],c['worst_three_cycle_drift_v']) for c in cases]}))
if __name__=='__main__':main()
