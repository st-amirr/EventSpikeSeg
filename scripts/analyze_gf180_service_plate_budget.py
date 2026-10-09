"""Conditional full-inventory service/MIM budget for the current shared-core schedule."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/results'
EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=Path(__file__);op=OUT/'sky130_float_fullframe_state_occupancy.json';occ=json.loads(op.read_text());wp=OUT/'gf180_encoder_writeback_typical27_input200_step20_probenone_resetDummy_integratesum_restore4_trim30_a36f4a3f8b_parkBuf1_src16c18f5db8dc.json';w=json.loads(wp.read_text());sources={source,op,wp};cp=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
 if digest(cp)!=EXPECTED or occ['checkpoint_sha256']!=EXPECTED or occ['qat_enabled'] or not occ['full_frame'] or not w['simulation_completed'] or w['learned_beta_metadata']['checkpoint_sha256']!=EXPECTED:raise ValueError('Original float/native inputs differ')
 sources.add(cp)
 for name,sha in w['sha256'].items():
  p=ROOT/name
  if digest(p)!=sha:raise ValueError('Physical source/native inputs differ')
  sources.add(p)
 dp=ROOT/w['donor_evidence'];d=json.loads(dp.read_text());sources.add(dp);args=d['command_arguments'];count=args['integration_mim_count'];encode_us=args['encode_us']
 actors=occ['records'][0]['actors'];states=sum(v['resident'] for v in actors.values())
 if len(actors)!=25 or states!=occ['inventory_states'] or states!=30976000:raise ValueError('Full resident inventory differs')
 for record in occ['records']:
  if {n:v['resident'] for n,v in record['actors'].items()}!={n:v['resident'] for n,v in actors.items()}:raise ValueError('Frame inventories differ')
 qp=ROOT/'artifacts/analog_asic/layout/gf180_mim_22x22/qualification.json';q=json.loads(qp.read_text());sources.add(qp)
 if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native feedback capacitor unqualified')
 for n,sha in q['sha256'].items():
  p=qp.parent/n
  if digest(p)!=sha:raise ValueError('Native capacitor geometry differs')
  sources.add(p)
 plate_per_bank=count*q['square_size_um']**2;scenarios=[]
 for time in [encode_us,10,5,1]:
  slots=math.floor(5000/time);channels={n:math.ceil(v['resident']/slots) for n,v in actors.items()};cores=sum(channels.values())
  scenarios.append({'serial_slot_us':time,'current_tested_encode_duration':time==encode_us,'hypothetical_shorter_slot_not_qualified':time!=encode_us,'slots_per_channel_per_5ms_ignoring_all_other_work':slots,'actor_channel_counts':channels,'total_conditional_channels':cores,'feedback_plate_only_um2_per_channel':plate_per_bank,'conditional_feedback_plate_only_mm2':plate_per_bank*cores/1e6})
 screened=[];sp=OUT/'gf180_feedback_scaling_boundary.json';sb=json.loads(sp.read_text());sources.add(sp)
 for name,sha in sb['sha256'].items():
  f=ROOT/name
  if digest(f)!=sha:raise ValueError('Screened physical scaling provenance differs')
  sources.add(f)
 settings_seen=set()
 for case in sb['cases']:
  t=case['timing_and_capacitance'];key=(t['encode_us'],t['feedback_mim_count'],t.get('encoder_extra_hold_mim_count',16),t.get('active_bias_root_ua',5))
  if key in settings_seen:continue
  settings_seen.add(key);slots=math.floor(5000/key[0]);channels={n:math.ceil(v['resident']/slots) for n,v in actors.items()};cores=sum(channels.values());bank=key[1]*q['square_size_um']**2
  screened.append({'encode_us':key[0],'feedback_mim_count':key[1],'extra_encoder_hold_mim_count':key[2],'bias_root_ua':key[3],'slots_per_channel_per_5ms_ignoring_all_other_work':slots,'actor_channel_counts':channels,'total_conditional_channels':cores,'feedback_plate_only_um2_per_channel':bank,'conditional_feedback_plate_only_mm2':bank*cores/1e6,'any_completed_diagnostic':any(c['simulation_completed'] and (c['timing_and_capacitance']['encode_us'],c['timing_and_capacitance']['feedback_mim_count'],c['timing_and_capacitance'].get('encoder_extra_hold_mim_count',16),c['timing_and_capacitance'].get('active_bias_root_ua',5))==key for c in sb['cases']),'screened_primitive_not_qualified_service':True,'full_5ms_service_accepted':False})
 result={'screened_native_feedback_scenarios':screened,'checkpoint_sha256':EXPECTED,'qat_or_quantized_reference_used':False,'resident_states':states,'actor_count':len(actors),'integration_mim_count':count,'native_square_plate_size_um':q['square_size_um'],'current_tested_encoding_us':encode_us,'scenarios':scenarios,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'scope':'Conditional scheduling/geometry analysis, not a measured service minimum or full-chip area. Assumes every resident identity requires one serial visit per5ms, one physical32-MIM feedback bank per channel, permanent actor assignment and no overlap of distinct states within a channel. Uses current tested50us encoding as a scenario, not proof that faster encoding is impossible.50us excludes beta, events, threshold/reset/adaptation, input/read/restore overhead, buffering and graph completion dependencies; shorter scenarios entirely hypothetical. MIM plate geometry only excludes all resident storage, amplifiers, trim/control, contacts/wells/routing and peripheral area. Does not qualify sparsity skipping, pipelining, revised analog topology, manufacturing dimensions or full accuracy. The current50us/32-cap prototype must undergo service/density optimization before array replication.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
 target=OUT/'gf180_shared_core_service_plate_budget.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(target),'scenarios':[{k:v for k,v in row.items() if k!='actor_channel_counts'} for row in scenarios]},indent=2))
if __name__=='__main__':main()
