"""Audit lower-noise linear-storage sensitivity against its lossless control."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/results'
EXPECTED = 'c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checkpoint = ROOT / 'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    if digest(checkpoint) != EXPECTED:
        raise ValueError('Original float checkpoint differs')
    sources = {Path(__file__), checkpoint}
    base = 'sky130_float_state_saturation_validation_0_all_neurons_full_'
    control_path = OUT / (base+'none_g1_n0uv_channel_ranges.json')
    control = json.loads(control_path.read_text())
    cases = []
    for path in [control_path, *sorted(OUT.glob(base+'writeback_every_bin_g1_n*uv_channel_ranges.json'))]:
        r = json.loads(path.read_text())
        if r['checkpoint_sha256'] != EXPECTED or r['qat_or_quantized_reference_used'] or not r['full_frame'] or r['scope'] != 'all-neurons' or r['encoding'] != 'linear-clipped' or r['gains'] != [1.0] or r['range_scope'] != 'channel' or r['retention_law'] != 'none':
            raise ValueError('Sensitivity contract differs')
        if r.get('affine_restore_active') or r.get('linear_compute_noise_sigma_uv', 0):
            raise ValueError('Additional perturbation present')
        if r['baseline_present_class_mean_iou'] != control['baseline_present_class_mean_iou'] or r['channel_max_absolute_candidate_model_units'] != control['channel_max_absolute_candidate_model_units']:
            raise ValueError('Different baseline or channel normalization')
        sources.add(path)
        snapshot_verified = False
        if r.get('replay_source_snapshot'):
            snapshot = ROOT / r['replay_source_snapshot']
            if digest(snapshot) != r['replay_source_sha256'] or r['replay_source_sha256'] != control['replay_source_sha256']:
                raise ValueError('Replay source differs from matched control')
            sources.add(snapshot)
            snapshot_verified = True
        trials = r['trials']
        if path == control_path or r['injected_state_noise_sigma_uv_rms'] == 0:
            if any(t['final_fuse_spike_mismatch'] != 0 or t['segmentation_pixel_agreement_with_float'] != 1 for t in trials):
                raise ValueError('Lossless control differs')
        elif r['noise_mode'] != 'writeback-every-bin' or {t['seed'] for t in trials} != {1729, 1730, 1731}:
            raise ValueError('Three-seed noise screen differs')
        mean_iou = sum(t['present_class_mean_iou'] for t in trials)/len(trials)
        cases.append({
            'evidence': path.relative_to(ROOT).as_posix(),
            'noise_sigma_uv_rms': r['injected_state_noise_sigma_uv_rms'],
            'source_snapshot_verified_against_control': snapshot_verified,
            'historical_report_without_snapshot': not snapshot_verified,
            'mean_present_class_iou': mean_iou,
            'mean_iou_delta_from_float': mean_iou-control['baseline_present_class_mean_iou'],
            'mean_pixel_agreement': sum(t['segmentation_pixel_agreement_with_float'] for t in trials)/len(trials),
            'trials': trials,
        })
    result = {
        'checkpoint_sha256': EXPECTED,
        'qat_or_quantized_reference_used': False,
        'lossless_control_passed': True,
        'zero_amplitude_writeback_control_passed': any(c['noise_sigma_uv_rms'] == 0 and 'writeback_every_bin' in c['evidence'] for c in cases),
        'baseline_present_class_iou': control['baseline_present_class_mean_iou'],
        'cases': cases,
        'scope': 'One selected full frame, ten updates, all 25 actors. Independent Gaussian noise at initialization and every post-bin membrane. Ideal per-record channel normalization to +/-0.9V; perfect weights, beta, threshold, reset, adaptation and graph computation. Historical rows without immutable source snapshots are labeled separately. No physical sampled-noise or validation-set accuracy qualification, retention, service or full-chip acceptance. No acceptance threshold is inferred.',
        'original_float_accuracy_accepted': False,
        'physical_storage_accepted': False,
        'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(sources)},
    }
    target = OUT / 'float_linear_storage_noise_boundary.json'
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'report': str(target), 'cases': [{k:v for k,v in c.items() if k != 'trials'} for c in cases]}, indent=2))


if __name__ == '__main__':
    main()
