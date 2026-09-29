"""Bounded DC branch-current audit of the ASAP7 transmission-gate hold path."""
import argparse
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/asap7'
BENCH = OUT / 'benches'
RES = OUT / 'results'


def make_deck(name, n_gate, p_gate, n_model='nmos_rvt', p_model='pmos_rvt', cap_model=None):
    cap_lines = ''
    if cap_model:
        pin = 'vdd capgate vdd vdd ' if cap_model.startswith('pmos_') else 'vcm capgate vcm 0 '
        cap_lines = '\n'.join(f'Ncap{i} {pin}{cap_model}' for i in range(1, 9))
    return f'''ASAP7 off-state access leakage; no MOSCAP; state clamped to isolate TG branches
.include "../models/tt_osdi.spice"
Vinput input 0 0.28
Vstate state 0 0.28
Vcapprobe capgate state 0
Vnprobe nstate state 0
Vpprobe pstate state 0
Vdd vdd 0 0.7
Vcm vcm 0 0.35
VnGate ng 0 {n_gate}
VpGate pg 0 {p_gate}
Naccess input ng nstate 0 {n_model}
Npaccess input pg pstate vdd {p_model}
{cap_lines}
.options abstol=1e-18 reltol=1e-6 vntol=1e-9 gmin=1e-18
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
dc Vinput 0.28 0.42 0.07 Vstate 0.28 0.42 0.07
wrdata ../results/{name}.dat v(state) v(input) i(Vnprobe) i(Vpprobe) i(Vstate) i(Vcapprobe)
quit
.endc
.end
'''


def run(name, n_gate, p_gate, n_model='nmos_rvt', p_model='pmos_rvt', cap_model=None):
    (BENCH / f'{name}.cir').write_text(make_deck(name, n_gate, p_gate, n_model, p_model, cap_model))
    command = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic/asap7',
        '--workdir', '/workspace/artifacts/analog_asic/asap7/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        '60', '../tools/ngspice45/bin/ngspice', '-b', f'{name}.cir',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=90)
    (RES / f'{name}.log').write_text(proc.stdout + proc.stderr)
    dat = RES / f'{name}.dat'
    lines = dat.read_text().splitlines() if dat.is_file() else []
    rows = [[float(v) for v in line.split()] for line in lines[1:] if line.strip()]
    values = []
    for row in rows:
        if len(row) < 7 or not all(math.isfinite(x) for x in row):
            continue
        _scale, state, input_v, in_n, in_p, in_clamp, in_cap = row[:7]
        values.append({
            'state_v': state, 'input_v': input_v,
            'nmos_access_current_a': in_n,
            'pmos_access_current_a': in_p,
            'state_clamp_current_a': in_clamp,
            'storage_gate_current_a': in_cap,
            'kcl_residual_a': in_clamp - in_n - in_p - in_cap,
        })
    return {
        'bench': name, 'nmos_off_gate_v': n_gate, 'pmos_off_gate_v': p_gate,
        'nmos_device': n_model, 'pmos_device': p_model,
        'storage_device': cap_model,
        'abstol_a': 1e-18, 'reltol': 1e-6, 'gmin_s': 1e-18,
        'simulation_completed': proc.returncode == 0 and len(values) == 9,
        'exit_code': proc.returncode, 'dc_points': values,
        'maximum_abs_kcl_residual_a': max((abs(x['kcl_residual_a']) for x in values), default=None),
    }


def run_hold_probe(name, cap_model, n_gate_off=0.0, p_gate_off=0.7, instances=8, state_initial=0.42, input_after=0.28):
    if cap_model == 'ideal20pf':
        store = 'Cmem state vcm 20p\n'
    elif cap_model.startswith('pmos_mid_'):
        model = cap_model.removeprefix('pmos_mid_')
        store = '\n'.join(f'Ncap{i} vcm capgate vcm vdd {model}' for i in range(1, instances + 1)) + '\n'
    elif cap_model.startswith('pmos_'):
        store = '\n'.join(f'Ncap{i} vdd capgate vdd vdd {cap_model}' for i in range(1, instances + 1)) + '\n'
    else:
        store = '\n'.join(f'Ncap{i} vcm capgate vcm 0 {cap_model}' for i in range(1, instances + 1)) + '\n'
    deck = f'''ASAP7 transient hold current probes: {name}
.include "../models/tt_osdi.spice"
.include "../modules.spice"
Vdd vdd 0 0.7
Vcm vcm 0 0.35
Vin input 0 PWL(0 {state_initial} 2u {state_initial} 2.001u {input_after} 5.002m {input_after})
Vsample sample 0 PWL(0 0.7 1u 0.7 1.001u {n_gate_off} 5.002m {n_gate_off})
Vsampleb sample_b 0 PWL(0 0 1u 0 1.001u {p_gate_off} 5.002m {p_gate_off})
Vnprobe nstate state 0
Vpprobe pstate state 0
Vcapprobe capgate state 0
Naccess input sample nstate 0 nmos_rvt
Npaccess input sample_b pstate vdd pmos_rvt
{store}
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
tran 1u 5.002m 0 1u
wrdata ../results/{name}.dat v(state) i(Vnprobe) i(Vpprobe) i(Vcapprobe) i(Vin)
quit
.endc
.end
'''
    (BENCH / f'{name}.cir').write_text(deck)
    command = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic/asap7',
        '--workdir', '/workspace/artifacts/analog_asic/asap7/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        '120', '../tools/ngspice45/bin/ngspice', '-b', f'{name}.cir',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=150)
    (RES / f'{name}.log').write_text(proc.stdout + proc.stderr)
    dat = RES / f'{name}.dat'
    lines = dat.read_text().splitlines() if dat.is_file() else []
    rows = [[float(v) for v in line.split()] for line in lines[1:] if line.strip()]
    tail = [row for row in rows if row[0] >= 4.5e-3]
    first = next((row for row in rows if row[0] >= 1.1e-6), None)
    last = rows[-1] if rows else None
    means = [sum(row[i] for row in tail) / len(tail) for i in range(2, 6)] if tail else []
    return {
        'bench': name, 'storage': cap_model, 'instances': instances if cap_model != 'ideal20pf' else None,
        'nmos_off_gate_v': n_gate_off, 'pmos_off_gate_v': p_gate_off,
        'simulation_completed': proc.returncode == 0 and bool(last) and last[0] >= 5.002e-3 * 0.999,
        'exit_code': proc.returncode, 'hold_start_v_at_1p1us': first[1] if first else None,
        'hold_end_v': last[1] if last else None,
        'hold_drift_v': last[1] - first[1] if last and first else None,
        'max_abs_hold_excursion_v': max((abs(row[1] - first[1]) for row in rows if row[0] >= 1.1e-6), default=None) if first else None,
        'state_at_100us_v': next((row[1] for row in rows if row[0] >= 100e-6), None),
        'normalized_model_drift': (last[1] - first[1]) / 0.07 if last and first else None,
        'provisional_0_02_unit_pass': max((abs(row[1] - first[1]) for row in rows if row[0] >= 1.1e-6), default=float('inf')) / 0.07 < 0.02 if first else False,
        'mean_i_nmos_source_a': means[0] if means else None,
        'mean_i_pmos_source_a': means[1] if means else None,
        'mean_i_storage_gate_a': means[2] if means else None,
        'mean_i_input_a': means[3] if means else None,
        'sample_count': len(rows),
    }


def run_bias_map(state, input_v):
    name = f'bias_map_s{state:.2f}_i{input_v:.2f}'
    nmax = min(state, input_v) - 0.05
    pmin = max(state, input_v) + 0.05
    nstep, pstep = nmax / 4, (0.7 - pmin) / 4
    caps = '\n'.join(f'Ncap{i} vdd capgate vdd vdd pmos_rvt' for i in range(1, 9))
    deck = f'''ASAP7 pMOS Cgg off-gate reachability DC map; state/input fixed
.include "../models/tt_osdi.spice"
Vinput input 0 {input_v}
Vstate state 0 {state}
Vcapprobe capgate state 0
Vnprobe nstate state 0
Vpprobe pstate state 0
Vdd vdd 0 0.7
VnGate ng 0 0
VpGate pg 0 {pmin}
Naccess input ng nstate 0 nmos_rvt
Npaccess input pg pstate vdd pmos_rvt
{caps}
.options abstol=1e-18 reltol=1e-6 vntol=1e-9 gmin=1e-18
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
dc VnGate 0 {nmax:.12g} {nstep:.12g} VpGate {pmin:.12g} 0.7 {pstep:.12g}
wrdata ../results/{name}.dat v(ng) v(pg) i(Vstate) i(Vnprobe) i(Vpprobe) i(Vcapprobe)
quit
.endc
.end
'''
    (BENCH / f'{name}.cir').write_text(deck)
    command = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic/asap7',
        '--workdir', '/workspace/artifacts/analog_asic/asap7/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        '60', '../tools/ngspice45/bin/ngspice', '-b', f'{name}.cir',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=90)
    (RES / f'{name}.log').write_text(proc.stdout + proc.stderr)
    dat = RES / f'{name}.dat'
    lines = dat.read_text().splitlines() if dat.is_file() else []
    rows = [[float(v) for v in line.split()] for line in lines[1:] if line.strip()]
    points = []
    for row in rows:
        if len(row) < 7 or not all(math.isfinite(x) for x in row):
            continue
        scale, gn, gp, clamp, in_n, in_p, in_cap = row[:7]
        residual = clamp - in_n - in_p - in_cap
        points.append({
            'n_off_v': gn, 'p_off_v': gp, 'i_state_clamp_a': clamp,
            'i_n_access_a': in_n, 'i_p_access_a': in_p,
            'i_storage_gate_a': in_cap, 'kcl_residual_a': residual,
        })
    finite_nonzero = sorted(set(abs(p['i_state_clamp_a']) for p in points if p['i_state_clamp_a']))
    lsb = min((b - a for a, b in zip(finite_nonzero, finite_nonzero[1:]) if b > a), default=None)
    return {
        'bench': name, 'state_v': state, 'input_v': input_v,
        'n_gate_range_v': [0.0, nmax], 'p_gate_range_v': [pmin, 0.7],
        'storage': '8 x pmos_rvt, each model NFIN=3, D=S=B=VDD',
        'tolerances': 'ABSTOL=1e-18 RELTOL=1e-6 VNTOL=1e-9 GMIN=1e-18',
        'simulation_completed': proc.returncode == 0 and len(points) == 25,
        'exit_code': proc.returncode, 'points': points,
        'minimum_abs_i_state_a': min((abs(p['i_state_clamp_a']) for p in points), default=None),
        'current_resolution_lsb_estimate_a': lsb,
        'maximum_abs_kcl_residual_a': max((abs(p['kcl_residual_a']) for p in points), default=None),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-sweep-only', action='store_true', help='Test the interior-bias pMOS hold path at three stored states and adversarial input steps.')
    parser.add_argument('--bias-map', action='store_true', help='Sweep conservative in-rail OFF-gate biases over the 3x3 state/input grid.')
    args = parser.parse_args()
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    if args.bias_map:
        results = [run_bias_map(s, i) for s in (0.28, 0.35, 0.42) for i in (0.28, 0.35, 0.42)]
        path = RES / 'mos_off_bias_reachability.json'
        path.write_text(json.dumps({'results': results}, indent=2) + '\n')
        print(json.dumps(results, indent=2))
        print('wrote', path)
        return 0 if all(r['simulation_completed'] for r in results) else 2
    if args.state_sweep_only:
        cases = [
            (0.28, 0.42),
            (0.35, 0.28),
            (0.35, 0.42),
            (0.42, 0.28),
        ]
        results = [
            run_hold_probe(f'hold_probe_pmos8_interior_s{state:.2f}_i{inp:.2f}', 'pmos_rvt', 0.15, 0.55, 8, state, inp)
            for state, inp in cases
        ]
        path = RES / 'mos_interior_bias_state_sweep.json'
        path.write_text(json.dumps({'results': results}, indent=2) + '\n')
        midpoint = [
            run_hold_probe(f'hold_probe_pmos_mid_s{state:.2f}_i{inp:.2f}', 'pmos_mid_pmos_rvt', 0.15, 0.55, 8, state, inp)
            for state, inp in cases
        ]
        mid_path = RES / 'mos_pmos_midpoint_state_sweep.json'
        mid_path.write_text(json.dumps({'results': midpoint}, indent=2) + '\n')
        print(json.dumps(results, indent=2))
        print('wrote', path)
        print(json.dumps(midpoint, indent=2))
        print('wrote', mid_path)
        return 0 if all(r['simulation_completed'] for r in results + midpoint) else 2
    results = [
        run('tg_off_leak_default_bias', 0.0, 0.7, cap_model='nmos_rvt'),
        run('tg_off_leak_interior_bias', 0.15, 0.55, cap_model='nmos_rvt'),
        run('tg_off_leak_sram_access', 0.0, 0.7, 'nmos_sram', 'pmos_sram', 'nmos_rvt'),
        run('tg_off_leak_pmos_storage', 0.0, 0.7, cap_model='pmos_rvt'),
        run('tg_off_leak_pmos_storage_interior', 0.15, 0.55, cap_model='pmos_rvt'),
    ]
    path = RES / 'tg_off_leakage_diagnosis.json'
    path.write_text(json.dumps({'results': results}, indent=2) + '\n')
    print(json.dumps(results, indent=2))
    print('wrote', path)
    hold_results = [
        run_hold_probe('hold_probe_nmos8', 'nmos_rvt'),
        run_hold_probe('hold_probe_pmos8', 'pmos_rvt'),
        run_hold_probe('hold_probe_pmos8_interior', 'pmos_rvt', 0.15, 0.55),
        run_hold_probe('hold_probe_ideal20pf', 'ideal20pf'),
    ]
    hold_path = RES / 'hold_branch_currents.json'
    hold_path.write_text(json.dumps({'results': hold_results}, indent=2) + '\n')
    print(json.dumps(hold_results, indent=2))
    print('wrote', hold_path)
    return 0 if all(r['simulation_completed'] for r in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
