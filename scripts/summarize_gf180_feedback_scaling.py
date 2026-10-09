"""Audit physical feedback/timing variants and full-float beta pulse coverage."""
import hashlib,json,math,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/results'
EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';manifest=ROOT/'artifacts/analog_asic/model_reference/eventspikeseg140k_float_reference.json';archive=manifest.with_name('eventspikeseg140k_float_parameters.npz');meta=json.loads(manifest.read_text());sources={Path(__file__),checkpoint,manifest,archive};cases=[];method_groups={};load_groups={}
 if digest(checkpoint)!=EXPECTED or meta['checkpoint_sha256']!=EXPECTED or meta['epoch']!=58 or not meta['is_best']:raise ValueError('Original float reference differs')
 z=np.load(archive);betas=np.concatenate([z[k].reshape(-1) for k in z.files if k.startswith('beta__')]);minimum=float(betas.min());maximum=float(betas.max())
 boundary_path=OUT/'gf180_encoder_writeback_boundary.json';boundary=json.loads(boundary_path.read_text());sources.add(boundary_path)
 for name,sha in boundary['sha256'].items():
  f=ROOT/name
  if digest(f)!=sha:raise ValueError('Audited physical boundary inputs differ')
  sources.add(f)
 for row in boundary['cases']:
  if row['kind']!='physical_writeback_loop':continue
  p=ROOT/row['evidence'];r=json.loads(p.read_text());timing=r.get('timing_and_capacitance')
  if not timing:continue
  args=r['settings'];count=args['feedback_mim_count'];window=r['learned_beta_metadata']['reference_window_us']
  if count!=timing['feedback_mim_count'] or window!=4*count/32 or r['learned_beta_metadata']['checkpoint_sha256']!=EXPECTED or not row['feedback_bank_count_and_unit_window_audited']:raise ValueError('Physical count/window differs')
  if r['sha256'].get(archive.relative_to(ROOT).as_posix())!=digest(archive):raise ValueError('Beta archive provenance differs')
  case={'evidence':row['evidence'],'simulation_completed':r['simulation_completed'],'settings':args,'timing_and_capacitance':timing,'feedback_plate_only_um2':count*22**2,'minimum_trained_beta_pulse_ns':1000*window*minimum,'command_rise_plus_fall_ns':200,'all_trained_beta_pulses_fit_current_100ns_ramp_template':window*minimum>=.2,'selected_actor_beta':r['learned_beta_metadata'],'measurements':r['measurements'],'analysis':r['analysis'],'first_charge_relative_error_percent':None,'preservation_error_percent':row.get('readback_relative_to_first_charge_error_percent'),'waveform_path':r.get('waveform_path'),'physical_precision_accepted':False,'partial_first_charge_before_incomplete_run':None}
  if r['simulation_completed']:
   a=r['analysis'];target=a['first_beta_target_fc'];case['first_charge_relative_error_percent']=100*(a['first_beta_charge_fc']-target)/target if target else None
  if not r['simulation_completed'] and all(k in r['measurements'] for k in ['q_initial','q_after_beta']):
   m=r['measurements'];q=-(m['q_after_beta']-m['q_initial'])*1e15;target=args['input_na']*window*r['learned_beta_metadata']['beta_float32'];case['partial_first_charge_before_incomplete_run']={'observed_fc':q,'target_fc':target,'error_percent':100*(q-target)/target if target else None,'full_run_accepted':False}
  deck=next(ROOT/n for n in r['sha256'] if '/benches/' in n and n.endswith('.spice'))
  physical_lines=[]
  for line in deck.read_text().split('.control')[0].splitlines():
   if line.startswith('.options '):
    line=re.sub(r'\s+(?:method=(?:trap|gear)|maxord=[12])\b','',line)
    if line=='.options':continue
   physical_lines.append(line)
  physical='\n'.join(physical_lines)
  signature=hashlib.sha256(physical.encode()).hexdigest();case['physical_and_command_deck_sha256']=signature;case['integration_method']=row['numerical_integration_method'];case['integration_order']=row['integration_order'];case['requested_integration_method']=row['requested_integration_method'];method_groups.setdefault(signature,[]).append(case)
  load_physical='\n'.join(x for x in deck.read_text().split('.control')[0].splitlines() if not re.match(r'^Xcaptureextra\d+ ',x))
  load_signature=hashlib.sha256(load_physical.encode()).hexdigest();load_groups.setdefault(load_signature,[]).append(case);case['physical_deck_except_encoder_extra_hold_instances_sha256']=load_signature
  m=r['measurements']
  if all(k in m for k in ['mirror_pre_capture','mirror_post_capture']):
   case['capture_transition_diagnostic']={'mirror_pre_capture_na':m['mirror_pre_capture']*1e9,'mirror_post_capture_na':m['mirror_post_capture']*1e9,'mirror_change_na':(m['mirror_post_capture']-m['mirror_pre_capture'])*1e9,'enc_initial_v':m.get('enc_initial'),'enc_recaptured_v':m.get('enc_recaptured'),'mirror_pre_recapture_na':m.get('mirror_pre_recapture',0)*1e9,'mirror_post_recapture_na':m.get('mirror_post_recapture',0)*1e9,'scope':'Different mode/drain operating points; observed current change does not uniquely isolate switch injection or independently prove precision.'}
  if r.get('waveform_path'):
   wave=ROOT/r['waveform_path'];sources.add(wave);samples=np.loadtxt(wave,skiprows=1);capture=(10+args['encode_us'])*1e-6;plateau=samples[(samples[:,0]>=capture-1e-6)&(samples[:,0]<=capture-.3e-6)]
   if len(plateau):
    current=plateau[:,5]*1e9;case['pre_capture_waveform_diagnostic']={'sample_count':len(plateau),'window_us':[capture*1e6-1,capture*1e6-.3],'mirror_mean_na':float(current.mean()),'mirror_peak_to_peak_na':float(np.ptp(current)),'target_na':args['input_na'],'enc_peak_to_peak_uv':float(np.ptp(plateau[:,1])*1e6),'waveform_end_us':float(samples[-1,0]*1e6),'completed_loop':r['simulation_completed'],'scope':'Raw mirror settling window only; does not establish charge precision, noise, or numerical agreement.'}
  cases.append(case)
 comparisons=[]
 for signature,group in method_groups.items():
  for left in group:
   if left['integration_method']!='trap':continue
   for right in group:
    if right['integration_method']!='gear':continue
    comparisons.append({'trap_evidence':left['evidence'],'gear_evidence':right['evidence'],'physical_and_command_deck_sha256':signature,'identical_physical_instances_and_phase_commands':True,'both_completed':left['simulation_completed'] and right['simulation_completed'],'first_charge_difference_fc':right['analysis'].get('first_beta_charge_fc',0)-left['analysis'].get('first_beta_charge_fc',0) if left['simulation_completed'] and right['simulation_completed'] else None,'unity_readback_difference_fc':right['analysis'].get('unity_readback_charge_fc',0)-left['analysis'].get('unity_readback_charge_fc',0) if left['simulation_completed'] and right['simulation_completed'] else None,'numerical_precision_accepted':False})
 load_comparisons=[]
 for signature,group in load_groups.items():
  for left in group:
   for right in group:
    if left['settings'].get('encoder_hold_mim_count',16)>=right['settings'].get('encoder_hold_mim_count',16):continue
    load_comparisons.append({'smaller_load_evidence':left['evidence'],'larger_load_evidence':right['evidence'],'identical_physical_and_command_deck_except_extra_hold_instances':True,'physical_deck_except_encoder_extra_hold_instances_sha256':signature,'smaller_extra_hold_count':left['settings'].get('encoder_hold_mim_count',16),'larger_extra_hold_count':right['settings'].get('encoder_hold_mim_count',16),'both_completed':left['simulation_completed'] and right['simulation_completed'],'smaller_first_charge_error_percent':left['first_charge_relative_error_percent'],'larger_first_charge_error_percent':right['first_charge_relative_error_percent'],'smaller_preservation_error_percent':left['preservation_error_percent'],'larger_preservation_error_percent':right['preservation_error_percent'],'precision_accepted':False})
 result={'encoder_hold_matched_comparisons':load_comparisons,'numerical_method_matched_comparisons':comparisons,'checkpoint_sha256':EXPECTED,'qat_or_quantized_reference_used':False,'trained_beta_minimum':minimum,'trained_beta_maximum':maximum,'beta_scalar_count':len(betas),'cases':cases,'case_count':len(cases),'simulations_completed':sum(x['simulation_completed'] for x in cases),'source_native_and_feedback_timing_provenance_verified':True,'full_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'scope':'Native feedback MIM instances and actual beta/unity unit windows scaled together, with external commands driving actual physical gates. Pulse fit is only an ordering check for100ns command ramps across trained betas, not delivered-beta precision/jitter coverage. Actual native root current changes MOS bias, not geometry or ideal output/gain. First-pulse charge error must be assessed independently of writeback preservation; matching a wrongly computed state does not prove float semantics. Single or sparse points/corners cannot qualify transfer, saturation, sampled noise/mismatch, exact weighted PLIF or complete5ms service/combined layout. Plate area only, no assembled module/chip estimate.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
 target=OUT/'gf180_feedback_scaling_boundary.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(target),'case_count':len(cases),'simulations_completed':result['simulations_completed'],'beta_min':minimum,'cases':[{'evidence':x['evidence'],'first_charge_error_percent':x['first_charge_relative_error_percent'],'all_beta_pulses_fit':x['all_trained_beta_pulses_fit_current_100ns_ramp_template']} for x in cases]},indent=2))
if __name__=='__main__':main()
