"""Isolate ASAP7 MOSCAP 5 ms storage loss with bounded controls (ngspice45 in Docker)."""
import argparse
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/asap7'
BENCH = OUT / 'benches'
RES = OUT / 'results'
TERM = 'drain gate source bulk'
CEFF_PER_FINGER = 0.06758806170288091  # latest leakage-subtracted 4-finger C-V


def deck(name, kind, fingers=8, tight=False):
    stack_switch = kind.endswith('_stack')
    if stack_switch:
        kind = kind.removesuffix('_stack')
    interior_bias = kind.endswith('_interior')
    if interior_bias:
        kind = kind.removesuffix('_interior')
    floating = kind.startswith('float_')
    if floating:
        kind = kind.removeprefix('float_')
    mos = '\n'.join(
        f'Ncap{i} vcm state vcm 0 nmos_rvt' for i in range(1, fingers + 1)
    )
    if kind == 'moscap':
        storage = f'* D-G-S-B MOSCAP, gate=state; {fingers} parallel fingers\n{mos}'
    elif kind.startswith('nmoscap_'):
        model = kind.removeprefix('nmoscap_')
        devs = '\n'.join(
            f'Ncap{i} vcm state vcm 0 {model}' for i in range(1, fingers + 1)
        )
        storage = f'* D-G-S-B NMOS Cgg ({model}); {fingers} parallel fingers\n{devs}'
    elif kind.startswith('pmoscap'):
        model = kind.removeprefix('pmoscap_') if '_' in kind else 'pmos_rvt'
        pmos = '\n'.join(
            f'Npcap{i} vdd state vdd vdd {model}' for i in range(1, fingers + 1)
        )
        storage = f'* D-G-S-B PMOS Cgg ({model}), gate=state; {fingers} parallel fingers\n{pmos}'
    elif kind == 'ideal':
        c_f = fingers * CEFF_PER_FINGER * 1e-15
        storage = f'* Ideal control sized to {fingers} x measured Ceff per finger\nCstore state vcm {c_f:.12g}\n'
    elif kind.startswith('ideal_pf_'):
        c_f = float(kind.removeprefix('ideal_pf_')) * 1e-12
        storage = f'* Ideal capacitor control, C={c_f:g} F\nCstore state vcm {c_f:.12g}\n'
    else:
        raise ValueError(kind)
    stack = '''.subckt tg_stack a b en enb vdd vss
Nn1 a en mid vss nmos_rvt
Np1 a enb mid vdd pmos_rvt
Nn2 mid en b vss nmos_rvt
Np2 mid enb b vdd pmos_rvt
.ends tg_stack
'''
    if floating:
        switch = ''
    elif stack_switch:
        switch = stack + 'Xsw input state sample sample_b vdd 0 tg_stack\n'
    else:
        switch = 'Xsw input state sample sample_b vdd 0 transmission_gate\n'
    initial = '.ic v(state)=0.42\n' if floating else ''
    uic = ' uic' if floating else ''
    options = '.options abstol=1e-18 reltol=1e-6 vntol=1e-9 chgtol=1e-20 gmin=1e-18\n' if tight else ''
    n_off, p_off = (0.15, 0.55) if interior_bias else (0.0, 0.7)
    sample = f'Vsample sample 0 PWL(0 0.7 1u 0.7 1.001u {n_off} 5.002m {n_off})\n'
    sampleb = f'Vsampleb sample_b 0 PWL(0 0 1u 0 1.001u {p_off} 5.002m {p_off})\n'
    return f'''ASAP7 MOSCAP retention isolation: {name}; D-G-S-B={TERM}
.include "../models/tt_osdi.spice"
.include "../modules.spice"
Vdd vdd 0 0.7
Vcm vcm 0 0.35
Vin input 0 PWL(0 0.42 2u 0.42 2.001u 0.28 5.002m 0.28)
{sample}{sampleb}
{switch}{initial}
{storage}
{options}
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
tran 1u 5.002m 0 1u{uic}
wrdata ../results/{name}.dat v(state) v(input) i(Vcm) i(Vdd)
quit
.endc
.end
'''


def run(name, kind, fingers, tight=False):
    topology = kind
    base_kind = kind.removesuffix('_stack').removesuffix('_interior')
    cir = BENCH / f'{name}.cir'
    cir.write_text(deck(name, kind, fingers, tight))
    command = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic/asap7',
        '--workdir', '/workspace/artifacts/analog_asic/asap7/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        '120', '../tools/ngspice45/bin/ngspice', '-b', cir.name,
    ]
    p = subprocess.run(command, capture_output=True, text=True, timeout=150)
    (RES / f'{name}.log').write_text(p.stdout + p.stderr)
    data_path = RES / f'{name}.dat'
    lines = data_path.read_text().splitlines() if data_path.is_file() else []
    rows = [[float(v) for v in line.split()] for line in lines[1:] if line.strip()]
    complete = bool(rows) and rows[-1][0] >= 5.002e-3 * 0.999 and all(
        math.isfinite(v) for row in rows for v in row
    ) and p.returncode == 0
    near_sample = next((r for r in rows if r[0] >= 5e-6), None)
    late = [r for r in rows if r[0] >= 4.5e-3]
    result = {
        'bench': name,
        'topology': topology,
        'fingers_or_matched_units': fingers,
        'capacitor_model': base_kind.removeprefix('nmoscap_') if base_kind.startswith('nmoscap_') else (base_kind.removeprefix('pmoscap_') if base_kind.startswith('pmoscap_') else 'pmos_rvt' if base_kind == 'pmoscap' else 'nmos_rvt' if base_kind == 'moscap' else None),
        'parallel_instances': fingers if base_kind in ('moscap', 'pmoscap') or base_kind.startswith(('nmoscap_', 'pmoscap_')) else None,
        'model_nfin_per_instance': 3 if base_kind in ('moscap', 'pmoscap') or base_kind.startswith(('nmoscap_', 'pmoscap_')) else None,
        'ideal_capacitance_f': (fingers * CEFF_PER_FINGER * 1e-15 if base_kind == 'ideal' else float(base_kind.removeprefix('ideal_pf_')) * 1e-12 if base_kind.startswith('ideal_pf_') else None),
        'terminal_order': TERM,
        'simulation_completed': complete,
        'exit_code': p.returncode,
        't_final_s': rows[-1][0] if rows else None,
        'state_after_sample_v': near_sample[1] if near_sample else None,
        'state_final_v': rows[-1][1] if rows else None,
        'drift_v': (rows[-1][1] - near_sample[1]) if rows and near_sample else None,
        'mean_i_vcm_last_0p5ms_a': (sum(r[3] for r in late) / len(late)) if late else None,
        'mean_i_vdd_last_0p5ms_a': (sum(r[4] for r in late) / len(late)) if late else None,
    }
    return result


def run_cv(model, fingers=8, tight=False):
    name = f'mos_cv_diag_{model}' + ('_tight' if tight else '')
    if model.startswith('pmos_'):
        cap = '\n'.join(f'Ncap{i} vdd g vdd vdd {model}' for i in range(1, fingers + 1))
        bias = 'Vdd vdd 0 0.7\n'
    else:
        cap = '\n'.join(f'Ncap{i} vcm g vcm 0 {model}' for i in range(1, fingers + 1))
        bias = 'Vcm vcm 0 0.35\n'
    options = '.options abstol=1e-18 reltol=1e-6 vntol=1e-9 chgtol=1e-20 gmin=1e-18\n' if tight else ''
    (BENCH / f'{name}.cir').write_text(f'''ASAP7 C-V diagnostic for {model}, gate range 0.28..0.42 V
.include "../models/tt_osdi.spice"
{bias}Vg g 0 PWL(0 0.28 10n 0.28 1.01u 0.42 2u 0.42)
{cap}
{options}
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
tran 1n 2u
wrdata ../results/{name}.dat v(g) i(Vg)
quit
.endc
.end
''')
    command = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic/asap7',
        '--workdir', '/workspace/artifacts/analog_asic/asap7/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        '120', '../tools/ngspice45/bin/ngspice', '-b', f'{name}.cir',
    ]
    p = subprocess.run(command, capture_output=True, text=True, timeout=150)
    (RES / f'{name}.log').write_text(p.stdout + p.stderr)
    data = RES / f'{name}.dat'
    lines = data.read_text().splitlines() if data.is_file() else []
    rows = [[float(v) for v in line.split()] for line in lines[1:] if line.strip()]
    plateau = [r for r in rows if 1.2e-6 <= r[0] <= 2e-6]
    ramp = [r for r in rows if 50e-9 <= r[0] <= 1e-6]
    leak = sum(r[2] for r in plateau) / len(plateau) if plateau else 0.0
    ceff = []
    for a, b in zip(ramp[:-1], ramp[1:]):
        dv = b[1] - a[1]
        dt = b[0] - a[0]
        if dt > 0 and abs(dv) >= 1e-8:
            ceff.append(abs(((a[2] + b[2]) / 2 - leak) / (dv / dt)))
    return {
        'bench': name, 'device': model, 'fingers': fingers,
        'model_nfin_per_instance': 3,
        'tolerances': 'tight: ABSTOL=1e-18 RELTOL=1e-6 VNTOL=1e-9 CHGTOL=1e-20 GMIN=1e-18' if tight else 'ngspice defaults',
        'terminal_order': TERM, 'simulation_completed': bool(rows and rows[-1][0] >= 1.998e-6 and p.returncode == 0),
        'exit_code': p.returncode, 'leakage_plateau_a': leak,
        'ceff_median_fF': (sorted(ceff)[len(ceff) // 2] * 1e15) if ceff else None,
        'ceff_per_finger_fF': (sorted(ceff)[len(ceff) // 2] * 1e15 / fingers) if ceff else None,
        'sample_count': len(ceff), 'v_start': rows[0][1] if rows else None,
        'v_end': rows[-1][1] if rows else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cv-only', action='store_true', help='Run only bounded C-V diagnostics across PDK device flavors.')
    parser.add_argument('--tolerance-audit', action='store_true', help='Compare default and tight numerical tolerances on retention and C-V controls.')
    parser.add_argument('--interior-only', action='store_true', help='Run only the 8-instance pMOS Cgg interior off-gate bias hold test.')
    args = parser.parse_args()
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    if args.interior_only:
        result = run('mos_retention_diag_pmos8_interior_bias', 'pmoscap_interior', 8)
        path = RES / 'mos_interior_bias_hold.json'
        path.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        print('wrote', path)
        return 0 if result['simulation_completed'] else 2
    if args.tolerance_audit:
        cases = [
            ('pmos_rvt', 'pmoscap', 8),
            ('ideal20pf', 'ideal_pf_20', 0),
        ]
        audit = []
        for label, kind, count in cases:
            audit.append(run(f'mos_tolerance_{label}_default', kind, count, False))
            audit.append(run(f'mos_tolerance_{label}_tight', kind, count, True))
        audit += [run_cv('pmos_rvt', 8, False), run_cv('pmos_rvt', 8, True)]
        path = RES / 'mos_tolerance_audit.json'
        path.write_text(json.dumps({'results': audit}, indent=2) + '\n')
        print(json.dumps(audit, indent=2))
        print('wrote', path)
        return 0 if all(r['simulation_completed'] for r in audit) else 2
    if args.cv_only:
        cv_results = [run_cv(model, 8) for model in (
            'nmos_rvt', 'nmos_lvt', 'nmos_slvt', 'nmos_sram',
            'pmos_rvt', 'pmos_lvt', 'pmos_slvt', 'pmos_sram',
        )]
        cv_path = RES / 'mos_cgg_device_cv_diagnosis.json'
        cv_path.write_text(json.dumps({'results': cv_results}, indent=2) + '\n')
        print(json.dumps(cv_results, indent=2))
        print('wrote', cv_path)
        return 0 if all(r['simulation_completed'] for r in cv_results) else 2
    results = [
        run('mos_retention_diag_nmos8', 'moscap', 8),
        run('mos_retention_diag_nmos32', 'moscap', 32),
        run('mos_retention_diag_ideal8matched', 'ideal', 8),
        run('mos_retention_diag_ideal1pf', 'ideal_pf_1', 0),
        run('mos_retention_diag_ideal20pf', 'ideal_pf_20', 0),
        run('mos_retention_diag_pmos8', 'pmoscap', 8),
        run('mos_retention_diag_pmos32', 'pmoscap', 32),
        run('mos_retention_diag_pmos128', 'pmoscap', 128),
        run('mos_retention_diag_nmos_lvt8', 'nmoscap_nmos_lvt', 8),
        run('mos_retention_diag_nmos_slvt8', 'nmoscap_nmos_slvt', 8),
        run('mos_retention_diag_nmos_sram8', 'nmoscap_nmos_sram', 8),
        run('mos_retention_diag_pmos_lvt8', 'pmoscap_pmos_lvt', 8),
        run('mos_retention_diag_pmos_slvt8', 'pmoscap_pmos_slvt', 8),
        run('mos_retention_diag_pmos_sram8', 'pmoscap_pmos_sram', 8),
        run('mos_retention_diag_pmos8_tgstack', 'pmoscap_stack', 8),
        run('mos_retention_diag_ideal1pf_tgstack', 'ideal_pf_1_stack', 0),
    ]
    path = RES / 'mos_retention_diagnosis.json'
    path.write_text(json.dumps({'results': results}, indent=2) + '\n')
    cv_results = [run_cv(model, 8) for model in (
        'nmos_rvt', 'nmos_lvt', 'nmos_slvt', 'nmos_sram',
        'pmos_rvt', 'pmos_lvt', 'pmos_slvt', 'pmos_sram',
    )]
    cv_path = RES / 'mos_cgg_device_cv_diagnosis.json'
    cv_path.write_text(json.dumps({'results': cv_results}, indent=2) + '\n')
    print(json.dumps(results, indent=2))
    print('wrote', path)
    print(json.dumps(cv_results, indent=2))
    print('wrote', cv_path)
    return 0 if all(r['simulation_completed'] for r in results + cv_results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
