"""ASAP7 Stage-3B: MOSFET Cgg storage characterization (Docker/ngspice45 only).

Option B: membrane storage uses FinFET gate capacitance (drain/source tied to
vcm, gate = state). ASAP7/BSIM-CMG instance order is drain, gate, source, bulk.
Not a PDK MIM/MOM device; voltage-dependent C must be measured and declared.
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/asap7'
BENCH = OUT / 'benches'
RES = OUT / 'results'

# BSIM-CMG / ASAP7 OSDI MOSFET terminal order (matches inverter benches).
#   Nname drain gate source bulk model
TERM_ORDER = 'drain gate source bulk'


def docker_ngspice(name: str, timeout_s: int = 90) -> tuple[int, str]:
    cmd = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic/asap7',
        '--workdir', '/workspace/artifacts/analog_asic/asap7/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        str(timeout_s), '../tools/ngspice45/bin/ngspice', '-b', f'{name}.cir',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 30)
    log = result.stdout + result.stderr
    (RES / f'{name}.log').write_text(log)
    return result.returncode, log


def load_dat(name: str):
    path = RES / f'{name}.dat'
    if not path.is_file():
        return [], []
    lines = path.read_text().splitlines()
    header = lines[0].split() if lines else []
    rows = [[float(x) for x in line.split()] for line in lines[1:] if line.strip()]
    return header, rows


def _moscap_fingers(gate_node: str, n: int, bulk: str = '0') -> str:
    """Parallel nmos_rvt MOSCAPs.

    Terminal order is drain, gate, source, bulk. Gate holds the membrane;
    drain and source are tied to vcm.
    """
    lines = [f'* MOSCAP fingers: N d g s b nmos_rvt with g={gate_node}, d=s=vcm (order: {TERM_ORDER})']
    for i in range(1, n + 1):
        lines.append(f'Nmoscap{i} vcm {gate_node} vcm {bulk} nmos_rvt')
    return '\n'.join(lines)


def write_benches(cv_fingers: int = 4, retention_fingers: int = 8, adjust_fingers: int = 8):
    """Write bounded (small finger-count) storage benches. Not a scaled design."""
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)

    (BENCH / 'mos_cgg_cv.cir').write_text(f'''ASAP7 MOSCAP Cgg vs Vgate; d=s=vcm, gate ramp; terminals D-G-S-B
.include "../models/tt_osdi.spice"
Vcm vcm 0 0.35
{_moscap_fingers('g', cv_fingers)}
* Ramp 0.20 -> 0.50 V in 1us, then hold (leakage sample)
Vg g 0 PWL(0 0.20 10n 0.20 1.01u 0.50 2u 0.50)
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
tran 1n 2u
wrdata ../results/mos_cgg_cv.dat v(g) i(Vg)
quit
.endc
.end
''')

    (BENCH / 'mos_retention_5ms.cir').write_text(f'''ASAP7 MOSCAP 5ms hold after TG sample; Option B; terminals D-G-S-B
.include "../models/tt_osdi.spice"
.include "../modules.spice"
Vdd vdd 0 0.7
Vcm vcm 0 0.35
Vin input 0 PWL(0 0.42 2u 0.42 2.001u 0.28 5.002m 0.28)
Vsample sample 0 PWL(0 0.7 1u 0.7 1.001u 0 5.002m 0)
Vsampleb sample_b 0 PWL(0 0 1u 0 1.001u 0.7 5.002m 0.7)
Xsw input state sample sample_b vdd 0 transmission_gate
{_moscap_fingers('state', retention_fingers)}
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
tran 1u 5.002m 0 1u
wrdata ../results/mos_retention_5ms.dat v(state) v(input) i(Vdd)
quit
.endc
.end
''')

    (BENCH / 'mos_drain_adjust.cir').write_text(f'''ASAP7 MOSCAP drain-to-vcm then rewrite; terminals D-G-S-B
.include "../models/tt_osdi.spice"
.include "../modules.spice"
Vdd vdd 0 0.7
Vcm vcm 0 0.35
Vdrv drv 0 PWL(0 0.42 3u 0.42 3.001u 0.28 8u 0.28 8.001u 0.49 20u 0.49)
Vsam sample 0 PWL(0 0 0.5u 0 0.501u 0.7 1.5u 0.7 1.501u 0 20u 0)
Vsamb sample_b 0 PWL(0 0.7 0.5u 0.7 0.501u 0 1.5u 0 1.501u 0.7 20u 0.7)
Vrst reset 0 PWL(0 0 4u 0 4.001u 0.7 5u 0.7 5.001u 0 20u 0)
Vrstb reset_b 0 PWL(0 0.7 4u 0.7 4.001u 0 5u 0 5.001u 0.7 20u 0.7)
Vsam2 sample2 0 PWL(0 0 9u 0 9.001u 0.7 10u 0.7 10.001u 0 20u 0)
Vsam2b sample2_b 0 PWL(0 0.7 9u 0.7 9.001u 0 10u 0 10.001u 0.7 20u 0.7)
Xw1 drv state sample sample_b vdd 0 transmission_gate
Xr state vcm reset reset_b vdd 0 transmission_gate
Xw2 drv state sample2 sample2_b vdd 0 transmission_gate
{_moscap_fingers('state', adjust_fingers)}
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
tran 10n 20u
wrdata ../results/mos_drain_adjust.dat v(state) v(drv) v(sample) v(reset) v(sample2)
quit
.endc
.end
''')


def analyze_cv(rows, fingers: int):
    """Ceff from ramp displacement current after subtracting hold leakage.

    During the constant-V plateau, i(Vg) ≈ i_leak. During the ramp,
    i ≈ C*dv/dt + i_leak. Use sign-corrected charging current only.
    """
    if not rows:
        return dict(ceff_median_f=None, samples=0)
    ramp = [r for r in rows if 50e-9 <= r[0] <= 1.0e-6]
    hold = [r for r in rows if 1.2e-6 <= r[0] <= 2.0e-6]
    if len(ramp) < 10:
        return dict(ceff_median_f=None, samples=0, note='insufficient ramp samples')
    i_leak = 0.0
    if hold:
        i_leak = sum(r[2] for r in hold) / len(hold)
    ceffs = []
    for a, b in zip(ramp[:-1], ramp[1:]):
        dt = b[0] - a[0]
        dv = b[1] - a[1]
        if dt <= 0 or abs(dv) < 1e-6:
            continue
        i_raw = 0.5 * (a[2] + b[2])
        i_charge = i_raw - i_leak
        # ngspice i(V) sign depends on source orientation; use magnitude after
        # removing estimated leakage from the constant-V plateau.
        i_disp = abs(i_charge)
        ceff = i_disp / abs(dv / dt)
        if math.isfinite(ceff) and ceff > 0:
            ceffs.append(ceff)
    if not ceffs:
        return dict(
            fingers=fingers,
            ceff_median_f=None,
            i_leak_hold_a=i_leak,
            samples=0,
            note='no positive Ceff samples after leakage subtraction',
        )
    ceffs.sort()
    mid = ceffs[len(ceffs) // 2]
    return dict(
        fingers=fingers,
        terminal_order=TERM_ORDER,
        i_leak_hold_a=i_leak,
        ceff_median_f=mid,
        ceff_median_fF=mid * 1e15,
        ceff_per_finger_fF=(mid * 1e15) / fingers,
        ceff_p10_fF=ceffs[max(0, len(ceffs) // 10)] * 1e15,
        ceff_p90_fF=ceffs[min(len(ceffs) - 1, 9 * len(ceffs) // 10)] * 1e15,
        samples=len(ceffs),
        v_start=ramp[0][1],
        v_end=ramp[-1][1],
        note='Ceff=|i_raw-i_leak|/(dv/dt); i_leak from post-ramp constant-V plateau',
    )


def analyze_retention(rows, fingers: int, scale=0.07):
    if not rows:
        return dict(simulation_completed=False)
    initial = min(rows, key=lambda r: abs(r[0] - 1.1e-6))[1]
    final = rows[-1][1]
    drift = final - initial
    return dict(
        simulation_completed=rows[-1][0] >= 5.002e-3 * 0.999,
        t_final=rows[-1][0],
        hold_start_v=initial,
        hold_end_v=final,
        hold_drift_v=drift,
        normalized_model_drift=drift / scale,
        provisional_0_02_unit_retention_pass=abs(drift / scale) < 0.02,
        fingers=fingers,
        terminal_order=TERM_ORDER,
        caveat='MOSFET Cgg (gate storage) with TG; gate leakage and C(V); not MIM',
    )


def analyze_drain_adjust(rows, fingers: int):
    if not rows:
        return dict(simulation_completed=False)

    def at(t):
        return min(rows, key=lambda r: abs(r[0] - t))[1]

    # Sample while switches are off (hold windows).
    w1, drained, w2 = at(2e-6), at(6e-6), at(12e-6)
    return dict(
        simulation_completed=rows[-1][0] >= 20e-6 * 0.999,
        after_write1_v=w1,
        after_drain_v=drained,
        after_write2_v=w2,
        write1_near_target=abs(w1 - 0.42) < 0.05,
        drain_near_vcm=abs(drained - 0.35) < 0.05,
        rewrite_near_target=abs(w2 - 0.49) < 0.08,
        pass_drain_and_adjust=(
            abs(w1 - 0.42) < 0.05
            and abs(drained - 0.35) < 0.05
            and abs(w2 - 0.49) < 0.08
        ),
        fingers=fingers,
        terminal_order=TERM_ORDER,
    )


def complete(end_time, log, rows):
    abort = 'aborted' in log.lower() or 'timestep too small' in log.lower()
    return (bool(rows) and rows[-1][0] >= end_time * 0.999
            and all(math.isfinite(x) for r in rows for x in r) and not abort)


def run_one(name: str, end: float, fingers: int):
    dat = RES / f'{name}.dat'
    if dat.exists():
        dat.unlink()
    code, log = docker_ngspice(name, timeout_s=120 if 'retention' in name else 60)
    _header, rows = load_dat(name)
    ok = code == 0 and complete(end, log, rows)
    entry = dict(
        bench=name,
        simulation_completed=ok,
        exit_code=code,
        final_independent_value=rows[-1][0] if rows else None,
        terminal_order=TERM_ORDER,
    )
    if name == 'mos_cgg_cv' and ok:
        entry.update(analyze_cv(rows, fingers))
    if name == 'mos_retention_5ms' and ok:
        entry.update(analyze_retention(rows, fingers))
    if name == 'mos_drain_adjust' and ok:
        entry.update(analyze_drain_adjust(rows, fingers))
    if not ok:
        for line in log.splitlines():
            if 'timestep' in line.lower() or 'trouble' in line.lower() or 'error' in line.lower():
                entry['failure_hint'] = line.strip()
                break
    return entry


def build_qualification(reports, finger_counts):
    cv = next((r for r in reports if r['bench'] == 'mos_cgg_cv'), {})
    ret = next((r for r in reports if r['bench'] == 'mos_retention_5ms'), {})
    adj = next((r for r in reports if r['bench'] == 'mos_drain_adjust'), {})
    per_fF = cv.get('ceff_per_finger_fF')
    positive_c = isinstance(per_fF, (int, float)) and per_fF > 0 and math.isfinite(per_fF)
    fingers_for_20pF = None if not positive_c else int(math.ceil(20000.0 / per_fF))

    # Acceptance requires CV + 5ms retention smoke + drain/adjust — not reset alone.
    accepted = bool(
        cv.get('simulation_completed')
        and positive_c
        and ret.get('simulation_completed')
        and ret.get('provisional_0_02_unit_retention_pass')
        and adj.get('simulation_completed')
        and adj.get('pass_drain_and_adjust')
    )
    return dict(
        decision='B_mos_cgg_storage',
        decided_at='2026-09-23',
        rationale=(
            'User selected MOSFET Cgg so membrane charge can be drained and adjusted; '
            'open ASAP7 PDK has no MIM/MOM card'
        ),
        topology=(
            f'nmos_rvt terminals {TERM_ORDER}; gate=state, drain=source=vcm (MOSCAP); '
            'write/reset via transmission gates'
        ),
        wiring_fix='2026-09-23_codex_review_gate_was_drain_now_corrected',
        pdk_device='nmos_rvt BSIM-CMG 107 OSDI; not a discrete capacitor',
        voltage=dict(vdd=0.7, vcm=0.35, characterized_gate_range_v=[0.20, 0.50]),
        finger_counts=finger_counts,
        benches=reports,
        effective_capacitance=cv,
        retention_5ms=ret,
        drain_adjust=adj,
        sizing_hint=dict(
            target_ideal_c_for_0_02_smoke_fF=20000,
            measured_ceff_per_finger_fF=per_fF if positive_c else None,
            fingers_to_match_20pF_approx=fingers_for_20pF,
            population_area='not computed; layout not started',
        ),
        accepted_as_physical_mim=False,
        accepted_as_option_b_candidate=accepted,
        acceptance_requires=[
            'mos_cgg_cv completed with positive Ceff after leakage subtraction',
            'mos_retention_5ms provisional_0_02_unit_retention_pass',
            'mos_drain_adjust pass_drain_and_adjust (write, drain, rewrite)',
        ],
        limitations=[
            'C is voltage-dependent; median Ceff is not a constant linear capacitor',
            'Bounded finger counts only; not a scaled membrane library',
            'No Calibre extraction; schematic MOSCAP only',
            'Ideal-C PLIF smoke remains separate until membrane_hold switches to MOSCAP',
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--only',
        choices=['mos_cgg_cv', 'mos_retention_5ms', 'mos_drain_adjust', 'all'],
        default='mos_cgg_cv',
        help='Bounded default: one C-V storage test. Use all only after wiring is trusted.',
    )
    args = parser.parse_args()

    # Small finger counts — characterization only, not design scaling.
    finger_counts = dict(mos_cgg_cv=4, mos_retention_5ms=8, mos_drain_adjust=8)
    write_benches(
        cv_fingers=finger_counts['mos_cgg_cv'],
        retention_fingers=finger_counts['mos_retention_5ms'],
        adjust_fingers=finger_counts['mos_drain_adjust'],
    )

    plan = {
        'mos_cgg_cv': (2e-6, finger_counts['mos_cgg_cv']),
        'mos_retention_5ms': (5.002e-3, finger_counts['mos_retention_5ms']),
        'mos_drain_adjust': (20e-6, finger_counts['mos_drain_adjust']),
    }
    names = list(plan) if args.only == 'all' else [args.only]
    reports = []
    for name in names:
        end, fingers = plan[name]
        entry = run_one(name, end, fingers)
        print(json.dumps(entry))
        reports.append(entry)

    # Merge prior bench results into qualification when running a single test so
    # acceptance does not silently flip true without retention evidence.
    prior_path = RES / 'mos_storage_checks.json'
    prior_by = {}
    if prior_path.is_file():
        try:
            prior = json.loads(prior_path.read_text())
            for r in prior.get('results', []):
                prior_by[r.get('bench')] = r
        except json.JSONDecodeError:
            pass
    for r in reports:
        prior_by[r['bench']] = r
    # Drop stale results that still show the pre-fix drain-first wiring.
    merged = []
    for name in ('mos_cgg_cv', 'mos_retention_5ms', 'mos_drain_adjust'):
        r = prior_by.get(name)
        if not r:
            continue
        if r.get('terminal_order') != TERM_ORDER:
            continue
        topo = (r.get('topology') or '') + (r.get('caveat') or '')
        if 'gate=state' in str(json.dumps(r)) or r.get('terminal_order') == TERM_ORDER:
            merged.append(r)

    qual = build_qualification(merged, finger_counts)
    # If only CV was run, candidate cannot be accepted (retention missing).
    if args.only != 'all':
        qual['accepted_as_option_b_candidate'] = False
        qual['partial_run'] = args.only
        qual['note'] = (
            f'Partial run (--only {args.only}); option-B candidate acceptance '
            'requires all three benches including 5ms retention'
        )

    (OUT / 'capacitor_qualification.json').write_text(json.dumps(qual, indent=2) + '\n')
    (RES / 'mos_storage_checks.json').write_text(
        json.dumps(dict(results=merged, qualification=qual), indent=2) + '\n'
    )
    print('wrote', OUT / 'capacitor_qualification.json')
    print('accepted_as_option_b_candidate', qual['accepted_as_option_b_candidate'])
    return 0 if reports and reports[0].get('simulation_completed') else 2


if __name__ == '__main__':
    raise SystemExit(main())
