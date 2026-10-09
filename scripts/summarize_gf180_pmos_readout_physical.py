"""Audit physical PMOS readout and conditional float precision evidence."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audited(path):
    report = json.loads(path.read_text(encoding='utf-8'))
    for name, expected in report.get('sha256', {}).items():
        assert digest(ROOT / name) == expected, name
    for flag in ['weighted_charge_accepted', 'original_float_accuracy_accepted',
                 'complete_PLIF_accepted', 'full_chip_accepted']:
        assert not report.get(flag, False), flag
    return report


def main():
    records = []
    for pattern in ['gf180_paired_pmos_follower_pex_noise_src*.json',
                    'gf180_assembled_pmos_follower_readout_*_src*.json',
                    'gf180_pmos_follower_pex_transfer_src*.json']:
        for path in sorted((BASE / 'results').glob(pattern)):
            report = audited(path)
            records.append({'report': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
                            'completed': report['simulation_completed'],
                            'settings': report.get('settings', {}),
                            'measurements': report['measurements']})
    physical = {}
    for cell in ['gf180_read_pf10_l1', 'gf180_read_pf80_l1',
                 'gf180_pmos_follower_baseline_readout_fullroute_guarded']:
        folder = BASE / 'layout' / cell
        entries = {}
        for filename in ['qualification.json', 'abstract_qualification.json']:
            path = folder / filename
            if not path.exists():
                assert filename == 'abstract_qualification.json' and cell != 'gf180_pmos_follower_baseline_readout_fullroute_guarded'
                continue
            report = json.loads(path.read_text(encoding='utf-8'))
            for key, values in report.items():
                if 'sha256' in key and isinstance(values, dict):
                    for name, expected in values.items():
                        target = ROOT / name if '/' in name else folder / name
                        assert digest(target) == expected, str(target)
            if filename == 'qualification.json':
                assert report['magic_drc_count'] == report['gds_roundtrip_drc_count'] == 0
                assert report['lvs_unique'] and report['gds_roundtrip_lvs_unique']
                assert report['extraction_feedback'] == ''
            entries[filename] = {'sha256': digest(path),
                                 'checks': {k: v for k, v in report.items() if 'sha256' not in k}}
        physical[cell] = entries
    noise_path = BASE / 'results/gf180_paired_pmos_follower_pex_noise_src63d6c6f9adf2.json'
    noise = audited(noise_path)
    spectrum = np.loadtxt(ROOT / noise['spectrum'], skiprows=1)
    averages = [{'ideal_average_s': duration,
                 'output_noise_uv_rms': float(np.sqrt(np.trapezoid(
                     spectrum[:, 1] ** 2 * np.sinc(spectrum[:, 0] * duration) ** 2,
                     spectrum[:, 0]))) * 1e6}
                for duration in [0, 1e-6, 4e-6, 20e-6, 100e-6]]
    for row in averages:
        duration = row['ideal_average_s']
        row['ideal_two_sample_CDS_gap_2T_output_noise_uv_rms'] = None if not duration else float(np.sqrt(np.trapezoid(
            spectrum[:, 1] ** 2 * np.sinc(spectrum[:, 0] * duration) ** 2 *
            (2 * np.sin(np.pi * spectrum[:, 0] * 2 * duration)) ** 2, spectrum[:, 0]))) * 1e6
    assert abs(averages[0]['output_noise_uv_rms'] / (noise['measurements']['noise2.onoise_total'] * 1e6) - 1) < .001
    transfer_path = BASE / 'results/gf180_pmos_follower_pex_transfer_src17cf52e1eee4.json'
    transfer = audited(transfer_path)
    values = np.loadtxt(ROOT / transfer['dc_transfer'], skiprows=1)
    gain = np.gradient(values[:, 1], values[:, 0])
    centre = int(np.argmin(abs(values[:, 0] - 1.65)))
    mask = (values[:, 0] >= 1.35 - 1e-8) & (values[:, 0] <= 1.95 + 1e-8)
    residual = values[:, 1] - (values[centre, 1] + gain[centre] * (values[:, 0] - values[centre, 0]))
    nominal = next(row for row in records if row['completed'] and 'assembled' in row['report']
                   and row['settings']['mismatch_seed'] is None)
    nominal_gain = nominal['measurements']['buffered_step_0'] / nominal['measurements']['eventstep_0']
    sensitivity = []
    for pattern in ['gf180_float_read_noise_record*_src*.json', 'gf180_float_channel_read_noise_record*_src*.json',
                    'gf180_float_fixed_channel_read_noise_record*_src*.json']:
        for path in sorted((BASE / 'results').glob(pattern)):
            report = audited(path)
            baseline = report['results'][0]
            previous = BASE / 'results' / ('gf180_float_signed_gain_record' + str(report['record']['validation_record_index']) + '_src60cee0bd359a.json')
            prior = audited(previous)
            assert report['input_sequence_sha256'] == prior['input_sequence_sha256']
            assert report['target_sha256'] == prior['target_sha256']
            assert baseline['prediction_sha256'] == prior['results'][0]['prediction_sha256']
            grouped = []
            for sigma in sorted({r['candidate_read_error_sigma_uv'] for r in report['results']}):
                rows = [r for r in report['results'] if r['candidate_read_error_sigma_uv'] == sigma]
                grouped.append({'hypothetical_candidate_noise_sigma_uv': sigma, 'seed_count': len(rows),
                                'mean_iou': float(np.mean([r['mean_iou'] for r in rows])),
                                'mean_iou_range': [min(r['mean_iou'] for r in rows), max(r['mean_iou'] for r in rows)],
                                'mean_pixel_change_fraction': float(np.mean([r['pixel_change_fraction'] for r in rows]))})
            sensitivity.append({'report': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
                                'scope': 'fixed_channel_separate_calibration' if 'fixed_channel' in path.name else ('per_channel_oracle' if 'channel' in path.name else 'per_actor_oracle'),
                                'record': report['record'], 'physical_half_range_v': report['physical_half_range_v'],
                                'calibration_record': report.get('calibration_record'),
                                'baseline_channels_exceeding_calibration': report.get('baseline_channels_exceeding_calibration'),
                                'baseline_observed_over_calibration_max_ratio': report.get('baseline_observed_over_calibration_max_ratio'),
                                'fixed_zero_range_channels': sum(v == 0 for values in report.get('channel_fixed_calibration_absmax', {}).values() for v in values) if 'channel_fixed_calibration_absmax' in report else None,
                                'fixed_range_feasible': False if 'channel_fixed_calibration_absmax' in report else None,
                                'baseline_reproduced': True, 'grouped_results': grouped})
    report = {'stage': 'physical_pmos_readout_and_float_precision_method_selection',
              'completed_diagnostics': sum(r['completed'] for r in records),
              'failed_diagnostics_preserved': sum(not r['completed'] for r in records),
              'failed_bench_cause': 'Initial external diode instances omitted extra VSUBS port present in parent-context extraction. Corrected benches connect fifth substrate port to ground; native extracted netlists unchanged.',
              'records': records, 'physical': physical, 'all_provenance_hashes_match': True,
              'ideal_filter_proxies': averages, 'nominal_integrator_to_buffered_output_gain': nominal_gain,
              'conditional_4us_noise_referred_to_integrator_uv': averages[2]['output_noise_uv_rms'] / nominal_gain,
              'central_input_range_v': [1.35, 1.95], 'central_gain_range': [float(gain[mask].min()), float(gain[mask].max())],
              'central_max_sampled_linear_fit_error_uv': float(abs(residual[mask]).max()) * 1e6,
              'float_sensitivity': sensitivity,
              'scope': 'Nominal physical module DRC/LVS/GDS/cap extraction/LEF and bounded circuit evidence; no RPEX/PVT/gate leakage/sampled noise/full-state service acceptance. Fixed-reference offset adjustment uses actual clamp, but external ideal precision reference/offline trim is not an implemented servo. Ideal time averaging is spectrum math, not physical filter. Conditional independent candidate noise with optimistic per-record oracle ranges is sensitivity only, not measured error distribution or validation accuracy. Spacious macro geometry is not dense tile/chip area.',
              'method_selection': 'Per-channel scaling preferred for further work, but single-record fixed ranges rejected as implementable: observed range overflows and zero calibration ranges; unclipped software replay is optimistic and does not repair them. Chopped/auto-zeroed differential readout is next bounded circuit alternative; physically implemented companded/charge-domain path remains fallback. No error or accuracy acceptance inferred.',
              'method_reference': 'https://www.analog.com/en/resources/technical-articles/2018/05/25/03/08/to-chop-or-auto-zero-that-is-the-question.html',
              'next': 'Use calibration ranges from separate records with rail checks; implement and measure chopped/auto-zeroed differential readout including switch injection, settling and sampled noise. Compare physically realizable companded/charge-domain compute if it fails, before adding read lanes/cap area. Calibrate signed weights/reference delivery then complete PLIF, retention/service and dense assembly.',
              'original_float_accuracy_accepted': False, 'complete_PLIF_accepted': False,
              'full_5ms_population_service_accepted': False, 'full_chip_accepted': False,
              'live_sessions': [], 'audit_source_sha256': digest(Path(__file__))}
    path = BASE / 'results/gf180_pmos_readout_physical_boundary.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'completed': report['completed_diagnostics'],
                      'failed_preserved': report['failed_diagnostics_preserved'], 'float_reports': len(sensitivity),
                      'nominal_read_gain': nominal_gain, 'ideal_4us_input_noise_uv': report['conditional_4us_noise_referred_to_integrator_uv']}))


if __name__ == '__main__':
    main()
