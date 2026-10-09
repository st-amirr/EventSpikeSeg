"""Native stationary capture-aperture noise; not transient switched-noise qualification."""
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
    original = BASE / 'results/gf180_charge_shared_chopped_readout_eb536f262c_src7084f104ffe2.json'
    report = json.loads(original.read_text(encoding='utf-8'))
    assert report['simulation_completed'] and report['settings']['mismatch_seed'] is None
    sources = {original}
    for filename, expected in report['sha256'].items():
        path = ROOT / filename
        assert digest(path) == expected, filename
        sources.add(path)
    bench = next(ROOT / p for p in report['sha256'] if p.endswith('.spice') and '/benches/' in p)
    lines = bench.read_text(encoding='utf-8').split('.control')[0].splitlines()
    for index, line in enumerate(lines):
        match = re.match(r'^V(init|a|b|samplea|sampleb|share) (\S+) 0 PWL\(', line)
        if match:
            value = 3.3 if match[1] in ['a', 'samplea'] else 0
            lines[index] = f'V{match[1]} {match[2]} 0 {value}'
    lines.extend(['Vinput statew 0 DC 1.65 AC 1', 'Vinputr stater 0 DC 1.65 AC 0'])
    stem = 'gf180_chopped_capture_noise_src' + digest(Path(__file__))[:12]
    snapshot = BASE / 'tools/source_snapshots' / (stem + '.py')
    snapshot.write_bytes(Path(__file__).read_bytes())
    sources.add(snapshot)
    capture_spectrum = BASE / 'results' / (stem + '_capture_spectrum.txt')
    direct_spectrum = BASE / 'results' / (stem + '_direct_spectrum.txt')
    lines.extend(['.control', 'set numdgt=15', 'op', 'print v(outa) v(pa)',
                  'noise v(pa,na) Vinput dec 100 1 1e8',
                  'print noise2.onoise_total noise2.inoise_total',
                  'setplot noise1', 'set wr_singlescale', 'set wr_vecnames',
                  'wrdata /workspace/' + capture_spectrum.relative_to(ROOT).as_posix() + ' onoise_spectrum',
                  'noise v(outb,outa) Vinput dec 100 1 1e8',
                  'print noise4.onoise_total noise4.inoise_total',
                  'setplot noise3', 'set wr_singlescale', 'set wr_vecnames',
                  'wrdata /workspace/' + direct_spectrum.relative_to(ROOT).as_posix() + ' onoise_spectrum',
                  'quit', '.endc', '.end'])
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
    values = {k: float(v) for k, v in re.findall(
        r'(?m)^(noise[24]\.(?:onoise_total|inoise_total)|v\(outa\)|v\(pa\))\s*=\s*([-+0-9.eE]+)', log)}
    complete = run.returncode == 0 and len(values) == 6 and capture_spectrum.exists() and direct_spectrum.exists()
    sources.update(p for p in [capture_spectrum, direct_spectrum] if p.exists())
    result = {'simulation_completed': complete, 'simulator_returncode': run.returncode,
              'measurements': values, 'capture_spectrum': capture_spectrum.relative_to(ROOT).as_posix(),
              'direct_spectrum': direct_spectrum.relative_to(ROOT).as_posix(),
              'scope': 'Stationary phase-A capture aperture using actual extracted TG/MIM/PF/inverter circuits, nominal27C, ideal-forced input state only for small-signal noise. PhaseA and sampleA stay on, other phases off. Native switch/channel/amp noise included; spectrum at differential capture capacitor before opening is not proof of final sampled covariance, chopping suppression, transient switching artifacts, hold retention or full-model error. Clock sources ideal but inverter circuits native. One-shot two-phase sampler is not a continuous chopper/filter. No noise or precision acceptance.',
              'sampled_noise_qualified': False, 'original_float_accuracy_accepted': False,
              'complete_PLIF_accepted': False, 'full_chip_accepted': False,
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(sources)}}
    path = BASE / 'results' / (stem + '.json')
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'completed': complete, 'measurements': values}), flush=True)
    if not complete:
        raise RuntimeError(log[-2000:])


if __name__ == '__main__':
    main()
