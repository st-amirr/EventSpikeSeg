"""Audit loop isolation, asymmetric native readout, nominal replay and mismatch/headroom boundary."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files={Path(__file__)}
 def verify(p):
  d=json.loads(p.read_text(encoding='utf-8'));files.add(p)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in d.get(key,{}).items():
    item=p.parent/n if key=='sha256' and not n.startswith(('artifacts/','scripts/','docs/','src/')) else ROOT/n
    assert sha(item)==h,str(item)
    files.add(item)
  return d
 baseline=verify(BASE/'results/gf180_readout_baseline_waveform_validation.json');assert baseline['audit_completed'] and baseline['simulation_completed']
 isolation=[]
 for p in sorted((BASE/'results').glob('gf180_readout_loop_isolation_*.json')):
  d=verify(p);assert d['simulation_completed']
  isolation.append({'report':p.relative_to(ROOT).as_posix(),'ideal_debug_node':d['ideal_debug_node'],'windows':d['windows']})
 assert len(isolation)==2
 qp=BASE/'layout/gf180_regulated_current_readout_clamp4/qualification.json';q=verify(qp);aq=verify(qp.parent/'abstract_qualification.json')
 assert q['native_mim_count']==5 and q['mos_count']==25 and q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
 cases=[];mismatch=[]
 for pattern in ['gf180_writer_memory_readout_clamp4_*.json','gf180_writer_memory_readout_mismatch_localization_*.json','gf180_writer_memory_readout_headroom020_*.json']:
  for p in sorted((BASE/'results').glob(pattern)):
   d=verify(p)
   if not d['simulation_completed']:
    row={'report':p.relative_to(ROOT).as_posix(),'simulation_completed':False,'simulator_returncode':d['simulator_returncode'],'mismatch_seed':d.get('mismatch_seed'),'column_reference_v':d.get('column_reference_v',.01),'scope':'Incomplete bounded transient; no final measurements or improvement conclusion'}
    cases.append(row);mismatch.append(row);continue
   m=d['measurements'];target=d['target_levels_v']
   row={'report':p.relative_to(ROOT).as_posix(),'target_levels_v':target,'mismatch_seed':d.get('mismatch_seed'),'column_reference_v':d.get('column_reference_v',.01),'max_late_decode_target_error_v':max(abs(m[n+'_decoded_late']-v) for n,v in target.items()),'max_persistent_read_error_v':max(abs(m[n+'_read_error']) for n in target),'printed_max_late_window_v':max(m[n+'_decoded_window_max']-m[n+'_decoded_window_min'] for n in target),'decoded_levels_v':{n:m[n+'_decoded_late'] for n in target},'held_levels_v':{n:m[n+'_state_held'] for n in target}}
   if all(n+'_replica_column_v' in m for n in target):row['column_pairs_v']={n:[m[n+'_column_v'],m[n+'_replica_column_v']] for n in target}
   cases.append(row)
   if d.get('mismatch_seed') is not None:mismatch.append(row)
 assert len(cases)==5 and len(mismatch)==3
 static_paths=list((BASE/'results').glob('gf180_readout_headroom020_static_src*.json'));assert len(static_paths)==1
 static=verify(static_paths[0]);assert static['simulation_completed'] and len(static['points'])==13
 replays=[]
 for p in sorted((BASE/'results').glob('gf180_asymmetric_memory_transfer_record*_src*.json')):
  d=verify(p);assert d['simulation_completed'] and d['baseline_reproduced'] and not d['qat_or_quantized_reference_used'];assert len(d['state_counts'])==25 and sum(d['state_counts'].values())==30976000
  replays.append({'report':p.relative_to(ROOT).as_posix(),'record_index':d['record_index'],'results':[{k:r[k] for k in ['policy','mean_iou','pixel_change_fraction','prediction_sha256']} for r in d['results']]})
 assert len(replays)==2
 report={'audit_completed':True,'baseline_waveform_validation':baseline['raw_report'],'diagnostic_isolations':isolation,'native_cases':cases,'nominal_original_float_replays':replays,'headroom_static_diagnostic':{'report':static_paths[0].relative_to(ROOT).as_posix(),'mid_decode_minus_state_v':static['points'][0]['v(decoded_mid)']-static['points'][0]['v(state_mid)'],'high_decode_minus_state_v':static['points'][0]['v(decoded_high)']-static['points'][0]['v(state_high)'],'scope':static['scope']},'physical_module':{'cell':q['cell'],'mos_count':q['mos_count'],'native_mim_count':q['native_mim_count'],'size_um':aq['size_um'],'ports':len(aq['ports'])},
 'decision':'Select asymmetric compensation for nominal readout exploration: clamp-loop isolation explains low-state variation, while inverse retains one compensation capacitor for speed. Nominal late-window equality is printed resolution only. One native mismatch seed rejects robust uncalibrated readout at10mV; 200mV transient is incomplete at120s bound. Its static diagnosis completes with residual roughly-95mV/+117mV read errors on two lanes; stable/transient improvement is unproven. Next compare native offset cancellation and calibrated/same-device current transfer; a reference increase alone does not establish robustness. Do not replicate the uncalibrated nominal reader.',
 'scope':'Baseline waveform postprocessor rounding error independently validated without rerun or altering prior report. Ideal frozen mirror/decoder nodes are diagnostic only, never proposed hardware. New actual readout layout DRC/LVS/GDS/LEF qualified, writer-memory connection schematic. Two nominal extracted-transfer model replays from one sequence use ideal tiled conversion, no random noise or mismatch, ideal other PLIF operations; IoU improvement does not establish dataset accuracy. Selected native local-mismatch seed is not statistical distribution/yield. External reference/bias/timing, cap-only extraction, unqualified leakage/noise/PVT and25us diagnostic read, no full5ms population service.',
 'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 p=BASE/'results/gf180_asymmetric_readout_mismatch_boundary.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':str(p),'native_cases':len(cases),'nominal_replays':replays,'mismatch_cases':mismatch},indent=2))
if __name__=='__main__':main()
