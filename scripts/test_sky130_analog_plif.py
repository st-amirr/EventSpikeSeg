"""SKY130 mixed-signal analog PLIF channel screen (Docker ngspice only).

Proves transistor+MIM inject / hold / leak / threshold on one physical channel.
Population mapping: multiplexed analog channel + digital membrane codes (documented).
"""
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic'
BENCH = OUT / 'benches'
RES = OUT / 'results'

VDD, VCM, SCALE = 1.8, 0.9, 0.2
THETA = 0.4
DRIFT_LIM = 0.02 * SCALE


def docker_ngspice(name: str, timeout_s: int = 120):
    cmd = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic',
        '--workdir', '/workspace/artifacts/analog_asic/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        str(timeout_s), 'ngspice', '-b', f'{name}.cir',
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 30)
    (RES / f'{name}.log').write_text(r.stdout + r.stderr)
    return r.returncode, r.stdout + r.stderr


def load_rows(name):
    p = RES / f'{name}.dat'
    if not p.is_file():
        return []
    return [[float(x) for x in line.split()] for line in p.read_text().splitlines()[1:] if line.strip()]


def nearest(rows, t):
    return min(rows, key=lambda r: abs(r[0] - t))


COMMON = f'''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
'''


def write_benches():
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)

    # 1) Hold after MOS inject
    (BENCH / 'ms_plif_inject_hold.cir').write_text(f'''SKY130 MS PLIF: MOS inject then 5ms MIM hold
{COMMON}
Vdd vdd 0 {VDD}
Vcm vcm 0 {VCM}
Vbias bias 0 0.65
Vibp ibias_p 0 1.2
Vibn ibias_n 0 0.4
Vrst reset 0 PWL(0 {VDD} 0.5u {VDD} 0.501u 0 6m 0)
Vrstb reset_b 0 PWL(0 0 0.5u 0 0.501u {VDD} 6m {VDD})
Vpp pulse_pos 0 PWL(0 {VDD} 1u {VDD} 1.001u 0 2u 0 2.001u {VDD} 6m {VDD})
Vpn pulse_neg 0 0
Vle leak_en 0 0
Vleb leak_enb 0 {VDD}
Vcap capture 0 0
Vcapb capture_b 0 {VDD}
Xplif state snapshot spike capture capture_b reset reset_b leak_en leak_enb
+ pulse_pos pulse_neg ibias_p ibias_n bias vdd 0 vcm analog_plif_channel
+ theta={THETA} scale={SCALE} w_um=100 l_um=100
.control
set wr_singlescale
set wr_vecnames
tran 1u 5.002m 0 1u
wrdata ../results/ms_plif_inject_hold.dat v(state) v(spike) i(Vdd)
quit
.endc
.end
''')

    # 2) Leak/decay phase after inject
    (BENCH / 'ms_plif_leak.cir').write_text(f'''SKY130 MS PLIF: MOS leak toward vcm after inject
{COMMON}
Vdd vdd 0 {VDD}
Vcm vcm 0 {VCM}
Vbias bias 0 0.65
Vibp ibias_p 0 1.2
Vibn ibias_n 0 0.4
Vrst reset 0 PWL(0 {VDD} 0.4u {VDD} 0.401u 0 50u 0)
Vrstb reset_b 0 PWL(0 0 0.4u 0 0.401u {VDD} 50u {VDD})
Vpp pulse_pos 0 PWL(0 {VDD} 1u {VDD} 1.001u 0 2u 0 2.001u {VDD} 50u {VDD})
Vpn pulse_neg 0 0
* leak window 10u-30u
Vle leak_en 0 PWL(0 0 10u 0 10.001u {VDD} 30u {VDD} 30.001u 0 50u 0)
Vleb leak_enb 0 PWL(0 {VDD} 10u {VDD} 10.001u 0 30u 0 30.001u {VDD} 50u {VDD})
Vcap capture 0 0
Vcapb capture_b 0 {VDD}
Xplif state snapshot spike capture capture_b reset reset_b leak_en leak_enb
+ pulse_pos pulse_neg ibias_p ibias_n bias vdd 0 vcm analog_plif_channel
+ theta={THETA} scale={SCALE} w_um=100 l_um=100
.control
set wr_singlescale
set wr_vecnames
tran 50n 50u
wrdata ../results/ms_plif_leak.dat v(state) v(leak_en) i(Vdd)
quit
.endc
.end
''')

    # 3) Threshold: inject enough to cross theta, capture, see spike
    (BENCH / 'ms_plif_threshold.cir').write_text(f'''SKY130 MS PLIF: inject above theta then capture/compare
{COMMON}
Vdd vdd 0 {VDD}
Vcm vcm 0 {VCM}
Vbias bias 0 0.65
Vibp ibias_p 0 1.4
Vibn ibias_n 0 0.4
Vrst reset 0 PWL(0 {VDD} 0.4u {VDD} 0.401u 0 20u 0)
Vrstb reset_b 0 PWL(0 0 0.4u 0 0.401u {VDD} 20u {VDD})
Vpp pulse_pos 0 PWL(0 {VDD} 1u {VDD} 1.001u 0 4u 0 4.001u {VDD} 20u {VDD})
Vpn pulse_neg 0 0
Vle leak_en 0 0
Vleb leak_enb 0 {VDD}
Vcap capture 0 PWL(0 0 5u 0 5.001u {VDD} 6u {VDD} 6.001u 0 20u 0)
Vcapb capture_b 0 PWL(0 {VDD} 5u {VDD} 5.001u 0 6u 0 6.001u {VDD} 20u {VDD})
Xplif state snapshot spike capture capture_b reset reset_b leak_en leak_enb
+ pulse_pos pulse_neg ibias_p ibias_n bias vdd 0 vcm analog_plif_channel
+ theta={THETA} scale={SCALE} w_um=100 l_um=100
.control
set wr_singlescale
set wr_vecnames
tran 20n 20u
wrdata ../results/ms_plif_threshold.dat v(state) v(snapshot) v(spike) v(capture)
quit
.endc
.end
''')


def complete(rows, end, log):
    return (bool(rows) and rows[-1][0] >= end * 0.999
            and 'timestep too small' not in log.lower() and 'aborted' not in log.lower()
            and all(math.isfinite(x) for r in rows for x in r))


def main():
    write_benches()
    reports = []

    # inject + hold
    name, end = 'ms_plif_inject_hold', 5.002e-3
    (RES / f'{name}.dat').unlink(missing_ok=True)
    code, log = docker_ngspice(name, 180)
    rows = load_rows(name)
    ok = code == 0 and complete(rows, end, log)
    entry = dict(bench=name, simulation_completed=ok, exit_code=code)
    if ok:
        # after inject ~3u, after hold end
        post = nearest(rows, 3e-6)[1]
        final = rows[-1][1]
        drift = final - post
        entry.update(
            post_inject_v=post, hold_end_v=final, hold_drift_v=drift,
            normalized_drift=drift / SCALE,
            inject_moved_from_vcm=abs(post - VCM) > 0.02,
            provisional_hold_pass=abs(drift) < DRIFT_LIM and abs(post - VCM) > 0.02,
        )
    else:
        for line in log.splitlines():
            if 'error' in line.lower() or 'undefined' in line.lower() or 'timestep' in line.lower():
                entry['failure_hint'] = line.strip()
                break
    print(json.dumps(entry))
    reports.append(entry)

    # leak
    name, end = 'ms_plif_leak', 50e-6
    (RES / f'{name}.dat').unlink(missing_ok=True)
    code, log = docker_ngspice(name, 90)
    rows = load_rows(name)
    ok = code == 0 and complete(rows, end, log)
    entry = dict(bench=name, simulation_completed=ok, exit_code=code)
    if ok:
        before = nearest(rows, 9e-6)[1]
        after = nearest(rows, 31e-6)[1]
        entry.update(
            pre_leak_v=before, post_leak_v=after,
            leak_delta_v=after - before,
            leak_toward_vcm=abs(after - VCM) < abs(before - VCM),
            leak_pass=abs(after - VCM) < abs(before - VCM) and abs(before - VCM) > 0.02,
        )
    else:
        for line in log.splitlines():
            if 'error' in line.lower() or 'undefined' in line.lower() or 'timestep' in line.lower():
                entry['failure_hint'] = line.strip()
                break
    print(json.dumps(entry))
    reports.append(entry)

    # threshold
    name, end = 'ms_plif_threshold', 20e-6
    (RES / f'{name}.dat').unlink(missing_ok=True)
    code, log = docker_ngspice(name, 90)
    rows = load_rows(name)
    ok = code == 0 and complete(rows, end, log)
    entry = dict(bench=name, simulation_completed=ok, exit_code=code)
    if ok:
        # cols: t state snapshot spike capture
        pre = nearest(rows, 4.5e-6)
        cap = nearest(rows, 5.5e-6)
        thr = VCM + SCALE * THETA
        entry.update(
            pre_capture_state_v=pre[1], snapshot_v=cap[2], spike_v=cap[3],
            threshold_v=thr, above_threshold=pre[1] > thr,
            spike_high=cap[3] > VDD * 0.5,
            threshold_pass=pre[1] > thr and cap[3] > VDD * 0.5,
        )
    else:
        for line in log.splitlines():
            if 'error' in line.lower() or 'undefined' in line.lower() or 'timestep' in line.lower():
                entry['failure_hint'] = line.strip()
                break
    print(json.dumps(entry))
    reports.append(entry)

    summary = dict(
        architecture='sky130_mixed_signal_analog_plif_multiplexed',
        asap7_analog_storage='rejected_no_mim_mos_cgg_fails',
        digital_blocks='ASAP7_or_SKY130_digital_routing_control_preserved_paused',
        population_policy=(
            'Representative physical MIM+MOS PLIF channel only; logical-state '
            'multiplexing is not yet shown area- or throughput-feasible for 30,976,000 '
            'identities. The 24-step SAR lower bound is 743,424,000 comparisons per '
            '5ms update (at least 1,487 lanes at 100MHz before other phases). '
            'Not 31M resident MIMs.'
        ),
        results=reports,
        channel_smoke_pass=all([
            next((r.get('provisional_hold_pass') for r in reports if r['bench'] == 'ms_plif_inject_hold'), False),
            next((r.get('leak_pass') for r in reports if r['bench'] == 'ms_plif_leak'), False),
            next((r.get('threshold_pass') for r in reports if r['bench'] == 'ms_plif_threshold'), False),
        ]),
    )
    (RES / 'sky130_ms_plif_screen.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('channel_smoke_pass', summary['channel_smoke_pass'])
    print('wrote', RES / 'sky130_ms_plif_screen.json')
    return 0 if summary['channel_smoke_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
