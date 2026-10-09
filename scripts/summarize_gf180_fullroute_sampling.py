"""Preserve and compare extracted sampling variants, including failed runs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/results'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    sources = {Path(__file__)}
    cases = []
    for path in sorted(OUT.glob('gf180_fullroute_tg_hold_step*.json')):
        r = json.loads(path.read_text())
        sources.add(path)
        for name, expected in r['sha256'].items():
            p = ROOT / name
            if digest(p) != expected:
                raise ValueError('Physical/simulation input differs: '+name)
            sources.add(p)
        snapshot = ROOT / r['source_snapshot']
        settings = r['settings']
        rows = r['cases']
        case = {'evidence': path.relative_to(ROOT).as_posix(),
                'source_sha256': digest(snapshot), 'settings': settings,
                'simulation_completed': r['simulation_completed'],
                'all_source_model_geometry_and_log_hashes_verified': True,
                'cases': rows}
        if r['simulation_completed']:
            if [row['target_v'] for row in rows] != [.3, 1.65, 3.0]:
                raise ValueError('Voltage grid differs')
            release_errors = [row['voltage_measurements']['released']-row.get('desired_capacitor_voltage_v', row['target_v']) for row in rows]
            held_errors = [row['voltage_measurements']['held']-row.get('desired_capacitor_voltage_v', row['target_v']) for row in rows]
            case['maximum_absolute_release_error_mv'] = max(map(abs, release_errors))*1e3
            case['maximum_absolute_held_error_mv'] = max(map(abs, held_errors))*1e3
            case['relative_to_midpoint_release_error_mv'] = [(error-release_errors[1])*1e3 for error in release_errors]
            case['relative_to_midpoint_held_error_mv'] = [(error-held_errors[1])*1e3 for error in held_errors]
            case['midpoint_subtraction_is_analysis_only_not_physical_calibration'] = True
        cases.append(case)
    matches = []
    for c in cases:
        if not c['simulation_completed'] or not c['settings'].get('dummy_count', 0):
            continue
        candidates = [b for b in cases if b['simulation_completed'] and b['source_sha256'] == c['source_sha256'] and b['settings']['max_step_ns'] == c['settings']['max_step_ns'] and b['settings'].get('bottom_plate', False) == c['settings'].get('bottom_plate', False) and b['settings'].get('dummy_count', 0) == 0]
        if len(candidates) == 1:
            b = candidates[0]
            matches.append({'variant': c['evidence'], 'baseline': b['evidence'],
                            'same_executable_and_sampling_mode_and_step': True,
                            'release_max_error_reduction_mv': b['maximum_absolute_release_error_mv']-c['maximum_absolute_release_error_mv'],
                            'held_max_error_reduction_mv': b['maximum_absolute_held_error_mv']-c['maximum_absolute_held_error_mv']})
    numerical = []
    def physical_deck(case):
        report = json.loads((ROOT/case['evidence']).read_text())
        paths = [ROOT/n for n in report['sha256'] if '/benches/' in n and n.endswith('.spice')]
        if len(paths) != 1:
            raise ValueError('Unique physical deck required')
        return '\n'.join(line for line in paths[0].read_text().splitlines() if not line.startswith('tran '))
    for fine in cases:
        if not fine['simulation_completed'] or fine['settings']['max_step_ns'] != 10:
            continue
        settings = {k:v for k,v in fine['settings'].items() if k != 'max_step_ns'}
        candidates = [c for c in cases if c['simulation_completed'] and c['source_sha256'] == fine['source_sha256'] and c['settings']['max_step_ns'] == 100 and {k:v for k,v in c['settings'].items() if k != 'max_step_ns'} == settings]
        if len(candidates) != 1:
            continue
        coarse = candidates[0]
        if physical_deck(fine) != physical_deck(coarse):
            raise ValueError('Numerical comparison changes physical deck')
        differences = [abs(f['voltage_measurements'][key]-c['voltage_measurements'][key])*1e6 for f,c in zip(fine['cases'],coarse['cases']) for key in ['acquired','on','released','held']]
        numerical.append({'fine_evidence': fine['evidence'], 'coarse_evidence': coarse['evidence'],
                          'physical_deck_identical_except_transient_step': True,
                          'maximum_reported_endpoint_difference_uv': max(differences),
                          'scope': 'Agreement at reported scalar precision for three voltages and endpoint apertures; not sampled noise, model accuracy or general convergence qualification.'})
    result = {'cases': cases, 'case_count': len(cases),
              'completed_case_count': sum(c['simulation_completed'] for c in cases),
              'matched_dummy_comparisons': matches,
              'matched_numerical_step_comparisons': numerical,
              'physical_storage_accepted': False, 'original_float_accuracy_accepted': False,
              'complete_PLIF_accepted': False, 'full_chip_accepted': False,
              'scope': 'Nominal deterministic extracted primitive combination at three input voltages. Individual switch geometry/export connectivity qualified; combined sampling macro not laid out. Ideal input and clock drivers, native MIM and unchanged model cards. Floating differential bottom-plate mode changes readout requirements. Rounded scalar measurement precision limits fine numerical comparisons. Includes failed metrology/startup evidence. No physical calibration inferred from midpoint subtraction, sampled noise, mismatch, PVT, silicon leakage or 5ms population-service qualification.',
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(sources)}}
    target = OUT / 'gf180_fullroute_sampling_boundary.json'
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'report': str(target), 'case_count': len(cases), 'matched_dummy_comparisons': matches}, indent=2))


if __name__ == '__main__':
    main()
