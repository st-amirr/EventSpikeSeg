"""Audit selective analog precision and emit a provisional actor budget, never chip acceptance."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
RESULTS = BASE / 'results'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audited(path):
    report = json.loads(path.read_text(encoding='utf-8'))
    for filename, expected in report['sha256'].items():
        assert digest(ROOT / filename) == expected, filename
    assert report['simulation_completed']
    assert not any(report.get(key, False) for key in ['original_float_accuracy_accepted', 'complete_PLIF_accepted', 'full_chip_accepted'])
    return report


def grouped(report, key):
    results = []
    for value in dict.fromkeys(row[key] for row in report['results']):
        rows = [row for row in report['results'] if row[key] == value]
        results.append({'case': value, 'seed_count': len(rows),
                        'mean_iou': sum(row['mean_iou'] for row in rows) / len(rows),
                        'mean_pixel_change_fraction': sum(row['pixel_change_fraction'] for row in rows) / len(rows),
                        'candidate_rail_excursions': [row.get('candidate_rail_excursions') for row in rows],
                        'post_state_rail_excursions': [row.get('post_state_rail_excursions') for row in rows]})
    return results


def main():
    calibration_path = RESULTS / 'gf180_float_channel_calibration_dc685af8e3_src224604b6e23d.json'
    calibration = audited(calibration_path)
    counts = calibration['actor_state_counts']
    assert len(counts) == 25 and sum(counts.values()) == 30976000
    assert all(value > 0 for values in calibration['channel_fixed_calibration_absmax'].values() for value in values)
    evidence = []
    forwards = len(calibration['records'])
    for pattern in ['gf180_float_stage_noise_record*_src*.json', 'gf180_float_precision_allocation_record*_src*.json',
                    'gf180_float_fixed_precision_allocation_record*_src*.json',
                    'gf180_float_fixed_precision_rail_control_record*_src*.json']:
        for path in sorted(RESULTS.glob(pattern)):
            report = audited(path)
            forwards += len(report['results'])
            index = report['record']['validation_record_index']
            if index in [0, 1]:
                reference_path = RESULTS / f'gf180_float_channel_read_noise_record{index}_src69efab1ceb5e.json'
                reference = audited(reference_path)
                assert report['input_sequence_sha256'] == reference['input_sequence_sha256']
                assert report['target_sha256'] == reference['target_sha256']
                assert report['results'][0]['prediction_sha256'] == reference['results'][0]['prediction_sha256']
            if 'fixed_precision' in path.name:
                assert index not in [row['validation_record_index'] for row in calibration['records']]
                assert report['channel_fixed_calibration_absmax'] == calibration['channel_fixed_calibration_absmax']
                assert report['clipping_applied_to_perturbed_cases_only']
                if 'rail_control' in path.name:
                    reference = audited(RESULTS / f'gf180_float_fixed_precision_allocation_record{index}_src02a3298c7e50.json')
                    assert report['results'][0]['prediction_sha256'] == reference['results'][0]['prediction_sha256']
                    assert all(row['other_actor_candidate_error_sigma_uv'] < 1e-20 for row in report['results'])
            elif 'precision_allocation' in path.name:
                assert report['actor_state_counts'] == counts
                reference = audited(RESULTS / f'gf180_float_channel_read_noise_record{index}_src69efab1ceb5e.json')
                for row in report['results']:
                    if row['precision_policy'] == 'uniform15':
                        previous = next(r for r in reference['results'] if r['candidate_read_error_sigma_uv'] == 15 and r['seed'] == row['seed'])
                        assert row['prediction_sha256'] == previous['prediction_sha256']
            evidence.append({'report': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
                             'record': report['record'], 'forwards': len(report['results']),
                             'range_source': 'fixed_separate_eight_record_calibration' if 'fixed_precision' in path.name else 'optimistic_target_record_channel_oracle',
                             'cases': grouped(report, 'noisy_group' if 'stage_noise' in path.name else 'precision_policy')})
    macro_references = {}
    for cell in ['gf180_autozero_charge_integrator_fullroute_guarded',
                 'gf180_precharged_weight_current_cell_fullroute_guarded',
                 'gf180_pmos_follower_baseline_readout_fullroute_guarded']:
        folder = BASE / 'layout' / cell
        for filename in ['qualification.json', 'abstract_qualification.json']:
            path = folder / filename
            report = json.loads(path.read_text(encoding='utf-8'))
            for key, values in report.items():
                if 'sha256' in key and isinstance(values, dict):
                    for name, expected in values.items():
                        assert digest(ROOT / name if '/' in name else folder / name) == expected
            if filename == 'qualification.json':
                assert report['magic_drc_count'] == report['gds_roundtrip_drc_count'] == 0
                assert report['lvs_unique'] and report['gds_roundtrip_lvs_unique']
            macro_references[path.relative_to(ROOT).as_posix()] = digest(path)
    actors = [{'name': name, 'logical_resident_states': count,
               'hypothetical_candidate_error_target_uv_rms': 3 if name == 'stem' else 15,
               'precision_implementation': 'special_precision_path_unimplemented' if name == 'stem' else 'ordinary_charge_integrator_readout_candidate_unqualified_as_complete_chain',
               'fixed_channel_absmax_model_units': calibration['channel_fixed_calibration_absmax'][name],
               'physical_half_range_v': .3, 'physical_error_target_qualified': False,
               'weight_mapping_reference_delivery_qualified': False}
              for name, count in counts.items()]
    mapping_path = RESULTS / 'gf180_original_float_pulse_mapping_boundary.json'
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    archive_path = BASE / 'model_reference/gf180_source_mapping_float/eventspikeseg140k_float_parameters.npz'
    assert mapping['checkpoint_sha256'] == calibration['checkpoint_sha256']
    assert digest(archive_path) == mapping['sha256'][archive_path.relative_to(ROOT).as_posix()]
    with np.load(archive_path) as arrays:
        effective_weights = arrays['weight__stem'] * arrays['affine_gain__stem'][:, None, None, None]
        assert effective_weights.shape == (32, 2, 5, 5)
        ranges = np.asarray(calibration['channel_fixed_calibration_absmax']['stem'])
        steps = effective_weights * (.3 / ranges)[:, None, None, None]
        packet_targets = {'status': 'ideal_linear_state_packet_targets_not_physical_programming', 'actor': 'stem',
            'checkpoint_sha256': calibration['checkpoint_sha256'], 'weight_count': int(effective_weights.size),
            'effective_float_weights_after_affine': effective_weights.tolist(),
            'ideal_linear_state_voltage_increment_v_per_input_count': steps.tolist(),
            'absolute_step_uv_quantiles': dict(zip(['minimum', 'p01', 'p10', 'median', 'p90', 'p99', 'maximum'],
                                                  (np.quantile(abs(steps), [0, .01, .1, .5, .9, .99, 1]) * 1e6).tolist())),
            'beta_once_per_bin': arrays['beta__stem'].tolist(),
            'base_threshold_model_units': arrays['threshold__stem'].tolist(),
            'affine_gain_folded_once': True, 'input_multiplicity_preserved': True,
            'scope': 'Original float coefficients mapped to fixed channel voltage scales mathematically. One input count contributes coefficient times voltage scale; raw multiplicity multiplies contributions, does not change weight-defined firing frequency. This is an integrator/state-domain target, not a buffered-output target or actual current/pulse calibration. No minimum pulse, charge-electron resolution, underflow, noise or physical weight acceptance inferred. No QAT or retraining.',
            'source_archive_sha256': digest(archive_path), 'mapping_report_sha256': digest(mapping_path),
            'calibration_report_sha256': digest(calibration_path), 'weighted_charge_accepted': False}
    packets_path = RESULTS / 'gf180_stem_float_packet_targets.json'
    packets_path.write_text(json.dumps(packet_targets, indent=2) + '\n', encoding='utf-8')
    manifest = {'status': 'provisional_heterogeneous_analog_precision_allocation_not_accepted_hardware',
                'float_checkpoint_sha256': calibration['checkpoint_sha256'], 'actors': actors,
                'special_precision_actors': ['stem'], 'special_precision_state_count': counts['stem'],
                'special_precision_fraction': counts['stem'] / sum(counts.values()),
                'qualified_reusable_macro_reference_sha256': macro_references,
                'calibration_report': calibration_path.relative_to(ROOT).as_posix(),
                'calibration_report_sha256': digest(calibration_path),
                'stem_packet_targets': packets_path.relative_to(ROOT).as_posix(),
                'stem_packet_targets_sha256': digest(packets_path),
                'scope': 'Continuous analog state/weight path, no QAT, no retraining, no digital-state fallback. Targets3/15uV are hypothetical sensitivity budgets, not accepted tolerances or measured full-chain errors. Ordinary readout ideal4us proxy13uV excludes sampled/storage/source/reference errors; therefore other24actors are not qualified either. Source state identities count logical capacity, not implemented resident cells. Calibrated ranges and ideal clamps are not physical reference/gain/limiter circuits.',
                'original_float_accuracy_accepted': False, 'complete_PLIF_accepted': False,
                'full_5ms_population_service_accepted': False, 'full_chip_accepted': False}
    manifest_path = RESULTS / 'gf180_actor_precision_allocation.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    stem_lanes = math.ceil(counts['stem'] * 20e-6 / .005)
    other_lanes = math.ceil((sum(counts.values()) - counts['stem']) * 4e-6 / .005)
    boundary = {'stage': 'selective_input_stem_precision_feasibility', 'evidence': evidence,
                'completed_replay_reports': len(evidence), 'calibration_records': len(calibration['records']),
                'completed_model_forwards': forwards, 'all_provenance_hashes_match': True,
                'calibration_report_sha256': digest(calibration_path),
                'actor_precision_manifest': manifest_path.relative_to(ROOT).as_posix(),
                'actor_precision_manifest_sha256': digest(manifest_path),
                'illustrative_service_lower_bounds': {'assumed_stem_read_window_us': 20,
                    'assumed_other_read_window_us': 4, 'dedicated_stem_min_lanes': stem_lanes,
                    'other_min_lanes': other_lanes, 'combined_min_lanes': stem_lanes + other_lanes,
                    'uniform20us_all_state_min_lanes': math.ceil(sum(counts.values()) * 20e-6 / .005),
                    'scope': 'Arithmetic only, assumes perfect utilization and no other work;20us is not proven to achieve3uV,4us not full-chain15uV, no event/beta/reset/adaptation/writeback/clock/bank conflicts included. No implemented service claim.'},
                'method_decision': 'Prioritize special precision/range-coded charge-domain circuitry for the input stem, retain ordinary analog path as candidate for remaining actors. Broader independent calibration and physical complete-chain noise required. Original float architecture and checkpoint unchanged; noise-aware fine-tuning is a literature-backed alternative only, not authorized/selected or executed.',
                'optional_training_reference': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8794842/',
                'scope': 'Noise localization and selective allocation are software sensitivity evidence. Oracle cases optimistic; separate fixed-calibration held-out cases include ideal rail clipping. All available records are from one Zurich sequence, not cross-scene/full validation accuracy. No claim that few pixel changes or near-baseline IoU qualifies exact output fidelity. Physical precision, retention, 5ms service, dense assembly and full-chip layout remain open.',
                'original_float_accuracy_accepted': False, 'complete_PLIF_accepted': False,
                'full_5ms_population_service_accepted': False, 'full_chip_accepted': False,
                'live_sessions': [], 'audit_source_sha256': digest(Path(__file__))}
    path = RESULTS / 'gf180_precision_allocation_boundary.json'
    path.write_text(json.dumps(boundary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'reports': len(evidence), 'forwards': forwards, 'special_actor': 'stem',
                      'special_state_fraction': manifest['special_precision_fraction']}))


if __name__ == '__main__':
    main()
