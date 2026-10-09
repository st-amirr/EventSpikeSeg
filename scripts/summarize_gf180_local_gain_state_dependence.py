"""Audit the stored-state challenge without promoting incomplete simulations."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audited(p):
 r=json.loads(p.read_text(encoding='utf-8'))
 for name,h in r.get('sha256',{}).items():assert sha(ROOT/name)==h,name
 return r

def main():
 c=audited(BASE/'gf180_local_gain_timing_calibration.json');targets=c['base_model_state_voltage_increments_v']*2;targets=[x*16 for x in targets]
 rows=[]
 for pattern in ['gf180_preloaded_local_gain_injection_*_src7a626b5e4426.json','gf180_balanced_steering_local_gain_*_src107cdc3def11.json','gf180_balanced_steering_finite_reference_*_src21871aa25e37.json']:
  for p in sorted(BASE.glob(pattern)):
   r=audited(p);a=r['settings'];m=r['measurements'];lp=next(ROOT/name for name in r['sha256'] if name.endswith('.log'));log=lp.read_text(encoding='utf-8')
   row={'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'settings':a,'completed':r['simulation_completed'],'returncode':r['simulator_returncode'],'failure_class':None if r['simulation_completed'] else ('bounded_timeout' if r['simulator_returncode']==124 else 'transient_abort_or_missing_measurements'),'abort_lines':re.findall(r'(?m)^.*(?:Timestep too small|tran simulation.*aborted).*$',log),'initial_differential_state_v':m.get('signal_before'),'initial_sum_w_v':m.get('sum_w_before'),'initial_sum_r_v':m.get('sum_r_before'),'buffered_baseline_uv':m.get('buffered_before',0)*1e6}
   if r['simulation_completed'] and not a['no_events']:
    steps=[m[f'eventstep_{i}'] for i in range(4)];row.update({'actual_packet_steps_uv':[x*1e6 for x in steps],'target_packet_steps_uv':[x*1e6 for x in targets],'packet_relative_error_percent':[(x-y)/y*100 for x,y in zip(steps,targets)]})
   else:row['partial_measurements_diagnostic_only']=m
   rows.append(row)
 assert len(rows)==11 and sum(x['completed'] for x in rows)==3
 qdir=ROOT/'artifacts/analog_asic/layout/gf180_fixed_body_tg_fullroute_quarter';qp=qdir/'qualification.json';q=json.loads(qp.read_text(encoding='utf-8'))
 assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for name,h in q.get(key,{}).items():assert sha(qdir/name if key=='sha256' else ROOT/name)==h,name
 software=[]
 for p in sorted(BASE.glob('gf180_float_spatial_stem_error_record*_srce512e5e711fa.json')):
  r=audited(p);assert r['simulation_completed'];index=r['record']['validation_record_index']
  prior=audited(BASE/f'gf180_float_spatial_capped_gain_record{index}_srca7150f7125ac.json')
  assert r['results'][0]['prediction_sha256']==prior['results'][0]['prediction_sha256']
  control=next(x for x in r['results'] if x['stem_candidate_error_sigma_uv']==15)
  previous=next(x for x in prior['results'] if x['precision_policy']=='tile8_all15' and x['other_actor_candidate_error_sigma_uv']==15)
  assert control['prediction_sha256']==previous['prediction_sha256']
  assert r['input_sequence_sha256']==prior['input_sequence_sha256'] and r['target_sha256']==prior['target_sha256']
  # Preserve inherited prose and correct ONLY descriptive metadata to match audited code and row parameters.
  if 'scope_metadata_correction' not in r:
   recovery=BASE/'report_recovery';recovery.mkdir(exist_ok=True);original=recovery/p.name;assert not original.exists();original.write_bytes(p.read_bytes())
   r['scope_metadata_correction']={'reason':'Derived generator inherited contradictory legacy3uV/15uV prose; numerical implementation and explicit row sigmas are unchanged. Corrected description after terminal run; original JSON retained.','original_report':original.relative_to(ROOT).as_posix(),'original_report_sha256':sha(original)}
   r['scope']='Original float epoch58 checkpoint, fixed8x8 gain-capped stem ranges from independent calibration, unchanged model equations/QAToff. Each row specifies stem sigma; other24actors15uV in noisy cases. Independent Gaussian error before candidate threshold/reset plus ideal counted candidate/poststate clipping; no target range fitting. Baseline unclipped. Requested15/30/60uV are hypothetical errors, not native measured noise. One seed, two heldouts of same sequence, not full validation. No physical reference/gain/noise/PLIF/service/area/chip acceptance.'
   r['sha256'][original.relative_to(ROOT).as_posix()]=sha(original);p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');audited(p)
  software.append({'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'record_index':index,'cases':[{k:x[k] for k in ['stem_candidate_error_sigma_uv','other_actor_candidate_error_sigma_uv','mean_iou','pixel_change_fraction']} for x in r['results']]})
 assert len(software)==2
 aqp=qdir/'abstract_qualification.json';aq=audited(aqp);assert aq['physical_ports_and_size_verified'] and aq['all_rectangles_within_abstract_boundary']
 out={'stage':'State-dependent injection failure localized; interface regulation method change required','circuits':rows,'circuit_case_count':11,'completed_cases':3,'incomplete_cases':8,'new_native_cell':{'qualification':qp.relative_to(ROOT).as_posix(),'sha256':sha(qp),'cell':q['cell'],'widths_um':[q['nf_width_um'],q['pf_width_um']],'drc_full':0,'lvs_unique':True,'gds_readback_drc_full':0,'gds_readback_lvs_unique':True,'capacitance_extracted':True,'assembled_steering_selected':False,'lef_abstract_qualification':aqp.relative_to(ROOT).as_posix(),'lef_abstract_qualification_sha256':sha(aqp),'lef_size_um':aq['size_um']},'isolated_stem_error_replays':software,'new_model_forwards':8,'findings':['Actual preload writers establish approximately+90/-91mV differential state rather than exact requested+/-100mV; incomplete preload transfer remains unqualified.','Frozen near-reset gate programming does not preserve packet accuracy at nonzero state. Uncompensated negative-state completed case and compensated positive-state completed case both have large errors.','Quarter-width opposite-phase SUM dummy is not selected: no demonstrated complete multi-state precision improvement; numerical aborts retained separately from physical errors.','Other24actor noise also matters: holding them15uV while stem30/60uV gives substantially better IoU than raising all25actor errors. This is conditional one-seed/same-sequence evidence, not additive error decomposition or accepted tolerance.'],'next_method':'Diagnose and strengthen physical summing-node/current-compliance regulation, using separately qualified native components and preserving original float operations. Do not propagate near-reset per-cell calibration or multiply parallel OTAs solely from stationary noise. Resolve preload/interface errors and total sampled noise before layout replication.','scope':'Cap-extracted native components combined schematically; physical state writers release before events. Static native mismatchseed29 only; no transient random-noise/PVT/5ms/gate leakage/RPEX or combined assembly qualification. Finite-reference variant resistor has standalone DRC/LVS/cap extraction but lacks GDS-readback evidence. Three earlier preflight launches rejected missing optional GDS schema before simulations; not included in11cases.','weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False}
 p=BASE/'gf180_local_gain_state_dependence_boundary.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(p),'complete':3,'incomplete':8,'software':software,'completed_circuits':[x for x in rows if x['completed']]},indent=2))
if __name__=='__main__':main()
