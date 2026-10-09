"""Bounded GF180 extracted gate-cap hold/event screen with fixed-body access."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
PDK = BASE / 'pdk/gf180_primitive_source'
LAYOUT = BASE / 'layout/gf180_mos_gate_cap_10x1'
REV = 'e11a8c98dfc905561d38813b1416e65a4b9280e9'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offset-mv', type=float, default=750)
    parser.add_argument('--corner', choices=['ff', 'ss', 'typical'], default='ff')
    parser.add_argument('--temp-c', type=float, default=85)
    parser.add_argument('--physical-access', action='store_true')
    parser.add_argument('--combined-cell', action='store_true')
    parser.add_argument('--event-time', action='store_true')
    parser.add_argument('--max-step-ns', type=float, default=500)
    args = parser.parse_args()
    if not 0 < args.offset_mv <= 750:
        raise ValueError('offset outside the bounded 0.9..2.4V state window')
    if not 20 <= args.max_step_ns <= 500:
        raise ValueError('bounded transient maximum step must be20..500ns')
    revision = subprocess.check_output(['git', '-C', str(PDK), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != REV:
        raise RuntimeError('GF180 primitive revision changed')
    extracted = (LAYOUT / 'gatecap_capacitance.spice').read_text()
    devices = re.findall(r'(?m)^X[^\r\n]+', extracted)
    caps = re.findall(r'(?m)^C[^\r\n]+', extracted)
    if len(devices) != 1 or len(caps) != 1 or devices[0].split()[1:6] != ['VSS', 'GATE', 'VSS', 'VSS', 'nfet_03v3']:
        raise RuntimeError('unexpected physical capacitor extraction')
    stem = f'gf180_extracted_gatecap_schematic_access_{args.corner}_temp{args.temp_c:g}_offset{args.offset_mv:g}mv'
    access_path = BASE/'layout/gf180_fixed_body_tg/gf180_fixed_body_tg_cap.spice'
    if args.physical_access:
        stem = stem.replace('schematic_access', 'extracted_access')
    combined_path = BASE/'layout/gf180_gate_state_cell/gf180_gate_state_cell_cap.spice'
    if args.combined_cell:
        stem = f'gf180_combined_gate_state_{args.corner}_temp{args.temp_c:g}_offset{args.offset_mv:g}mv'
    if args.event_time:
        stem += f'_equalevents_step{args.max_step_ns:g}ns'
    kinds = ['access_control', 'access_early', 'access_late', 'bare_control', 'bare_early', 'bare_late'] if args.event_time else ['access', 'bare']
    deck = BASE / f'benches/{stem}.spice'
    result = BASE / f'results/{stem}.json'
    deck.parent.mkdir(parents=True, exist_ok=True)
    result.parent.mkdir(parents=True, exist_ok=True)
    prefix = '/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice'
    lines = ['GF180 physical gate cap with schematic access, native 3.3V window',
             f'.include {prefix}/design.spice', '.param sw_stat_global=0 sw_stat_mismatch=0',
             f'.lib {prefix}/sm141064.spice {args.corner}',
             '.options gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-11',
             f'.temp {args.temp_c:g}', '.subckt physical_cap GATE VSS', *devices, *caps, '.ends',
             'Vbus bus 0 1.65', 'Vdd vdd 0 3.3', 'Ven en 0 0', 'Venb enb 0 3.3',
             'Vinit init_en 0 PWL(0 3.3 0.9u 3.3 1u 0 5.01m 0)',
             '.model ideal_init SW(Ron=10 Roff=1e30 Vt=1.65 Vh=0.1)']
    if args.physical_access:
        lines += access_path.read_text().splitlines()
    if args.combined_cell:
        lines += combined_path.read_text().splitlines()
    for kind in kinds:
        for side, sign in [('low', -1), ('high', 1)]:
            node = f'{kind}_{side}'
            lines += [f'Vset_{node} init_{node} 0 {1.65 + sign * args.offset_mv / 1000:.12g}',
                      f'Sinit_{node} init_{node} {node} init_en 0 ideal_init',
                      ]
            if args.combined_cell and kind.startswith('access'):
                lines.append(f'Xcell_{node} bus {node} en enb 0 vdd gf180_gate_state_cell')
            else:
                lines.append(f'Xcap_{node} {node} 0 physical_cap')
            if kind.startswith('access'):
                if args.combined_cell:
                    pass
                elif args.physical_access:
                    lines.append(f'Xaccess_{node} bus {node} en enb 0 vdd gf180_fixed_body_tg')
                else:
                    lines += [f'Xn_{node} bus en {node} 0 nfet_03v3 w=1u l=0.28u as=0.5p ad=0.5p ps=3u pd=3u',
                          f'Xp_{node} bus enb {node} vdd pfet_03v3 w=2u l=0.28u as=1p ad=1p ps=5u pd=5u']
            if args.event_time and not kind.endswith('control'):
                t = 500 if kind.endswith('early') else 4500
                current = -sign*2e-9
                lines.append(f'Ievent_{node} {node} 0 PWL(0 0 {t:.12g}u 0 {t+0.001:.12g}u {current:.12g} {t+0.051:.12g}u {current:.12g} {t+0.052:.12g}u 0 5.01m 0)')
    lines += ['.control', 'set numdgt=15', f'tran {args.max_step_ns:g}n 5m']
    for kind in kinds:
        for side in ['low', 'high']:
            for point, time in [('start', '2u'), ('end', '5m')]:
                lines.append(f'meas tran {kind}_{side}_{point} find v({kind}_{side}) at={time}')
    lines += ['quit', '.endc', '.end']
    deck.write_text('\n'.join(lines) + '\n', encoding='ascii')
    command = ['docker', 'run', '--rm', '--network', 'none', '--memory', '4g', '--cpus', '2',
               '--env', 'NGSPICE_MEAS_PRECISION=15', '--volume', f'{ROOT}:/workspace', '--workdir', prefix,
               '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice47', '120', 'ngspice', '-b',
               f'/workspace/{deck.relative_to(ROOT).as_posix()}']
    proc = subprocess.run(command, capture_output=True, text=True, timeout=135)
    log = proc.stdout + proc.stderr
    logpath = result.with_suffix('.log'); logpath.write_text(log)
    values = {key: float(value) for key, value in re.findall(r'(?m)^\s*((?:access|bare)(?:_(?:control|early|late))?_(?:low|high)_(?:start|end))\s*=\s*([-+0-9.eE]+)', log)}
    completed = proc.returncode == 0 and 'ngspice-47 done' in log and len(values) == 4*len(kinds)
    rows = {}
    if completed:
        for kind in kinds:
            start = values[f'{kind}_high_start'] - values[f'{kind}_low_start']
            end = values[f'{kind}_high_end'] - values[f'{kind}_low_end']
            rows[kind] = {'start_differential_mv': start*1000, 'end_differential_mv': end*1000,
                          'retained_fraction': end/start,
                          'max_initialization_error_v': max(abs(values[f'{kind}_{side}_start'] - (1.65 + sign*args.offset_mv/1000)) for side, sign in [('low', -1), ('high', 1)])}
        if args.event_time:
            for group in ['access', 'bare']:
                early = rows[f'{group}_early']['end_differential_mv']-rows[f'{group}_control']['end_differential_mv']
                late = rows[f'{group}_late']['end_differential_mv']-rows[f'{group}_control']['end_differential_mv']
                rows[f'{group}_event_time'] = {'early_increment_mv':early, 'late_increment_mv':late, 'early_to_late_ratio':early/late}
    sources = [Path(__file__), deck, logpath, LAYOUT/'gatecap_capacitance.spice', PDK/'models/ngspice/sm141064.spice', PDK/'models/ngspice/design.spice']
    if args.physical_access:
        sources.append(access_path)
    if args.combined_cell:
        sources.append(combined_path)
    report = {'simulation_completed': completed, 'model_revision': revision, 'corner': args.corner,
              'temperature_c': args.temp_c, 'offset_mv': args.offset_mv, 'gmin_s': 1e-18,
              'storage': 'Magic-extracted10/1um gate capacitor; combined routing parasitics' if args.combined_cell else 'Magic-extracted10/1um gate capacitor including1.08681fF routing capacitance',
              'physical_access':args.physical_access or args.combined_cell, 'combined_routed_cell':args.combined_cell, 'equal_charge_event_time':args.event_time,
              'maximum_timestep_ns':args.max_step_ns,
              'gate_leakage_coverage':'Official3.3V MOS model cards set igbmod=0 and igcmod=0; silicon gate leakage is unqualified, untouched cards used.',
              'ideal_event_charge_c_per_rail':1.02e-16 if args.event_time else None,
              'physical_state_accepted': False, 'rows': rows,
              'limitations': 'Storage/access are capacitance-extracted as identified above, optionally combined into one routed cell. Initialization/control and event sources are ideal. No qualified gate leakage, resistance extraction, switched noise, mismatch, actual signed injector, read/write, full-float accuracy or population service qualification.',
              'source_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    result.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if not completed:
        raise RuntimeError(log[-2000:])


if __name__ == '__main__':
    main()
