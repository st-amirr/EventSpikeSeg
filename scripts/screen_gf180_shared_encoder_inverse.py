"""Physical mode-switching encoder/inverse reuse; diagnostic current commands only."""
import argparse, hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',required=True);p.add_argument('--physical-current-reference',action='store_true');p.add_argument('--physical-beta-driver',action='store_true');p.add_argument('--physical-park-driver',action='store_true');p.add_argument('--physical-mode-drivers',action='store_true');p.add_argument('--mode-driver-output-buffers',action='store_true');p.add_argument('--reference-filter-mim-count',type=int,choices=[0,1,4],default=0);p.add_argument('--cold-start-prelude-us',type=int,choices=[0,100,500,1000,2000,5000],default=0);p.add_argument('--calibration-current-override-na',type=float,choices=[.1,1,10],default=None);p.add_argument('--encoder-use-integrator-bias',action='store_true');p.add_argument('--lift-reference-override-na',type=int,choices=[20,200,2000],default=None);p.add_argument('--isolated-held-gate-layout',action='store_true');p.add_argument('--isolated-mirror-drain-layout',action='store_true');p.add_argument('--beta-delayed-start',action='store_true');p.add_argument('--route-break-before-make',action='store_true');p.add_argument('--integrator-route-dummy',action='store_true');p.add_argument('--integrator-route-dummy-count',type=int,choices=[1,2,4],default=1);p.add_argument('--beta-phase-charge-probes',action='store_true');p.add_argument('--beta-start-delay-ns',type=int,choices=[500,1500],default=500);p.add_argument('--learned-beta-actor',default=None);p.add_argument('--learned-beta-channel',type=int,default=0);p.add_argument('--beta-tail-compensation-ns',type=int,choices=[0,100,200],default=0);p.add_argument('--integrate-charge',action='store_true');p.add_argument('--boost-park-bias',action='store_true');p.add_argument('--dump-integration-waveforms',action='store_true');p.add_argument('--integrator-compensation-mim-count',type=int,choices=[1,4],default=1);p.add_argument('--integrator-compensation-size-um',type=int,choices=[7,22],default=22);p.add_argument('--integrator-reference-ua',type=int,choices=[1,5],default=1);p.add_argument('--mirror-route-overlap',action='store_true');p.add_argument('--charge-window-start-ns',type=int,choices=[200,500],default=200);p.add_argument('--integration-mim-count',type=int,choices=[32,64],default=32);p.add_argument('--current-set',choices=['wide','near-zero','near-zero-short'],default='wide');p.add_argument('--max-step-ns',type=int,choices=[5,20,100,500],default=500);p.add_argument('--tight-charge-solver',action='store_true');p.add_argument('--refined-charge-solver',action='store_true');p.add_argument('--capture-dummy',action='store_true');p.add_argument('--capture-dummy-nf-width-um',type=float,choices=[.25,.5,.75,1],default=None);p.add_argument('--capture-dummy-pf-width-um',type=float,choices=[.5,1,1.2,1.22,2],default=None);p.add_argument('--isolate-feedback-mode',action='store_true');p.add_argument('--feedback-release-advance-ns',type=int,choices=[-500,-200,0,200,500,1500],default=0);p.add_argument('--feedback-mode-nf-width-um',type=float,choices=[.25,.5,1],default=None);p.add_argument('--mode-switch-nf-width-um',type=float,choices=[.25,.5,1],default=1);p.add_argument('--extra-ota-compensation-mim',type=int,choices=[0,1],default=0);p.add_argument('--held-mim-count',type=int,choices=[0,1,4,16],default=0);p.add_argument('--held-mim-size-um',type=int,choices=[7,22],default=22);p.add_argument('--mismatch-seed',type=int,default=None);p.add_argument('--encode-us',type=int,choices=[20,50,100,200,1000],default=1000);p.add_argument('--decode-us',type=int,choices=[5,10,20],default=20);a=p.parse_args()
 start_offset=(10+a.cold_start_prelude_us)*1e-6
 source=Path(__file__);sha=digest(source);profile=ROOT/a.profile;r=json.loads(profile.read_text());settings=r['command_arguments']
 if not r.get('simulation_completed') or not settings.get('physical_controller_hysteresis') or settings.get('compensation_bank_clamp'):raise ValueError('Completed unclamped physical-controller trajectory required')
 sources=[source,profile]
 beta_metadata=None
 if a.learned_beta_actor is not None:
  if not (a.integrate_charge and a.mirror_route_overlap and a.charge_window_start_ns==500):raise ValueError('Beta pulse requires integrator, overlap and500ns window start')
  import numpy as np
  checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';manifest=BASE/'model_reference/eventspikeseg140k_float_reference.json';archive=manifest.parent/'eventspikeseg140k_float_parameters.npz';meta=json.loads(manifest.read_text());expected='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
  if digest(checkpoint)!=expected or meta['checkpoint_sha256']!=expected or meta['epoch']!=58 or not meta['is_best']:raise ValueError('Original float checkpoint contract mismatch')
  z=np.load(archive);key='beta__'+a.learned_beta_actor.replace('.','__');betas=z[key];beta=float(betas[a.learned_beta_channel])
  if not .1<beta<.99:raise ValueError('Beta pulse bounds exceeded')
  beta_metadata={'actor':a.learned_beta_actor,'channel':a.learned_beta_channel,'beta_float32':beta,'checkpoint_sha256':expected,'reference_window_us':4,'tail_compensation_ns':a.beta_tail_compensation_ns,'delayed_start':a.beta_delayed_start,'start_delay_ns':a.beta_start_delay_ns,'scope':'One actual current-routing pulse based on original float beta, not a full PLIF or5ms population controller.'};sources += [checkpoint,manifest,archive]
 if a.encoder_use_integrator_bias and not (a.integrate_charge and a.integrator_reference_ua==5 and not a.boost_park_bias):raise ValueError('Steady encoder bias requires existing physical5uA integrator reference and no dynamic bias option')
 if a.route_break_before_make and not (beta_metadata is not None and a.beta_delayed_start and a.mirror_route_overlap):raise ValueError('Break-before-make requires delayed beta routing')
 if a.integrator_route_dummy and not (beta_metadata is not None and a.mode_switch_nf_width_um==.5):raise ValueError('Route dummy requires learned beta and qualified NF0.5 TG')
 if a.beta_phase_charge_probes and not (beta_metadata is not None and a.beta_delayed_start):raise ValueError('Phase charge probes require delayed learned beta')
 for name,expected in r['sha256'].items():
  if name=='scripts/screen_gf180_nonlinear_encoder.py':continue
  path=ROOT/name
  if digest(path)!=expected:raise ValueError('Provenance mismatch: '+name)
  sources.append(path)
 original=next(ROOT/name for name in r['sha256'] if '/benches/' in name and name.endswith('.spice'))
 lines=original.read_text().split('.control')[0].splitlines()
 if a.calibration_current_override_na is not None:
  if not settings.get('self_biased_span'):raise ValueError('Calibration override requires physical diode-stack references')
  indices=[i for i,x in enumerate(lines) if x.startswith('Icalibration ')]
  if len(indices)!=1:raise ValueError('Expected one physical calibration-stack current')
  lines[indices[0]]=f'Icalibration vdd calspan {a.calibration_current_override_na:g}n'
  settings=dict(settings,donor_calibration_na=settings['calibration_na'],calibration_na=a.calibration_current_override_na/settings['feedback_scale'])
 if a.lift_reference_override_na is not None:
  if not settings.get('source_lifted') or settings.get('lift_reference_node')!='nf-diode':raise ValueError('Physical low-reference override requires NF-diode source-lifted donor')
  indices=[i for i,x in enumerate(lines) if x.startswith('Ilowreference ')]
  if len(indices)!=1:raise ValueError('Expected one physical low-reference current')
  lines[indices[0]]=f'Ilowreference vdd lowcalspan {a.lift_reference_override_na}n'
  settings=dict(settings,donor_lift_reference_na=settings['lift_reference_na'],lift_reference_na=a.lift_reference_override_na)
 if a.reference_filter_mim_count and not a.physical_current_reference:raise ValueError('Physical reference filter requires current divider')
 if a.physical_current_reference:
  if a.calibration_current_override_na is not None or a.lift_reference_override_na is not None:raise ValueError('Physical divider excludes ideal current overrides')
  if not settings.get('source_lifted') or settings.get('lift_reference_node')!='nf-diode':raise ValueError('Physical current divider requires lifted NF-diode reference')
  cell='gf180_encoder_current_reference_divider';qpath=BASE/'layout'/cell/'qualification.json';q=json.loads(qpath.read_text());cap=qpath.parent/(cell+'_cap.spice')
  if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Unqualified current-divider layout')
  for name,expected in q['sha256'].items():
   path=qpath.parent/name
   if digest(path)!=expected:raise ValueError('Current-divider provenance mismatch')
   sources.append(path)
  sources.append(qpath);lines[1:1]=cap.read_text().splitlines()
  if sum(x.startswith('Icalibration ') for x in lines)!=1 or sum(x.startswith('Ilowreference ') for x in lines)!=1:raise ValueError('Expected both diagnostic currents')
  lines=[x for x in lines if not x.startswith(('Icalibration ','Ilowreference '))]
  lines+=['Xcurrentreference bias calfeed lowfeed vdd 0 '+cell,'Vcalprobe calfeed calspan 0','Vlowprobe lowfeed lowcalspan 0']
  settings=dict(settings,calibration_current_source='physical_cascaded_divider',low_current_source='physical_pf_mirror',geometry_target_calibration_na=1,geometry_target_low_na=2000,donor_currents_only=True)
  r['qualified_layout_components'].append(q)
  lines += [f'Xreferencefilter{i} calspan 0 0 gf180_mim_22x22' for i in range(a.reference_filter_mim_count)]
 if a.isolated_mirror_drain_layout and not a.isolated_held_gate_layout:raise ValueError("Mirror-drain isolation requires held-gate isolation")
 if a.isolated_held_gate_layout:
  cell='gf180_mirrored_encoder_feedback_grounded_source_lifted_w10_isolated_enc_observer_ports';cell='gf180_encoder_w10_isolated_enc_sum_observer_ports' if a.isolated_mirror_drain_layout else cell;qpath=BASE/'layout'/cell/'qualification.json';q=json.loads(qpath.read_text());cap=qpath.parent/(cell+'_cap.spice')
  if settings.get('feedback_scale')!=10 or q['magic_drc_count']!=0 or not q['lvs_unique'] or digest(cap)!=q['sha256'][cap.name]:raise ValueError('Isolated-gate layout qualification mismatch')
  sources.extend([qpath,cap]);lines[1:1]=cap.read_text().splitlines();lines=[x.rsplit(' ',1)[0]+' '+cell if x.startswith('Xfeedback ') else x for x in lines];r['qualified_layout_components'].append(q)
 lines=[x for x in lines if not x.startswith('Iinput ')]
 lines=[x.replace('reltol=1e-7','reltol=1e-6').replace('vntol=1e-11','vntol=1e-9') for x in lines]
 if a.tight_charge_solver and a.refined_charge_solver:raise ValueError('Select one explicit solver refinement')
 if a.refined_charge_solver:lines=[x.replace('reltol=1e-6','reltol=1e-7').replace('vntol=1e-9','vntol=1e-11') for x in lines]
 if a.tight_charge_solver:lines=[x.replace('reltol=1e-6','reltol=1e-8').replace('vntol=1e-9','vntol=1e-11').replace('abstol=1e-17','abstol=1e-19') for x in lines]
 lines=[x.replace('Xota common sum enc ','Xota common sum drive ').replace('Xcomp cmp enc ','Xcomp cmp drive ').replace('Xfeedback sum enc ','Xfeedback mirrorsum enc ') for x in lines]
 if a.feedback_release_advance_ns and not a.isolate_feedback_mode:raise ValueError('Early feedback release requires physical isolation TG')
 if a.isolate_feedback_mode:
  lines=[x.replace(' enc ', ' feedbackenc ',1) if x.startswith('Xinputfeedback') else x for x in lines]
  lines+=['Xfeedbackmode enc feedbackenc encode encodeb 0 vdd gf180_fixed_body_tg']
 lines+=['Vprobe sum mirrorsum 0','Xdriveload drive 0 0 gf180_mim_7x7','Xencodemode drive enc encode encodeb 0 vdd gf180_fixed_body_tg','Xdecodemode drive sum decode decodeb 0 vdd gf180_fixed_body_tg']
 if a.capture_dummy:lines+=['Xcapturedummy enc enc encodeb encode 0 vdd gf180_fixed_body_tg']
 if a.mode_switch_nf_width_um!=1:
  cell='gf180_fixed_body_tg_nf'+f'{a.mode_switch_nf_width_um:g}'.replace('.','p');qpath=BASE/'layout'/cell/'qualification.json';q=json.loads(qpath.read_text());cap=qpath.parent/(cell+'_cap.spice')
  if q['magic_drc_count']!=0 or not q['lvs_unique'] or digest(cap)!=q['sha256'][cap.name]:raise ValueError('Unqualified mode TG')
  sources.extend([qpath,cap]);lines[1:1]=cap.read_text().splitlines();lines=[x.replace(' gf180_fixed_body_tg',' '+cell) if x.startswith(('Xencodemode ','Xdecodemode ','Xfeedbackmode ','Xcapturedummy ')) else x for x in lines];r['qualified_layout_components'].append(q)
 if a.capture_dummy_pf_width_um is not None and (a.capture_dummy_nf_width_um is None or not a.capture_dummy):raise ValueError('Independent PF dummy size requires explicit NF dummy size and capture dummy')
 if a.capture_dummy_nf_width_um is not None:
  if not a.capture_dummy:raise ValueError('Explicit dummy size requires capture dummy')
  cell='gf180_fixed_body_tg' if a.capture_dummy_nf_width_um==1 else 'gf180_fixed_body_tg_nf'+f'{a.capture_dummy_nf_width_um:g}'.replace('.','p')
  if a.capture_dummy_pf_width_um is not None:cell='gf180_fixed_body_tg_nf'+f'{a.capture_dummy_nf_width_um:g}'.replace('.','p')+'_pf'+f'{a.capture_dummy_pf_width_um:g}'.replace('.','p')
  qpath=BASE/'layout'/cell/'qualification.json';q=json.loads(qpath.read_text());cap=qpath.parent/(cell+'_cap.spice')
  if q['magic_drc_count'] or not q['lvs_unique'] or digest(cap)!=q['sha256'][cap.name]:raise ValueError('Unqualified capture dummy')
  sources.extend([qpath,cap])
  if not any(x.startswith('.subckt '+cell+' ') for x in lines):lines[1:1]=cap.read_text().splitlines()
  lines=[x.rsplit(' ',1)[0]+' '+cell if x.startswith('Xcapturedummy ') else x for x in lines];r['qualified_layout_components'].append(q)
 if a.feedback_mode_nf_width_um is not None:
  if a.feedback_mode_nf_width_um!=1:raise ValueError('Independent feedback switch currently supports original NF1/PF2 only')
  lines=[x.rsplit(' ',1)[0]+' gf180_fixed_body_tg' if x.startswith('Xfeedbackmode ') else x for x in lines]
 lines += [f'Xmodecomp{i} cmp drive 0 gf180_mim_22x22' for i in range(a.extra_ota_compensation_mim)]
 lines += [f'Xcaptureextra{i} enc 0 0 gf180_mim_{a.held_mim_size_um}x{a.held_mim_size_um}' for i in range(a.held_mim_count)]
 current_sets={'near-zero':[-.1,-.01,-.001,-.0001,0,.0001,.001,.01,.1,0],'near-zero-short':[0,-.01,.01,0],'wide':[value*settings['feedback_scale'] for value in [0,1,20,200,-200,-20,-1,0]]}
 currents=current_sets[a.current_set]
 ec=a.encode_us*1e-6;dc=a.decode_us*1e-6;slot=ec+dc;points={name:[(0,value)] for name,value in [('current',0),('encode',3.3),('decode',0)]}
 for i,current in enumerate(currents):
  start=start_offset+i*slot;cut=start+ec;end=start+slot
  points['current'] += [(start-100e-9,0),(start,current*1e-9),(cut+10e-9,current*1e-9),(cut+20e-9,0),(end-100e-9,0)]
  points['encode'] += [(start-100e-9,0 if i else 3.3),(start,3.3),(cut-100e-9,3.3),(cut,0),(end-100e-9,0)]
  points['decode'] += [(start-200e-9,3.3 if i else 0),(start-100e-9,0),(cut,0),(cut+100e-9,3.3),(end-200e-9,3.3),(end-100e-9,0)]
 for name,terminal,invert in [('Iinput','sum 0',False),('Vencode','encode 0',False),('Vencodeb','encodeb 0',True),('Vdecode','decode 0',False),('Vdecodeb','decodeb 0',True)]:
  key='current' if name=='Iinput' else ('encode' if name.startswith('Vencode') else 'decode')
  merged={float(f'{t:.12g}'):v for t,v in points[key]}
  waveform=sorted(merged.items())
  if not all(y[0]>x[0] for x,y in zip(waveform,waveform[1:])):raise ValueError('Non-increasing command waveform')
  lines.append(name+' '+terminal+' PWL('+' '.join(f'{t:.12g} {(3.3-v if invert else v):.12g}' for t,v in waveform)+')')
 if a.feedback_release_advance_ns:
  lines=[x.replace('Xfeedbackmode enc feedbackenc encode encodeb ', 'Xfeedbackmode enc feedbackenc feedbackphase feedbackphaseb ') for x in lines]
  fp=[(0,3.3)]
  for i in range(len(currents)):
   start=start_offset+i*slot;release=start+ec-a.feedback_release_advance_ns*1e-9;end=start+slot
   fp += [(start-100e-9,0 if i else 3.3),(start,3.3),(release-100e-9,3.3),(release,0),(end-100e-9,0)]
  fw=sorted({float(f'{t:.12g}'):v for t,v in fp}.items())
  for name,node,invert in [('Vfeedbackphase','feedbackphase',False),('Vfeedbackphaseb','feedbackphaseb',True)]:lines.append(name+' '+node+' 0 PWL('+' '.join(f'{t:.12g} {(3.3-v if invert else v):.12g}' for t,v in fw)+')')
 if a.integrate_charge:
  if a.decode_us not in [5,10]:raise ValueError('Charge integration requires5/10us decode diagnostic')
  if beta_metadata is not None and a.beta_start_delay_ns*1e-9+beta_metadata['beta_float32']*4e-6+a.beta_tail_compensation_ns*1e-9 >= dc-.5e-6:raise ValueError('Beta pulse must finish before final measurement window')
  lines=[x.replace('Vprobe sum mirrorsum 0','Vprobe mirrorroute mirrorsum 0') for x in lines]
  lines+=['Xmirrorencode mirrorroute sum encode encodeb 0 vdd gf180_fixed_body_tg','Xmirrordecode mirrorroute integratefeed decode decodeb 0 vdd gf180_fixed_body_tg','Xintegrator common integratesum linear vdd 0 bias integratecmp gf180_shared_ota_core_pmos_input','Xintegratorcomp integratecmp linear 0 gf180_mim_22x22','Xintegratorload linear 0 0 gf180_mim_7x7','Xintegratorreset linear integratesum encode encodeb 0 vdd gf180_fixed_body_tg','Vcap linear caplinear 0','Vint integratefeed integratesum 0']
  if a.integrator_compensation_size_um!=22:
   lines=[x.replace('gf180_mim_22x22','gf180_mim_7x7') if x.startswith('Xintegratorcomp ') else x for x in lines]
  lines += [f'XintegratorcompExtra{i} integratecmp linear 0 gf180_mim_{a.integrator_compensation_size_um}x{a.integrator_compensation_size_um}' for i in range(a.integrator_compensation_mim_count-1)]
  if a.integrator_reference_ua!=1:
   lines=[x.replace(' 0 bias ', ' 0 integratorbias ') if x.startswith('Xintegrator ') else x for x in lines]
   lines += [f'Iintegratorbias integratorbias 0 {a.integrator_reference_ua}u','Xintegratorbias integratorbias vdd 0 gf180_pmos_bias_reference_grounded']
  if a.encoder_use_integrator_bias:lines=[x.replace(' 0 bias ', ' 0 integratorbias ') if x.startswith('Xota ') else x for x in lines]
  if a.boost_park_bias:
   if a.integrator_reference_ua!=5:raise ValueError('Park bias uses existing physical5uA bias reference')
   lines=[x.replace(' 0 bias ', ' 0 encoderbias ') if x.startswith('Xota ') else x for x in lines]
   lines+=['Xencoderbiasmode bias encoderbias encode encodeb 0 vdd gf180_fixed_body_tg','Xparkbiasmode integratorbias encoderbias decode decodeb 0 vdd gf180_fixed_body_tg']
  if a.mirror_route_overlap:
   lines=[x.replace('Xmirrorencode mirrorroute sum encode encodeb ', 'Xmirrorencode mirrorroute sum routeencode routeencodeb ') for x in lines]
   routepoints=[(0,3.3)]
   for i in range(len(currents)):
    start=start_offset+i*slot;cut=start+ec;end=start+slot
    routepoints += [(start-100e-9,0 if i else 3.3),(start,3.3),(cut+((a.beta_start_delay_ns+(-100 if a.route_break_before_make else 100))*1e-9 if a.beta_delayed_start else 100e-9),3.3),(cut+((a.beta_start_delay_ns+(0 if a.route_break_before_make else 200))*1e-9 if a.beta_delayed_start else 200e-9),0)]
    if beta_metadata is not None:
     stop=cut+a.beta_start_delay_ns*1e-9+beta_metadata['beta_float32']*4e-6+a.beta_tail_compensation_ns*1e-9
     routepoints += [(stop+(0 if a.route_break_before_make else -200e-9),0),(stop+(100e-9 if a.route_break_before_make else -100e-9),3.3),(end-100e-9,3.3)]
    else:routepoints += [(end-100e-9,0)]
   routewave=sorted({float(f'{t:.12g}'):v for t,v in routepoints}.items())
   for name,node,invert in [('Vrouteencode','routeencode',False),('Vrouteencodeb','routeencodeb',True)]:lines.append(name+' '+node+' 0 PWL('+' '.join(f'{t:.12g} {(3.3-v if invert else v):.12g}' for t,v in routewave)+')')
  if beta_metadata is not None:
   lines=[x.replace('Xmirrordecode mirrorroute integratefeed decode decodeb ', 'Xmirrordecode mirrorroute integratefeed betaroute betarouteb ') for x in lines];betapoints=[(0,0)]
   for i in range(len(currents)):
    start=start_offset+i*slot;cut=start+ec;end=start+slot;stop=cut+a.beta_start_delay_ns*1e-9+beta_metadata['beta_float32']*4e-6+a.beta_tail_compensation_ns*1e-9
    betapoints += [(cut+(a.beta_start_delay_ns*1e-9 if a.beta_delayed_start else 0),0),(cut+((a.beta_start_delay_ns+100)*1e-9 if a.beta_delayed_start else 100e-9),3.3),(stop-100e-9,3.3),(stop,0),(end,0)]
   betawave=sorted({float(f'{t:.12g}'):v for t,v in betapoints}.items())
   for name,node,invert in [('Vbetaroute','betaroute',False),('Vbetarouteb','betarouteb',True)]:lines.append(name+' '+node+' 0 PWL('+' '.join(f'{t:.12g} {(3.3-v if invert else v):.12g}' for t,v in betawave)+')')
  if a.integrator_route_dummy:lines += [f'Xintegratordummy{i} integratesum integratesum betarouteb betaroute 0 vdd gf180_fixed_body_tg_nf0p5' for i in range(a.integrator_route_dummy_count)]
  elif a.integrator_route_dummy_count!=1:raise ValueError('Dummy count requires physical integrator route dummy')
  lines += [f'Xintegratorfeedback{i} caplinear integratesum 0 gf180_mim_22x22' for i in range(a.integration_mim_count)]
 if a.physical_park_driver and not (a.physical_beta_driver and a.route_break_before_make):raise ValueError('Physical park driver requires matched beta driver and non-overlap command')
 if a.mode_driver_output_buffers and not a.physical_mode_drivers:raise ValueError('Mode output buffers require physical mode drivers')
 if a.physical_mode_drivers and a.feedback_release_advance_ns:raise ValueError('Physical mode driver diagnostic requires simultaneous feedback/drive release')
 if a.physical_beta_driver or a.physical_mode_drivers:
  if a.physical_beta_driver and beta_metadata is None:raise ValueError('Physical beta gate driver requires beta pulse')
  cell='gf180_phase_inverter';qpath=BASE/'layout'/cell/'qualification.json';q=json.loads(qpath.read_text());cap=qpath.parent/(cell+'_cap.spice')
  if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Unqualified inverter')
  for name,expected in q['sha256'].items():
   path=qpath.parent/name
   if digest(path)!=expected:raise ValueError('Driver provenance mismatch')
   sources.append(path)
  sources.append(qpath);lines[1:1]=cap.read_text().splitlines();r['qualified_layout_components'].append(q)
  if a.physical_beta_driver:
   lines=[x.replace('Vbetaroute betaroute 0 ', 'Vbetacommand betacommand 0 ') for x in lines if not x.startswith('Vbetarouteb ')]
   lines+=['XbetadriverA betacommand betarouteb vdd 0 '+cell,'XbetadriverB betarouteb betaroute vdd 0 '+cell]
  if a.physical_mode_drivers:
   for phase in ['encode','decode']:
    lines=[x.replace('V'+phase+' '+phase+' 0 ', 'V'+phase+'command '+phase+'command 0 ') for x in lines if not x.startswith('V'+phase+'b ')]
    if a.mode_driver_output_buffers:
     lines+=['X'+phase+'preA '+phase+'command '+phase+'preb vdd 0 '+cell,'X'+phase+'preB '+phase+'preb '+phase+'pre vdd 0 '+cell,'X'+phase+'outP '+phase+'preb '+phase+' vdd 0 '+cell,'X'+phase+'outN '+phase+'pre '+phase+'b vdd 0 '+cell]
    else:lines+=['X'+phase+'driverA '+phase+'command '+phase+'b vdd 0 '+cell,'X'+phase+'driverB '+phase+'b '+phase+' vdd 0 '+cell]
  if a.physical_park_driver:
   lines=[x.replace('Vrouteencode routeencode 0 ', 'Vparkcommand parkcommand 0 ') for x in lines if not x.startswith('Vrouteencodeb ')]
   lines+=['XparkdriverA parkcommand routeencodeb vdd 0 '+cell,'XparkdriverB routeencodeb routeencode vdd 0 '+cell]
 if a.cold_start_prelude_us:
  if not a.physical_current_reference:raise ValueError('Cold startup requires physical reference prototype')
  rebuilt=[]
  for line in lines:
   if line.startswith('Vdd '):line='Vdd vdd 0 PWL(0 0 1u 3.3)'
   elif line.startswith('Ireference '):line='Ireference bias 0 PWL(0 0 1u 0 1.1u 1u)'
   elif line.startswith('Iintegratorbias '):line=f'Iintegratorbias integratorbias 0 PWL(0 0 1u 0 1.1u {a.integrator_reference_ua}u)'
   elif line.startswith('V') and ' PWL(' in line:
    prefix,wave=line.split(' PWL(',1);entries=list(map(float,wave.rstrip(')').split()))
    if entries[0]==0 and entries[1]==3.3:line=prefix+' PWL(0 0 1e-6 3.3 '+' '.join(f'{v:.12g}' for v in entries[2:])+')'
   rebuilt.append(line)
  lines=rebuilt
 if a.mismatch_seed is not None:lines=[x.replace('sw_stat_mismatch=0','sw_stat_mismatch=1') for x in lines]
 lines+=['.control','set numdgt=15',f'setseed {a.mismatch_seed if a.mismatch_seed is not None else 17}','reset',f'tran {a.max_step_ns}n {start_offset+len(currents)*slot:.12g}','let signed_current=-i(vprobe)','let power_vdd=-v(vdd)*i(vdd)']
 if a.integrate_charge:
  # Query every native model capacitor and extracted top-to-bottom parasitic;
  # do not infer C from area or integrate cancellation-heavy displacement spikes.
  terms=[f'@c.xintegratorfeedback{i}.x0.c_cap[capacitance]+@c.xintegratorfeedback{i}.c0[capacitance]' for i in range(a.integration_mim_count)]
  lines += ['let feedback_capacitance=0*v(caplinear)+('+ '+'.join(terms)+')','let feedback_stored_charge=(v(caplinear)-v(integratesum))*feedback_capacitance']
  leak_terms=[f'1/@r.xintegratorfeedback{i}.x0.r_leak[resistance]' for i in range(a.integration_mim_count)]
  lines += ['let feedback_leak_current=(v(caplinear)-v(integratesum))*('+ '+'.join(leak_terms)+')']
 if a.cold_start_prelude_us:lines += [f'meas tran startup_calvoltage find v(calspan) at={start_offset-1e-6:.12g}',f'meas tran startup_calcurrent find i(vcalprobe) at={start_offset-1e-6:.12g}',f'meas tran startup_energy integ power_vdd from=0 to={start_offset:.12g}']
 for i,current in enumerate(currents):
  start=start_offset+i*slot;cut=start+ec;end=start+slot
  lines += [f'meas tran encpre_{i} find v(enc) at={cut-300e-9:.12g}',f'meas tran encpost_{i} find v(enc) at={end-.5e-6:.12g}',f'meas tran decoded_{i} find signed_current at={end-.5e-6:.12g}',f'meas tran imin_{i} min signed_current from={end-1e-6:.12g} to={end-.5e-6:.12g}',f'meas tran imax_{i} max signed_current from={end-1e-6:.12g} to={end-.5e-6:.12g}',f'meas tran sumlate_{i} find v(sum) at={end-.5e-6:.12g}',f'meas tran commonlate_{i} find v(common) at={end-.5e-6:.12g}',f'meas tran energy_{i} integ power_vdd from={start:.12g} to={end:.12g}']
  lines += [f'meas tran feedbackpre_{i} find v(enc) at={cut-a.feedback_release_advance_ns*1e-9-200e-9:.12g}',f'meas tran capturepre_{i} find v(enc) at={cut-1e-9:.12g}',f'meas tran captureearly_{i} find v(enc) at={cut+200e-9:.12g}']
  if a.physical_current_reference:lines += [f'meas tran calcurrent_{i} find i(vcalprobe) at={cut-300e-9:.12g}',f'meas tran lowcurrent_{i} find i(vlowprobe) at={cut-300e-9:.12g}',f'meas tran calvoltage_{i} find v(calspan) at={cut-300e-9:.12g}',f'meas tran lowvoltage_{i} find v(lowcalspan) at={cut-300e-9:.12g}']
  if a.integrate_charge:
   lines += [f'meas tran linpre_{i} find v(linear) at={cut+(a.beta_start_delay_ns if beta_metadata is not None and a.beta_delayed_start else a.charge_window_start_ns)*1e-9:.12g}',f'meas tran linpost_{i} find v(linear) at={end-.5e-6:.12g}',f'meas tran qinput_{i} integ i(vint) from={cut+(a.beta_start_delay_ns if beta_metadata is not None and a.beta_delayed_start else a.charge_window_start_ns)*1e-9:.12g} to={end-.5e-6:.12g}',f'meas tran qcap_{i} integ i(vcap) from={cut+(a.beta_start_delay_ns if beta_metadata is not None and a.beta_delayed_start else a.charge_window_start_ns)*1e-9:.12g} to={end-.5e-6:.12g}',f'meas tran intsumlate_{i} find v(integratesum) at={end-.5e-6:.12g}']
  if a.integrate_charge:
   aperture=cut+(a.beta_start_delay_ns if beta_metadata is not None and a.beta_delayed_start else a.charge_window_start_ns)*1e-9
   lines += [f'meas tran cfvalue_{i} find feedback_capacitance at={aperture:.12g}',f'meas tran qstoredpre_{i} find feedback_stored_charge at={aperture:.12g}',f'meas tran qstoredpost_{i} find feedback_stored_charge at={end-.5e-6:.12g}',f'meas tran qstoredsettledpre_{i} find feedback_stored_charge at={aperture-300e-9:.12g}',f'meas tran qcapsettled_{i} integ i(vcap) from={aperture-300e-9:.12g} to={end-.5e-6:.12g}',f'meas tran qleak_{i} integ feedback_leak_current from={aperture:.12g} to={end-.5e-6:.12g}',f'meas tran qleaksettled_{i} integ feedback_leak_current from={aperture-300e-9:.12g} to={end-.5e-6:.12g}']
  if a.physical_mode_drivers:lines += [f'meas tran encodefall_{i} when v(encode)=1.65 fall=1 td={cut-100e-9:.12g}',f'meas tran decoderise_{i} when v(decode)=1.65 rise=1 td={cut-100e-9:.12g}',f'meas tran encodebrise_{i} when v(encodeb)=1.65 rise=1 td={cut-100e-9:.12g}',f'meas tran decodebfall_{i} when v(decodeb)=1.65 fall=1 td={cut-100e-9:.12g}']
  if a.physical_beta_driver:lines += [f'meas tran betarise_{i} when v(betaroute)=1.65 rise=1 td={cut:.12g}',f'meas tran betafall_{i} when v(betaroute)=1.65 fall=1 td={cut:.12g}']
  if a.physical_park_driver:lines += [f'meas tran parkfall_{i} when v(routeencode)=1.65 fall=1 td={cut:.12g}',f'meas tran parkrise_{i} when v(routeencode)=1.65 rise=1 td={cut:.12g}']
  if a.beta_phase_charge_probes:
   pulsebegin=cut+a.beta_start_delay_ns*1e-9;pulseend=pulsebegin+beta_metadata['beta_float32']*4e-6+a.beta_tail_compensation_ns*1e-9
   for label,left,right in [('qstartup',pulsebegin,pulsebegin+200e-9),('qsteady',pulsebegin+200e-9,pulseend-200e-9),('qclosing',pulseend-200e-9,pulseend+200e-9),('qpark',pulseend+200e-9,end-.5e-6)]:
    lines.append(f'meas tran {label}_{i} integ i(vint) from={left:.12g} to={right:.12g}')

 lines+=['quit','.endc','.end'];snapshot=BASE/'tools/source_snapshots'/f'shared_encoder_inverse_{sha}.py'
 if not snapshot.exists():snapshot.write_bytes(source.read_bytes())
 sources.append(snapshot);stem=f"gf180_shared_encoder_inverse_{settings['corner']}{settings['temp_c']:g}_src{sha[:12]}_enc{a.encode_us}us_dec{a.decode_us}us"
 if a.calibration_current_override_na is not None:stem+=f'_calref{a.calibration_current_override_na:g}na'
 if a.encoder_use_integrator_bias:stem+='_encoderBias5ua'
 if a.physical_current_reference:stem+='_physicalCurrentDivider'
 if a.physical_beta_driver:stem+='_physicalBetaDriver'
 if a.physical_park_driver:stem+='_physicalParkDriver'
 if a.physical_mode_drivers:stem+='_physicalModeDrivers'
 if a.mode_driver_output_buffers:stem+='_modeOutputBuffers'
 if a.reference_filter_mim_count:stem+=f'_calFilter{a.reference_filter_mim_count}mim22'
 if a.cold_start_prelude_us:stem+=f'_coldPrelude{a.cold_start_prelude_us}us'
 if a.lift_reference_override_na is not None:stem+=f'_liftref{a.lift_reference_override_na}na'
 if a.beta_delayed_start:stem+='_betaDelayedStart'
 if a.beta_delayed_start:stem+=f'_betaStart{a.beta_start_delay_ns}ns'
 if a.isolated_held_gate_layout:stem+='_isolatedHeldGate'
 if a.isolated_mirror_drain_layout:stem+='_isolatedMirrorDrains'
 if a.boost_park_bias:stem+='_boostParkBias'
 if beta_metadata is not None:stem+='_beta'+a.learned_beta_actor.replace('.','_')+f'_ch{a.learned_beta_channel}_tail{a.beta_tail_compensation_ns}ns'
 if a.integrate_charge:stem+=f'_integrate{a.integration_mim_count}mim'
 if a.integrate_charge and a.integrator_compensation_size_um!=22:stem+=f'_intcomp{a.integrator_compensation_size_um}um'
 if a.integrate_charge and a.integrator_compensation_mim_count!=1:stem+=f'_intcompcount{a.integrator_compensation_mim_count}'
 if a.dump_integration_waveforms:stem+='_waveforms'
 if a.integrate_charge and a.integrator_reference_ua!=1:stem+=f'_intbias{a.integrator_reference_ua}ua'
 if a.mirror_route_overlap:stem+='_routeoverlap'
 if a.charge_window_start_ns!=200:stem+=f'_chargeStart{a.charge_window_start_ns}ns'
 if a.current_set!='wide':stem+='_'+a.current_set.replace('-','')
 if a.max_step_ns!=500:stem+=f'_maxstep{a.max_step_ns}ns'
 if a.tight_charge_solver:stem+='_tightChargeSolver'
 if a.refined_charge_solver:stem+='_refinedChargeSolver'
 if a.capture_dummy:stem+='_captureDummy'
 if a.capture_dummy_pf_width_um is not None:stem+='_capturePF'+f'{a.capture_dummy_pf_width_um:g}'
 if a.capture_dummy_nf_width_um is not None:stem+='_captureDummyNF'+f'{a.capture_dummy_nf_width_um:g}'.replace('.','p')
 if a.feedback_mode_nf_width_um is not None:stem+='_feedbackModeNF1'
 if a.mode_switch_nf_width_um!=1:stem+='_modeTGnf'+f'{a.mode_switch_nf_width_um:g}'.replace('.','p')
 if a.extra_ota_compensation_mim:stem+='_extraMiller'
 if a.route_break_before_make:stem+='_routeBreakBeforeMake'
 if a.integrator_route_dummy:stem+='_routeDummyNf0p5'
 if a.integrator_route_dummy and a.integrator_route_dummy_count!=1:stem+=f'_routeDummyCount{a.integrator_route_dummy_count}'
 if a.beta_phase_charge_probes:stem+='_phaseChargeProbes'
 if a.held_mim_count:stem+=f'_held{a.held_mim_count}mim{a.held_mim_size_um}'
 if a.isolate_feedback_mode:stem+='_feedbackisolated'
 if a.feedback_release_advance_ns:stem+=f'_feedbackEarly{a.feedback_release_advance_ns}ns'
 if a.mismatch_seed is not None:stem+=f'_mismatchseed{a.mismatch_seed}'
 descriptive_stem=stem
 if len(stem)>210:stem=stem[:100]+'_run'+hashlib.sha256(stem.encode()).hexdigest()[:24]
 wavepath=BASE/'results'/(stem+'_waveforms.dat')
 if a.dump_integration_waveforms:
  if not a.integrate_charge:raise ValueError('Integration waveform dump requires physical integrator')
  lines[lines.index('quit'):lines.index('quit')]=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+wavepath.relative_to(ROOT).as_posix()+' v(linear) v(integratesum) v(common) v(enc) signed_current i(vcap) i(vint)']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
 proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2','--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir','/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=135)
 if wavepath.exists():sources.append(wavepath)
 log=proc.stdout;logpath=BASE/'results'/(stem+'.log');logpath.write_text(log);sources+=[deck,logpath]
 values={k:float(v) for k,v in re.findall(r'(?m)^\s*((?:encodebrise|decodebfall|encodefall|decoderise|qleaksettled|qleak|cfvalue|qstoredpre|qstoredpost|qstoredsettledpre|qcapsettled|parkfall|parkrise|betarise|betafall|calcurrent|lowcurrent|calvoltage|lowvoltage|feedbackpre|capturepre|captureearly|encpre|encpost|decoded|imin|imax|sumlate|commonlate|energy|linpre|linpost|qinput|qcap|intsumlate|qstartup|qsteady|qclosing|qpark)_\d+)\s*=\s*([-+0-9.eE]+)',log)}
 fields=['feedbackpre','capturepre','captureearly','encpre','encpost','decoded','imin','imax','sumlate','commonlate','energy']+(['linpre','linpost','qinput','qcap','intsumlate','cfvalue','qstoredpre','qstoredpost','qstoredsettledpre','qcapsettled','qleak','qleaksettled'] if a.integrate_charge else [])+(['qstartup','qsteady','qclosing','qpark'] if a.beta_phase_charge_probes else [])+(['calcurrent','lowcurrent','calvoltage','lowvoltage'] if a.physical_current_reference else [])+(['betarise','betafall'] if a.physical_beta_driver else [])+(['parkfall','parkrise'] if a.physical_park_driver else [])+(['encodefall','decoderise','encodebrise','decodebfall'] if a.physical_mode_drivers else []);rows=[]
 if len(values)==len(fields)*len(currents):
  for i,current in enumerate(currents):
   row={'input_current_na':current,**{k:values[f'{k}_{i}'] for k in fields}};row.update({'decoded_current_na':row['decoded']*1e9,'current_error_na':row['decoded']*1e9-current,'encode_to_decode_voltage_change_uv':(row['encpost']-row['encpre'])*1e6,'decoded_final_window_ripple_na':(max(row['imax'],row['decoded'])-min(row['imin'],row['decoded']))*1e9,'sum_minus_reference_uv':(row['sumlate']-row['commonlate'])*1e6});
   if a.integrate_charge:row.update({'linear_voltage_change_v':row['linpost']-row['linpre'],'delivered_mirror_charge_fc':row['qinput']*1e15,'capacitor_top_charge_fc':row['qcap']*1e15,'mirror_plus_cap_top_charge_fc':(row['qinput']+row['qcap'])*1e15,'integrator_sum_minus_reference_uv':(row['intsumlate']-row['commonlate'])*1e6})
   if a.integrate_charge:row.update({'feedback_capacitance_f':row['cfvalue'],'endpoint_capacitor_top_charge_fc':(row['qstoredpost']-row['qstoredpre'])*1e15,'endpoint_integral_difference_fc':(row['qstoredpost']-row['qstoredpre']-row['qcap'])*1e15,'settled_endpoint_capacitor_top_charge_fc':(row['qstoredpost']-row['qstoredsettledpre'])*1e15,'settled_endpoint_integral_difference_fc':(row['qstoredpost']-row['qstoredsettledpre']-row['qcapsettled'])*1e15,'feedback_leak_charge_fc':row['qleak']*1e15,'settled_feedback_leak_charge_fc':row['qleaksettled']*1e15})
   rows.append(row)
 startup_measures={k:float(v) for k,v in re.findall(r'(?m)^\s*(startup_calvoltage|startup_calcurrent|startup_energy)\s*=\s*([-+0-9.eE]+)',log)}
 complete=proc.returncode==0 and 'ngspice-47 done' in log and len(rows)==len(currents) and (not a.cold_start_prelude_us or len(startup_measures)==3)
 analysis={} if not complete else {'maximum_current_error_na':max(abs(x['current_error_na']) for x in rows),'maximum_encode_to_decode_voltage_change_uv':max(abs(x['encode_to_decode_voltage_change_uv']) for x in rows),'maximum_decoded_ripple_na':max(x['decoded_final_window_ripple_na'] for x in rows),'maximum_sum_minus_reference_uv':max(abs(x['sum_minus_reference_uv']) for x in rows),'mean_vdd_energy_per_encode_decode_pj':sum(x['energy']*1e12 for x in rows)/len(rows)}
 if complete and beta_metadata is not None:
  for row in rows:
   row['beta_command_charge_fc']=row['input_current_na']*4*beta_metadata['beta_float32'];row['beta_command_charge_error_fc']=row['delivered_mirror_charge_fc']-row['beta_command_charge_fc'];row['effective_integrated_charge_fc']=-row['capacitor_top_charge_fc'];row['effective_beta_charge_error_fc']=row['effective_integrated_charge_fc']-row['beta_command_charge_fc']
 if complete and a.integrate_charge:
  analysis.update({'maximum_integrator_sum_minus_reference_uv':max(abs(x['integrator_sum_minus_reference_uv']) for x in rows),'maximum_charge_balance_residual_fc':max(abs(x['mirror_plus_cap_top_charge_fc']) for x in rows),'linear_output_range_v':[min(x['linpost'] for x in rows),max(x['linpost'] for x in rows)]})
 report={'cold_start_measurements':startup_measures,'simulation_completed':complete,'simulator_returncode':proc.returncode,'command_arguments':vars(a),'learned_beta_metadata':beta_metadata,'encoder_settings':settings,'mismatch_seed_applied_via_reset':a.mismatch_seed is not None,'descriptive_run_name':descriptive_stem,'waveform_path':wavepath.relative_to(ROOT).as_posix() if wavepath.exists() else None,'source_snapshot':snapshot.relative_to(ROOT).as_posix(),'rows':rows,'analysis':analysis,'qualified_layout_components':r['qualified_layout_components'],'operating_point_solver_warning':bool(re.search('singular matrix|stepping failed|Transient op started',log,re.I)),'physical_state_accepted':False,'inverse_accepted':False,'full_chip_accepted':False,'scope':'Shared extracted six-MOS mirror and seven-MOS OTA, two physical output mode TGs; ENC held on actual load/capture capacitance during inverse, held_mim_count adds physical7/22um MIMs only to this shared module bench, not a proven per-resident-state array design. Physical hysteresis compensation controller/reference buffers included. Diagnostic input current and complementary mode clocks remain ideal. Clock ramps100ns and solver reltol1e-6/vntol1e-9 explicit; numerical repeat still required. capture_dummy adds a same-size extracted TG with both analog terminals tied to ENC and opposite gate clocks; cancellation must be measured. Measures actual reuse/mode charge disturbance including local statistical cards when enabled; no ideal voltage command or mathematical inverse. No PLIF beta/reset/adaptation, actual weighted-event generator, tiny-current generator, sampled noise, packed resident array, combined layout/RPEX/silicon gate leakage or model/service acceptance. With isolate_feedback_mode an additional physical TG opens the feedback-capacitor ENC path during decode; otherwise feedback MIMs remain attached. Input command is removed after encoded gate isolation, not before capture; this is a module diagnostic, not a qualified minimum storage cell.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in set(sources)}}
 if a.feedback_release_advance_ns:report['scope']+=' Physical feedback-capacitor isolation TG uses independent phase relative to held-gate drive TG; positive advance opens earlier, negative advance opens later; native circuit unchanged, independent ideal diagnostic phase clock. Passive measurements separate feedback release, drive capture and early held movement; settling/stability/noise remain unqualified.'
 if a.physical_current_reference:report['scope']+=' Extracted six-MOS divider/low mirror replaces both ideal calibration currents using existing physical1uA PF bias gate. Actual current and compliance measured per slot; donor settings are historical nominal values, not actual currents. Root1uA and integrator5uA generators remain ideal/external. Shared extra current-reference supply cost included; noise/startup/combined routing/model precision remain unqualified.'
 if a.calibration_current_override_na is not None:report['scope']+=' Actual physical calibration diode-stack current changed explicitly; same native devices/buffers, no ideal voltage/gain correction. Current generator, noise, precision and minimum service still require qualification.'
 if a.refined_charge_solver:report['scope']+=' Refined solver explicitly overrides generic scope tolerances: reltol1e-7/vntol1e-11, original abstol1e-17 retained. Same physical deck; comparisons do not define analog tolerance.'
 if a.physical_beta_driver:report['scope']+=' Actual extracted inverter pair generates beta complementary gates from one ideal upstream command; supply cost, finite drive, gate loading and rise/fall timing measured. Other phase clocks and upstream sequencing remain ideal; actual non-overlap/charge/noise need qualification.'
 if a.integrate_charge:report['scope']+=' Additional endpoint charge uses the simulator-reported temperature/statistics-adjusted capacitance of every actual native feedback MIM and its extracted P-to-M parasitic, and voltage across caplinear/integratesum. Same-aperture and300ns-before-route apertures are diagnostic comparisons; retain legacy current integral and do not treat disagreement as physical precision.'
 if a.mode_driver_output_buffers:report['scope']+=' Mode inverter trees have separately driven final complementary outputs (four actual qualified inverter instances per encode/decode tree). Reverses stage-count asymmetry versus simple two-inverter chain and isolates output gate loads from predriver internal nodes; physical complementary edge skew measured, not guaranteed balance/non-overlap. Four extra shared inverter standalone footprints, no combined layout/physical sequencer acceptance.'
 if a.physical_mode_drivers:report['scope']+=' Actual separate native inverter pairs replace encode/decode complementary gate sources, including capture/feedback/reset switches, with their real gate loading and supply current. Midpoint capture/decode gap measured. Upstream PWL commands still ideal; no fabricated sequencer, sampled-noise or combined route acceptance.'
 if a.physical_park_driver:report['scope']+=' Matched extracted inverter pair generates complementary park gates, replacing both ideal park gate sources. Actual park rise/fall and beta/park midpoint deadtimes measured; midpoint timing does not prove transistor conduction non-overlap. Upstream sequencer/encode/decode clocks still ideal.'
 if a.tight_charge_solver:report['scope']+=' Tight solver explicitly overrides generic scope tolerances: reltol1e-8/vntol1e-11/abstol1e-19; same physical deck, no accuracy acceptance from convergence alone.'
 if a.cold_start_prelude_us:report['scope']+=' Diagnostic cold startup ramps supplies/high initial controls0-to3.3V in1us and ideal root currents after supply ramp; all event/measurement times shift by specified prelude, no initialized operating point at powered voltage. Actual floating CAL voltage/current and VDD startup energy measured before first command. Physical power-on/reference/controller sequencing remains unimplemented.'
 if a.reference_filter_mim_count:report['scope']+=' Physical22um MIM shunts CAL diode-stack reference to grounded substrate/ground for stationary-noise filtering. Added shared reference area, startup and sampled/phase noise must be measured; no ideal filter or precision acceptance.'
 if a.encoder_use_integrator_bias:report['scope']+=' Encoder OTA directly uses existing physical5uA PF integrator reference during all phases, without added ideal bias voltage or mode switches. Original detector/reference-buffer bias stays1uA. Extra OTA supply current is measured; stability/capture/noise require evidence.'
 if a.lift_reference_override_na is not None:report['scope']+=' Physical diode-stack low-reference current changed from donor setting by explicit diagnostic override; reference geometry/buffer/cards unchanged, ideal current generator remains unqualified. No ideal voltage translation or mathematical curve correction.'
 if a.route_break_before_make:report['scope']+=' Diagnostic non-overlap routes turn park fully off before beta starts and reconnect only after beta fully off. Tests overlap cross-current between offset virtual sums; floating mirror drain/held-gate disturbance still requires qualification.'
 if a.capture_dummy_nf_width_um is not None:report['scope']+=' Explicit independent capture dummy uses native NF/PF width pair'+str([a.capture_dummy_nf_width_um,a.capture_dummy_pf_width_um if a.capture_dummy_pf_width_um is not None else 2*a.capture_dummy_nf_width_um])+'um; both analog terminals tied to ENC and complementary mode gates reversed. Actual charge/noise/PVT cancellation must be measured; no ideal subtraction.'
 if a.integrator_route_dummy:report['scope']+=' '+str(a.integrator_route_dummy_count)+' half-width actual extracted TG dummy instance(s) has both analog ports tied to integrator SUM and beta gates reversed; test physical edge-charge cancellation. Dummy current bypasses Vint, so effective integrated charge is minus measured capacitor-top charge; Vint remains main-route current and charge-balance residual includes dummy injection. No ideal correction.'
 if a.isolated_mirror_drain_layout:report['scope']+=' SUM output-drain rail also separated to-20um with connected VSS guard; actual new qualified layout instance, capacitance extraction only.'
 if a.isolated_held_gate_layout:report['scope']+=' Feedback instance uses new separately qualified isolated ENC rail/VSS guard layout; original profile components remain provenance inputs, modified instance is explicit. Device topology/dimensions unchanged; transfer/noise/PVT/combined-layout qualification still required.'
 if a.integrate_charge:report['scope']+=' Vint probes actual integrator-route current, not total mirror current parked after beta. Learned beta when selected physically gates that route off; beta_delayed_start opens it only after the feedback reset/capture startup, so pre-window current is parked rather than integrated and parks current at encoder sum; clocks remain ideal, capture and pulse-edge errors require calibration, no weighted-event/reset/adaptation/5ms semantic acceptance. Additional separate physical7MOS charge OTA,32/64 actual22um feedback MIMs, mirror routing TGs and feedback-reset TG integrate decoded current. Input current probe observes actual mirror charge; cap-top probe observes actual capacitor current. Encoder OTA stays unity-clamped in decode. boost_park_bias optionally uses two physical TGs to select1uA-reference gate bias during encode and existing5uA-reference gate bias during decode/park, with actual MOS timing/charge included; no ideal bias voltage. Separate integrator compensation size and optional physical PF bias instance/current are explicit in arguments; source-current generator remains ideal, physical bias noise and VDD cost included in circuit. Upstream control waveforms remain ideal; switch gate sources are physical only where explicitly selected. Integration window excludes first charge_window_start_ns (200/500ns) and last500ns; mirror_route_overlap keeps encode route on until decode route conducts, while held ENC capture timing is unchanged; no delivered-weight or once-per-bin beta/reset/adaptation semantics acceptance. Capacitors are shared diagnostic feedback, not31M resident cells.'
 target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(target),'simulation_completed':complete,'analysis':analysis},indent=2))
 if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
