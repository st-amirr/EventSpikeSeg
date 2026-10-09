"""Conditional read-error sensitivity of the original float model, not circuit acceptance."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
EXPECTED = 'c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tensor_digest(value):
    return hashlib.sha256(value.detach().contiguous().cpu().numpy().tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--record-index', type=int, default=8)
    parser.add_argument('--calibration-report', type=Path, required=True)
    parser.add_argument('--noise-uv', default='1e-30')
    parser.add_argument('--seeds', default='1729')
    parser.add_argument('--headroom-v', type=float, default=0.3)
    args = parser.parse_args()
    assert args.headroom_v > 0
    torch.set_num_threads(2)
    checkpoint = ROOT / 'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    assert digest(checkpoint) == EXPECTED
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    assert saved['epoch'] == 58 and saved['architecture'] == 'EventSpikeSeg140k'
    sequence, frame = saved['temporal_protocol']['validation_record_ids'][args.record_index]
    records = [r for r in discover_dsec_records(args.dataset_root, 'train')
               if r.sequence_id == sequence and r.frame_index == frame]
    assert len(records) == 1
    dataset = DSECRawEventDataset(args.dataset_root, split='train', output_size=(440, 640),
                                internal_updates=10, class_count=6, records=records)
    events, target, _ = dataset[0]
    inputs = events.unsqueeze(1)
    valid = target != 255
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=10)
    model.load_state_dict(saved['model_state_dict'], strict=True)
    model.set_mechanism_scale(float(saved.get('mechanism_scale', 1)))
    for module in model.modules():
        toggle = getattr(module, 'set_asic_qat_enabled', None)
        if callable(toggle):
            toggle(False)
    model.eval()
    named = dict(model.named_modules())
    neurons = {name: named[name].neuron for name in EVENTSPIKESEG140K_INFERENCE_STAGES}
    assert len(neurons) == 25
    original = {name: neuron._candidate_membrane for name, neuron in neurons.items()}
    maxima = {name: None for name in neurons}
    actor_state_counts = {}
    precision_policies = {'rail_only': []}
    calibration = json.loads(args.calibration_report.read_text(encoding='utf-8'))
    assert calibration['checkpoint_sha256'] == EXPECTED
    assert args.record_index not in [row['validation_record_index'] for row in calibration['records']]
    fixed_ranges = {name: torch.tensor(calibration['channel_fixed_calibration_absmax'][name]).view(1, -1, 1, 1) for name in neurons}
    assert all(value.numel() == neurons[name].channels and torch.all(value > 0) for name, value in fixed_ranges.items())
    state = {'sigma_uv': 0.0, 'collect_ranges': True, 'policy': 'none', 'candidate_excursions': 0, 'candidate_elements': 0, 'post_state_excursions': 0}
    for name, neuron in neurons.items():
        def candidate(current, elapsed, _name=name, _base=original[name]):
            result = _base(current, elapsed)
            if state['collect_ranges']:
                actor_state_counts[_name] = result.numel()
                observed = result.abs().amax(dim=(0, 2, 3), keepdim=True)
                maxima[_name] = observed if maxima[_name] is None else torch.maximum(maxima[_name], observed)
            if state['sigma_uv']:
                # Oracle per-record channel range is deliberately optimistic, never clipping.
                noise_uv = 3.0 if _name in precision_policies[state['policy']] else state['sigma_uv']
                sigma = noise_uv * 1e-6 * fixed_ranges[_name] / args.headroom_v
                result = result + torch.randn_like(result) * sigma
            state['candidate_excursions'] += int((result.abs() > fixed_ranges[_name]).sum())
            state['candidate_elements'] += result.numel()
            if state['sigma_uv']:
                result = torch.maximum(torch.minimum(result, fixed_ranges[_name]), -fixed_ranges[_name])
            return result
        neuron._candidate_membrane = candidate
        original_forward = neuron.forward
        def bounded_forward(current, elapsed_steps=1.0, update_mask=None, _name=name, _neuron=neuron, _original=original_forward):
            spikes = _original(current, elapsed_steps, update_mask)
            state['post_state_excursions'] += int((_neuron.membrane.abs() > fixed_ranges[_name]).sum())
            if state['sigma_uv']:
                _neuron.membrane = torch.maximum(torch.minimum(_neuron.membrane, fixed_ranges[_name]), -fixed_ranges[_name])
            return spikes
        neuron.forward = bounded_forward

    def metric(prediction):
        confusion = torch.bincount(target[valid].long() * 6 + prediction[valid].long(),
                                   minlength=36).reshape(6, 6)
        intersection = confusion.diagonal()
        union = confusion.sum(0) + confusion.sum(1) - intersection
        return float((intersection[union > 0] / union[union > 0]).float().mean()), confusion.tolist()

    rows = []
    baseline = None
    cases = [('none', 0.0, None)] + [(policy, float(sigma), int(seed)) for policy in precision_policies
                            for sigma in args.noise_uv.split(',') for seed in args.seeds.split(',')]
    for policy, sigma, seed in cases:
        state['policy'] = policy
        state['candidate_excursions'] = state['candidate_elements'] = state['post_state_excursions'] = 0
        state['sigma_uv'] = sigma
        state['collect_ranges'] = sigma == 0
        if seed is not None:
            torch.manual_seed(seed)
        with torch.inference_mode():
            model.reset()
            started = time.monotonic()
            output = model(inputs)
            prediction = output['segmentation_logits'].argmax(1)[0].cpu()
            iou, confusion = metric(prediction)
            if baseline is None:
                baseline = prediction.clone()
            row = {'precision_policy': policy, 'other_actor_candidate_error_sigma_uv': sigma, 'seed': seed,
                   'mean_iou': iou, 'pixel_change_fraction': float((prediction != baseline).float().mean()),
                   'candidate_rail_excursions': state['candidate_excursions'],
                   'candidate_rail_excursion_fraction': state['candidate_excursions'] / state['candidate_elements'],
                   'post_state_rail_excursions': state['post_state_excursions'],
                   'confusion': confusion, 'runtime_seconds': time.monotonic() - started,
                   'prediction_sha256': tensor_digest(prediction)}
            rows.append(row)
            print(json.dumps(row), flush=True)
            del output
    source = Path(__file__)
    snapshot = BASE / 'tools/source_snapshots' / ('gf180_float_fixed_precision_rail_control_' + digest(source) + '.py')
    snapshot.write_bytes(source.read_bytes())
    files = [checkpoint, source, snapshot, args.calibration_report, *sorted((ROOT / 'src/eventspikeseg').rglob('*.py'))]
    report = {'simulation_completed': True, 'checkpoint_sha256': EXPECTED, 'checkpoint_epoch': 58,
              'record': {'sequence_id': sequence, 'frame_index': frame, 'validation_record_index': args.record_index},
              'input_sequence_sha256': tensor_digest(inputs), 'target_sha256': tensor_digest(target),
              'full_frame_shape': [440, 640], 'update_count': 10, 'bin_us': 5000, 'actor_count': 25, 'actor_state_counts': actor_state_counts,
              'precision_policy_actors_at3uv': precision_policies,
              'channel_observed_target_candidate_absmax': {name: value.flatten().tolist() for name, value in maxima.items()}, 'physical_half_range_v': args.headroom_v, 'results': rows,
              'calibration_records': calibration['records'],
              'channel_fixed_calibration_absmax': calibration['channel_fixed_calibration_absmax'],
              'clipping_applied_to_perturbed_cases_only': True,
              'scope': 'Near-zero1e-30uV candidate-noise control: fixed voltage-rail clipping is the material perturbation, isolating saturation from noise. Near-zero noise is added to each canonical actor candidate before threshold and subtractive reset at every update, propagating through recurrent state and adaptation. Original float checkpoint, no QAT, no quantization, no retraining. Perturbed cases include explicitly counted rail clipping. Fixed per-channel ranges from separate calibration records with nonzero threshold floors and guard margin; target maxima never set scale. Original baseline is unclipped; perturbed cases clamp candidate before threshold and stored membrane after reset/inhibition to model fixed voltage rails. Excursions counted even in baseline. Clipping is an ideal saturation surrogate, NOT implemented rail-limiter circuitry. Hypothetical input error sigma is NOT measured device distribution: continuous buffer spectra/ideal boxcar averaging do not establish sampled or independent read error. Excludes bias/nonlinearity/weight/storage/sampling/reference noise/PVT/correlations/service. Two records or three seeds do not qualify full validation accuracy or accepted tolerance. Perfect other operations. Software model replay, not full-model SPICE.',
              'qat_or_quantized_reference_used': False, 'original_float_accuracy_accepted': False,
              'complete_PLIF_accepted': False, 'full_5ms_population_service_accepted': False,
              'full_chip_accepted': False,
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in files}}
    destination = BASE / 'results' / (f'gf180_float_fixed_precision_rail_control_record{args.record_index}_src{digest(source)[:12]}.json')
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('REPORT ' + str(destination), flush=True)


if __name__ == '__main__':
    main()
