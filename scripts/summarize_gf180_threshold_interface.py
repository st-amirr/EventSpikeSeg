"""Audit compact native threshold development; retain failed offsets/loading and scope limits."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_threshold_interface_boundary.json';assert not out.exists();files={Path(__file__)};cases=[]
 names=[f'gf180_compact_threshold_dc_seed{s}_src3eb187b3160f.json' for s in [0,29]]+['gf180_state_threshold_loading_src47d21447abfd.json']+[f'gf180_compact_threshold_autozero_seed{s}_src43f5dfca2591.json' for s in [0,29]]+['gf180_compact_threshold_autozero_dummy_seed0_src9e1e21628abc.json']+[f'gf180_compact_threshold_autozero_dummy_slow_seed{s}_srcdb82e6902531.json' for s in [0,29]]+['gf180_state_threshold_autozero_loading_srccc7d4a7b5d30.json']
 for name in names:
  rp=R/name;d=json.loads(rp.read_text());assert d['simulation_completed'] and d['simulator_returncode']==0;files.add(rp)
  for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n
  w=np.loadtxt(rp.with_suffix('.dat'),skiprows=1);assert w.ndim==2 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0)
  record={'report':rp.relative_to(ROOT).as_posix(),'primary_trace_finite':True}
  if 'trip_input_v' in d:
   dc='_dc_' in name;slow='_slow_' in name;v=w if dc else w[(w[:,0]>=8e-6)&(w[:,0]<=(108e-6 if slow else 18e-6))];cross=np.where((v[:-1,3]<1.65)&(v[1:,3]>=1.65))[0];assert len(cross)==d['rising_logic_crossings']==1;i=int(cross[0]);trip=float(v[i,1]+(1.65-v[i,3])*(v[i+1,1]-v[i,1])/(v[i+1,3]-v[i,3]));assert abs(trip-d['trip_input_v'])<1e-12;record.update(seed=d['seed'],trip_offset_v=trip-1.85)
   if not dc:
    assert abs(w[-1,0]-(110e-6 if slow else 20e-6))<1e-12;after=w[w[:,0]>=1e-6,5];record.update(autozero_release_shift_v=d['autozero_release_reference_shift_v'],startup_reference_peak_v=float(np.max(w[:,5])),after1us_reference_range_v=[float(np.min(after)),float(np.max(after))],early_scan_logic_high_transient_present=bool(v[0,3]>1.65))
  else:
   assert abs(w[-1,0]-50e-6)<1e-12;record.update(sensing_logic_v=d['sensing_logic_v'],worst_loaded_minus_bare_commit_v=max(abs(row['commit']) for row in d['loaded_minus_bare_by_phase_v'].values()))
  cases.append(record)
 ip=R/'gf180_float_threshold_voltage_inventory.json';inv=json.loads(ip.read_text());assert inv['measurement_completed'];files.add(ip)
 for n,h in inv['sha256'].items():assert sha(ROOT/n)==h,n
 result={'audit_completed':True,'cases':cases,'actual_threshold_offset_range_v':[inv['base_threshold_offset_v_min'],inv['base_threshold_offset_v_max']],'conclusion':'Two compact comparator cores physically checked. Uncorrected detector9.5/27.5mV DC offset and gated-bias state disturbance4.64mV fail direct-use precision. Shielded native startup autozero+NFdummy cancels release; slow1mV/us rising trip errors-0.363/+0.143mV nominal/seed29, with early transient and initialization overshoot retained. Continuously biased resident setup gives clear wide-margin decisions and stable late state; changed beta loading up to1.503mV needs combined qualification. Trained fixed-range thresholds can be as small as7.8uV, so component1.85V fixture is not trained-threshold acceptance. Evaluate original-model range compression before more comparator geometry.','scope':'Nine bounded completed native cases; extracted children, schematic autozero/combined parents. Seed variants across changed topology are not matched per-device causal controls. Rising ramps only, dynamic lag/hysteresis/settling/noise remain open. UIC stored reference overshoots supply at50ps; no startup/headroom qualification. No50ms reference retention, gated power/service, native noise/RPEX/PVT/yield, subtractive reset, full PLIF/model/chip acceptance.','acceptance':{'threshold_interface':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'audit_completed':True,'cases':len(cases),'threshold_range_v':result['actual_threshold_offset_range_v']},indent=2))
if __name__=='__main__':main()
