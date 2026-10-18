"""Audit bounded calibration, actual-activity replay and overlap comparison."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 r=json.loads(p.read_text(encoding='utf-8'))
 for name,h in r.get('sha256',{}).items():assert sha(ROOT/name)==h,name
 return r
def main():
 cp=BASE/'gf180_fourbank_parking_programming_calibration.json';c=read(cp);assert c['calibration_completed'];fit=c['iterations'][-1];fitted=read(ROOT/fit['report'])
 model=[]
 for index in [8,64]:
  p=BASE/f'replay_gf180_packet_state_bias_record{index}_srcfc94fbe1c2da.json';r=read(p);assert r['simulation_completed']
  prior=read(BASE/f'gf180_float_spatial_stem_error_record{index}_srce512e5e711fa.json')
  assert r['results'][0]['prediction_sha256']==prior['results'][0]['prediction_sha256']
  assert r['input_sequence_sha256']==prior['input_sequence_sha256'] and r['target_sha256']==prior['target_sha256']
  total=sum(a['weighted_event_deliveries'] for a in r['results'][0]['activity'].values())
  model.append({'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'record_index':index,'selected_state_coefficient':r['selected_coefficient'],'baseline_hashes_reproduced':True,'cases':[{k:x[k] for k in ['policy','mean_iou','pixel_change_fraction']} for x in r['results']],'baseline_weighted_deliveries_over50ms':total,'illustrative_serial_lane_equivalents_at1us_per_delivery':total/50000,'scope':r['scope']})
 frozen=[]
 for p in BASE.glob('gf180_autozero_tracking_park_fourbank_*_srcea4d8d629b44.json'):
  r=read(p);a=r['settings']
  if [float(v) for v in a['pf_program_levels'].split(',')][:2]!=fit['program_v']:continue
  x={'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'completed':r['simulation_completed'],'preload_v':a['preload_differential_v'],'no_events':a['no_events'],'returncode':r['simulator_returncode']}
  if r['simulation_completed'] and a['no_events']:x['zero_event_state_change_uv']=r['measurements']['signal_delta']*1e6
  elif r['simulation_completed']:x['packet_target_errors_uv']=[r['measurements'][f'eventstep_{i}']*1e6-fit['targets_uv'][i%2] for i in range(4)]
  else:x['partial_measurements_diagnostic_only']=r['measurements']
  frozen.append(x)
 overlap=[]
 for p in sorted([*BASE.glob('gf180_parallel_tracking_packet_*.json'),*BASE.glob('gf180_staggered_tracking_packet_*.json')]):
  r=read(p);x={'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'completed':r['simulation_completed'],'returncode':r['simulator_returncode'],'turnon_stagger_ns':100 if 'staggered' in p.name else 0}
  if r['simulation_completed']:
   m=r['measurements'];serial=fitted['measurements'];x.update({'parallel_total_increment_uv':m['signal_delta']*1e6,'serial_total_increment_uv':serial['signal_delta']*1e6,'parallel_minus_serial_uv':(m['signal_delta']-serial['signal_delta'])*1e6,'group_steps_uv':[m[f'eventstep_{i}']*1e6 for i in range(4)],'idle_tail_uv':m['signal_tail']*1e6,'common_mode_before_v':(m['out_w_before']+m['out_r_before'])/2,'common_mode_after_v':(m['out_w_event']+m['out_r_event'])/2})
  overlap.append(x)
 out={'stage':'Four-bank fit and actual-activity bias replay complete; service architecture requires parallelism','calibration':{'report':cp.relative_to(ROOT).as_posix(),'sha256':sha(cp),'fit':fit,'scope':c['scope']},'frozen_circuit_cases':frozen,'model_replays':model,'overlapping_packet_cases':overlap,'new_completed_model_forwards':6,'failed_initial_replay':'See gf180_packet_state_bias_failed_src*.json; baseline-only failure retained, inference-mode reset fixed before successful replay.','interpretation':['Selected cumulative state-bias approximation causes little IoU change on two same-sequence heldouts; this does not qualify native noise, all weights or exact event ordering.','Real connectivity/activity yields billions of weighted deliveries over50ms. Illustrative one-packet-per-lane serial arithmetic motivates shared fanout/parallel analog summation; it is not a fundamental lower bound if contributions combine or execute concurrently.','Per-bin peak load, lane area, state storage, weight/reference distribution, common-mode charge, read/restore and commit overhead must be included before population service acceptance.','Calibration is external metrology; frozen negative-state aborted and its partial measurements cannot qualify range accuracy.'],'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'combined_layout_qualified':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False}
 p=BASE/'gf180_fourbank_bias_service_boundary.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(p),'models':model,'overlap':overlap},indent=2))
if __name__=='__main__':main()
