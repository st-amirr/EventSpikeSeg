"""Audit the two-phase charge-sharing alternative without promoting it to ASIC acceptance."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic/results'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    report = json.loads(path.read_text(encoding='utf-8'))
    for filename, expected in report['sha256'].items():
        assert digest(ROOT / filename) == expected, filename
    for key in ['original_float_accuracy_accepted', 'complete_PLIF_accepted', 'full_chip_accepted']:
        assert not report.get(key, False)
    assert report['simulation_completed']
    return report


def main():
    diagnostics = []
    for pattern in ['gf180_charge_shared_chopped_readout_*_src*.json', 'gf180_chopped_capture_noise_src*.json']:
        for path in sorted(BASE.glob(pattern)):
            report = read(path)
            if 'settings' in report:
                bench = next(ROOT / filename for filename in report['sha256'] if '/benches/' in filename and filename.endswith('.spice'))
                deck = bench.read_text(encoding='utf-8')
                if report['settings'].get('cross_share'):
                    assert 'Xshare_p pa nb share shareb 0 vdd' in deck
                    assert 'Xshare_n na pb share shareb 0 vdd' in deck
                    assert 'Xsample_bp outb pb sampleb samplebb 0 vdd' in deck
                    assert abs(report['measurements']['average_a'] + report['measurements']['average_b']) < 1e-10
                else:
                    assert 'Xshare_p pa pb share shareb 0 vdd' in deck
            else:
                spectrum = np.loadtxt(ROOT / report['capture_spectrum'], skiprows=1)
                integrated = np.sqrt(np.trapezoid(spectrum[:, 1] ** 2, spectrum[:, 0]))
                assert abs(integrated / report['measurements']['noise2.onoise_total'] - 1) < .001
            diagnostics.append({'report': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
                                'settings': report.get('settings', {}), 'measurements': report['measurements']})
    models = []
    for pattern in ['gf180_float_comparator_noise_record*_src*.json', 'gf180_float_comparator_zero_control_record*_src*.json']:
        for path in sorted(BASE.glob(pattern)):
            report = read(path)
            index = report['record']['validation_record_index']
            comparison_path = BASE / f'gf180_float_channel_read_noise_record{index}_src69efab1ceb5e.json'
            comparison = read(comparison_path)
            assert report['input_sequence_sha256'] == comparison['input_sequence_sha256']
            assert report['target_sha256'] == comparison['target_sha256']
            assert report['results'][0]['prediction_sha256'] == comparison['results'][0]['prediction_sha256']
            grouped = []
            for sigma in sorted({row['comparator_error_sigma_uv'] for row in report['results']}):
                rows = [row for row in report['results'] if row['comparator_error_sigma_uv'] == sigma]
                grouped.append({'hypothetical_comparator_noise_sigma_uv': sigma,
                                'mean_iou': float(np.mean([r['mean_iou'] for r in rows])),
                                'mean_pixel_change_fraction': float(np.mean([r['pixel_change_fraction'] for r in rows]))})
            if 'zero_control' in path.name:
                assert all(row['prediction_sha256'] == report['results'][0]['prediction_sha256'] for row in report['results'])
            models.append({'report': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
                           'comparison_report': comparison_path.relative_to(ROOT).as_posix(),
                           'comparison_sha256': digest(comparison_path), 'grouped_results': grouped,
                           'forwards': len(report['results']), 'baseline_reproduced': True})
    nominal = next(row for row in diagnostics if row['settings'].get('cross_share') and
                   row['settings'].get('mismatch_seed') is None)
    crossed = [row for row in diagnostics if row['settings'].get('cross_share') and
               not row['settings'].get('gate_rezero') and row['settings'].get('mismatch_seed') == 29]
    positive = next(row for row in crossed if row['settings']['signal_uv'] == 100)
    negative = next(row for row in crossed if row['settings']['signal_uv'] == -100)
    zero = next(row for row in crossed if row['settings']['signal_uv'] == 0)
    noise = next(row for row in diagnostics if 'capture_noise' in row['report'])
    response_gain = (positive['measurements']['average_a'] - negative['measurements']['average_a']) / .0002
    geometric_cap_f = 9 * 7 * 7 * 2e-15
    report = {'stage': 'two_phase_readout_offset_improved_precision_candidate_rejected',
              'completed_circuit_diagnostics': len(diagnostics), 'completed_model_replay_reports': len(models),
              'model_forwards': sum(row['forwards'] for row in models),
              'records': diagnostics, 'float_sensitivity': models, 'all_provenance_hashes_match': True,
              'cross_share_nominal_zero_uv': nominal['measurements']['average_a'] * 1e6,
              'cross_share_seed29_zero_uv': zero['measurements']['average_a'] * 1e6,
              'cross_share_seed29_state_displacement_uv': zero['measurements']['stored_final'] * 1e6,
              'cross_share_seed29_two_point_signed_gain': response_gain,
              'capture_aperture_stationary_noise_uv_rms': noise['measurements']['noise2.onoise_total'] * 1e6,
              'illustrative_geometric_cap_f': geometric_cap_f,
              'illustrative_kTC_equilibrium_sigma_uv': (1.380649e-23 * 300.15 / geometric_cap_f) ** .5 * 1e6,
              'findings': ['Crossing second sample capacitor during charge sharing cancels much of follower offset and sampler pedestal physically; no arithmetic correction applied to circuit state.',
                           'Input-state disturbance and nonunity response remain. Extra real gate-reset switches worsen pedestal; four storage banks reduce some disturbance but do not solve precision and cost capacitor area.',
                           'Stationary native capture-aperture noise remains substantial; it is not switched sampled-noise covariance or evidence of chopping noise reduction.',
                           'Comparator-only hypothetical noise gives nearly the same15uV model degradation as candidate/state noise in these records. Avoiding noisy state writeback alone is insufficient under the tested linear channel encoding.'],
              'method_decision': 'Do not promote one-shot two-phase charge-sharing sampler to a selected precision solution or lay it out as a final PLIF readout. Keep qualified reusable leaves and failed/complete diagnostic evidence. Prioritize physically range-coded/companded charge-domain state updates and direct encoded threshold comparison; compare against prior measured encoder/inverse/range-transition limitations before another implementation. Broader nonzero calibration ranges/rail checks remain necessary.',
              'scope': 'Twelve deterministic transient cases using extracted children with schematic interconnect, one stationary aperture-noise case, two full-frame comparator-noise replays and one effectively-zero custom-forward control. Two records/three seeds and oracle channel ranges are sensitivity only. Gaussian comparator error is hypothetical, not native device distribution. State arithmetic and reset amplitude ideal in model replay; no complete physical PLIF, no sampled-noise/PVT/RPEX/gate-leakage/retention/service/area acceptance. Geometric kTC scale is an illustrative equilibrium estimate using nominal area density, not measured sample covariance or actual extracted bank C.',
              'new_combined_layout_qualified': False, 'sampled_noise_qualified': False,
              'original_float_accuracy_accepted': False, 'complete_PLIF_accepted': False,
              'full_5ms_population_service_accepted': False, 'full_chip_accepted': False,
              'live_sessions': [], 'audit_source_sha256': digest(Path(__file__))}
    assert len(diagnostics) == 13 and len(models) == 3
    path = BASE / 'gf180_chopped_readout_boundary.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['completed_circuit_diagnostics', 'completed_model_replay_reports',
                                          'cross_share_seed29_zero_uv', 'cross_share_seed29_two_point_signed_gain',
                                          'capture_aperture_stationary_noise_uv_rms']}))


if __name__ == '__main__':
    main()
