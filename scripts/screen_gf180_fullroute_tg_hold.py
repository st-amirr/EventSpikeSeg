"""Extracted corrected TG sampling/hold diagnostic; no full-PLIF acceptance."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-step-ns', type=int, choices=[10, 100], default=100)
    parser.add_argument('--dummy-count', type=int, choices=[0, 1, 2], default=0)
    parser.add_argument('--dummy-size', choices=['full', 'half'], default='half')
    parser.add_argument('--bottom-plate', action='store_true')
    parser.add_argument('--bottom-dummy', action='store_true')
    parser.add_argument('--combined-macro', action='store_true')
    parser.add_argument('--macro-cell', choices=['gf180_compensated_bottom_sampler','gf180_compensated_bottom_sampler_shielded'], default='gf180_compensated_bottom_sampler')
    args = parser.parse_args()
    if args.bottom_dummy and (not args.bottom_plate or not args.dummy_count):
        raise ValueError('Bottom dummy requires bottom-plate mode and explicit dummy count')
    if args.combined_macro and (not args.bottom_plate or not args.bottom_dummy or args.dummy_count != 1 or args.dummy_size != 'half'):
        raise ValueError('Combined macro implements both-terminal half-dummy bottom-plate sampling')
    sources = {Path(__file__)}
    tg = BASE / 'layout/gf180_fixed_body_tg_fullroute'
    qpath = tg / 'qualification.json'
    q = json.loads(qpath.read_text())
    if q['magic_drc_count'] or q['gds_roundtrip_drc_count'] or not q['gds_roundtrip_lvs_unique']:
        raise ValueError('Corrected TG GDS unqualified')
    sources.add(qpath)
    for name, expected in q['sha256'].items():
        p = tg / name
        if digest(p) != expected:
            raise ValueError('TG source/geometry changed')
        sources.add(p)
    for name, expected in q['gds_roundtrip_sha256'].items():
        p = ROOT / name
        if digest(p) != expected:
            raise ValueError('GDS roundtrip evidence changed')
        sources.add(p)
    dummy_cell = 'gf180_fixed_body_tg_fullroute'+('_half' if args.dummy_size == 'half' else '')
    dummy_text = []
    if args.dummy_count and args.dummy_size == 'half':
        dummy_dir = BASE / 'layout' / dummy_cell
        dummy_qpath = dummy_dir / 'qualification.json'
        dummy_q = json.loads(dummy_qpath.read_text())
        if dummy_q['magic_drc_count'] or dummy_q['gds_roundtrip_drc_count'] or not dummy_q['gds_roundtrip_lvs_unique'] or dummy_q['nf_width_um'] != .5 or dummy_q['pf_width_um'] != 1:
            raise ValueError('Half-size dummy primitive unqualified')
        sources.add(dummy_qpath)
        for name, expected in dummy_q['sha256'].items():
            p = dummy_dir / name
            if digest(p) != expected:
                raise ValueError('Half-size dummy geometry changed')
            sources.add(p)
        for name, expected in dummy_q['gds_roundtrip_sha256'].items():
            p = ROOT / name
            if digest(p) != expected:
                raise ValueError('Dummy GDS roundtrip evidence changed')
            sources.add(p)
        dummy_text = (dummy_dir/(dummy_cell+'_cap.spice')).read_text().splitlines()
    capdir = BASE / 'layout/gf180_mim_7x7'
    cp = capdir / 'qualification.json'
    capq = json.loads(cp.read_text())
    sources.add(cp)
    for name, expected in capq['sha256'].items():
        p = capdir / name
        if digest(p) != expected:
            raise ValueError('MIM geometry changed')
        sources.add(p)
    models = BASE / 'pdk/gf180_primitive_source/models/ngspice'
    macro_text = None
    if args.combined_macro:
        macro_dir = BASE / 'layout' / args.macro_cell
        mqp = macro_dir / 'qualification.json'
        mq = json.loads(mqp.read_text())
        if mq['magic_drc_count'] or mq['gds_roundtrip_drc_count'] or not mq['gds_roundtrip_lvs_unique'] or mq['mos_count'] != 8 or mq['native_mim_count'] != 1:
            raise ValueError('Combined macro physical checks incomplete')
        sources.add(mqp)
        for name, expected in mq['sha256'].items():
            p = macro_dir / name
            if digest(p) != expected:
                raise ValueError('Combined macro changed')
            sources.add(p)
        for key in ['input_sha256', 'gds_roundtrip_sha256']:
            for name, expected in mq[key].items():
                p = ROOT / name
                if digest(p) != expected:
                    raise ValueError('Combined macro input/readback changed')
                sources.add(p)
        macro_text = (macro_dir/(args.macro_cell+'_cap.spice')).read_text().splitlines()
    sources.update(models.rglob('*.spice'))
    prefix = '/workspace/'+models.relative_to(ROOT).as_posix()
    source_sha = digest(Path(__file__))
    stem = f'gf180_fullroute_tg_hold_step{args.max_step_ns}_dummy{args.dummy_count}{args.dummy_size}_bottom{int(args.bottom_plate)}_bdummy{int(args.bottom_dummy)}_macro{int(args.combined_macro)}_shield{int(args.macro_cell.endswith("_shielded"))}_src{source_sha[:12]}'
    snapshot = BASE / 'tools/source_snapshots' / f'{stem}.py'
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        snapshot.write_bytes(Path(__file__).read_bytes())
    sources.remove(Path(__file__))
    sources.add(snapshot)
    lines = ['Corrected GF180 extracted TG into audited native MIM',
             f'.include {prefix}/design.spice', '.param sw_stat_global=0 sw_stat_mismatch=0',
             f'.lib {prefix}/sm141064.spice typical', f'.lib {prefix}/sm141064.spice mimcap_typical',
             '.temp 27', '.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',
             *(macro_text if macro_text is not None else [*(tg/'gf180_fixed_body_tg_fullroute_cap.spice').read_text().splitlines(),*dummy_text,*(capdir/'gf180_mim_7x7_cap.spice').read_text().splitlines()]),
             'Vdd vdd 0 3.3',
             'Ven en 0 PWL(0 0 10n 0 20n 3.3 990n 3.3 1u 0 5.001m 0)',
             'Venb enb 0 PWL(0 3.3 10n 3.3 20n 0 990n 0 1u 3.3 5.001m 3.3)']
    if args.bottom_plate:
        lines += ['Vcm vcm 0 PWL(0 0 30n 0 60n 1.65 5.002m 1.65)',
                  'Vbottom bottom_en 0 PWL(0 0 10n 0 20n 3.3 970n 3.3 980n 0 5.002m 0)',
                  'Vbottomb bottom_enb 0 PWL(0 3.3 10n 3.3 20n 0 970n 0 980n 3.3 5.002m 3.3)']
    targets = {'low': .3, 'mid': 1.65, 'high': 3.0}
    for name, voltage in targets.items():
        if args.combined_macro:
            lines += [f'Vin_{name} input_{name} 0 PWL(0 0 30n 0 60n {voltage} 5.002m {voltage})',
                      f'Xmacro_{name} hold_{name} bottom_{name} input_{name} vcm en enb bottom_en bottom_enb 0 vdd {args.macro_cell}',
                      f'.ic v(hold_{name})=0 v(bottom_{name})=0']
            continue
        lines += [f'Vin_{name} input_{name} 0 PWL(0 0 30n 0 60n {voltage} 5.002m {voltage})',
                  f'Xtg_{name} input_{name} hold_{name} en enb 0 vdd gf180_fixed_body_tg_fullroute',
                  f'Xcap_{name} hold_{name} '+(f'bottom_{name}' if args.bottom_plate else '0')+' 0 gf180_mim_7x7', f'.ic v(hold_{name})=0']
        if args.bottom_plate:
            lines += [f'Xbottom_{name} vcm bottom_{name} bottom_en bottom_enb 0 vdd gf180_fixed_body_tg_fullroute', f'.ic v(bottom_{name})=0']
        for i in range(args.dummy_count):
            lines.append(f'Xdummy_{name}_{i} hold_{name} hold_{name} enb en 0 vdd {dummy_cell}')
            if args.bottom_dummy:
                lines.append(f'Xbottomdummy_{name}_{i} bottom_{name} bottom_{name} bottom_enb bottom_en 0 vdd {dummy_cell}')
    lines += ['.control', 'set numdgt=12', f'tran {args.max_step_ns}n 5.002m 0 {args.max_step_ns}n uic']
    for name in targets:
        signal = f'v(hold_{name})-v(bottom_{name})' if args.bottom_plate else f'v(hold_{name})'
        lines.append(f'let signal_{name} = {signal}')
        for label, time in [('acquired', '100n'), ('on', '960n'), ('released', '1.1u'), ('held', '5.001m')]:
            lines.append(f'meas tran {name}_{label} find signal_{name} at={time}')
    lines.append('print '+' '.join(name+'_'+label for name in targets for label in ['acquired', 'on', 'released', 'held']))
    lines += ['quit', '.endc', '.end']
    deck = BASE / 'benches' / f'{stem}.spice'
    deck.write_text('\n'.join(lines)+'\n')
    sources.add(deck)
    command = ['docker', 'run', '--rm', '--network', 'none', '--memory', '2g', '--cpus', '2',
               '--volume', f'{ROOT}:/workspace', '--workdir', '/workspace', '--entrypoint', 'timeout',
               'eventspikeseg:analog-ngspice47', '120', 'ngspice', '-b', '/workspace/'+deck.relative_to(ROOT).as_posix()]
    result = subprocess.run(command, capture_output=True, text=True, timeout=135)
    log = result.stdout+result.stderr
    logpath = BASE / 'results' / f'{stem}.log'
    logpath.write_text(log)
    sources.add(logpath)
    values = {k: float(v) for k, v in re.findall(r'(?m)^((?:low|mid|high)_(?:acquired|on|released|held))\s*=\s*([-+0-9.eE]+)', log)}
    completed = result.returncode == 0 and len(values) == 12 and 'timestep too small' not in log.lower()
    cases = []
    if completed:
        for name, target in targets.items():
            desired = target-1.65 if args.bottom_plate else target
            cases.append({'target_v': target, 'desired_capacitor_voltage_v': desired, 'voltage_measurements': {k: values[name+'_'+k] for k in ['acquired', 'on', 'released', 'held']},
                          'acquisition_error_uv_at_100ns': (values[name+'_acquired']-desired)*1e6,
                          'release_step_uv': (values[name+'_released']-values[name+'_on'])*1e6,
                          'post_release_hold_drift_uv': (values[name+'_held']-values[name+'_released'])*1e6})
    report = {'simulation_completed': completed, 'returncode': result.returncode,
              'settings': vars(args), 'cases': cases, 'source_snapshot': snapshot.relative_to(ROOT).as_posix(),
              'signal_is_differential_capacitor_voltage': args.bottom_plate,
              'physical_storage_accepted': False, 'full_chip_accepted': False,
              'scope': 'Nominal deterministic sampling through corrected exported-GDS-connected TG into one 7um native MIM. Optional opposite-clock dummy TG has both analog terminals connected to the held node; individual primitive GDS connectivity is qualified, combined dummy wiring/layout is not yet implemented. Ideal input/clock sources; actual extracted capacitances and official unchanged MOS/MIM cards. No clock driver, interconnect resistance, sampled noise, mismatch, gate-leakage qualification, nonlinear encoding, PLIF semantics or population service acceptance. Endpoint hold includes circuit leakage allowed by these model cards only.',
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(sources)}}
    if args.bottom_plate:
        report['scope'] += ' Bottom plate samples1.65V through another corrected TG, opens20ns before the input TG. Output is floating differential capacitor voltage, not a ground-referenced membrane; differential read/restore and combined physical routing remain unimplemented.'
    if args.combined_macro:
        report['scope'] = 'Nominal deterministic combined physically routed/GDS-readback-qualified sampler with all newly extracted hierarchy and routing capacitances. Hierarchical TG junctions preserved; one native7um MIM is flattened for correctly exported terminal routing. Ideal external input/reference/clocks and unchanged model cards. Floating differential capacitor output requires actual read/restore circuitry. No RPEX, sampled noise, mismatch/PVT, qualified gate leakage, nonlinear encoding, complete PLIF, full-model accuracy or 5ms population-service acceptance.'
    target = BASE / 'results' / f'{stem}.json'
    target.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'report': str(target), 'simulation_completed': completed, 'cases': cases}, indent=2))
    if not completed:
        raise RuntimeError(log[-2000:])


if __name__ == '__main__':
    main()
