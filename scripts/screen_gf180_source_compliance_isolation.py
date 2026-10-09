"""Bounded native source/switch diagnostic with an ideal metrology termination.

This isolates delivered charge from the active integrator. It is NOT an ASIC
implementation, a virtual-ground solution, or a transfer of seed29 calibration.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sum-w-v', type=float, default=1.65)
    p.add_argument('--sum-r-v', type=float, default=1.65)
    p.add_argument('--clock-only', action='store_true')
    p.add_argument('--park-mode', choices=['vcm', 'termination', 'buffer'], default='vcm')
    a = p.parse_args()
    assert 1.6 <= a.sum_w_v <= 1.7 and 1.6 <= a.sum_r_v <= 1.7
    files = set()
    definitions = []
    cells = ['gf180_fixed_body_tg_fullroute_half', 'gf180_phase_inverter_fullroute',
                 'gf180_precharged_weight_current_cell_fullroute_guarded']
    if a.park_mode == 'buffer':
        cells.append('gf180_shared_ota_core_pmos_input_fullroute')
    for cell in cells:
        folder = BASE / 'layout' / cell
        qp = folder / 'qualification.json'
        q = json.loads(qp.read_text(encoding='utf-8'))
        assert q['magic_drc_count'] == q['gds_roundtrip_drc_count'] == 0
        assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
        files.add(qp)
        for key in ['sha256', 'input_sha256', 'gds_roundtrip_sha256']:
            for name, h in q.get(key, {}).items():
                f = folder / name if key == 'sha256' else ROOT / name
                assert sha(f) == h, str(f)
                files.add(f)
        f = folder / (cell + '_cap.spice')
        files.add(f)
        text = f.read_text(encoding='utf-8')
        for child in re.findall(r'(?m)^\.subckt (\S+)', text):
            if child != cell:
                text = re.sub(r'(?<![A-Za-z0-9_])' + re.escape(child) + r'(?![A-Za-z0-9_])',
                              cell + '__' + child, text)
        definitions.append(text)
    models = BASE / 'pdk/gf180_primitive_source/models/ngspice'
    files.update(models.rglob('*.spice'))
    prefix = '/workspace/' + models.relative_to(ROOT).as_posix()
    stem = 'gf180_source_compliance_isolation_' + hashlib.sha256(
        json.dumps(vars(a), sort_keys=True).encode()).hexdigest()[:10] + '_src' + sha(Path(__file__))[:12]
    lines = ['Native source compliance isolation; ideal bench termination only',
             f'.include {prefix}/design.spice', f'.lib {prefix}/sm141064.spice typical',
             f'.lib {prefix}/sm141064.spice mimcap_typical',
             '.param sw_stat_global=0 sw_stat_mismatch=0', '.temp 27',
             '.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',
             *definitions, 'Vdd vdd 0 3.3', 'Vcm vcm 0 1.65', 'Vncas ncas 0 1.1',
             'Vpcas pcas 0 2.2', 'Vprecharge_ref precharge_reference 0 2.9']
    # Same PROGRAM/timing values are stimuli only; there is no transplanted calibration claim.
    levels = [2.6840099445261996, 2.704527893300186]
    widths = [1.4219261595896255, 2.112382981502571]
    clocks = {'write': 'PWL(0 3.3 9.99u 3.3 10u 0)',
              'precharge': 'PWL(0 3.3 9.99u 3.3 10u 0)'}
    for tag in ['w', 'r']:
        lines.append(f'Vtermination_{tag} sum_{tag} 0 {getattr(a, "sum_" + tag + "_v")}')
        lines.append(f'Vmeter_{tag} inject_{tag} sum_{tag} 0')
        if a.park_mode == 'termination':
            lines.append(f'Vpark_{tag} park_{tag} 0 {getattr(a, "sum_" + tag + "_v")}')
        elif a.park_mode == 'buffer':
            lines.extend([f'Xparkbuffer_{tag} sum_{tag} park_{tag} park_{tag} vdd 0 bias cmp_{tag} gf180_shared_ota_core_pmos_input_fullroute',
                          f'Xparkcomp_{tag} park_{tag} cmp_{tag} cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u',
                          f'Cparkload_{tag} park_{tag} 0 50f'])
    if a.park_mode == 'buffer':
        lines.extend(['Ireference bias 0 1u', 'Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u'])
    for i in range(2):
        start = 122 + 8 * i
        end = start + widths[i]
        clocks[f'event{i}'] = f'PWL(0 0 {start-.01:.12g}u 0 {start}u 3.3 {end-.01:.12g}u 3.3 {end:.12g}u 0)'
        clocks[f'idle{i}'] = f'PWL(0 3.3 {start-.03:.12g}u 3.3 {start-.02:.12g}u 0 {end+.01:.12g}u 0 {end+.02:.12g}u 3.3)'
        for tag in ['w', 'r']:
            level = levels[i] if tag == 'w' and not a.clock_only else 2.7
            lines.extend([f'Vprogram_{i}_{tag} program_{i}_{tag} 0 {level}',
                          f'Xsource_{i}_{tag} program_{i}_{tag} write writeb vcm pout_{i}_{tag} ncas pcas vdd 0 gate_{i}_{tag} ni_{i}_{tag} pi_{i}_{tag} precharge_reference precharge prechargeb gf180_precharged_weight_current_cell_fullroute_guarded',
                          f'Xselect_{i}_{tag} pout_{i}_{tag} inject_{tag} event{i} event{i}b 0 vdd gf180_fixed_body_tg_fullroute_half',
                          f'Xidle_{i}_{tag} pout_{i}_{tag} {"vcm" if a.park_mode == "vcm" else "park_" + tag} idle{i} idle{i}b 0 vdd gf180_fixed_body_tg_fullroute_half'])
    for phase, command in clocks.items():
        lines.extend([f'V{phase} {phase}_command 0 {command}',
                      f'Xcb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',
                      f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
    lines.extend(['.control', 'set numdgt=15', 'tran 5n 145u 0 5n uic',
                  'let current_diff=i(Vmeter_w)-i(Vmeter_r)'])
    for i in range(2):
        start = 122 + 8 * i
        lines.extend([f'meas tran idle_{i} avg current_diff from={start-1}u to={start-.5}u',
                      f'meas tran charge_{i} integ current_diff from={start-.25}u to={start+4}u',
                      f'meas tran plateau_{i} avg current_diff from={start+.1}u to={start+widths[i]-.1:.12g}u'])
    if a.park_mode == 'buffer':
        for tag in ['w', 'r']:
            lines.append(f'meas tran park_{tag} find v(park_{tag}) at=121u')
    lines.extend(['quit', '.endc', '.end'])
    deck = BASE / 'benches' / (stem + '.spice')
    deck.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    snap = BASE / 'tools/source_snapshots' / (stem + '.py')
    snap.write_bytes(Path(__file__).read_bytes())
    files.update([deck, snap])
    run = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--memory', '2g',
                          '--cpus', '2', '--volume', f'{ROOT}:/workspace', '--workdir', '/workspace',
                          '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice47', '120',
                          'ngspice', '-b', '/workspace/' + deck.relative_to(ROOT).as_posix()],
                         capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    lp = BASE / 'results' / (stem + '.log')
    lp.write_text(log, encoding='utf-8')
    files.add(lp)
    values = {k: float(v) for k, v in re.findall(r'(?m)^((?:idle|charge|plateau)_[01]|park_[wr])\s*=\s*([-+0-9.eE]+)', log)}
    complete = run.returncode == 0 and len(values) == (8 if a.park_mode == 'buffer' else 6) and 'timestep too small' not in log.lower()
    report = {'simulation_completed': complete, 'simulator_returncode': run.returncode,
              'settings': vars(a), 'measurements': values,
              'idle_subtracted_charge_c': [values[f'charge_{i}'] - values[f'idle_{i}'] * 4.25e-6
                                           for i in range(2)] if complete else None,
              'scope': 'Native extracted source, TG and inverter components; ideal fixed-voltage current-meter termination deliberately replaces integrator. Parking modes: vcm original, termination ideal diagnostic voltage matching receiving node, buffer actual native seven-MOS OTA unity follower with native7um MIM compensation and external1uA bias. Buffer assembly is schematic, not a qualified combined layout. Nominal TT, no mismatch or random noise. Gate programming stimuli inherited from prior seed29 bench are not calibrated to this hierarchy. This measures source/switch sensitivity to termination voltage only, not stored-state behavior, complete PLIF, accuracy, retention, throughput or combined layout.',
              'physical_solution_accepted': False, 'full_chip_accepted': False,
              'sha256': {f.relative_to(ROOT).as_posix(): sha(f) for f in sorted(files)}}
    rp = BASE / 'results' / (stem + '.json')
    rp.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(rp), 'complete': complete, 'measurements': values,
                      'charge_c': report['idle_subtracted_charge_c']}))
    if not complete:
        raise RuntimeError(log[-2500:])


if __name__ == '__main__':
    main()
