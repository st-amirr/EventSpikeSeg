"""Bound a shared, prebiased OTA read of isolated 20um differential MIM state."""
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
    arg = lambda k, d: next((a.split('=', 1)[1] for a in sys.argv[1:]
                             if a.startswith(k+'=')), str(d))
    step_ns = float(arg('--tstep-ns', 10))
    read_duration_us = float(arg('--read-duration-us', 10))
    input_width_um = float(arg('--input-width-um', 10))
    compensation_cap_ff = float(arg('--comp-cap-ff', 100))
    read_start_us = float(arg('--read-start-us', 4900))
    input_sample_us = float(arg('--input-sample-us', read_duration_us))
    corner = arg('--mos-corner', 'tt')
    temperature_c = float(arg('--temperature-c', 27))
    bias_n = float(arg('--bias-n-v', 0.65))
    bias_p = float(arg('--bias-p-v', 0.75))
    threshold_mv = float(arg('--threshold-mv', 15.5))
    threshold_mode = arg('--threshold-mode', 'ideal')
    comparator_noise_na_uv = float(arg('--comparator-noise-na-uv', 0.0))
    comparator_noise_nt_ns = float(arg('--comparator-noise-nt-ns', 50.0))
    first_ota_noise_na_mv = float(arg('--first-ota-noise-na-mv', 0.0))
    first_ota_noise_nt_ns = float(arg('--first-ota-noise-nt-ns', 50.0))
    noise_seed = int(arg('--noise-seed', 1729))
    offset_cap_um = float(arg('--offset-cap-um', 1.7))
    offset_drive_v = float(arg('--offset-drive-v', 1.8))
    event_mode = arg('--event-mode', 'prepared')
    if event_mode not in ('prepared', 'weighted'):
        raise ValueError('event mode must be prepared or weighted')
    if corner not in ('tt', 'ss', 'ff'):
        raise ValueError('MOS corner must be tt, ss or ff')
    if (threshold_mode not in ('ideal', 'capacitive') or offset_cap_um <= 0
            or not 0 <= offset_drive_v <= 1.8):
        raise ValueError('threshold mode must be ideal or capacitive; offset cap must be positive')
    if (step_ns <= 0 or read_duration_us < 10 or input_width_um <= 0
            or compensation_cap_ff <= 0 or read_start_us < 200
            or input_sample_us <= 0 or input_sample_us > read_duration_us):
        raise ValueError('positive timestep and at least 10us read duration required')
    read_start_ms = read_start_us / 1000
    read_disconnect_ms = read_start_ms + input_sample_us / 1000
    event_ms = read_start_ms - 0.100
    read_off_ms = read_start_ms + read_duration_us / 1000
    stop_ms = read_off_ms + 0.010
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    cases = [('zero', 0.0), ('d3', 3.0), ('d6', 6.0)] if event_mode == 'prepared' else [
        ('zero', 0.0), ('pos065', 0.65), ('neg065', -0.65)]
    lines = [f'SKY130 {corner.upper()} shared prebiased OTA readout of held differential MIM state',
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
             'Vdd vdd 0 1.8', 'Vcm vcm 0 0.9', 'Vpre pre 0 0.918',
             f'Vbn vbnn 0 {bias_n:g}', f'Vbp vbpp 0 {bias_p:g}',
             f'Vinit init_en 0 PWL(0 1.8 20u 1.8 20.0001u 0 {stop_ms:.9f}m 0)',
             f'Vinitb init_enb 0 PWL(0 0 20u 0 20.0001u 1.8 {stop_ms:.9f}m 1.8)',
             f'Vclamp clamp_en 0 PWL(0 1.8 {read_start_ms-.001:.9f}m 1.8 {read_start_ms-.0009999:.9f}m 0 {stop_ms:.9f}m 0)',
             f'Vclampb clamp_enb 0 PWL(0 0 {read_start_ms-.001:.9f}m 0 {read_start_ms-.0009999:.9f}m 1.8 {stop_ms:.9f}m 1.8)',
             f'Vsample sample_en 0 PWL(0 0 {read_start_ms-.003:.9f}m 0 {read_start_ms-.0029999:.9f}m 1.8 {read_start_ms-.002:.9f}m 1.8 {read_start_ms-.0019999:.9f}m 0 {stop_ms:.9f}m 0)',
             f'Vsampleb sample_enb 0 PWL(0 1.8 {read_start_ms-.003:.9f}m 1.8 {read_start_ms-.0029999:.9f}m 0 {read_start_ms-.002:.9f}m 0 {read_start_ms-.0019999:.9f}m 1.8 {stop_ms:.9f}m 1.8)',
             f'Vread read_en 0 PWL(0 0 {read_start_ms:.9f}m 0 {read_start_ms+.0000001:.9f}m 1.8 {read_disconnect_ms:.9f}m 1.8 {read_disconnect_ms+.0000001:.9f}m 0 {stop_ms:.9f}m 0)',
             f'Vreadb read_enb 0 PWL(0 1.8 {read_start_ms:.9f}m 1.8 {read_start_ms+.0000001:.9f}m 0 {read_disconnect_ms:.9f}m 0 {read_disconnect_ms+.0000001:.9f}m 1.8 {stop_ms:.9f}m 1.8)']
    if threshold_mode == 'capacitive':
        lines.append(f'Voffsetbot offsetbot 0 PWL(0 {offset_drive_v:g} {read_start_ms-.0015:.9f}m {offset_drive_v:g} {read_start_ms-.0014999:.9f}m 0 {stop_ms:.9f}m 0)')
    if event_mode == 'weighted':
        lines += ['.subckt diff_inject vp vn pp np pn nn vdd vss',
                  'Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10',
                  'Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w=1 l=10',
                  'Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10',
                  'Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w=1 l=10',
                  '.ends diff_inject']
    for name, delta_uv in cases:
        vp, vn, gp, gn, out, held, comp = (f'{stem}_{name}' for stem in
                                        ('vp', 'vn', 'gp', 'gn', 'out', 'held', 'comp'))
        delta = delta_uv*1e-6 if event_mode == 'prepared' else 0.0
        lines += [f'Vinitp_{name} initp_{name} 0 {0.918+delta/2:.12f}',
                  f'Vinitn_{name} initn_{name} 0 {0.918-delta/2:.12f}',
                  f'Xmem_p_{name} {vp} vcm membrane_mim w_um=20 l_um=20',
                  f'Xmem_n_{name} {vn} vcm membrane_mim w_um=20 l_um=20',
                  f'Xinit_p_{name} initp_{name} {vp} init_en init_enb vdd 0 transmission_gate',
                  f'Xinit_n_{name} initn_{name} {vn} init_en init_enb vdd 0 transmission_gate',
                  f'Xclamp_p_{name} pre {gp} clamp_en clamp_enb vdd 0 transmission_gate',
                  f'Xclamp_n_{name} pre {gn} clamp_en clamp_enb vdd 0 transmission_gate',
                  f'Xread_p_{name} {vp} {gp} read_en read_enb vdd 0 transmission_gate',
                  f'Xread_n_{name} {vn} {gn} read_en read_enb vdd 0 transmission_gate',
                  f'Xota_{name} {gp} {gn} {out} vbnn vbpp vdd 0 sky130_sc_ota win={input_width_um:g} wn3=2 wp3=27.8 cc={compensation_cap_ff:g}f',
                  f'Rload_{name} {out} vcm 1Meg',
                  f'Xsample_{name} {out} {held} sample_en sample_enb vdd 0 transmission_gate',
                  f'Xhold_{name} {held} vcm membrane_mim w_um=20 l_um=20']
        if threshold_mode == 'ideal':
            lines.append(f'Vthreshold_{name} cmpref_{name} {held} {-threshold_mv/1000:.12g}')
        else:
            lines.append(f'Xoffset_{name} {held} offsetbot membrane_mim w_um={offset_cap_um:g} l_um={offset_cap_um:g}')
        cmpref = f'cmpref_{name}' if threshold_mode == 'ideal' else held
        lines += [f'Xcomp_{name} {cmpref} {out} {comp} vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc={compensation_cap_ff:g}f',
                  f'Rcomp_{name} {comp} vcm 1Meg']
        if first_ota_noise_na_mv > 0:
            ota_line = next(line for line in lines if line.startswith(f'Xota_{name} '))
            lines.insert(lines.index(ota_line),
                         f'Vfirstnoise_{name} {out} first_raw_{name} DC 0 TRNOISE({first_ota_noise_na_mv:g}m {first_ota_noise_nt_ns:g}n 0 0)')
            lines[lines.index(ota_line)] = ota_line.replace(f' {out} vbnn ', f' first_raw_{name} vbnn ')
        if comparator_noise_na_uv > 0:
            comp_line = next(line for line in lines if line.startswith(f'Xcomp_{name} '))
            lines.insert(lines.index(comp_line),
                         f'Vcmpnoise_{name} cmpref_noise_{name} {cmpref} DC 0 TRNOISE({comparator_noise_na_uv:g}u {comparator_noise_nt_ns:g}n 0 0)')
            lines.insert(lines.index(comp_line), f'Rcmpnoise_dc_{name} cmpref_noise_{name} 0 1e12')
            lines[lines.index(comp_line)] = comp_line.replace(f' {cmpref} {out} ', f' cmpref_noise_{name} {out} ')
        if event_mode == 'weighted':
            fraction = abs(delta_uv)
            gates = {'pp': 1.8, 'pn': 1.8, 'np': 0.0, 'nn': 0.0}
            if delta_uv > 0:
                gates.update(pp=1.8-fraction*1.08, nn=fraction*0.6)
            elif delta_uv < 0:
                gates.update(pn=1.8-fraction*1.08, np=fraction*0.6)
            for gate, active in gates.items():
                off = 1.8 if gate.startswith('p') else 0.0
                wave = f'{off:.12g}' if active == off else (
                    f'PWL(0 {off:.12g} {event_ms-.0000001:.9f}m {off:.12g} {event_ms:.9f}m {active:.12g} '
                    f'{event_ms+.0000105:.9f}m {active:.12g} {event_ms+.0000106:.9f}m {off:.12g} {stop_ms:.9f}m {off:.12g})')
                lines.append(f'V{gate}_{name} {gate}_{name} 0 {wave}')
            lines.append(f'Xinj_{name} {vp} {vn} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject')
    lines += ['.control', 'set numdgt=15', f'setseed {noise_seed}', f'tran {step_ns:g}n {stop_ms:.9f}m uic']
    late_phase = f'r{read_duration_us-1:g}'.replace('.', 'p')
    times = [('before', f'{read_start_ms-.0001:.9f}m'),
             ('r1', f'{read_start_ms+.001:.9f}m'),
             ('r5', f'{read_start_ms+.005:.9f}m')]
    if event_mode == 'weighted':
        times = [('preevent', f'{event_ms-.0001:.9f}m'),
                 ('postevent', f'{event_ms+.005:.9f}m')] + times
    times += [(f'r{offset}', f'{read_start_ms+offset/1000:.9f}m')
              for offset in (10, 20, 30, 40) if offset < read_duration_us-1]
    times += [(late_phase, f'{read_off_ms-0.001:.9f}m'),
             ('after', f'{read_off_ms+0.005:.9f}m')]
    for name, _ in cases:
        vp, vn, gp, gn, out, held, comp = (f'{stem}_{name}' for stem in
                                        ('vp', 'vn', 'gp', 'gn', 'out', 'held', 'comp'))
        lines += [f'let diff_{name}=v({vp})-v({vn})',
                  f'let sense_{name}=v({out})-v({held})']
        if comparator_noise_na_uv > 0:
            lines.append(f'let noise_{name}=v(cmpref_noise_{name})-v({cmpref})')
        for phase, at in times:
            measure_expressions = [('diff', f'diff_{name}'), ('sense', f'sense_{name}'),
                                   ('out', f'v({out})'), ('held', f'v({held})'),
                                   ('comp', f'v({comp})')]
            if comparator_noise_na_uv > 0:
                measure_expressions.append(('noise', f'noise_{name}'))
            for metric, expr in measure_expressions:
                lines.append(f'meas tran {phase}_{metric}_{name} find {expr} at={at}')
    lines += [f'meas tran supply_current find i(Vdd) at={read_start_ms+.005:.9f}m',
              'quit', '.endc', '.end']
    tag = (f'{event_mode}_at{read_start_us:g}u_s{step_ns:g}n_r{read_duration_us:g}u_'
           f'win{input_width_um:g}_cc{compensation_cap_ff:g}_hold{input_sample_us:g}_mos{corner}_temp{temperature_c:g}_'
           f'bn{bias_n:g}_bp{bias_p:g}_{threshold_mode}'
           f'{threshold_mv if threshold_mode == "ideal" else offset_cap_um:g}'
           f'{"" if threshold_mode == "ideal" else f"_drive{offset_drive_v:g}"}').replace('.', 'p')
    if comparator_noise_na_uv > 0 or first_ota_noise_na_mv > 0:
        tag += f'_cmpnoise{comparator_noise_na_uv:g}uv_firstnoise{first_ota_noise_na_mv:g}mv_nt{comparator_noise_nt_ns:g}n_seed{noise_seed}'.replace('.', 'p')
    deck = BENCH / f'sky130_ms_diff_mux_readout_{tag}.cir'
    deck.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    cmd = ['docker', 'run', '--rm', '--memory', '8g', '--cpus', '2',
           '--volume', f'{ROOT}:/workspace:ro', '--volume', f'{OUT}:/workspace/artifacts/analog_asic',
           '--workdir', '/workspace/artifacts/analog_asic/benches', '--entrypoint', 'timeout',
           'eventspikeseg:analog-ngspice36', '400' if event_mode == 'weighted' else '180',
           'ngspice', '-b', deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True,
                         timeout=415 if event_mode == 'weighted' else 195)
    log = run.stdout + run.stderr
    (RES / f'sky130_ms_diff_mux_readout_{tag}.log').write_text(log, encoding='utf-8')
    found = {(phase, metric, name): float(value) for phase, metric, name, value in re.findall(
        r'(?im)^\s*(preevent|postevent|before|r[0-9p]+|after)_(diff|sense|out|held|comp|noise)_(\w+)\s*=\s*([-+0-9.eE]+)', log)}
    supply = re.search(r'(?im)^\s*supply_current\s*=\s*([-+0-9.eE]+)', log)
    metric_count = 6 if comparator_noise_na_uv > 0 else 5
    complete = run.returncode == 0 and len(found) == len(cases)*len(times)*metric_count
    rows = []
    if complete:
        for name, initial_uv in cases:
            row = {'case': name,
                   'prepared_differential_uv': initial_uv if event_mode == 'prepared' else 0.0,
                   'event_gate_fraction': abs(initial_uv) if event_mode == 'weighted' else None,
                   'event_polarity': ('positive' if initial_uv > 0 else 'negative'
                                      if initial_uv < 0 else 'none') if event_mode == 'weighted' else None}
            for phase, _ in times:
                for metric in (('diff', 'sense', 'out', 'held', 'comp', 'noise')
                               if comparator_noise_na_uv > 0 else ('diff', 'sense', 'out', 'held', 'comp')):
                    row[f'{phase}_{metric}_v'] = found[phase, metric, name]
                    row[f'{phase}_{metric}_relative_to_zero_v'] = (
                        found[phase, metric, name]-found[phase, metric, 'zero'])
            rows.append(row)
    report = {'test':'sky130_shared_prebiased_OTA_mux_readout',
              'simulation_completed':complete, 'return_code':run.returncode,
              'mos_corner':corner, 'temperature_c':temperature_c,
              'ideal_ota_bias_n_v':bias_n, 'ideal_ota_bias_p_v':bias_p,
              'transient_step_ns':step_ns, 'read_window_us':[read_start_us,read_start_us+read_duration_us],
              'state_input_connected_us':input_sample_us,
              'first_ota_input_width_um':input_width_um,
              'ota_compensation_cap_ff':compensation_cap_ff, 'event_mode':event_mode,
              'weighted_event_time_ms':event_ms if event_mode == 'weighted' else None,
              'weighted_event_width_ns':10.5 if event_mode == 'weighted' else None,
              'sample_window_us':[read_start_us-3,read_start_us-2],
              'threshold_mode':threshold_mode,
              'ideal_threshold_offset_mv':threshold_mv if threshold_mode == 'ideal' else None,
              'physical_offset_cap_square_width_um':offset_cap_um if threshold_mode == 'capacitive' else None,
              'ideal_offset_bottom_drive_v':offset_drive_v if threshold_mode == 'capacitive' else None,
              'equivalent_comparator_input_transient_noise_na_v':comparator_noise_na_uv*1e-6 if comparator_noise_na_uv > 0 else None,
              'comparator_transient_noise_sample_interval_s':comparator_noise_nt_ns*1e-9 if comparator_noise_na_uv > 0 else None,
              'first_ota_output_transient_noise_na_v':first_ota_noise_na_mv*1e-3 if first_ota_noise_na_mv > 0 else None,
              'first_ota_transient_noise_sample_interval_s':first_ota_noise_nt_ns*1e-9 if first_ota_noise_na_mv > 0 else None,
              'comparator_transient_noise_seed':noise_seed if comparator_noise_na_uv > 0 else None,
              'total_supply_current_a_at_read_plus_5us':float(supply.group(1)) if supply else None,
              'cases':rows,
              'scope':('Schematic with physical MIM state, TG init/clamp/mux/output sample and two OTA stages. TRNOISE is an externally injected white equivalent noise source: first-OTA noise is placed at its output before the physical sample MIM; second-OTA noise is placed at its input. Amplitudes are screened against separate PDK .noise results, not a fitted colored/transient model; flicker, mismatch and correlations are excluded. Capacitive threshold mode uses physical MIM offset with ideal drive. No extraction, shared throughput or full PLIF.' if comparator_noise_na_uv > 0 or first_ota_noise_na_mv > 0 else 'Schematic with physical MIM state, TG init/clamp/mux/output sample and two OTA stages. Capacitive threshold mode uses a physical MIM bottom-plate offset but an ideal programmable drive; it is not a calibrated DAC or DRC-qualified layout. One readout channel is replicated per test case only; sharing throughput, physical bias generation, noise, mismatch, extraction and full PLIF are absent. Weighted mode includes one signed 10.5ns direct MOS event; prepared mode has no event pulse.')}
    path = RES / f'sky130_ms_diff_mux_readout_{tag}.json'
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
