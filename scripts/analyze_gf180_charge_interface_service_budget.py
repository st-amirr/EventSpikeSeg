"""Conditional current charge-interface storage/access budget, not a chip feasibility proof."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_charge_interface_service_budget.json';assert not out.exists();files={Path(__file__)}
 activity=next(BASE.glob('gf180_float_bin_activity_record8_src*.json'));a=json.loads(activity.read_text());assert a['measurement_completed'] and a['prior_baseline_reproduced'];files.add(activity)
 actors={name:v['destinations'] for name,v in a['activity'].items() if v['is_PLIF_population']};assert len(actors)==25 and sum(actors.values())==30976000
 for n,h in a['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 module=BASE/'gf180_memory_charge_sample_corrected_independent_isolate_repeated3_seed0_src8f7c9627040a.json';m=json.loads(module.read_text());assert m['simulation_completed'];files.add(module)
 coupling=m['coupling_unit_count'];states=sum(actors.values());adapt=10982400
 scenarios=[]
 for azbanks in [1,4]:
  # ReaderAZ9, restoreAZ9*banks, both feedback banks9 each, one compensation plate per OTA.
  units=coupling+9+9*azbanks+18+2;plate=49*units
  for access_us in [100,50,10,1]:
   lanes={n:math.ceil(count*access_us/5000) for n,count in actors.items()};total=sum(lanes.values())
   scenarios.append({'restore_AZ_banks':azbanks,'assumed_complete_state_access_us':access_us,'qualification':'Current100us accelerated cycle period, not demonstrated minimum' if access_us==100 else ('Current read25us+restore25us only; omits AZ/reset/access/commit overhead' if access_us==50 else 'Unqualified aggressive timing scenario'),'conditional_actor_lane_counts':lanes,'total_conditional_lanes':total,'bare_MIM_plate_um2_per_lane':plate,'bare_shared_lane_MIM_plate_mm2':total*plate/1e6,'membrane_plus_shared_lane_plate_mm2':states*25/1e6+total*plate/1e6})
 report={'status':'conditional_current_charge_interface_budget','resident_membranes':states,'adaptation_states':adapt,'one_minimum5um_MIM_per_membrane_mm2':states*25/1e6,'one_same_MIM_per_adaptation_amplitude_additional_mm2':adapt*25/1e6,'scenarios':scenarios,'decision':'Current characterization interface cannot be replicated without a much faster/scalable organization. Even optimistic shared-lane timing leaves substantial plate area, atop774.4mm2 membrane plates and hypothetical274.56mm2 adaptation plates. Capacitance growth must be justified jointly with service and storage organization before combined layout expansion. This diagnoses present organization, not impossibility of analog ASICs.','scope':'Assumes every logical membrane needs one complete shared-lane access per5ms bin; permanent populations retain separate lane allocations. Serial-access capacity only, no actual schedule, pipelining, compute, fan-in, threshold/beta/inhibition/adaptation/reference/routing/ADC/writeback or power overhead. Current circuits have100us characterization period; faster scenarios are hypothetical, not measured limits. Geometry sums bare nativeMIM areas, excludes transistors/routing/spacing and resident sense/switch periphery. No dense parent layout or technology-independent lower bound; alternative storage or organization may change the budget. Adaptation plate scenario is hypothetical and omitted from combined columns. No model/task acceptance established.','acceptance':{'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'scenarios':[{k:s[k] for k in ['restore_AZ_banks','assumed_complete_state_access_us','total_conditional_lanes','membrane_plus_shared_lane_plate_mm2']} for s in scenarios]},indent=2))
if __name__=='__main__':main()
