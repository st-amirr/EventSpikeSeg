"""Source-hashed continuous-bank evidence; never infer physical/model acceptance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical_deck(report):
    paths = [ROOT / name for name in report['sha256']
             if name.startswith('artifacts/analog_asic/benches/') and name.endswith('.spice')]
    if len(paths) != 1:
        raise ValueError('Exactly one transient deck required')
    # Measurement commands are post-transient diagnostics; only integration step differs.
    lines = [line for line in paths[0].read_text().splitlines()
             if not line.startswith(('meas tran ', 'tran '))]
    return hashlib.sha256('\n'.join(lines).encode()).hexdigest()


def main():
    sources = [Path(__file__)]
    cases = []
    reports = []
    for path in sorted((BASE / 'results').glob('gf180_sensor_zero_servo_*sampledrestore*.json')):
        report = json.loads(path.read_text())
        if not report.get('offset_continuous_clamp_startup_only'):
            continue
        sources.append(path)
        snapshot = ROOT / report['source_snapshot']
        expected = report['sha256']['scripts/screen_gf180_sensor_zero_servo.py']
        if digest(snapshot) != expected:
            raise ValueError(f'Source snapshot mismatch: {path}')
        sources.append(snapshot)
        for name, expected_sha in report['sha256'].items():
            if name == 'scripts/screen_gf180_sensor_zero_servo.py':
                continue  # Historical source is checked against its immutable snapshot.
            source = ROOT / name
            if digest(source) != expected_sha:
                raise ValueError(f'Input provenance mismatch: {source}')
            sources.append(source)
        rows = report.get('rows', [])
        case = {key: report.get(key) for key in [
            'simulation_completed','simulator_returncode','simulation_timeout_s', 'corner', 'temperature_c', 'seed',
            'local_mismatch_enabled', 'max_step_ns', 'diagnostic_ideal_charge_fc','sample_switch_nf_width_um','physical_acquisition_buffer']}
        case['sample_switch_nf_width_um']=report.get('sample_switch_nf_width_um',1)
        case['physical_acquisition_buffer']=report.get('physical_acquisition_buffer',False)
        case['source'] = path.relative_to(ROOT).as_posix()
        case['physical_deck_without_measurements_or_tran_sha256'] = physical_deck(report)
        mean = report.get('statistics', {}).get('program_mean_v')
        if mean is not None:
            case['initial_program_minus_command_mv'] = (mean-report['setpoint_v'])*1000
            case['coarse_initialization_within_5mv'] = abs(case['initial_program_minus_command_mv']) <= 5
        if report['simulation_completed'] and rows:
            zero = rows[0]
            case['next_read_error_uv'] = [row['next_read_error_mv']*1000 for row in rows]
            case['zero_relative_signal_gain'] = [
                (row['followread']-zero['followread'])/(row['beforecapture']-zero['beforecapture'])
                for row in rows[1:]]
            case['vdd_service_energy_pj'] = report['statistics'].get('energyserviceperiod_mean_pj')
            case['sampling_phase_diagnostics_uv'] = [row.get('sampling_phase_diagnostics_uv') for row in rows]
            if all(row.get('sampling_phase_diagnostics_uv') for row in rows):
                control = zero['sampling_phase_diagnostics_uv']
                case['signal_minus_zero_sampling_uv'] = [
                    {key:row['sampling_phase_diagnostics_uv'][key]-control[key] for key in control}
                    for row in rows[1:]]
        reports.append((path, report, case))
        cases.append(case)
    def normalized_settings(report):
        settings=dict(report['command_arguments'])
        settings.setdefault('sample_switch_nwidth_um',1)
        settings.setdefault('physical_acquisition_buffer',False)
        settings.pop('simulation_timeout_s',None)
        settings.pop('max_step_ns',None)
        return settings
    numerical = []
    for path, report, case in reports:
        if report.get('max_step_ns') != 50 or not report['simulation_completed']:
            continue
        settings = normalized_settings(report)
        matches = [(p,r,c) for p,r,c in reports if r.get('max_step_ns') == 100
                   and r['simulation_completed']
                   and normalized_settings(r) == settings]
        if not matches:
            continue
        prior_path, prior, prior_case = max(matches, key=lambda item:item[0].stat().st_mtime)
        same_deck = (case['physical_deck_without_measurements_or_tran_sha256'] ==
                     prior_case['physical_deck_without_measurements_or_tran_sha256'])
        if not same_deck:
            raise ValueError('Numerical comparison changes physical deck')
        differences = [new-old for new,old in zip(case['next_read_error_uv'],prior_case['next_read_error_uv'])]
        numerical.append({'step50_source':case['source'], 'step100_source':prior_case['source'],
                          'same_physical_deck':True, 'next_read_error_step50_minus100_uv':differences,
                          'maximum_absolute_difference_uv':max(abs(value) for value in differences),
                          'scope':'Sensitivity observation, not convergence proof or model-derived tolerance.'})
    retries=[]
    for path,report,case in reports:
        if not report['simulation_completed'] or report.get('simulation_timeout_s')!=240:
            continue
        prior=[(p,r,c) for p,r,c in reports if not r['simulation_completed'] and normalized_settings(r)==normalized_settings(report)]
        for old_path,old,old_case in prior:
            retries.append({'incomplete_source':old_case['source'],'completed_source':case['source'],
                            'same_physical_deck':case['physical_deck_without_measurements_or_tran_sha256']==old_case['physical_deck_without_measurements_or_tran_sha256'],
                            'completed_simulator_returncode':report.get('simulator_returncode'),
                            'historical_simulator_returncode':old.get('simulator_returncode')})
    noise = []
    for path in sorted((BASE/'results').glob('gf180_restore_phase_noise_*continuousstartupclamp*.json')):
        report = json.loads(path.read_text());sources.append(path)
        noise.append({key:report.get(key) for key in ['simulation_completed', 'transient_source',
                     'physical_acquisition_buffer','diagnostic_ideal_charge_fc','sample_switch_nf_width_um','values', 'dc_minus_transient_mv', 'bias_matches_transient_within_100uv',
                     'integration_band_hz', 'scope']})
        for name, expected_sha in report['sha256'].items():
            if name == 'scripts/characterize_gf180_restore_phase_noise.py':
                name = report['source_snapshot']
            source = ROOT/name
            if digest(source) != expected_sha:
                raise ValueError(f'Noise provenance mismatch: {source}')
            sources.append(source)
    sample_layouts=[]
    for cell in ['gf180_fixed_body_tg','gf180_fixed_body_tg_nf0p5']:
        path=BASE/'layout'/cell/'qualification.json'
        if not path.exists():
            continue
        layout=json.loads(path.read_text());sources.append(path)
        for name,expected_sha in layout['sha256'].items():
            source=path.parent/name
            if digest(source)!=expected_sha:
                raise ValueError(f'Sampling layout provenance mismatch: {source}')
            sources.append(source)
        sample_layouts.append(layout)
    result = {'physical_state_accepted':False, 'original_float_accuracy_accepted':False,
              'full_chip_accepted':False, 'sampling_switch_layouts':sample_layouts,'cases':cases, 'numerical_comparisons':numerical,
              'matched_stationary_noise':noise,'terminal_case_retries':retries,
              'scope':'Four-slot diagnostic +/-1fC benches, typical MIM, ideal controls/reference currents. '
                      'FF85 negative and SS0 positive are paired corner/temperature screens, not full PVT coverage. '
                      'One mismatch seed is not yield qualification. Sampling changes include read settling. '
                      '5mV initialization is coarse sanity only, not model accuracy tolerance. '
                      'No RPEX, sampled-noise covariance, silicon gate leakage, full PLIF or 5ms population service.',
              'next_step':'Physically reduce sampling disturbance and qualify sampled-noise handling/nonlinear encoding; '
                          'preserve original-float accuracy and full population scope before assembly expansion.',
              'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sources}}
    target = BASE/'results/gf180_continuous_restore_qualification_boundary.json'
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(target),'cases':len(cases),'numerical_comparisons':numerical},indent=2))


if __name__ == '__main__':
    main()
