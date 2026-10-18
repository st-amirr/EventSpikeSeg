"""Audit resident reset task, retained failures, fresh target, and routed selector cases."""
import hashlib,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files={Path(__file__)};paths=[]
 patterns=['gf180_resident_subtractive_reset_4fc563dbe5_src177e3f5966b3.json','gf180_resident_reset_warmup_hold_a9f693b30a_src156822f86ece.json','gf180_resident_reset_tracking_park_a9f693b30a_src3606117cf13c.json','gf180_resident_reset_tracking_select_a9f693b30a_src8f33bda38e60.json','gf180_resident_reset_tracking_check_4c2746e8ab_srceab4155da2f3.json']
 for pattern in patterns:
  matches=list((BASE/'results').glob(pattern));assert len(matches)==1;paths+=matches
 physical=list((BASE/'results').glob('gf180_resident_reset_physical_select_*_src*.json'));assert len(physical)==2
 assert {json.loads(p.read_text())['settings']['seed'] for p in physical}=={0,29};paths+=physical
 cases=[]
 for p in paths:
  r=json.loads(p.read_text());assert r['simulation_completed'];files.add(p)
  for name,h in r['sha256'].items():assert sha(ROOT/name)==h,name
  summary=[]
  for c in r['cases']:
   arm=c['arms']['active'];fired=arm['latched_spike_before_v']>1.65;reset=-c['active_minus_idle_step_v'];row={'target_v':c['target_v'],'latched_spike':fired,'actual_net_reset_v':reset,'requested_reset_v':.006875 if fired else 0,'reset_error_v':reset-(.006875 if fired else 0),'neutral_pulse_kick_v':c['neutral_minus_idle_step_v']}
   if 'hold_drift_v' in arm:
    row['hold_drift_by_arm_v']={name:a['hold_drift_v'] for name,a in c['arms'].items()};row['net_reset_after_5ms_v']=-((arm['state_after_5ms_hold_v']-arm['state_before_v'])-(c['arms']['idle']['state_after_5ms_hold_v']-c['arms']['idle']['state_before_v']))
   if 'decision_sample_disturbance_v' in arm:row['decision_sample_disturbance_v']=arm['decision_sample_disturbance_v'];row['selector_midpulse_v']=arm['selection_midpulse_v'];row['state_at_decision_sample_v']=arm['state_before_sample_v']
   summary.append(row)
  entry={'report':p.relative_to(ROOT).as_posix(),'settings':r['settings'],'cases':summary}
  if 'physical_select_' in p.name:
   paths_dat=[ROOT/n for n in r['sha256'] if n.endswith('.dat')];assert len(paths_dat)==1
   w=np.loadtxt(paths_dat[0],skiprows=1);assert w.shape[1]==61
   sq=BASE/'layout/gf180_state_update_detailstem_ch3_pad06_v2/qualification.json';trained=json.loads(sq.read_text())['target_float_channel']['trained_beta'];pairs=[]
   for i,c in enumerate(r['cases']):
    # State column for idle arm; every target has3arms*10 exported signals.
    col=1+30*i;before=float(np.interp(1019e-6,w[:,0],w[:,col]));after=float(np.interp(1041.5e-6,w[:,0],w[:,col]));pairs.append((before,after))
   entry['loaded_beta_diagnostic']={'trained_beta':trained,'two_target_slope':(pairs[1][1]-pairs[0][1])/(pairs[1][0]-pairs[0][0]),'residuals_against_original_trained_beta_v':[after-1.65-trained*(before-1.65) for before,after in pairs],'scope':'Idle-arm actual state before beta1019us and after beta/rearm/sensing settle1041.5us, before reset. Only two targets, added tracking OTA and detector load; diagnostic does not qualify trained beta or nonlinear transfer.'}
  cases.append(entry)
 for kind in ['qualification.json','abstract_qualification.json']:
  p=BASE/'layout/gf180_reset_select_and_fullroute'/kind;q=json.loads(p.read_text());files.add(p)
  if kind=='qualification.json':assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and q['mos_count']==6
  else:assert q['source_geometry_hashes_unchanged'] and q['physical_ports_and_size_verified'] and q['routing_obstructions_present'] and q['all_rectangles_within_abstract_boundary'] and q['ports']==['A','B','Y','YB','VDD','VSS']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for name,h in q.get(key,{}).items():
    f=p.parent/name if key=='sha256' and '/' not in name else ROOT/name;assert sha(f)==h,name
 failed=BASE/'results/gf180_resident_reset_tracking_select_a9f693b30a_src35b4003676d3.json';r=json.loads(failed.read_text());assert not r['simulation_completed'];files.add(failed)
 for n,h in r['sha256'].items():assert sha(ROOT/n)==h,n
 files.add(BASE/'results/gf180_resident_subtractive_reset_4fc563dbe5_src177e3f5966b3_postprocess_failure.json')
 timeout=BASE/'results/gf180_reset_physical_select_seed29_timeout.json';t=json.loads(timeout.read_text());assert not t['simulation_completed'];files.add(timeout)
 for n,h in t['sha256'].items():assert sha(ROOT/n)==h,n
 for name in ['gf180_resident_reset_width_prediction.json','gf180_tracking_reset_width_prediction.json']:files.add(BASE/'results'/name)
 out=BASE/'results/gf180_resident_reset_task_boundary.json';assert not out.exists()
 result={'audit_completed':True,'cases':cases,'retained_failures':['Direct pulsed gate/cascode sink fails5ms lifecycle; startup warmup does not cure pulse tail','First current-steering series switch path attaches floating node when spike latch changes and disturbs state; replaced by phase AND latched-spike selection','Initial physical-cell PF instantiation had surplus substrate pin; failed native log/report retained; pin count corrected in separate source','First seed29 physical-selector run hit120s runtime bound and saved incomplete waveform; separately named180s unchanged-circuit followup required','Initial successful native run hit removed numpy.trapz in host postprocessing; measurements recovered from saved waveform without rerun'],'calibration_scope_erratum':'Some frozen native scopes retain phrase width predicted from earlier2.1V target. The tracking-check and physical-select scripts actually read gf180_tracking_reset_width_prediction.json: donor is1.68V repaired-selector case, width1.474995516us from nominal transfer and neutral switching control. Earlier1.132799942us direct-pulse prediction is only the first tracking diagnostic width. Use recorded calibration input graph, not outdated prose.','scope':'Single resident reset after beta/sensing with idle and zero-program controls; full routed six-MOS selector and abstract exist. Other components extracted, complete analog assembly still schematic. Native mismatch seed29 is one configured sample, not matched per-device control across arms or yield/noise characterization. New tracking OTA adds state capacitance and invalidates old beta transfer; reset evidence does not qualify combined original trained beta. All references, bias, startup/sample/reset phases are external. No adaptive reset, all coefficients, inhibition/adaptation, sampled noise/longer reference retention/PVT/yield, shared-state mux/access, population area/service or complete physical PLIF/chip acceptance. Range64 remains unaccepted; full-float model authoritative.','next_action':'Use routed-selector check to decide reset direction, then physically combine sensing/reset with resident beta and characterize final commit before any model replay or inventory replication. Include shared-lane access/loading and count tracking/reference overhead.','acceptance':{'subtractive_reset':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(out),'case_count':sum(len(c['cases']) for c in cases),'latest':cases[-2:]},indent=2))
if __name__=='__main__':main()
