"""Audit static inverse and shared-mode trajectories; no SNN/chip acceptance."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized_settings(settings):
 result=dict(settings)
 for name,value in [('physical_current_reference',False),('reference_filter_mim_count',0),('cold_start_prelude_us',0),('feedback_release_advance_ns',0),('capture_dummy_nf_width_um',None),('capture_dummy_pf_width_um',None),('tight_charge_solver',False),('refined_charge_solver',False),('physical_beta_driver',False),('physical_park_driver',False),('physical_mode_drivers',False),('mode_driver_output_buffers',False),('integrator_route_dummy_count',1)]:result.setdefault(name,value)
 return result

def main():
 sources={Path(__file__)};cases=[]
 for pattern,script in [('gf180_physical_encoder_inverse_*.json','screen_gf180_physical_encoder_inverse.py'),('gf180_shared_encoder_inverse_*.json','screen_gf180_shared_encoder_inverse.py')]:
  for path in sorted((BASE/'results').glob(pattern)):
   r=json.loads(path.read_text());snapshot=ROOT/r['source_snapshot']
   if digest(snapshot)!=r['sha256']['scripts/'+script]:raise ValueError('Executable snapshot mismatch: '+str(path))
   sources.update([path,snapshot])
   for name,expected in r['sha256'].items():
    if name=='scripts/'+script:continue
    input_path=ROOT/name
    if digest(input_path)!=expected:raise ValueError('Input provenance mismatch: '+name)
    sources.add(input_path)
   for q in r['qualified_layout_components']:
    for name,expected in q['sha256'].items():
     view=BASE/'layout'/q['cell']/name
     if digest(view)!=expected:raise ValueError('Layout provenance mismatch: '+str(view))
     sources.add(view)
   logfile=path.with_suffix('.log');failure=None
   if not r['simulation_completed']:
    log=logfile.read_text()
    failure='bounded_timeout' if r['simulator_returncode']==124 else ('operating_point_failure' if re.search('Transient op failed|Finding the operating point for transient simulation failed',log,re.I) else ('transient_abort' if re.search('tran simulation\(s\) aborted',log,re.I) else 'incomplete_measurements_or_other_error'))
   ripple=max((max(x['imax'],x['decoded'])-min(x['imin'],x['decoded']))*1e9 for x in r.get('rows',[]) if 'decoded' in x) if any('decoded' in x for x in r.get('rows',[])) else None
   near_zero={}
   if r.get('simulation_completed') and r['command_arguments'].get('current_set') in ['near-zero','near-zero-short']:
    zeros=[x for x in r['rows'] if x['input_current_na']==0];offset=zeros[0]['current_error_na']
    near_zero={'first_zero_offset_pa':offset*1000,'maximum_zero_corrected_current_error_pa':max(abs(x['current_error_na']-offset)*1000 for x in r['rows']),'zero_repeat_difference_pa':(zeros[-1]['current_error_na']-offset)*1000,'scope':'Analysis-only zero subtraction, no implemented correction circuit or sampled-noise acceptance.'}
   cases.append({'decoded_current_metric_scope':'Late post-pulse park current, not delivered-beta charge error' if r.get('learned_beta_metadata') else 'Late decode current','learned_beta_metadata':r.get('learned_beta_metadata'),'delivered_charge_rows':[{'input_current_na':x['input_current_na'],'held_encoder_pre_v':x.get('encpre'),'held_encoder_post_v':x.get('encpost'),'feedback_release_pre_v':x.get('feedbackpre'),'capture_pre_v':x.get('capturepre'),'capture_early_v':x.get('captureearly'),'integrator_virtual_sum_deviation_uv':x.get('integrator_sum_minus_reference_uv'),'calibration_current_na':x['calcurrent']*1e9 if 'calcurrent' in x else None,'low_reference_current_ua':x['lowcurrent']*1e6 if 'lowcurrent' in x else None,'calibration_reference_voltage_v':x.get('calvoltage'),'low_reference_voltage_v':x.get('lowvoltage'),'delivered_mirror_charge_fc':x['delivered_mirror_charge_fc'],'beta_command_charge_fc':x.get('beta_command_charge_fc'),'beta_command_charge_error_fc':x.get('beta_command_charge_error_fc'),'effective_integrated_charge_fc':-x['capacitor_top_charge_fc'],'effective_beta_charge_error_fc':-x['capacitor_top_charge_fc']-x['beta_command_charge_fc'] if 'beta_command_charge_fc' in x else None,'route_phase_charge_fc':{key:x[key]*1e15 for key in ['qstartup','qsteady','qclosing','qpark'] if key in x}} for x in r.get('rows',[]) if 'delivered_mirror_charge_fc' in x],'near_zero_offset_analysis':near_zero,'maximum_decoded_ripple_including_late_endpoint_na':ripple,'evidence':path.relative_to(ROOT).as_posix(),'kind':'static_inverse' if 'physical_encoder_inverse' in pattern else 'shared_mode','simulation_completed':r['simulation_completed'],'failure_kind':failure,'simulator_returncode':r['simulator_returncode'],'operating_point_solver_warning':r['operating_point_solver_warning'],'settings':r['command_arguments'],'mismatch_seed_applied_via_reset':r.get('mismatch_seed_applied_via_reset',False),'encoder_settings':r['encoder_settings'],'cold_start_measurements':r.get('cold_start_measurements',{}),'cold_start_energy_measurement_valid':not r['command_arguments'].get('cold_start_prelude_us') or 'let power_vdd=-v(vdd)*i(vdd)' in snapshot.read_text(),'analysis':r['analysis'],'scope':r['scope']})
 # Delivered charge is the semantic interface; parked current is excluded here.
 for case in cases:
  rows=case['delivered_charge_rows']
  report=json.loads((ROOT/case['evidence']).read_text())
  edges=[{'input_current_na':x['input_current_na'],'beta_midpoint_width_ns':(x['betafall']-x['betarise'])*1e9,'opening_midpoint_gap_ns':(x['betarise']-x['parkfall'])*1e9 if 'parkfall' in x else None,'closing_midpoint_gap_ns':(x['parkrise']-x['betafall'])*1e9 if 'parkrise' in x else None} for x in report.get('rows',[]) if all(k in x for k in ['betarise','betafall'])]
  if edges:case['physical_driver_midpoint_timing']={'rows':edges,'scope':'Measured 1.65V logic crossings; not transistor conduction non-overlap, charge-equivalent beta width or physical sequencer qualification.'}
  mode_edges=[{'input_current_na':x['input_current_na'],'encode_fall_to_decode_rise_midpoint_gap_ns':(x['decoderise']-x['encodefall'])*1e9,'encode_complement_midpoint_skew_ns':(x['encodebrise']-x['encodefall'])*1e9 if 'encodebrise' in x else None,'decode_complement_midpoint_skew_ns':(x['decodebfall']-x['decoderise'])*1e9 if 'decodebfall' in x else None} for x in report.get('rows',[]) if all(k in x for k in ['encodefall','decoderise'])]
  if mode_edges:case['physical_mode_midpoint_timing']={'rows':mode_edges,'scope':'Actual1.65V logic crossings; not transistor conduction overlap, sampled accuracy or sequencer qualification.'}
  endpoint_rows=[{'input_current_na':x['input_current_na'],'native_feedback_capacitance_f':x['feedback_capacitance_f'],'same_aperture_effective_charge_fc':-x['endpoint_capacitor_top_charge_fc'],'same_aperture_endpoint_minus_integral_fc':x['endpoint_integral_difference_fc'],'settled_aperture_effective_charge_fc':-x['settled_endpoint_capacitor_top_charge_fc'],'settled_aperture_endpoint_minus_integral_fc':x['settled_endpoint_integral_difference_fc'],'modeled_leak_charge_fc':x.get('feedback_leak_charge_fc'),'settled_modeled_leak_charge_fc':x.get('settled_feedback_leak_charge_fc'),'settled_branch_charge_balance_residual_fc':x['settled_endpoint_integral_difference_fc']+x['settled_feedback_leak_charge_fc'] if 'settled_feedback_leak_charge_fc' in x else None} for x in report.get('rows',[]) if 'feedback_capacitance_f' in x]
  if rows:case['legacy_capacitor_current_integral_sub_fc_precision_qualified']=False
  case['feedback_endpoint_leak_measured']=bool(endpoint_rows and endpoint_rows[0]['modeled_leak_charge_fc'] is not None)
  if endpoint_rows:case['feedback_endpoint_charge']={'rows':endpoint_rows,'scope':'All actual feedback model capacitors plus extracted top/bottom parasitics; charge from their reported capacitance and actual two-terminal voltage. Same-aperture and300ns-earlier pre-route charge deltas compared with legacy integrals. No physical correction or model tolerance from agreement alone.'}
  active=[x for x in rows if x.get('beta_command_charge_fc') not in [None,0]]
  zero=[x for x in rows if x.get('beta_command_charge_fc')==0]
  if zero and active and case['settings'].get('current_set') in ['near-zero','near-zero-short']:
   first=zero[0]['effective_integrated_charge_fc']
   case['near_zero_delivered_charge_analysis']={
    'first_last_zero_charge_fc':[first,zero[-1]['effective_integrated_charge_fc']],
    'zero_repeat_difference_fc':zero[-1]['effective_integrated_charge_fc']-first,
    'maximum_raw_error_fc':max(abs(x['effective_beta_charge_error_fc']) for x in active),
    'maximum_analysis_only_zero_subtracted_error_fc':max(abs(x['effective_beta_charge_error_fc']-first) for x in active),
    'scope':'Delivered capacitor charge, finite near-zero sequence. Zero subtraction is analysis only and has no implemented correction circuit; parked-current subtraction is separate.'}
  case['delivered_charge_accuracy']={
   'maximum_absolute_error_fc':max((abs(x['effective_beta_charge_error_fc']) for x in active),default=None),
   'maximum_relative_error_percent':max((abs(x['effective_beta_charge_error_fc']/x['beta_command_charge_fc'])*100 for x in active),default=None),
   'zero_effective_charge_fc':[x['effective_integrated_charge_fc'] for x in zero],
   'maximum_held_voltage_change_uv':max((abs(x['held_encoder_post_v']-x['held_encoder_pre_v'])*1e6 for x in rows if x.get('held_encoder_post_v') is not None),default=None),
   'scope':'Finite diagnostic signed command sequence; no model tolerance, physical correction, sampled noise or service acceptance.'}
  if rows and case['settings'].get('mismatch_seed') is not None and case['simulation_completed']:
   settings=normalized_settings(case['settings']);settings['mismatch_seed']=None
   nominal=[c for c in cases if c['simulation_completed'] and normalized_settings(c['settings'])==settings]
   if len(nominal)==1:
    base=nominal[0];reference=base['delivered_charge_rows']
    if [x['input_current_na'] for x in reference] != [x['input_current_na'] for x in rows]:raise ValueError('Matched mismatch command sequence differs')
    case['matched_nominal_charge_comparison']={
     'nominal_evidence':base['evidence'],
     'maximum_difference_fc':max(abs(x['effective_integrated_charge_fc']-y['effective_integrated_charge_fc']) for x,y in zip(rows,reference)),
     'difference_rows_fc':[x['effective_integrated_charge_fc']-y['effective_integrated_charge_fc'] for x,y in zip(rows,reference)],
     'scope':'Same command arguments except local mismatch seed; limited seeds do not prove statistical yield.'}
 for case in cases:
  if not case['simulation_completed'] or not case.get('feedback_endpoint_leak_measured') or not case['settings'].get('physical_mode_drivers'):continue
  settings=normalized_settings(case['settings']);settings['physical_mode_drivers']=False
  matches=[b for b in cases if b['simulation_completed'] and b.get('feedback_endpoint_leak_measured') and normalized_settings(b['settings'])==settings]
  if len(matches)==1:
   base=matches[0];rows=case['feedback_endpoint_charge']['rows'];ref=base['feedback_endpoint_charge']['rows']
   if [x['input_current_na'] for x in rows]!=[x['input_current_na'] for x in ref]:raise ValueError('Physical mode comparison sequence mismatch')
   case['matched_ideal_mode_gate_reference']={'reference_evidence':base['evidence'],'settled_endpoint_charge_difference_rows_fc':[x['settled_aperture_effective_charge_fc']-y['settled_aperture_effective_charge_fc'] for x,y in zip(rows,ref)],'scope':'Only encode/decode mode gate generation changed from ideal sources to actual inverter pairs; upstream PWL commands and native circuit otherwise matched. No sub-fC convergence/noise/sequencer/model acceptance.'}
 for case in cases:
  if not case['simulation_completed'] or not case.get('feedback_endpoint_leak_measured') or not case['settings'].get('integrator_route_dummy'):continue
  settings=normalized_settings(case['settings']);settings['integrator_route_dummy']=False;settings['integrator_route_dummy_count']=1
  matches=[b for b in cases if b['simulation_completed'] and b.get('feedback_endpoint_leak_measured') and normalized_settings(b['settings'])==settings]
  if len(matches)==1:
   base=matches[0];rows=case['feedback_endpoint_charge']['rows'];ref=base['feedback_endpoint_charge']['rows']
   if [x['input_current_na'] for x in rows]!=[x['input_current_na'] for x in ref]:raise ValueError('Dummy comparison sequence mismatch')
   case['matched_no_integrator_dummy_endpoint_comparison']={'no_dummy_evidence':base['evidence'],'count':case['settings']['integrator_route_dummy_count'],'settled_charge_difference_rows_fc':[x['settled_aperture_effective_charge_fc']-y['settled_aperture_effective_charge_fc'] for x,y in zip(rows,ref)],'scope':'Same physical settings/sequence/20ns solver and native endpoint/leak observables; real dummy devices and their gate loading added. No ideal zero subtraction, sampled-noise, mismatch or model acceptance.'}
 for case in cases:
  if not case['simulation_completed'] or not case['delivered_charge_rows']:continue
  settings=normalized_settings(case['settings']);step=settings.pop('max_step_ns',None)
  if step is None:continue
  matches=[]
  for base in cases:
   b=normalized_settings(base['settings']);otherstep=b.pop('max_step_ns',None)
   if b==settings and otherstep is not None and otherstep>step and base['simulation_completed'] and bool(base.get('feedback_endpoint_charge'))==bool(case.get('feedback_endpoint_charge')) and base.get('feedback_endpoint_leak_measured',False)==case.get('feedback_endpoint_leak_measured',False):matches.append((otherstep,base))
  if matches:
   nearest=min(x[0] for x in matches);matches=[x[1] for x in matches if x[0]==nearest]
   if len(matches)==1:
    base=matches[0];rows=case['delivered_charge_rows'];ref=base['delivered_charge_rows']
    if [x['input_current_na'] for x in rows]!=[x['input_current_na'] for x in ref]:raise ValueError('Timestep comparison sequence mismatch')
    diffs=[x['effective_integrated_charge_fc']-y['effective_integrated_charge_fc'] for x,y in zip(rows,ref)]
    case['matched_larger_timestep_comparison']={'reference_evidence':base['evidence'],'maximum_step_ns':[step,nearest],'maximum_charge_difference_fc':max(map(abs,diffs)),'charge_difference_rows_fc':diffs,'scope':'Same physical settings and commands, changed maximum timestep only. A finite comparison does not establish convergence or model tolerance.'}
    if case.get('feedback_endpoint_charge') and base.get('feedback_endpoint_charge'):
     e=case['feedback_endpoint_charge']['rows'];r=base['feedback_endpoint_charge']['rows']
     case['matched_larger_timestep_comparison']['maximum_same_aperture_endpoint_charge_difference_fc']=max(abs(x['same_aperture_effective_charge_fc']-y['same_aperture_effective_charge_fc']) for x,y in zip(e,r))
     case['matched_larger_timestep_comparison']['maximum_settled_aperture_endpoint_charge_difference_fc']=max(abs(x['settled_aperture_effective_charge_fc']-y['settled_aperture_effective_charge_fc']) for x,y in zip(e,r))
 for case in cases:
  if not case['simulation_completed'] or not case['settings'].get('cold_start_prelude_us'):continue
  settings=normalized_settings(case['settings']);settings['cold_start_prelude_us']=0
  matches=[]
  for base in cases:
   b=normalized_settings(base['settings'])
   if b==settings and base['simulation_completed']:matches.append(base)
  if len(matches)==1:
   base=matches[0];rows=case['delivered_charge_rows'];ref=base['delivered_charge_rows']
   if [x['input_current_na'] for x in rows]!=[x['input_current_na'] for x in ref]:raise ValueError('Cold/warm sequence mismatch')
   case['matched_powered_initialization_comparison']={'powered_evidence':base['evidence'],'maximum_delivered_charge_difference_fc':max(abs(x['effective_integrated_charge_fc']-y['effective_integrated_charge_fc']) for x,y in zip(rows,ref)),'scope':'Explicit diagnostic power/root/control ramps versus powered DC initialization at equal sequence/timing. No physical power-on controller or service acceptance.'}
 abstracts=[]
 for path in sorted((BASE/'layout').glob('*/abstract_qualification.json')):
  abstract=json.loads(path.read_text())
  for name,expected in abstract['sha256'].items():
   input_path=ROOT/name
   if digest(input_path)!=expected:raise ValueError('Physical abstract provenance mismatch: '+name)
   sources.add(input_path)
  sources.add(path)
  abstracts.append({'cell':abstract['cell'],'size_um':abstract['size_um'],'ports':abstract['ports'],'evidence':path.relative_to(ROOT).as_posix(),'scope':abstract['scope']})
 import_path=BASE/'results/gf180_component_lef_import.json'
 router_import=None
 if import_path.exists():
  router_import=json.loads(import_path.read_text())
  for name,expected in router_import['sha256'].items():
   input_path=ROOT/name
   if digest(input_path)!=expected:raise ValueError('Router import provenance mismatch: '+name)
   sources.add(input_path)
  sources.add(import_path)
 result={'router_abstract_import':{'evidence':import_path.relative_to(ROOT).as_posix(),'verified':router_import['router_import_verified'],'provenance_verified':True,'scope':router_import['scope']} if router_import else None,'physical_layout_abstracts':abstracts,'physical_layout_abstract_count':len(abstracts),'physical_abstract_provenance_verified':True,'cases':cases,'case_count':len(cases),'simulations_completed':sum(c['simulation_completed'] for c in cases),'source_and_physical_provenance_verified':True,'physical_inverse_prototype_implemented':True,'qualified_inverse_accepted':False,'physical_state_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'scope':'Static inverse is real extracted MOS voltage-to-signed-current transfer under ideal voltage command. Shared mode uses the same actual MOS realization for encoder/inverse with physical TGs and held capacitance, diagnostic currents/clocks. Nominal transfer is not mismatch, sample-charge, beta/reset/adaptation or full population service acceptance. Qualified components are separate layouts, no combined layout/RPEX/gate-leakage/sampled-noise qualification.','next_step':'Resolve physical mode-switch charge disturbance and verify matched local variation/numerical sensitivity, then signed-charge integrator virtual-sum/charge delivery, state loading/restore, exact PLIF updates, full-float actor calibration and full5ms service before assembled routing.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
 result['failure_counts']={kind:sum(c.get('failure_kind')==kind for c in cases) for kind in sorted({c['failure_kind'] for c in cases if c.get('failure_kind')})}
 target=BASE/'results/gf180_encoder_inverse_boundary.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(target),'case_count':len(cases),'simulations_completed':result['simulations_completed']}))
if __name__=='__main__':main()
