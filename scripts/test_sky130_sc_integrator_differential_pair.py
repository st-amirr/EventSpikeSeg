"""Bounded differential active-bucket replay using complementary full-float packets."""
from __future__ import annotations
import json, random, re, subprocess, sys
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
SOURCES={
 'near_threshold_scale':'sky130_ms_first_touch_float_fanin_ss0_near_threshold_scale_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly',
 'high_cancellation':'sky130_ms_first_touch_float_fanin_ss0_high_cancellation_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly',
 'max_fanin':'sky130_ms_first_touch_float_fanin_ss0_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n',
}

def main():
    order=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--order=')),'shuffle')
    probe=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--probe=')),'full')
    corner=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--corner=')),'tt')
    site=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--site=')),'near_threshold_scale')
    cmfb='--cmfb' in sys.argv[1:]
    cmfb_assist_w=float(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--cmfb-assist-w=')),'0.42'))
    cmfb_assist_l=float(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--cmfb-assist-l=')),'10'))
    if cmfb_assist_w<=0 or cmfb_assist_l<=0: raise ValueError('CMFB PMOS dimensions must be positive')
    cmfb_sense_resistance=float(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--cmfb-sense-resistance=')),'1e6'))
    if not 1e6<=cmfb_sense_resistance<=1e9: raise ValueError('CMFB sense resistance must be within1Meg..1Gig ohm')
    threshold_latch='--threshold-latch' in sys.argv[1:]
    event_gated_ota='--event-gated-ota' in sys.argv[1:]
    zero_initial_state_diagnostic='--zero-initial-state-diagnostic' in sys.argv[1:]
    complementary_input='--complementary-input' in sys.argv[1:]
    complementary_scale=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--complementary-scale=')),'1'))
    if not 0.1<=complementary_scale<=4: raise ValueError('complementary scale must be between0.1 and4')
    level_shift='--mim-level-shift' in sys.argv[1:]
    physical_tg='--physical-tg' in sys.argv[1:]
    pex_cap_scale=float(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--pex-cap-scale=')),'1'))
    if not 0<=pex_cap_scale<=2: raise ValueError('PEX capacitance scale must be from0 to2')
    max_step_ns=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--max-step-ns=')),'50'))
    event_gain=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--event-gain=')),'1'))
    if not 0.25<=event_gain<=1.5: raise ValueError('event gain must be within0.25..1.5')
    event_width_us=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--event-width-us=')),'1.4'))
    if not 0.1<=event_width_us<=4.0: raise ValueError('event width must be within0.1..4.0us')
    threshold_shift_uv=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--threshold-shift-uv=')),'0'))
    readout_attenuation=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--readout-attenuation=')),'1'))
    threshold_source_r=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--threshold-source-r=')),'0'))
    integration_method=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--integration-method=')),'trap')
    if order not in ('forward','reverse','shuffle'): raise ValueError('order must be forward, reverse or shuffle')
    if probe not in ('full','single-positive','single-negative'): raise ValueError('invalid probe')
    if site not in SOURCES: raise ValueError('unknown full-float site')
    if threshold_latch and cmfb: raise ValueError('threshold latch is not combined with the unqualified CMFB')
    if event_gated_ota and not threshold_latch: raise ValueError('event-gated OTA requires the held-output bucket')
    if level_shift and not threshold_latch: raise ValueError('MIM level shift requires threshold latch')
    if not 0.5<=max_step_ns<=50: raise ValueError('max step must be between0.5 and50ns')
    if abs(threshold_shift_uv)>50: raise ValueError('threshold diagnostic shift is bounded to +/-50uV')
    if not 0.1<=readout_attenuation<=1: raise ValueError('readout attenuation must be between 0.1 and 1')
    if threshold_source_r<0: raise ValueError('threshold source resistance cannot be negative')
    if integration_method not in ('trap','gear'): raise ValueError('integration method must be trap or gear')
    temp_c={'ss':0,'tt':27,'ff':85}.get(corner)
    if temp_c is None: raise ValueError('corner must be ss, tt or ff')
    meta=json.loads((RES/f'{SOURCES[site]}_deck.json').read_text()); params=npz=None
    import numpy as np
    trace=json.loads((OUT/'model_reference/float_patch_trace_all.json').read_text())
    if meta['checkpoint_sha256']!='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7' or meta['qat_or_quantized_reference_used'] or trace['qat_or_quantized_reference_used']:
        raise RuntimeError('expected verified original full-float checkpoint')
    margins=json.loads((RES/'sky130_ms_fanin_threshold_margin_screen.json').read_text())
    float_site=margins['cases'][site]
    vpu=float(margins['volts_per_model_unit'])
    threshold_v=float(float_site['float_threshold'])*vpu if threshold_latch else 0.0
    initial_state_v=((float(float_site['float_candidate'])-float(float_site['float_current']))*vpu
                     if threshold_latch and not zero_initial_state_diagnostic else 0.0)
    ar=np.load(OUT/'model_reference'/trace['trace_archive']); wt=np.load(OUT/'model_reference/eventspikeseg140k_float_parameters.npz')['weight__final_fuse__standard']
    ev=ar['presynaptic_input__final_fuse__standard']; b=meta['selected_flat_batch']; o=meta['selected_output_channel']; y,x=meta['selected_yx']; seq=[]
    for c in range(wt.shape[1]):
      for ky in range(wt.shape[2]):
       for kx in range(wt.shape[3]):
        yy,xx=y+ky-1,x+kx-1
        if 0<=yy<ev.shape[-2] and 0<=xx<ev.shape[-1]: seq.extend([float(wt[o,c,ky,kx])]*int(ev[b,c,yy,xx]))
    if len(seq)!=meta['event_count']: raise RuntimeError('fan-in event count mismatch')
    seq=sorted(seq,key=lambda v:(v>0,abs(v)))
    if order=='reverse': seq.reverse()
    elif order=='shuffle': random.Random(140).shuffle(seq)
    if probe!='full':
      polarity=1 if probe=='single-positive' else -1
      candidates=[v for v in seq if v*polarity>0]
      seq=[max(candidates,key=abs)]
    vpu=6.521267959225942e-5
    target=sum(seq)*vpu*event_gain; scale=.78*event_gain; packet=1.; cmem=100.
    times=[500+i*4000/max(len(seq)-1,1) for i in range(len(seq))]
    write_seq=seq
    common=COMMON.replace('__tt.corner.spice',f'__{corner}.corner.spice').replace('.option scale=1u',f'.option scale=1u\n.temp {temp_c}')
    if physical_tg:
      modules=(ROOT/'asic/analog/modules.spice').read_text(encoding='ascii')
      tg=re.compile(r'(?ms)^\.subckt transmission_gate[^\n]*\n.*?^\.ends transmission_gate\s*')
      pex_src=ROOT/'artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice'
      pex_text=pex_src.read_text(encoding='ascii')
      pex_text,ncaps=re.subn(r'(?im)^(C\S+\s+\S+\s+\S+\s+)([-+0-9.eE]+)fF\s*$',lambda m:m.group(1)+f'{float(m.group(2))*pex_cap_scale:.9g}fF',pex_text)
      if ncaps!=10: raise RuntimeError(f'Expected10 TG PEX capacitors, found {ncaps}')
      scaled_pex=BENCH/f'tg_pex_caps_{pex_cap_scale:g}.spice'; scaled_pex.write_text(pex_text,encoding='ascii')
      replacement=f''' .include "/workspace/{scaled_pex.relative_to(ROOT).as_posix()}"
.subckt transmission_gate a b en enb vdd vss
Xphysical a b en enb vdd vss sky130_transmission_gate_raw
.ends transmission_gate
'''.lstrip()
      modules,n=tg.subn(replacement,modules,count=1)
      if n!=1: raise RuntimeError('Could not replace the SKY130 transmission_gate model')
      physical_modules=BENCH/'modules_physical_tg.spice'
      physical_modules.write_text(modules,encoding='ascii')
      common=common.replace('../../../asic/analog/modules.spice',f'/workspace/{physical_modules.relative_to(ROOT).as_posix()}')
    if cmfb and ((cmfb_assist_w,cmfb_assist_l)!=(0.42,10) or cmfb_sense_resistance!=1e6):
      charge=(ROOT/'asic/analog/sky130_sc_charge_integrator.spice').read_text(encoding='ascii')
      if (cmfb_assist_w,cmfb_assist_l)!=(0.42,10):
       charge,nassist=re.subn(r'(?m)(Xp_assist_[pn] out[ pn]+vbiasp_aux vdd vdd sky130_fd_pr__pfet_01v8 )w=0\.42 l=10',rf'\g<1>w={cmfb_assist_w:g} l={cmfb_assist_l:g}',charge)
       if nassist!=2: raise RuntimeError(f'Expected two CMFB assist devices, replaced {nassist}')
      if cmfb_sense_resistance!=1e6:
       charge,nrc=re.subn(r'(?m)(\.subckt sky130_sc_bucket_cmfb .* params: rcmfb=)1Meg',rf'\g<1>{cmfb_sense_resistance:g}',charge)
       if nrc!=1: raise RuntimeError('Could not parameterize CMFB sensing resistance')
      assist_file=BENCH/f'charge_integrator_cmfb_w{cmfb_assist_w:g}_l{cmfb_assist_l:g}_rcm{cmfb_sense_resistance:g}.spice'
      assist_file.write_text(charge,encoding='ascii')
      common=common.replace('../../../asic/analog/sky130_sc_charge_integrator.spice',f'/workspace/{assist_file.relative_to(ROOT).as_posix()}')
    common += f'\n.option method={integration_method} maxord=2'
    lines=[f'SKY130 {corner.upper()}/{temp_c} differential active bucket, float {order}',common,'Vdd vdd 0 1.8','Vcm vcm 0 0.9']
    if threshold_latch:
      lines += ['Vbp vbiasp 0 PWL(0 1.8 99.9u 1.8 100u 0.75 5005u 0.75)']
    else:
      lines += ['Vbp vbiasp 0 0.75']
    if cmfb: lines += ['Vbp_ref vbiasp_ref 0 0.75','Vbn_ref vbiasn_ref 0 0.65']
    for name,sgn in [('p',1),('n',-1)]:
      init_level=0.9 + sgn*initial_state_v
      bias_wave=("PWL(0 0 99.9u 0 100u 0.65 5005u 0.65)" if threshold_latch else "0.65")
      if threshold_latch:
       if event_gated_ota:
        amp_points=[('0','0'),('99.9u','0'),('100u','0')]
        for t in times: amp_points += [(f'{t-.55:g}u','0'),(f'{t-.45:g}u','1.8'),(f'{t+event_width_us+.05:g}u','1.8'),(f'{t+event_width_us+.15:g}u','0')]
        amp_points += [('5005u','0')]
        amp_pwl='PWL('+' '.join(f'{t} {v}' for t,v in amp_points)+')'
        ampb_pwl='PWL('+' '.join(f'{t} {1.8-float(v):g}' for t,v in amp_points)+')'
       else:
        amp_pwl='PWL(0 0 99.9u 0 100u 1.8 5005u 1.8)'
        ampb_pwl='PWL(0 1.8 99.9u 1.8 100u 0 5005u 0)'
       lines += [f'Vamp_{name} amp_{name} 0 {amp_pwl}',f'Vampb_{name} ampb_{name} 0 {ampb_pwl}']
      lines += [f'Vbn_{name} vbiasn_{name} 0 {bias_wave}',f'.ic v(out_{name})=0 v(sum_{name})=0.9',f'Vreset_{name} reset_{name} 0 0',f'Vresetb_{name} resetb_{name} 0 1.8',f'Vinit_level_{name} init_level_{name} 0 {init_level:.12g}',f'Vinit_{name} init_{name} 0 PWL(0 1.8 99.9u 1.8 100u 0 5005u 0)',f'Vinitb_{name} initb_{name} 0 PWL(0 0 99.9u 0 100u 1.8 5005u 1.8)']
      for ctrl in ('packet_reset','connect'):
       pts=[('0','1.8' if ctrl=='packet_reset' else '0')]
       for i,t in enumerate(times):
        if ctrl=='packet_reset':
         pts += [(f'{t-1.1:g}u','0'),(f'{t+event_width_us+.2:g}u','1.8')]
         if i+1<len(times): pts += [(f'{times[i+1]-1.1:g}u','0')]
        else:
         pts += [(f'{t-.5:g}u','0'),(f'{t-.4:g}u','1.8'),(f'{t+event_width_us:g}u','1.8'),(f'{t+event_width_us+.1:g}u','0')]
       if ctrl=='connect': pts += [('5005u','0')]
       lines += [f'V{ctrl}_{name} {ctrl}_{name} 0 PWL('+' '.join(f'{t} {v}' for t,v in pts)+')',f'V{ctrl}b_{name} {ctrl}b_{name} 0 PWL('+' '.join(f'{t} {1.8-float(v):g}' for t,v in pts)+')']
      pts=[('0','0.9')]
      for t,w in zip(times,write_seq):
       level=0.9-sgn*w*6.521267959225942e-5*scale*(cmem/packet)**2
       pts += [(f'{t-.1:g}u','0.9'),(f'{t:g}u',f'{level:g}'),(f'{t+event_width_us:g}u',f'{level:g}'),(f'{t+event_width_us+.1:g}u','0.9')]
      pts += [('5005u','0.9')]
      fb_en = ('PWL(0 0 5005u 0)' if threshold_latch else
               'PWL(0 1.8 449.9u 1.8 450u 0 5005u 0)')
      fb_dis = ('PWL(0 1.8 5005u 1.8)' if threshold_latch else
                'PWL(0 0 449.9u 0 450u 1.8 5005u 1.8)')
      if threshold_latch:
       cell_instance=(f'Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} init_level_{name} init_{name} initb_{name} connect_{name} connectb_{name} amp_{name} ampb_{name} vbiasn_{name} vbiasp vdd 0 vcm sky130_sc_charge_integrator_held_ota_vcm_init cpacket_um={packet:g} cmem_um={cmem:g}')
      else:
       cell_instance=(f'Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} init_level_{name} init_{name} initb_{name} connect_{name} connectb_{name} vbiasn_{name} vbiasp vdd 0 vcm sky130_sc_charge_integrator cpacket_um={packet:g} cmem_um={cmem:g}')
      lines += [f'Vpkt_{name} ptop_{name} 0 PWL('+' '.join(f'{t} {v}' for t,v in pts)+')',cell_instance,f'Vfb_{name} fb_{name} 0 {fb_en}',f'Vfbb_{name} fbb_{name} 0 {fb_dis}',f'Rfb_{name} out_{name} fbnode_{name} 1Meg',f'Xfb_{name} fbnode_{name} sum_{name} fb_{name} fbb_{name} vdd 0 transmission_gate']
    if cmfb: lines += ['Xcmfb out_p out_n vcm cmfb_gate vbiasn_ref vbiasp_ref vdd 0 sky130_sc_bucket_cmfb']
    if threshold_latch:
      latch=[
       'Vpre_latch pre_latch 0 PWL(0 1.8 4.984m 1.8 4.9841m 0 5.005m 0)',
       'Vpreb_latch preb_latch 0 PWL(0 0 4.984m 0 4.9841m 1.8 5.005m 1.8)',
       'Vread_latch read_latch 0 PWL(0 0 4.9889m 0 4.989m 1.8 4.9979m 1.8 4.998m 0 5.005m 0)',
       'Vreadb_latch readb_latch 0 PWL(0 1.8 4.9889m 1.8 4.989m 0 4.9979m 0 4.998m 1.8 5.005m 1.8)',
       'Vclk_latch clk_latch 0 PWL(0 0 4.9989m 0 4.999m 1.8 5.005m 1.8)',
       '.subckt weighted_regen inp inn clk outp outn vdd vss',
       'Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
       'Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
       'Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
       'Xln outp outn ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
       'Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
       'Xrn outn outp ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
       'Xlatch_tail ltail clk vss vss sky130_fd_pr__nfet_01v8 w=8 l=0.5',
       'Xin_p outp inp tail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
       'Xin_n outn inn tail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
       'Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w=4 l=1',
       *([f'Xptail ptail clkbar_latch vdd vdd sky130_fd_pr__pfet_01v8 w={8*complementary_scale:g} l=1',
          f'Xpin_p outp inp ptail vdd sky130_fd_pr__pfet_01v8 w={2*complementary_scale:g} l=0.5',
          f'Xpin_n outn inn ptail vdd sky130_fd_pr__pfet_01v8 w={2*complementary_scale:g} l=0.5'] if complementary_input else []),
       '.ends weighted_regen',
       'Xpre_inp_latch inp_latch vcm pre_latch preb_latch vdd 0 transmission_gate',
       'Xpre_inn_latch inn_latch vcm pre_latch preb_latch vdd 0 transmission_gate',
       *([f'Vthbias threshold_src out_n {2*(threshold_v+threshold_shift_uv*1e-6):.12g}',
          f'Rthbias threshold_src thresh_n {threshold_source_r:g}'] if threshold_source_r else
         [f'Vthbias thresh_n out_n {2*(threshold_v+threshold_shift_uv*1e-6):.12g}']),
       'Xregen_latch inp_latch inn_latch clk_latch op_latch on_latch vdd 0 weighted_regen',
       'Cloadp_latch op_latch 0 20f','Cloadn_latch on_latch 0 20f']
      if level_shift:
       latch += ['Vsampler_reset sampler_reset 0 PWL(0 1.8 4.9499m 1.8 4.95m 0 5.005m 0)',
        'Vsampler_resetb sampler_resetb 0 PWL(0 0 4.9499m 0 4.95m 1.8 5.005m 1.8)',
        'Vsampler_hi sampler_hi 0 PWL(0 0 4.9599m 0 4.96m 1.8 4.98m 1.8 4.9801m 0 5.005m 0)',
        'Vsampler_hib sampler_hib 0 PWL(0 1.8 4.9599m 1.8 4.96m 0 4.98m 0 4.9801m 1.8 5.005m 1.8)',
        'Vsampler_lo sampler_lo 0 PWL(0 0 4.9600m 0 4.9601m 1.8 4.9799m 1.8 4.98m 0 5.005m 0)',
        'Vsampler_lob sampler_lob 0 PWL(0 1.8 4.9600m 1.8 4.9601m 0 4.9799m 0 4.98m 1.8 5.005m 1.8)',
        'Xsampler thresh_n out_p sense_node sense_return sampler_hi sampler_hib sampler_lo sampler_lob sampler_reset sampler_resetb vdd 0 vcm sky130_sc_diff_cap_sampler_bp sample_um=20',
        'Xread_p_latch sense_node inp_latch read_latch readb_latch vdd 0 transmission_gate',
        'Xread_n_latch vcm inn_latch read_latch readb_latch vdd 0 transmission_gate']
      else:
       if readout_attenuation < 0.999999:
        # Gate each resistor divider at its source so the active bucket is not
        # loaded while it accumulates. The divider settles only during readout.
        rseries = 10e3 * (1-readout_attenuation) / readout_attenuation
        latch += ['Xatt_src_p out_p attp read_latch readb_latch vdd 0 transmission_gate',
                  'Xatt_src_n thresh_n attn read_latch readb_latch vdd 0 transmission_gate',
                  f'Rreadp attp readsig {rseries:g}', 'Rbiasp readsig vcm 10k',
                  f'Rreadn attn readref {rseries:g}', 'Rbiasn readref vcm 10k',
                  'Xread_p_latch readsig inp_latch read_latch readb_latch vdd 0 transmission_gate',
                  'Xread_n_latch readref inn_latch read_latch readb_latch vdd 0 transmission_gate']
       else:
        latch += ['Xread_p_latch out_p inp_latch read_latch readb_latch vdd 0 transmission_gate',
        'Xread_n_latch thresh_n inn_latch read_latch readb_latch vdd 0 transmission_gate']
      if complementary_input:
       latch += ['Vclkbar_latch clkbar_latch 0 PWL(0 1.8 4.9989m 1.8 4.999m 0 5.005m 0)']
      lines += latch
    lines += ['.control','set numdgt=15',f'tran {max_step_ns:g}n 5.005m uic','let differential=(v(out_p)-v(out_n))/2','let common_mode=(v(out_p)+v(out_n))/2']
    for t,n in [('499u','pre'),('2.5m','mid'),('4.9m','late'),('5m','final')]:
      lines += [f'meas tran {n}_diff find differential at={t}',f'meas tran {n}_cm find common_mode at={t}',f'meas tran {n}_outp find v(out_p) at={t}',f'meas tran {n}_outn find v(out_n) at={t}',f'meas tran {n}_vbiasp find v(vbiasp) at={t}']
      if cmfb: lines += [f'meas tran {n}_cmfb find v(cmfb_gate) at={t}']
    if threshold_latch:
      lines += ['meas tran init_99us find differential at=99u','meas tran init_100p1us find differential at=100.1u','meas tran init_110us find differential at=110u','meas tran init_449us find differential at=449u','let latch_diff=v(op_latch)-v(on_latch)','let sampled_input_diff=v(inp_latch)-v(inn_latch)','meas tran latch_early find latch_diff at=5.001m','meas tran latch_late find latch_diff at=5.004m','meas tran sampled_diff find sampled_input_diff at=4.9985m']
      if level_shift: lines += ['meas tran level_shift_output find v(sense_node) at=4.9835m']
    lines += ['quit','.endc','.end']; tag=f'sky130_sc_integrator_diffpair_{site}_{probe}_{order}_{corner}'+(f'_physTGcap{pex_cap_scale:g}'.replace('.','p') if physical_tg else '')+(f'_eg{event_gain:g}'.replace('.','p') if event_gain!=1 else '')+(f'_ew{event_width_us:g}u'.replace('.','p') if event_width_us!=1.4 else '')+('_eventgated' if event_gated_ota else '')+(f'_cmfbw{cmfb_assist_w:g}l{cmfb_assist_l:g}'.replace('.','p') if cmfb and (cmfb_assist_w,cmfb_assist_l)!=(0.42,10) else '_cmfb' if cmfb else '')+(f'_rcm{cmfb_sense_resistance:g}'.replace('.','p') if cmfb and cmfb_sense_resistance!=1e6 else '')+('_latch' if threshold_latch else '')+('_cinput' if complementary_input else '')+(f'_cscale{complementary_scale:g}'.replace('.','p') if complementary_input and complementary_scale!=1 else '')+(f'_att{readout_attenuation:g}'.replace('.','p') if readout_attenuation<0.999999 else '')+(f'_thr{threshold_source_r:g}'.replace('.','p') if threshold_source_r else '')+(f'_{integration_method}' if integration_method!='trap' else '')+('_mimls' if level_shift else '')+('_zeroinit' if zero_initial_state_diagnostic else '')+(f'_thshift{threshold_shift_uv:g}uv'.replace('-','m').replace('.','p') if threshold_shift_uv else '')+(f'_ts{max_step_ns:g}n' if max_step_ns!=50 else ''); deck=BENCH/f'{tag}.cir'; deck.write_text('\n'.join(lines)+'\n')
    cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','180','ngspice','-b',deck.name]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=195); log=p.stdout+p.stderr; (RES/f'{tag}.log').write_text(log)
    vals={k:float(v) for k,v in re.findall(r'(?im)^\s*(pre_diff|mid_diff|late_diff|final_diff|pre_cm|mid_cm|late_cm|final_cm|pre_outp|mid_outp|late_outp|final_outp|pre_outn|mid_outn|late_outn|final_outn|pre_vbiasp|mid_vbiasp|late_vbiasp|final_vbiasp|pre_cmfb|mid_cmfb|late_cmfb|final_cmfb)\s*=\s*([-+0-9.eE]+)',log)}
    if threshold_latch:
      for k,v in re.findall(r'(?im)^\s*(latch_early|latch_late|sampled_diff|level_shift_output|init_99us|init_100p1us|init_110us|init_449us)\s*=\s*([-+0-9.eE]+)',log): vals[k]=float(v)
    expected_values=((28 if level_shift else 27) if threshold_latch and not cmfb else (24 if cmfb else 20))
    complete=p.returncode==0 and len(vals)==expected_values and 'ngspice-36 done' in log
    state_increment=(vals.get('final_diff',0)-vals.get('pre_diff',0)) if complete else None
    result={'test':'sky130_differential_complementary_active_bucket_full_float','simulation_completed':complete,'site':site,'corner':corner.upper(),'temperature_c':temp_c,'probe':probe,'order':order,'event_gain':event_gain,'event_width_us':event_width_us,'physical_extracted_tg_enabled':physical_tg,'extracted_tg_capacitance_scale':pex_cap_scale if physical_tg else None,'max_transient_step_ns':max_step_ns,'readout_attenuation':readout_attenuation if threshold_latch else None,'threshold_reference_series_resistance_ohm':threshold_source_r if threshold_latch else None,'integration_method':integration_method,'threshold_shift_diagnostic_uv':threshold_shift_uv if threshold_latch else None,'physical_transistor_cmfb_enabled':cmfb,'cmfb_assist_pmos_w_l_um':[cmfb_assist_w,cmfb_assist_l] if cmfb else None,'physical_regenerative_latch_enabled':threshold_latch,'physical_complementary_input_pair_enabled':complementary_input,'physical_mim_level_shift_enabled':level_shift,'held_output_state_cell_enabled':threshold_latch,'event_gated_ota_enabled':event_gated_ota,'initial_state_load_ota_disabled':threshold_latch,'zero_initial_state_diagnostic_override':zero_initial_state_diagnostic,'ideal_differential_threshold_offset_v':(2*(threshold_v+threshold_shift_uv*1e-6)) if threshold_latch else None,'full_float_candidate':float(float_site['float_candidate']) if threshold_latch else None,'full_float_current':float(float_site['float_current']) if threshold_latch else None,'full_float_initial_state':float(float_site['float_candidate'])-float(float_site['float_current']) if threshold_latch else None,'initial_state_voltage_v':initial_state_v if threshold_latch else None,'full_float_threshold':float(float_site['float_threshold']) if threshold_latch else None,'full_float_candidate_margin_uv':(float(float_site['float_candidate'])-float(float_site['float_threshold']))*vpu*1e6 if threshold_latch else None,'events':len(seq),'target_differential_state_change_v':target,'measured_half_difference_v':vals.get('final_diff'),'measured_event_increment_v':state_increment,'error_v':(state_increment-target) if complete and threshold_latch else (vals.get('final_diff',0)-target if complete else None),'common_mode_v':vals,'initial_state_preload_tracking_v':{k:vals.get(k) for k in ('init_99us','init_100p1us','init_110us','init_449us')} if threshold_latch else None,'physical_latch_measurements':{k:vals.get(k) for k in ('sampled_diff','level_shift_output','latch_early','latch_late')} if threshold_latch else None,'checkpoint_sha256':meta['checkpoint_sha256'],'qat_or_quantized_reference_used':False,'scope':'Two schematic SKY130 OTA/MIM buckets receive complementary ideal full-float event packets from the verified epoch58 trace site. The selected switch option uses the extracted SKY130 TG capacitances without wire resistance. Threshold, weight delivery, mismatch/noise, and full-network replay remain unqualified.'}
    if threshold_latch and complete:
      result['initial_state_preload_error_uv']=(vals['init_99us']-initial_state_v)*1e6
      result['initial_state_preload_within_1uv']=abs(vals['init_99us']-initial_state_v)<=1e-6
      expected=bool(margins['cases'][site]['float_candidate']>margins['cases'][site]['float_threshold'])
      observed=bool(vals['latch_late']<0)
      resolved=abs(vals['latch_late'])>0.1
      result['float_spike_expected']=expected; result['physical_latch_spike']=observed if resolved else None
      result['physical_latch_resolved']=resolved
      result['decision_matches_float']=(expected==observed) if resolved else None
      result['read_disturbance_uv']=(vals['final_diff']-vals['late_diff'])*1e6
    result['simulation_completed']=complete; (RES/f'{tag}.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); return 0 if complete else 2

if __name__=='__main__': raise SystemExit(main())
