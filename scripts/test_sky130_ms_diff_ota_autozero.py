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
    step_ns = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                          if a.startswith('--tstep-ns=')), '2'))
    if stop_us < 500 or step_ns <= 0:
        raise ValueError('stop must cover the bounded event readout, and step must be positive')
    corner = next((a.split('=', 1)[1] for a in sys.argv[1:]
                   if a.startswith('--mos-corner=')), 'tt')
    temperature_c = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                if a.startswith('--temperature-c=')), '27'))
    bias_n = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                         if a.startswith('--bias-n-v=')), '0.65'))
    bias_p = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                         if a.startswith('--bias-p-v=')), '0.75'))
    initial_diff_uv = float(next((a.split('=', 1)[1] for a in sys.argv[1:]
                                  if a.startswith('--initial-diff-uv=')), '0'))
    if corner not in ('tt', 'ss', 'ff'):
        raise ValueError('MOS corner must be tt, ss or ff')
    tag = f'th{threshold_mv:g}_t{stop_us:g}u_s{step_ns:g}n_mos{corner}_temp{temperature_c:g}_bn{bias_n:g}_bp{bias_p:g}'.replace('.', 'p')
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
             f'Vsample sample_en 0 PWL(0 0 100u 0 100.0001u 1.8 110u 1.8 110.0001u 0 {stop_us:g}u 0)',
             f'Vsampleb sample_enb 0 PWL(0 1.8 100u 1.8 100.0001u 0 110u 0 110.0001u 1.8 {stop_us:g}u 1.8)',
             '.subckt diff_inject vp vn pp np pn nn vdd vss',
             'Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10',
             'Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w=1 l=10',
             'Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10',
             'Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w=1 l=10',
             '.ends diff_inject']
    for name, sign, fraction in cases:
        vp, vn, held, out, comp = (f'{stem}_{name}' for stem in ('vp', 'vn', 'held', 'out', 'comp'))
        lines += [f'Xmem_p_{name} {vp} vcm membrane_mim w_um=20 l_um=20',
                  f'Xmem_n_{name} {vn} vcm membrane_mim w_um=20 l_um=20',
                  f'Xinit_p_{name} state_init_p {vp} init_en init_enb vdd 0 transmission_gate',
                  f'Xinit_n_{name} state_init_n {vn} init_en init_enb vdd 0 transmission_gate',
                  f'Xota_{name} {vp} {vn} {out} vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f',
                  f'Rload_{name} {out} vcm 1Meg',
                  f'Xsample_{name} {out} {held} sample_en sample_enb vdd 0 transmission_gate',
                  f'Xhold_{name} {held} vcm membrane_mim w_um=20 l_um=20',
                  f'Vthreshold_{name} cmpref_{name} {held} {-threshold_mv/1000:.12g}',
                  f'Xcomp_{name} cmpref_{name} {out} {comp} vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f',
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
                wave = (f'PWL(0 {off:.12g} 149.999u {off:.12g} 150u {active:.12g} '
                        f'150.0105u {active:.12g} 150.0106u {off:.12g} {stop_us:g}u {off:.12g})')
            lines.append(f'V{gate}_{name} {gate}_{name} 0 {wave}')
        lines.append(f'Xinj_{name} {vp} {vn} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject')
    lines += ['.control', 'set numdgt=15', f'tran {step_ns:g}n {stop_us:g}u uic']
    for name, _, _ in cases:
        vp, vn, held, out, comp = (f'{stem}_{name}' for stem in ('vp', 'vn', 'held', 'out', 'comp'))
        lines += [f'let diff_{name}=v({vp})-v({vn})',
                  f'let sense_{name}=v({out})-v({held})']
        for phase, at in [('presample', '90u'), ('pre', '120u'), ('post', '155u'),
                          ('end', f'{stop_us-100:g}u')]:
            lines += [f'meas tran {phase}_diff_{name} find diff_{name} at={at}',
                      f'meas tran {phase}_sense_{name} find sense_{name} at={at}',
                      f'meas tran {phase}_out_{name} find v({out}) at={at}',
                      f'meas tran {phase}_held_{name} find v({held}) at={at}',
                      f'meas tran {phase}_comp_{name} find v({comp}) at={at}']
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
    found = {(phase, metric, name): float(value) for phase, metric, name, value in re.findall(
        r'(?im)^\s*(presample|pre|post|end)_(diff|sense|out|held|comp)_(\w+)\s*=\s*([-+0-9.eE]+)', log)}
    supply = re.search(r'(?im)^\s*supply_current_at_end\s*=\s*([-+0-9.eE]+)', log)
    complete = run.returncode == 0 and len(found) == len(cases)*4*5
    rows = []
    if complete:
        for name, sign, fraction in cases:
            row = {'case': name, 'polarity': sign, 'gate_fraction': fraction}
            for phase in ('presample', 'pre', 'post', 'end'):
                for metric in ('diff', 'sense', 'out', 'held', 'comp'):
                    row[f'{phase}_{metric}_v'] = found[phase, metric, name]
                    row[f'{phase}_{metric}_relative_to_zero_v'] = (
                        found[phase, metric, name] - found[phase, metric, 'zero'])
            rows.append(row)
    report = {'test': 'sky130_20um_diff_MIM_OTA_output_baseline_sample',
              'simulation_completed': complete, 'return_code': run.returncode,
              'mos_corner': corner, 'temperature_c': temperature_c,
              'ideal_ota_bias_n_v': bias_n, 'ideal_ota_bias_p_v': bias_p,
              'initial_differential_uv': initial_diff_uv,
              'initialization_window_us': [0, 20], 'sample_window_us': [100, 110],
              'event_time_us': 150, 'event_width_ns': 10.5,
              'transient_step_ns': step_ns, 'measurement_end_us': stop_us-100,
              'ideal_threshold_offset_mv_at_second_ota_input': threshold_mv,
              'total_supply_current_a_at_end': float(supply.group(1)) if supply else None,
              'cases': rows,
              'scope': 'Schematic physical MIM/TG/OTA input, 20um MIM OTA-output baseline sample and second OTA sense; selected MOS process corner and temperature, but passive R/C remains typical. Ideal timing, bias, state-init voltage, gate amplitudes and series threshold source. One event only; physical learned-threshold DAC, noise, mismatch, full PVT, extraction, reset/beta and network are absent.'}
    path = RES / f'sky130_ms_diff_ota_autozero_{tag}.json'
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
