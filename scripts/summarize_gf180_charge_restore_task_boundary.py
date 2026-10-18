"""Audit repeated native access and approximate original-float mean-transfer sensitivity."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_charge_restore_task_boundary.json';assert not out.exists();files={Path(__file__)};cases=[]
 repeated=BASE/'gf180_memory_charge_restore_repeated_boundary.json';r=json.loads(repeated.read_text());assert r['status']=='completed_two_native_three_cycle_comparisons';files.add(repeated)
 for n,h in r['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 for index in [8,64]:
  p=BASE/f'gf180_charge_restore_transfer_record{index}_src6810f522ac03.json';d=json.loads(p.read_text());files.add(p)
  assert d['simulation_completed'] and d['baseline_reproduced'] and not d['qat_or_quantized_reference_used']
  assert len(d['state_counts'])==25 and sum(d['state_counts'].values())==30976000
  assert [row['policy'] for row in d['results']]==['baseline','fixed_storage_range_zero_noise','measured_native_charge_restore']
  assert d['physical_storage_half_range_v']==.85 and min(d['transfer_input_levels_v'])<=.8 and max(d['transfer_input_levels_v'])>=2.5
  for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
  assert not any(d[k] for k in ['physical_storage_accepted','original_float_accuracy_accepted','complete_PLIF_accepted','full_5ms_population_service_accepted','full_chip_accepted'])
  cases.append({'record_index':index,'report':p.relative_to(ROOT).as_posix(),'mean_IoU_by_policy':{v['policy']:v['mean_iou'] for v in d['results']},'measured_transfer_pixel_change_fraction':d['results'][2]['pixel_change_fraction']})
 report={'status':'native_repeat_and_two_record_mean_transfer_replay_audited','repeated_native_access':{'report':repeated.relative_to(ROOT).as_posix(),'worst_three_cycle_drift_v':[c['worst_cumulative_drift_v'] for c in r['cases']]},'model_replays':cases,'checkpoint_sha256':d['checkpoint_sha256'],'scope':'Six original-float forwards on two same-sequence heldouts,records8/64 excluded from fixed range calibration0-7. Measured nominal held-to-restored transfer after every post-reset update, five interpolated levels, ideal+/-0.85V range conversion, no extrapolation. Baseline/input/target hashes reproduced. No native mismatch/noise/access schedule/history/5ms leakage or complete PLIF physical coverage. Native repeated access separately demonstrates persistent drift; two-record nominal IoU improvements cannot qualify mismatch or dataset-wide accuracy.','next_action':'Address or bound lane-dependent residual offset and release/disconnect error; measure representative native noise and evaluate its original-model effect before readout acceptance or array replication. A scoped reusable charge-interface layout can follow only with explicit circuit/noise and area/service coverage.','acceptance':{'readout':False,'original_float_accuracy':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'model_replays':cases},indent=2))
if __name__=='__main__':main()
