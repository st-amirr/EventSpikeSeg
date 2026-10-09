from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'artifacts/analog_asic'; BENCH=OUT/'benches'; RES=OUT/'results'
COMMON='''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
'''
def main():
  import re,sys
  arg=lambda k,d: next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith(k+'=')),str(d))
  count=int(arg('--events',100)); packet=float(arg('--packet-cap-um',1)); cmem=float(arg('--membrane-cap-um',100)); step=float(arg('--packet-step-v',.3)); tstep=float(arg('--tstep-ns',20)); timeout=int(arg('--timeout-s',180))
  corner=arg('--corner','tt'); temp_c={'ss':0,'tt':27,'ff':85}.get(corner)
  if temp_c is None: raise ValueError('--corner must be ss, tt, or ff')
  common=COMMON.replace('__tt.corner.spice',f'__{corner}.corner.spice').replace('.option scale=1u',f'.option scale=1u\n.temp {temp_c}')
  float_site=arg('--float-fanin-site',''); float_order=arg('--float-event-order','shuffle'); float_events=None; float_target=None; float_packet_scale=float(arg('--float-packet-scale',1.0))
  neutral_reference='--neutral-reference' in sys.argv[1:]
  global_bias_offset_mv=float(arg('--global-bias-offset-mv',0))
  neutral_bias_offset_mv=float(arg('--neutral-bias-offset-mv',0))
  physical_init='--physical-init' in sys.argv[1:]
  startup_feedback='--startup-feedback' in sys.argv[1:]
  active_case=arg('--active-case','all')
  if float_site:
    import random, numpy as np
    source_stems={'near_threshold_scale':'sky130_ms_first_touch_float_fanin_ss0_near_threshold_scale_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly','high_cancellation':'sky130_ms_first_touch_float_fanin_ss0_high_cancellation_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly','max_fanin':'sky130_ms_first_touch_float_fanin_ss0_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n'}
    if float_site not in source_stems or float_order not in ('forward','reverse','shuffle'): raise ValueError('invalid full-float site/order')
    ref=OUT/'model_reference'; meta=json.loads((ref/'float_patch_trace_all.json').read_text()); source=json.loads((RES/f'{source_stems[float_site]}_deck.json').read_text())
    if meta['checkpoint_sha256']!='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7' or meta['qat_or_quantized_reference_used'] or source['qat_or_quantized_reference_used']: raise ValueError('float source/checkpoint provenance mismatch')
    archive=np.load(ref/meta['trace_archive']); params=np.load(ref/'eventspikeseg140k_float_parameters.npz'); inputs=archive['presynaptic_input__final_fuse__standard']; weights=params['weight__final_fuse__standard']; batch=source['selected_flat_batch']; output=source['selected_output_channel']; y,x=source['selected_yx']; expanded=[]
    for ic in range(weights.shape[1]):
      for ky in range(weights.shape[2]):
        for kx in range(weights.shape[3]):
          iy,ix=y+ky-1,x+kx-1
          if 0<=iy<inputs.shape[-2] and 0<=ix<inputs.shape[-1]: expanded.extend([float(weights[output,ic,ky,kx])]*int(inputs[batch,ic,iy,ix]))
    if len(expanded)!=source['event_count'] or abs(sum(expanded)-source['sum_folded_float_event_weights'])>1e-4: raise ValueError('float event expansion failed source validation')
    ordered=sorted(expanded,key=lambda value:(value>0,abs(value)))
    if float_order=='reverse': ordered=list(reversed(ordered))
    elif float_order=='shuffle': random.Random(140).shuffle(ordered)
    float_events=ordered; count=len(ordered); active_case='float_fanin'; float_target=sum(ordered)*6.521267959225942e-5
  if active_case not in ('all','p_train','n_train','mixed','mixed_reverse','float_fanin'): raise ValueError('unknown active case')
  if not neutral_reference and neutral_bias_offset_mv: raise ValueError('neutral bias offset requires neutral reference')
  if startup_feedback and not physical_init: raise ValueError('startup feedback requires physical init')
  if abs(neutral_bias_offset_mv)>2: raise ValueError('neutral bias offset outside bounded screen')
  times=[500+i*4000/max(count-1,1) for i in range(count)]
  cases={'ref':[],'p_train':['p']*count,'n_train':['n']*count,'mixed':['p' if i%2==0 else 'n' for i in range(count)]}
  if float_events is not None: cases={'ref':[],'float_fanin':float_events}
  if active_case=='mixed_reverse': cases['mixed_reverse']=['n' if i%2==0 else 'p' for i in range(count)]
  if active_case!='all': cases={name:sequence for name,sequence in cases.items() if name in ('ref',active_case)}
  if neutral_reference: cases['neutral']=['z']*count
  lines=[f'SKY130 {corner.upper()} {temp_c}C active OTA virtual-node SC integrator many-event screen',common,'Vdd vdd 0 1.8','Vcm vcm 0 0.9','Vbp vbiasp 0 0.75']
  for name,seq in cases.items():
    bias_n=0.65+global_bias_offset_mv*1e-3+(neutral_bias_offset_mv*1e-3 if name=='neutral' else 0)
    init_node='vcm' if physical_init else '0'
    init_wave='PWL(0 1.8 99.9u 1.8 100u 0 5005u 0)' if physical_init else '0'
    initb_wave='PWL(0 0 99.9u 0 100u 1.8 5005u 1.8)' if physical_init else '1.8'
    lines += [f'Vbn_{name} vbiasn_{name} 0 {bias_n:.9g}',f'.ic v(out_{name})=0 v(sum_{name})=0.9',
      f'Vreset_{name} reset_{name} 0 0',f'Vresetb_{name} resetb_{name} 0 1.8',
      f'Vinit_{name} init_{name} 0 {init_wave}',f'Vinitb_{name} initb_{name} 0 {initb_wave}']
    for ctrl in ('packet_reset','connect'):
      off,on=(0,1.8)
      pts=[('0',str(1.8 if ctrl=='packet_reset' else 0))]
      if ctrl=='packet_reset':
        for i,t in enumerate(times):
          pts += [(f'{t-1.1:g}u','0'),(f'{t+1.6:g}u','1.8')]
          if i+1<len(times): pts.append((f'{times[i+1]-1.1:g}u','0'))
        if count==0: pts.append(('5005u','1.8'))
      else:
        for t in times: pts += [(f'{t-.5:g}u','0'),(f'{t-.4:g}u','1.8'),(f'{t+1.4:g}u','1.8'),(f'{t+1.5:g}u','0')]
      if ctrl=='connect': pts.append(('5005u','0'))
      wave='PWL('+' '.join(f'{t} {v}' for t,v in pts)+')'
      lines += [f'V{ctrl}_{name} {ctrl}_{name} 0 {wave}',f'V{ctrl}b_{name} {ctrl}b_{name} 0 '+('PWL('+' '.join(f'{t} {1.8-float(v):g}' for t,v in pts)+')')]
    pts=[('0','0.9')]
    for t,s in zip(times,seq):
      if s=='p': level=0.9+step
      elif s=='n': level=0.9-step
      elif s=='z': level=0.9
      else: level=0.9-float(s)*6.521267959225942e-5*float_packet_scale*(cmem/packet)**2
      pts += [(f'{t-.1:g}u','0.9'),(f'{t:g}u',f'{level:g}'),(f'{t+1.4:g}u',f'{level:g}'),(f'{t+1.5:g}u','0.9')]
    pts.append(('5005u','0.9'))
    if name=='ref': pts=[('0','0.9'),('5005u','0.9')]
    lines += [f'Vpkt_{name} ptop_{name} 0 PWL('+' '.join(f'{t} {v}' for t,v in pts)+')',
      f'Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} {init_node} init_{name} initb_{name} connect_{name} connectb_{name} vbiasn_{name} vbiasp vdd 0 vcm sky130_sc_charge_integrator cpacket_um={packet:g} cmem_um={cmem:g}']
    if startup_feedback:
      lines += [f'Vfb_{name} fb_{name} 0 PWL(0 1.8 449.9u 1.8 450u 0 5005u 0)',
                f'Vfbb_{name} fbb_{name} 0 PWL(0 0 449.9u 0 450u 1.8 5005u 1.8)',
                f'Rfb_{name} out_{name} fbnode_{name} 1Meg',
                f'Xfb_{name} fbnode_{name} sum_{name} fb_{name} fbb_{name} vdd 0 transmission_gate']
  lines += ['.control','set numdgt=15',f'tran {tstep:g}n 5.005m uic']
  for tm,tag in [('499u','pre'),('2.5m','mid'),('4.9m','late'),('5m','final')]:
    for name in cases: lines += [f'meas tran {tag}_{name} find v(out_{name}) at={tm}']
  lines += ['quit','.endc','.end']
  BENCH.mkdir(parents=True,exist_ok=True); RES.mkdir(parents=True,exist_ok=True)
  tag=f'n{count}_cp{packet:g}_cm{cmem:g}_step{step:g}_ts{tstep:g}n'+('_neutral' if neutral_reference else '')+('' if active_case=='all' else f'_{active_case}')+(f'_{float_site}_{float_order}_scale{float_packet_scale:g}'.replace('.','p') if float_site else '')+(f'_{corner}_temp{temp_c}' if float_site else '')+(f'_gbias{global_bias_offset_mv:g}mv'.replace('-','m').replace('.','p') if global_bias_offset_mv else '')+(f'_nbias{neutral_bias_offset_mv:g}mv'.replace('-','m').replace('.','p') if neutral_bias_offset_mv else '')+('_init100u' if physical_init else '')+('_fbstart1m' if startup_feedback else '')
  deck=BENCH/f'sky130_sc_integrator_many_events_{tag}.cir'; deck.write_text('\n'.join(lines)+'\n')
  cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36',str(timeout),'ngspice','-b',deck.name]
  proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout+15); log=proc.stdout+proc.stderr; (RES/f'sky130_sc_integrator_many_events_{tag}.log').write_text(log)
  names='|'.join(cases)
  vals={f'{phase}_{name}':float(value) for phase,name,value in re.findall(rf'(?im)^\s*(pre|mid|late|final)_({names})\s*=\s*([-+0-9.eE]+)',log)}
  complete=proc.returncode==0 and len(vals)==4*len(cases)
  changes={}; neutral_changes={}
  if complete:
    for name in ('p_train','n_train','mixed','mixed_reverse','float_fanin'):
      if name in cases: changes[name]={phase:(vals[f'{phase}_{name}']-vals[f'{phase}_ref'])*1e3 for phase in ('pre','mid','late','final')}
    if neutral_reference:
      for name in ('p_train','n_train','mixed','mixed_reverse','float_fanin'):
        if name in cases: neutral_changes[name]={phase:(vals[f'{phase}_{name}']-vals[f'{phase}_neutral'])*1e3 for phase in ('pre','mid','late','final')}
  report={'test':'sky130_active_ota_sc_virtual_node_many_event_screen','simulation_completed':complete,'return_code':proc.returncode,'mos_corner':corner,'temperature_c':temp_c,'global_bias_offset_mv':global_bias_offset_mv if float_site else None,'event_count_per_train':count,'active_case':active_case,'full_float_fanin_site':float_site or None,'full_float_event_order':float_order if float_site else None,'full_float_checkpoint_sha256':'c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7' if float_site else None,'qat_or_quantized_reference_used':False if float_site else None,'target_state_change_v':float_target,'packet_cap_square_um':packet,'membrane_feedback_cap_square_um':cmem,'packet_topplate_step_v':step,'ideal_weight_to_packet_ratio':6.521267959225942e-5*float_packet_scale*(cmem/packet)**2 if float_site else None,'shared_analog_packet_gain_scale':float_packet_scale if float_site else None,'packet_polarity_inverted_for_ota_sign':bool(float_site),'neutral_reference_ota_bias_offset_mv':neutral_bias_offset_mv if neutral_reference else None,'physical_vcm_init_duration_us':100 if physical_init else None,'startup_feedback_resistance_ohm':1e6 if startup_feedback else None,'startup_feedback_open_us':450 if startup_feedback else None,'event_times_us':[times[0],times[-1]],'requested_action_window_us':2.0,'physical_zero_charge_reference_branch':neutral_reference,'read_state_difference_from_no_event_reference_mv':changes,'read_state_difference_from_neutral_event_reference_mv':neutral_changes,'measured_absolute_nodes_v':vals,'scope':f"One active OTA virtual-summing-node integrator at SKY130 {corner.upper()}/{temp_c}C, matched no-event reference and full5ms transient. In full-float mode, each signed packet voltage is ideal and proportional to its original epoch58 float weight with polarity inverted to compensate OTA inversion and optionally scaled by one shared analog gain; this isolates active bucket write/hold, not physical weight encoding. Any global bias offset is common to both event and reference OTA branches; the optional neutral-reference offset is branch-specific. No physical weight DAC, noise/mismatch, threshold/reset/adaptation, layout/extraction, or full-network feedback."}
  out=RES/f'sky130_sc_integrator_many_events_{tag}.json'; out.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2)); return 0 if complete else 2
if __name__=='__main__': raise SystemExit(main())
