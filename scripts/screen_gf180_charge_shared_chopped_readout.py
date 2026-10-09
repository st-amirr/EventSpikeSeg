"""Bounded two-polarity sampling and physical charge-share cancellation diagnostic."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--signal-uv', type=float, default=0)
    parser.add_argument('--mismatch-seed', type=int)
    parser.add_argument('--cross-share', action='store_true')
    parser.add_argument('--gate-rezero', action='store_true')
    parser.add_argument('--storage-banks', type=int, choices=[1, 4], default=1)
    parser.add_argument('--max-step-ns', type=int, choices=[5, 10, 20], default=20)
    args = parser.parse_args()
    assert abs(args.signal_uv) <= 10000
    sources = set()
    text = []
    cells = ['gf180_pmos_follower_baseline_readout_fullroute_guarded', 'gf180_phase_inverter_fullroute']
    for cell in cells:
        directory = BASE / 'layout' / cell
        qualification = directory / 'qualification.json'
        report = json.loads(qualification.read_text(encoding='utf-8'))
        assert report['magic_drc_count'] == report['gds_roundtrip_drc_count'] == 0
        assert report['lvs_unique'] and report['gds_roundtrip_lvs_unique']
        sources.add(qualification)
        for key in ['sha256', 'input_sha256', 'gds_roundtrip_sha256']:
            for filename, expected in report.get(key, {}).items():
                path = directory / filename if key == 'sha256' else ROOT / filename
                assert digest(path) == expected, str(path)
                sources.add(path)
        # Preserve the parent-context substrate pins of the extracted children.
        text.append((directory / (cell + '_cap.spice')).read_text(encoding='utf-8'))
    settings = json.dumps(vars(args), sort_keys=True)
    stem = 'gf180_charge_shared_chopped_readout_' + hashlib.sha256(settings.encode()).hexdigest()[:10] + '_src' + digest(Path(__file__))[:12]
    snapshot = BASE / 'tools/source_snapshots' / (stem + '.py')
    snapshot.write_bytes(Path(__file__).read_bytes())
    sources.add(snapshot)
    models = BASE / 'pdk/gf180_primitive_source/models/ngspice'
    sources.update(models.rglob('*.spice'))
    prefix = '/workspace/' + models.relative_to(ROOT).as_posix()
    lines = ['Two-polarity readout sampled on actual MIM banks then physically charge shared',
             f'.include {prefix}/design.spice', f'.lib {prefix}/sm141064.spice typical',
             f'.lib {prefix}/sm141064.spice mimcap_typical',
             '.param sw_stat_global=0 sw_stat_mismatch=' + str(int(args.mismatch_seed is not None)),
             '.temp 27', '.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',
             *text, 'Vdd vdd 0 3.3', 'Vcm vcm 0 1.65', 'Iref pbias 0 10u',
             'Xref pbias pbias vdd vdd 0 gf180_read_pf10_l1',
             'Xfa 0 ga outa outa 0 gf180_read_pf80_l1',
             'Xfb 0 gb outb outb 0 gf180_read_pf80_l1',
             'Xsa outa pbias vdd vdd 0 gf180_read_pf10_l1',
             'Xsb outb pbias vdd vdd 0 gf180_read_pf10_l1',
             'Cload_a outa 0 500f', 'Cload_b outb 0 500f',
             f'Vprogram_w program_w 0 {1.65 - args.signal_uv * .5e-6:.12g}',
             f'Vprogram_r program_r 0 {1.65 + args.signal_uv * .5e-6:.12g}',
             'Xmemw statew vcm 0 gf180_mim_bank_7x7_n9',
             'Xmemr stater vcm 0 gf180_mim_bank_7x7_n9',
             'Xsamplea pa na 0 gf180_mim_bank_7x7_n9',
             'Xsampleb pb nb 0 gf180_mim_bank_7x7_n9']
    tg = 'gf180_fixed_body_tg_fullroute_half'
    for number in range(1, args.storage_banks):
        lines.extend([f'Xmemw_{number} statew vcm 0 gf180_mim_bank_7x7_n9',
                      f'Xmemr_{number} stater vcm 0 gf180_mim_bank_7x7_n9'])

    def switch(name, node_a, node_b, phase):
        lines.append(f'X{name} {node_a} {node_b} {phase} {phase}b 0 vdd {tg}')

    def pulse(phase, start, finish):
        if start == 0:
            waveform = f'0 3.3 {finish-.01:g}u 3.3 {finish:g}u 0 145u 0'
        else:
            waveform = f'0 0 {start-.01:g}u 0 {start:g}u 3.3 {finish-.01:g}u 3.3 {finish:g}u 0 145u 0'
        lines.append(f'V{phase} {phase}_command 0 PWL({waveform})')
        lines.extend([f'Xcb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',
                      f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])

    for phase, start, finish in [('init', 0, 110), ('a', 110.2, 120), ('b', 122, 132),
                                 ('samplea', 119, 120), ('sampleb', 131, 132), ('share', 134, 142)]:
        pulse(phase, start, finish)
    if args.gate_rezero:
        pulse('rezero', 120.2, 121.8)
        for node in ['ga', 'gb']:
            switch('rezero_' + node, node, 'vcm', 'rezero')
    switch('writer_w', 'program_w', 'statew', 'init')
    switch('writer_r', 'program_r', 'stater', 'init')
    for node in ['ga', 'gb', 'pa', 'na', 'pb', 'nb']:
        switch('init_' + node, node, 'vcm', 'init')
    switch('in_aw', 'statew', 'ga', 'a')
    switch('in_ar', 'stater', 'gb', 'a')
    switch('in_bw', 'stater', 'ga', 'b')
    switch('in_br', 'statew', 'gb', 'b')
    # The second sample reverses both input and output polarity.
    switch('sample_ap', 'outb', 'pa', 'samplea')
    switch('sample_an', 'outa', 'na', 'samplea')
    switch('sample_bp', 'outb' if args.cross_share else 'outa', 'pb', 'sampleb')
    switch('sample_bn', 'outa' if args.cross_share else 'outb', 'nb', 'sampleb')
    switch('share_p', 'pa', 'nb' if args.cross_share else 'pb', 'share')
    switch('share_n', 'na', 'pb' if args.cross_share else 'nb', 'share')
    lines.extend(['.control', 'set numdgt=15'])
    if args.mismatch_seed is not None:
        lines.extend([f'setseed {args.mismatch_seed}', 'reset'])
    lines.extend([f'tran {args.max_step_ns}n 145u 0 {args.max_step_ns}n uic',
                  'let statesignal=v(stater)-v(statew)', 'let directsignal=v(outb)-v(outa)',
                  'let sampleasignal=v(pa)-v(na)', 'let samplebsignal=v(pb)-v(nb)'])
    for name, vector, when in [('stored_before', 'statesignal', 109), ('stored_after_a', 'statesignal', 121),
                               ('stored_after_b', 'statesignal', 133), ('stored_final', 'statesignal', 140),
                               ('direct_a', 'directsignal', 119.5), ('direct_b', 'directsignal', 131.5),
                               ('sample_a', 'sampleasignal', 121), ('sample_b', 'samplebsignal', 133),
                               ('average_a', 'sampleasignal', 136), ('average_b', 'samplebsignal', 136),
                               ('average_late', 'sampleasignal', 140)]:
        lines.append(f'meas tran {name} find {vector} at={when}u')
    lines.extend(['quit', '.endc', '.end'])
    deck = BASE / 'benches' / (stem + '.spice')
    deck.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    sources.add(deck)
    run = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--memory', '2g', '--cpus', '2',
                          '--volume', f'{ROOT}:/workspace', '--workdir', '/workspace', '--entrypoint', 'timeout',
                          'eventspikeseg:analog-ngspice47', '120', 'ngspice', '-b',
                          '/workspace/' + deck.relative_to(ROOT).as_posix()], capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    log_path = BASE / 'results' / (stem + '.log')
    log_path.write_text(log, encoding='utf-8')
    sources.add(log_path)
    values = {name: float(value) for name, value in re.findall(
        r'(?m)^(stored_(?:before|after_a|after_b|final)|direct_[ab]|sample_[ab]|average_[ab]|average_late)\s*=\s*([-+0-9.eE]+)', log)}
    complete = run.returncode == 0 and len(values) == 11 and 'timestep too small' not in log.lower()
    report = {'simulation_completed': complete, 'simulator_returncode': run.returncode,
              'settings': vars(args), 'measurements': values,
              'scope': 'Native extracted source-body-tied PF80/PF10 pair with real input crossbar, actual inverter phases, actual MIM sample banks/output switches and physical same-polarity charge sharing. Stored differential input programmed through real TG then floats; no input/read-state forcing after release or arithmetic averaging/correction applied to circuit state. Bench interconnect is schematic, combined chopper macro layout unimplemented. Isolated native leaves extracted in parent context retain fifth substrate pin. Conditional deterministic offset/settling/loading/injection screen only; no transient sampled noise/PVT/gate leakage/RPEX/retention/model-accuracy/service. Ten microsecond polarity phases are diagnostic, not accepted timing.',
              'physical_charge_sharing_used': True, 'chopper_module_physically_assembled': False,
              'sampled_noise_qualified': False, 'original_float_accuracy_accepted': False,
              'complete_PLIF_accepted': False, 'full_5ms_population_service_accepted': False,
              'full_chip_accepted': False,
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(sources)}}
    path = BASE / 'results' / (stem + '.json')
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'completed': complete, 'measurements': values}), flush=True)
    if not complete:
        raise RuntimeError(log[-2500:])


if __name__ == '__main__':
    main()
