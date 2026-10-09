"""Bounded physical MIM/OTA baseline-sample readout with one signed MOS event."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic'
BENCH = OUT / 'benches'
RES = OUT / 'results'


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    threshold_mv = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                               if a.startswith('--threshold-mv=')), '0'))
    stop_us = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                          if a.startswith('--stop-us=')), '500'))
    bin_offset_us = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                if a.startswith('--bin-offset-us=')), '0'))
    step_ns = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                          if a.startswith('--tstep-ns=')), '2'))
    if stop_us < 500 or step_ns <= 0 or bin_offset_us < 0:
        raise ValueError('stop must cover the bounded event readout, and step must be positive')
    corner = next((a.split('=', 1)[1] for a in sys.argv[1:]
                   if a.startswith('--mos-corner=')), 'tt')
    temperature_c = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                if a.startswith('--temperature-c=')), '27'))
    bias_n = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                         if a.startswith('--bias-n-v=')), '0.65'))
    bias_p = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                         if a.startswith('--bias-p-v=')), '0.75'))
    buffer_bias_n = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                if a.startswith('--buffer-bias-n-v=')), str(bias_n)))
    buffer_bias_p = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                if a.startswith('--buffer-bias-p-v=')), str(bias_p)))
    buffer_out_n = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                               if a.startswith('--buffer-out-n-width-um=')), '20'))
    buffer_out_p = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                               if a.startswith('--buffer-out-p-width-um=')), '40'))
    buffer_comp_ff = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                 if a.startswith('--buffer-comp-cap-ff=')), '1000'))
    latch_divider_ratio = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                      if a.startswith('--latch-divider-ratio=')), '4'))
    initial_diff_uv = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                  if a.startswith('--initial-diff-uv=')), '0'))
    hold_cap_um = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                              if a.startswith('--hold-cap-um=')), '20'))
    regenerative_latch = '--regenerative-latch' in sys.argv[1:]
    buffered_sample = '--buffered-sample' in sys.argv[1:]
    attenuated_latch = '--attenuated-latch-inputs' in sys.argv[1:]
    physical_sample = '--physical-sample' in sys.argv[1:]
    if buffered_sample and not regenerative_latch:
        raise ValueError('buffered-sample is currently part of the regenerative readout diagnostic')
    if physical_sample and not (regenerative_latch and buffered_sample):
        raise ValueError('physical-sample requires regenerative-latch and buffered-sample')
    if attenuated_latch and not buffered_sample:
        raise ValueError('attenuated-latch-inputs requires buffered-sample')
    if latch_divider_ratio < 1:
        raise ValueError('latch-divider-ratio must be at least 1')
    if min(buffer_out_n, buffer_out_p, buffer_comp_ff) <= 0:
        raise ValueError('buffer output widths and compensation capacitance must be positive')
    if not 2 <= hold_cap_um <= 100:
        raise ValueError('hold MIM capacitor width must be within2..100um')
    if regenerative_latch and stop_us < bin_offset_us + 5000:
        raise ValueError('regenerative readout requires a 5ms bin endpoint after its offset')
    if corner not in ('tt', 'ss', 'ff'):
        raise ValueError('MOS corner must be tt, ss or ff')
    tag = f'th{threshold_mv:g}_t{stop_us:g}u_s{step_ns:g}n_mos{corner}_temp{temperature_c:g}_bn{bias_n:g}_bp{bias_p:g}_hold{hold_cap_um:g}u'.replace('.', 'p')
    if regenerative_latch:
        tag += '_regen'
    if buffered_sample:
        tag += '_buf'
        tag += f'_bw{buffer_out_n:g}-{buffer_out_p:g}-c{buffer_comp_ff:g}f'.replace('.', 'p')
    if physical_sample:
        tag += '_pex'
    if attenuated_latch:
        tag += '_attn'
        tag += f'_div{latch_divider_ratio:g}'.replace('.', 'p')
    if bin_offset_us:
        tag += f'_off{bin_offset_us:g}u'.replace('.', 'p')
    cases = [('zero', 'z', 0.0), ('pos05', 'p', 0.5), ('pos0525', 'p', 0.525),
             ('pos055', 'p', 0.55), ('pos06', 'p', 0.6), ('pos0601', 'p', 0.601),
             ('pos0605', 'p', 0.605), ('pos061', 'p', 0.61),
             ('pos0625', 'p', 0.625), ('neg06', 'n', 0.6),
             ('pos065', 'p', 0.65), ('pos066', 'p', 0.66), ('pos067', 'p', 0.67)]
    case_names = next((a.split('=', 1)[1] for a in sys.argv[1:]
                       if a.startswith('--cases=')), 'zero,pos06,neg06,pos065').split(',')
    cases = [case for case in cases if case[0] in case_names]
    if 'zero' not in [case[0] for case in cases] or len(cases) != len(case_names):
        raise ValueError('cases must name unique known cases and include zero')
    tag += '_' + '-'.join(case_names)
    if initial_diff_uv:
        tag += f'_dinit{initial_diff_uv:g}uv'.replace('-', 'm').replace('.', 'p')
    lines = [f'SKY130 {corner.upper()} MOS physical OTA baseline sampling on differential 20um MIM state',
             '.option scale=1u', f'.temp {temperature_c:g}',
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             '.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38',
             f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
             f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
             '.include "../../../asic/analog/modules.spice"',
             '.include "../../../asic/analog/sky130_ms_plif.spice"',
             '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
             'Vdd vdd 0 1.8', 'Vcm vcm 0 0.9',
             f'Vstate_init_p state_init_p 0 {0.918+initial_diff_uv*0.5e-6:.12f}',
             f'Vstate_init_n state_init_n 0 {0.918-initial_diff_uv*0.5e-6:.12f}',
             f'Vbn vbnn 0 {bias_n:g}', f'Vbp vbpp 0 {bias_p:g}',
             f'Vinit init_en 0 PWL(0 1.8 20u 1.8 20.0001u 0 {stop_us:g}u 0)',
             f'Vinitb init_enb 0 PWL(0 0 20u 0 20.0001u 1.8 {stop_us:g}u 1.8)',
             f'Vsample sample_en 0 PWL(0 0 {100+bin_offset_us:g}u 0 {100.0001+bin_offset_us:g}u 1.8 {110+bin_offset_us:g}u 1.8 {110.0001+bin_offset_us:g}u 0 {stop_us:g}u 0)',
             f'Vsampleb sample_enb 0 PWL(0 1.8 {100+bin_offset_us:g}u 1.8 {100.0001+bin_offset_us:g}u 0 {110+bin_offset_us:g}u 0 {110.0001+bin_offset_us:g}u 1.8 {stop_us:g}u 1.8)',
             '.subckt diff_inject vp vn pp np pn nn vdd vss',
             'Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10',
             'Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w=1 l=10',
             'Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10',
             'Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w=1 l=10',
             '.ends diff_inject']
    if physical_sample:
        lines += ['.include "/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"',
                  '.include "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"',
                  '.subckt transmission_gate_pex a b en enb vdd vss',
                  'Xpex a b en enb vdd vss sky130_transmission_gate_raw',
                  '.ends transmission_gate_pex']
    for name, sign, fraction in cases:
        vp, vn, held, out, comp = (f'{stem}_{name}' for stem in ('vp', 'vn', 'held', 'out', 'comp'))
        hold_instance = (f'Xhold_{name} {held} vcm mim_state_square_3x4_w30_l30' if physical_sample else
                         f'Xhold_{name} {held} vcm membrane_mim w_um={hold_cap_um:g} l_um={hold_cap_um:g}')
        lines += [f'Xmem_p_{name} {vp} vcm membrane_mim w_um=20 l_um=20',
                  f'Xmem_n_{name} {vn} vcm membrane_mim w_um=20 l_um=20',
                  f'Xinit_p_{name} state_init_p {vp} init_en init_enb vdd 0 transmission_gate',
                  f'Xinit_n_{name} state_init_n {vn} init_en init_enb vdd 0 transmission_gate',
                  f'Xota_{name} {vp} {vn} {out} vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f',
                  f'Rload_{name} {out} vcm 1Meg',
                  f'Vthreshold_{name} cmpref_{name} {held} {-threshold_mv/1000:.12g}']
        lines.append(hold_instance)
        sample_source = out
        if regenerative_latch:
            if buffered_sample:
                # OTA closed-loop voltage follower isolates the sensor output
                # from the large baseline MIM during the sample aperture.
                lines += [f'Vbufbn_{name} vbufbn_{name} 0 {buffer_bias_n:g}',
                          f'Vbufbp_{name} vbufbp_{name} 0 {buffer_bias_p:g}',
                          f'Xbuf_{name} bufout_{name} {out} bufout_{name} vbufbn_{name} vbufbp_{name} vdd 0 sky130_sc_ota wn3={buffer_out_n:g} wp3={buffer_out_p:g} cc={buffer_comp_ff:g}f',
                          f'Rbufload_{name} bufout_{name} vcm 1Meg']
                sample_source = f'bufout_{name}'
            latch_signal_source = sample_source
            latch_reference_source = f'cmpref_{name}'
            if attenuated_latch:
                r_shunt = 10_000.0
                r_series = r_shunt * (latch_divider_ratio - 1.0)
                lines += [f'Xrefbuf_{name} refbuf_{name} cmpref_{name} refbuf_{name} vbufbn_{name} vbufbp_{name} vdd 0 sky130_sc_ota wn3={buffer_out_n:g} wp3={buffer_out_p:g} cc={buffer_comp_ff:g}f',
                          f'Rlat_sig_{name} {sample_source} sigsrc_{name} {r_series:g}',
                          f'Rlat_sig_ref_{name} sigsrc_{name} vcm {r_shunt:g}',
                          f'Rlat_ref_{name} refbuf_{name} refsrc_{name} {r_series:g}',
                          f'Rlat_ref_ref_{name} refsrc_{name} vcm {r_shunt:g}']
                latch_signal_source = f'sigsrc_{name}'
                latch_reference_source = f'refsrc_{name}'
            sample_tg = 'transmission_gate_pex' if physical_sample else 'transmission_gate'
            lines.append(f'Xsample_{name} {sample_source} {held} sample_en sample_enb vdd 0 {sample_tg}')
            # Direct, time-gated sampling avoids a DC divider from the floating
            # MIM baseline node to VCM, which would discharge the stored level.
            lines += [
                      f'Xlat_pre_p_{name} inp_{name} vcm latpre latpreb vdd 0 {sample_tg}',
                      f'Xlat_pre_n_{name} inn_{name} vcm latpre latpreb vdd 0 {sample_tg}',
                      f'Xlat_read_p_{name} {latch_signal_source} inp_{name} latread latreadb vdd 0 {sample_tg}',
                      f'Xlat_read_n_{name} {latch_reference_source} inn_{name} latread latreadb vdd 0 {sample_tg}',
                      f'Xregen_{name} inp_{name} inn_{name} latclk latclkbar latchp_{name} latchn_{name} vdd 0 weighted_regen',
                      f'Clatchp_{name} latchp_{name} 0 20f', f'Clatchn_{name} latchn_{name} 0 20f',
                      f'Bcomp_{name} {comp} vcm V=V(latchp_{name})-V(latchn_{name})']
        else:
            lines += [f'Xcomp_{name} cmpref_{name} {out} {comp} vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f',
                      f'Rcomp_{name} {comp} vcm 1Meg']
        pg = 1.8 - fraction * 1.08
        ng = fraction * 0.6
        gates = {'pp': 1.8, 'pn': 1.8, 'np': 0.0, 'nn': 0.0}
        if sign == 'p': gates.update(pp=pg, nn=ng)
        elif sign == 'n': gates.update(pn=pg, np=ng)
        for gate, active in gates.items():
            off = 1.8 if gate.startswith('p') else 0.0
            if active == off:
                wave = f'{off:.12g}'
            else:
                wave = (f'PWL(0 {off:.12g} {149.999+bin_offset_us:g}u {off:.12g} '
                        f'{150+bin_offset_us:g}u {active:.12g} {150.0105+bin_offset_us:g}u {active:.12g} '
                        f'{150.0106+bin_offset_us:g}u {off:.12g} {stop_us:g}u {off:.12g})')
            lines.append(f'V{gate}_{name} {gate}_{name} 0 {wave}')
        lines.append(f'Xinj_{name} {vp} {vn} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject')
    if regenerative_latch:
        lines += [f'Vlatpre latpre 0 PWL(0 1.8 {4984+bin_offset_us:g}u 1.8 {4984.1+bin_offset_us:g}u 0 {5005+bin_offset_us:g}u 0)',
                  f'Vlatpreb latpreb 0 PWL(0 0 {4984+bin_offset_us:g}u 0 {4984.1+bin_offset_us:g}u 1.8 {5005+bin_offset_us:g}u 1.8)',
                  f'Vlatread latread 0 PWL(0 0 {4990+bin_offset_us:g}u 0 {4990.1+bin_offset_us:g}u 1.8 {4999.2+bin_offset_us:g}u 1.8 {4999.3+bin_offset_us:g}u 0 {5005+bin_offset_us:g}u 0)',
                  f'Vlatreadb latreadb 0 PWL(0 1.8 {4990+bin_offset_us:g}u 1.8 {4990.1+bin_offset_us:g}u 0 {4999.2+bin_offset_us:g}u 0 {4999.3+bin_offset_us:g}u 1.8 {5005+bin_offset_us:g}u 1.8)',
                  f'Vlatclk latclk 0 PWL(0 0 {4998.9+bin_offset_us:g}u 0 {4999+bin_offset_us:g}u 1.8 {5005+bin_offset_us:g}u 1.8)',
                  f'Vlatclkbar latclkbar 0 PWL(0 1.8 {4998.9+bin_offset_us:g}u 1.8 {4999+bin_offset_us:g}u 0 {5005+bin_offset_us:g}u 0)',
                  '.subckt weighted_regen inp inn clk clkbar outp outn vdd vss',
                  'Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
                  'Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
                  'Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
                  'Xln outp outn ltail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5',
                  'Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
                  'Xrn outn outp ltail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5',
                  'Xltail ltail clk 0 0 sky130_fd_pr__nfet_01v8 w=8 l=0.5',
                  'Xin_p outp inp tail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5',
                  'Xin_n outn inn tail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5',
                  'Xtail tail clk 0 0 sky130_fd_pr__nfet_01v8 w=4 l=1',
                  '.ends weighted_regen']
    lines += ['.control', 'set numdgt=15', f'tran {step_ns:g}n {stop_us:g}u uic']
    for name, _, _ in cases:
        vp, vn, held, out, comp = (f'{stem}_{name}' for stem in ('vp', 'vn', 'held', 'out', 'comp'))
        lines += [f'let diff_{name}=v({vp})-v({vn})',
                  f'let sense_{name}=v({out})-v({held})']
        if regenerative_latch:
            lines += [f'let latch_input_{name}=v(inp_{name})-v(inn_{name})',
                      f'let latch_output_{name}=v(latchp_{name})-v(latchn_{name})']
        if buffered_sample:
            lines.append(f'let sample_source_{name}=v(bufout_{name})')
        for phase, at in [('presample', f'{90+bin_offset_us:g}u'),
                          ('sample', f'{105+bin_offset_us:g}u'),
                          ('post_sample', f'{115+bin_offset_us:g}u'),
                          ('pre_eval', f'{4998.5+bin_offset_us:g}u'),
                          ('pre', f'{120+bin_offset_us:g}u'),
                          ('post', f'{155+bin_offset_us:g}u'),
                          ('end', f'{stop_us-100:g}u')]:
            lines += [f'meas tran {phase}_diff_{name} find diff_{name} at={at}',
                      f'meas tran {phase}_sense_{name} find sense_{name} at={at}',
                      f'meas tran {phase}_out_{name} find v({out}) at={at}',
                      f'meas tran {phase}_held_{name} find v({held}) at={at}',
                      f'meas tran {phase}_comp_{name} find v({comp}) at={at}']
            if regenerative_latch:
                lines += [f'meas tran {phase}_latch_input_{name} find latch_input_{name} at={at}',
                          f'meas tran {phase}_latch_output_{name} find latch_output_{name} at={at}']
            if buffered_sample:
                lines.append(f'meas tran {phase}_sample_source_{name} find sample_source_{name} at={at}')
    lines += [f'meas tran supply_current_at_end find i(Vdd) at={stop_us-100:g}u',
              'quit', '.endc', '.end']
    deck = BENCH / f'sky130_ms_diff_ota_autozero_{tag}.cir'
    deck.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    timeout_s = 400 if stop_us > 500 else 90
    cmd = ['docker', 'run', '--rm', '--memory', '8g', '--cpus', '2',
           '--volume', f'{ROOT}:/workspace:ro', '--volume', f'{OUT}:/workspace/artifacts/analog_asic',
           '--workdir', '/workspace/artifacts/analog_asic/benches', '--entrypoint', 'timeout',
           'eventspikeseg:analog-ngspice36', str(timeout_s), 'ngspice', '-b', deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s+15)
    log = run.stdout + run.stderr
    (RES / f'sky130_ms_diff_ota_autozero_{tag}.log').write_text(log, encoding='utf-8')
    metrics = 'diff|sense|out|held|comp' + ('|latch_input|latch_output' if regenerative_latch else '') + ('|sample_source' if buffered_sample else '')
    found = {(phase, metric, name): float(value) for phase, metric, name, value in re.findall(
        rf'(?im)^\s*(presample|sample|post_sample|pre_eval|pre|post|end)_({metrics})_(\w+)\s*=\s*([-+0-9.eE]+)', log)}
    supply = re.search(r'(?im)^\s*supply_current_at_end\s*=\s*([-+0-9.eE]+)', log)
    complete = run.returncode == 0 and len(found) == len(cases)*7*((7 if regenerative_latch else 5) + int(buffered_sample))
    rows = []
    if complete:
        for name, sign, fraction in cases:
            row = {'case': name, 'polarity': sign, 'gate_fraction': fraction}
            for phase in ('presample', 'sample', 'post_sample', 'pre_eval', 'pre', 'post', 'end'):
                for metric in (('diff', 'sense', 'out', 'held', 'comp', 'latch_input', 'latch_output') if regenerative_latch else
                               ('diff', 'sense', 'out', 'held', 'comp')) + (('sample_source',) if buffered_sample else ()):
                    row[f'{phase}_{metric}_v'] = found[phase, metric, name]
                    row[f'{phase}_{metric}_relative_to_zero_v'] = (
                        found[phase, metric, name] - found[phase, metric, 'zero'])
            rows.append(row)
    report = {'test': 'sky130_diff_MIM_OTA_output_baseline_sample',
              'simulation_completed': complete, 'return_code': run.returncode,
              'mos_corner': corner, 'temperature_c': temperature_c,
              'ideal_ota_bias_n_v': bias_n, 'ideal_ota_bias_p_v': bias_p,
              'buffer_ota_bias_n_v': buffer_bias_n, 'buffer_ota_bias_p_v': buffer_bias_p,
              'buffer_output_n_width_um': buffer_out_n,
              'buffer_output_p_width_um': buffer_out_p,
              'buffer_compensation_cap_ff': buffer_comp_ff,
              'initial_differential_uv': initial_diff_uv,
              'sample_hold_mim_cap_width_um': hold_cap_um,
              'regenerative_latch_enabled': regenerative_latch,
              'buffered_sample_enabled': buffered_sample,
              'symmetric_latch_input_attenuator_enabled': attenuated_latch,
              'latch_divider_ratio': latch_divider_ratio if attenuated_latch else None,
              'physical_mim_tg_sample_enabled': physical_sample,
              'initialization_window_us': [0, 20],
              'sample_window_us': [100+bin_offset_us, 110+bin_offset_us],
              'event_time_us': 150+bin_offset_us, 'event_width_ns': 10.5,
              'transient_step_ns': step_ns, 'measurement_end_us': stop_us-100,
              'readout_bin_offset_us': bin_offset_us,
              'ideal_threshold_offset_mv_at_second_ota_input': threshold_mv,
              'total_supply_current_a_at_end': float(supply.group(1)) if supply else None,
              'cases': rows,
              'scope': f'Schematic OTA/latch with {"existing extracted 21.8pF MIM bank and DRC/LVS-clean TG PEX" if physical_sample else f"{hold_cap_um:g}um square MIM model and schematic TG"} baseline sampler; optional OTA follower isolates the sensor output. Selected MOS process corner and temperature, but OTA, buffer and latch remain schematic and interconnect resistance is not extracted. Ideal timing, bias, state-init voltage, gate amplitudes and series threshold source. One event only; physical learned-threshold DAC, noise, mismatch, full PVT, reset/beta and network are absent.'}
    path = RES / f'sky130_ms_diff_ota_autozero_{tag}.json'
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
