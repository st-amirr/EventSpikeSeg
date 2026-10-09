"""Audit physical time-gain feasibility, original coefficient targets and unresolved errors."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audited(p):
 r=json.loads(p.read_text(encoding='utf-8'))
 assert r.get('simulation_completed',True),str(p)
 for name,h in r.get('sha256',{}).items():assert sha(ROOT/name)==h,name
 return r

def main():
 cp=BASE/'gf180_local_gain_timing_calibration.json';c=audited(cp)
 packet=audited(BASE/'gf180_stem_float_packet_targets.json');gains=audited(BASE/'gf180_spatial_gain_candidates.json')
 for index,target in zip(c['actual_float_weight_indices_out_in_y_x'],c['base_model_state_voltage_increments_v']):
  value=packet['ideal_linear_state_voltage_increment_v_per_input_count']
  for i in index:value=value[i]
  assert value==target
 assert gains['tile_candidates']['8']['gains'][0][2][0][10]==16
 assert c['checkpoint_sha256']==packet['checkpoint_sha256']==gains['checkpoint_sha256']
 rows=[]
 for pattern in ['gf180_local_time_gain_injection_*_srcf34e45bfbef2.json','gf180_calibrated_local_gain_injection_*_srcffa4a1d7a2a4.json']:
  for p in sorted(BASE.glob(pattern)):
   r=audited(p);a=r['settings'];m=r['measurements'];steps=[m[f'eventstep_{i}'] for i in range(4)]
   row={'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'settings':a,'integrator_event_steps_uv':[x*1e6 for x in steps],'loaded_buffered_baseline_uv':m['buffered_before']*1e6,'loaded_buffered_final_uv':m['buffered_step_3']*1e6}
   if a.get('base_widths_us') and not a['no_events']:
    base_targets=c['base_model_state_voltage_increments_v'];order=[int(x) for x in a['cell_order'].split(',')];assert all(x in [0,1] for x in order);targets=[base_targets[x]*a['local_gain'] for x in order]
    row['original_float_target_steps_uv']=[x*1e6 for x in targets]
    row['signed_error_uv']=[(x-y)*1e6 for x,y in zip(steps,targets)]
    row['relative_error_percent']=[(x-y)/y*100 for x,y in zip(steps,targets)]
    row['max_abs_relative_error_percent']=max(abs(x) for x in row['relative_error_percent'])
   rows.append(row)
 noise=[]
 for p in sorted(BASE.glob('gf180_float_spatial_total_error_record*_srce9977f30e53b.json')):
  r=audited(p);index=r['record']['validation_record_index'];prior=audited(BASE/f'gf180_float_spatial_capped_gain_record{index}_srca7150f7125ac.json')
  assert r['results'][0]['prediction_sha256']==prior['results'][0]['prediction_sha256']
  assert r['input_sequence_sha256']==prior['input_sequence_sha256'] and r['target_sha256']==prior['target_sha256']
  noise.append({'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'record_index':index,'cases':[{k:x[k] for k in ['precision_policy','other_actor_candidate_error_sigma_uv','mean_iou','pixel_change_fraction']} for x in r['results']]})
 assert len(noise)==2 and len(rows)>=9
 out={'stage':'Fixed local analog scale: physical signed injection feasibility, before fullPLIF','circuit_diagnostics_completed':len(rows),'timing_calibration_report':cp.relative_to(ROOT).as_posix(),'timing_calibration_sha256':sha(cp),'cases':rows,'larger_error_replay_reports':noise,'new_model_forwards':8,'original_float_weights_checked':c['actual_float_weight_indices_out_in_y_x'],'scope':'Native extracted weight/program/steering/integrator/capture/PMOSreadout/clock modules schematic-connected together. Fixed local scale implemented by real pulse duration, not ideal voltage gain. Timing fit is external nominal metrology; ideal bench phase/program/reference drivers remain. Only two selected actual float coefficients, four signed packets at near-reset commonmode; no fullweight range, event multiplicity/service, beta/threshold/subtractive reset/adaptation/common-unit competition, retained-state reload or total sampled noise qualification. Zero-event trim uses previously fixed external reference, not autonomous calibration. Native MIM/transistor cards unchanged. No new combined layout. Noise sensitivity independent Gaussian surrogate, two same-sequence heldouts and one seed, not measured native errors or full accuracy.','findings':['Uncorrected16x timing produces about13.6x voltage increments due nonzero pulse response intercept. Nominal shared18.508ns timing offset changes actual switching commands and largely repairs gain.','Nominal original-float target packet accuracy does not transfer directly to mismatch seed29. Per-cell current/programming and timing calibration still required.','Fixed8x8 capped analog scale is insufficient by itself: hypothetical30uV and larger total error still substantially degrades inference. Preserve low-noise/calibration requirements; do not promote prior15uV sensitivity to achieved physical performance.'],'weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False}
 pp=BASE/'gf180_local_gain_programming_calibration.json'
 if pp.exists():
  programming=audited(pp);out['external_programming_calibration']={'report':pp.relative_to(ROOT).as_posix(),'sha256':sha(pp),'iterations':programming['iterations'],'autonomous_onchip_controller_implemented':False}
 p=BASE/'gf180_local_gain_physical_boundary.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(p),'circuit_diagnostics_completed':len(rows),'noise_replays':noise,'actual_weights':[{'settings':x['settings'],'error_percent':x.get('relative_error_percent')} for x in rows if 'original_float_target_steps_uv' in x]},indent=2))
if __name__=='__main__':main()
