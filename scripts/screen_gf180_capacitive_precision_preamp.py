"""Bounded extracted-component capacitive preamplifier feasibility for the input stem."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gain', type=int, choices=[8, 32, 128], default=32)
    parser.add_argument('--parallel', type=int, choices=[1, 16, 64, 256], default=1)
    parser.add_argument('--mode', choices=['noise', 'transient'], default='noise')
    parser.add_argument('--mismatch-seed', type=int)
    args = parser.parse_args()
    assert args.mode != 'noise' or args.mismatch_seed is None
    sources = set()
    definitions = []
    for cell in ['gf180_shared_ota_core_pmos_input_fullroute',
                 'gf180_pmos_follower_baseline_readout_fullroute_guarded',
                 'gf180_phase_inverter_fullroute']:
        folder = BASE / 'layout' / cell
        qp = folder / 'qualification.json'
        q = json.loads(qp.read_text(encoding='utf-8'))
        assert q['magic_drc_count'] == q['gds_roundtrip_drc_count'] == 0
        assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
        sources.add(qp)
        for key in ['sha256', 'input_sha256', 'gds_roundtrip_sha256']:
            for name, expected in q.get(key, {}).items():
                path = folder / name if key == 'sha256' else ROOT / name
                assert digest(path) == expected, str(path)
                sources.add(path)
        definitions.append((folder / (cell + '_cap.spice')).read_text(encoding='utf-8'))
    stem = 'gf180_capacitive_precision_preamp_' + hashlib.sha256(json.dumps(vars(args), sort_keys=True).encode()).hexdigest()[:10] + '_src' + digest(Path(__file__))[:12]
    snapshot = BASE / 'tools/source_snapshots' / (stem + '.py')
    snapshot.write_bytes(Path(__file__).read_bytes())
    sources.add(snapshot)
    models = BASE / 'pdk/gf180_primitive_source/models/ngspice'
    sources.update(models.rglob('*.spice'))
    prefix = '/workspace/' + models.relative_to(ROOT).as_posix()
    lines = ['Capacitive preamplifier native noise and settling diagnostic',
             f'.include {prefix}/design.spice', f'.lib {prefix}/sm141064.spice typical',
             f'.lib {prefix}/sm141064.spice mimcap_typical',
             '.param sw_stat_global=0 sw_stat_mismatch=' + str(int(args.mismatch_seed is not None)),
             '.temp 27', '.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',
             *definitions, 'Vdd vdd 0 3.3', 'Vcm vcm 0 1.65',
             'Ireference bias 0 1u', 'Xreference bias bias vdd vdd 0 gf180_read_pf10_l1']
    if args.mode == 'noise':
        lines.extend(['Vinput input_w 0 DC 1.65 AC 1', 'Vinputr input_r 0 DC 1.65 AC 0',
                      'Vresetcommand reset_command 0 0'])
    else:
        lines.extend(['Vinput input_w 0 PWL(0 1.65 101.99u 1.65 102u 1.65001 109.99u 1.65001 110u 1.65 113.99u 1.65 114u 1.64999 121.99u 1.64999 122u 1.65 130u 1.65)',
                      'Vinputr input_r 0 1.65',
                      'Vresetcommand reset_command 0 PWL(0 3.3 99.99u 3.3 100u 0 130u 0)'])
    lines.extend(['Xresetb reset_command resetb vdd 0 gf180_phase_inverter_fullroute',
                  'Xreset resetb reset vdd 0 gf180_phase_inverter_fullroute'])
    for tag in ['w', 'r']:
        for index in range(args.parallel):
            lines.append(f'Xamp_{tag}_{index} vcm sum_{tag} out_{tag} vdd 0 bias cmp_{tag} gf180_shared_ota_core_pmos_input_fullroute')
        for index in range(args.gain):
            lines.append(f'Xinput_{tag}_{index} input_{tag} sum_{tag} 0 gf180_mim_bank_7x7_n9')
        lines.extend([f'Xfeedback_{tag} out_{tag} sum_{tag} 0 gf180_mim_bank_7x7_n9',
                      f'Xcomp_{tag} out_{tag} cmp_{tag} 0 gf180_mim_bank_7x7_n9',
                      f'Xclamp_{tag} out_{tag} sum_{tag} reset resetb 0 vdd gf180_fixed_body_tg_fullroute_half',
                      f'Cload_{tag} out_{tag} 0 500f'])
    lines.extend(['.nodeset v(sum_w)=1.65 v(sum_r)=1.65 v(out_w)=1.65 v(out_r)=1.65',
                  '.control', 'set numdgt=15'])
    spectrum = BASE / 'results' / (stem + '_spectrum.txt')
    transfer = BASE / 'results' / (stem + '_ac.txt')
    if args.mode == 'noise':
        lines.extend(['op', 'print v(out_w) v(out_r) v(sum_w) i(Vdd)',
                      'noise v(out_r,out_w) Vinput dec 100 1 1e8',
                      'print noise2.onoise_total noise2.inoise_total',
                      'setplot noise1', 'set wr_singlescale', 'set wr_vecnames',
                      'wrdata /workspace/' + spectrum.relative_to(ROOT).as_posix() + ' onoise_spectrum',
                      'ac dec 100 1 1e8', 'let h=v(out_r)-v(out_w)',
                      'wrdata /workspace/' + transfer.relative_to(ROOT).as_posix() + ' real(h) imag(h)'])
    else:
        if args.mismatch_seed is not None:
            lines.extend([f'setseed {args.mismatch_seed}', 'reset'])
        lines.extend(['tran 10n 130u 0 10n uic', 'let signal=v(out_r)-v(out_w)'])
        for name, when in [('baseline', 101.5), ('positive', 106), ('positive_late', 109),
                           ('return_zero', 112), ('negative', 118), ('negative_late', 121), ('final', 126)]:
            lines.append(f'meas tran {name} find signal at={when}u')
    lines.extend(['quit', '.endc', '.end'])
    deck = BASE / 'benches' / (stem + '.spice')
    deck.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    sources.add(deck)
    run = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--memory', '2g', '--cpus', '2',
                          '--volume', f'{ROOT}:/workspace', '--workdir', '/workspace', '--entrypoint', 'timeout',
                          'eventspikeseg:analog-ngspice47', '120', 'ngspice', '-b',
                          '/workspace/' + deck.relative_to(ROOT).as_posix()], capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    lp = BASE / 'results' / (stem + '.log')
    lp.write_text(log, encoding='utf-8')
    sources.add(lp)
    values = {key: float(value) for key, value in re.findall(
        r'(?m)^(noise2\.(?:onoise_total|inoise_total)|v\(out_[wr]\)|v\(sum_w\)|i\(vdd\)|baseline|positive|positive_late|return_zero|negative|negative_late|final)\s*=\s*([-+0-9.eE]+)', log)}
    complete = run.returncode == 0 and len(values) == (6 if args.mode == 'noise' else 7)
    complete = complete and 'timestep too small' not in log.lower()
    if args.mode == 'noise':
        complete = complete and spectrum.exists() and transfer.exists()
        sources.update(path for path in [spectrum, transfer] if path.exists())
    report = {'simulation_completed': complete, 'simulator_returncode': run.returncode, 'settings': vars(args),
              'measurements': values, 'spectrum': spectrum.relative_to(ROOT).as_posix() if spectrum.exists() else None,
              'ac_transfer': transfer.relative_to(ROOT).as_posix() if transfer.exists() else None,
              'scope': 'Extracted native7MOS OTA cores in parallel with actual shared bias, native MIM input/feedback/compensation banks and off-reset TG, actual inverter clocks. Closed-loop capacitance ratio8/32/128. No ideal resistive DC feedback or output buffer. Noise operating point relies on native off-switch path; check DC/gain/headroom before interpreting spectrum. Stationary noise excludes reset-sampled kTC/covariance/storage/source/clock transient noise. AC integration is not a sampled error assignment. Transient inputs ideal-driven low-impedance bench sources, not a floating resident membrane; loading upstream integrator and upstream noise unqualified. Parallel cores/internalCMP share wiring schematic; combined macro layout and PVT/RPEX/leakage/5ms service unqualified.',
              'reset_sampled_noise_qualified': False, 'new_combined_layout_qualified': False,
              'original_float_accuracy_accepted': False, 'complete_PLIF_accepted': False,
              'full_chip_accepted': False,
              'sha256': {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(sources)}}
    path = BASE / 'results' / (stem + '.json')
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'completed': complete, 'measurements': values}), flush=True)
    if not complete:
        raise RuntimeError(log[-2500:])


if __name__ == '__main__':
    main()
