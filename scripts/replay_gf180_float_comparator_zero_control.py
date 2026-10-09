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
    parser.add_argument('--record-index', type=int, default=0)
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
    state = {'sigma_uv': 0.0, 'collect_ranges': True}
    for name, neuron in neurons.items():
        def candidate(current, elapsed, _name=name, _base=original[name]):
            result = _base(current, elapsed)
            if state['collect_ranges']:
                observed = result.abs().amax(dim=(0, 2, 3), keepdim=True)
                maxima[_name] = observed if maxima[_name] is None else torch.maximum(maxima[_name], observed)
            return result
        neuron._candidate_membrane = candidate
        original_forward = neuron.forward
        def forward(current, elapsed_steps=1.0, update_mask=None, _name=name, _neuron=neuron, _original=original_forward):
            if not state['sigma_uv']:
                return _original(current, elapsed_steps, update_mask)
            assert not _neuron.asic_qat_enabled
            _neuron._ensure_state(current)
            elapsed = torch.as_tensor(elapsed_steps, device=current.device, dtype=current.dtype)
            from eventspikeseg.model_components import REFERENCE_NEURON_STEP_US
            _neuron.current_time_us = _neuron.current_time_us.to(current) + elapsed.detach() * REFERENCE_NEURON_STEP_US
            if update_mask is None:
                update_mask = torch.ones_like(current, dtype=torch.bool)
            else:
                update_mask = update_mask.to(device=current.device, dtype=torch.bool)
            if _neuron.config.inhibition_enabled and _neuron.config.inhibition_kind in {'peer_membrane', 'winner_peer'}:
                update_mask = update_mask.any(dim=1, keepdim=True).expand_as(current)
            elapsed_map = (_neuron.current_time_us - _neuron.last_update_us) / REFERENCE_NEURON_STEP_US
            _neuron._advance_threshold_adaptation(elapsed_map)
            updated = _neuron._candidate_membrane(current, elapsed_map)
            candidate = torch.where(update_mask, updated, _neuron.membrane)
            threshold = _neuron._threshold_tensor(current)
            sigma = state['sigma_uv'] * 1e-6 * maxima[_name] / args.headroom_v
            comparison_candidate = candidate + torch.randn_like(current) * sigma
            raw = _neuron.spike_function(comparison_candidate - threshold)
            above = (comparison_candidate >= threshold) & update_mask
            gate = _neuron._competition_gate(comparison_candidate, above)
            hard_spikes = raw * gate.to(raw.dtype)
            spikes = raw + (hard_spikes - raw).detach()
            reset = gate.to(candidate.dtype) * threshold
            loser = (above & ~gate).to(candidate.dtype) * _neuron.config.competitor_decrement
            _neuron.membrane = candidate - reset - loser
            _neuron.last_update_us = torch.where(update_mask, _neuron.current_time_us.expand_as(_neuron.last_update_us), _neuron.last_update_us)
            _neuron._apply_peer_membrane_inhibition(candidate, spikes)
            _neuron._update_threshold_adaptation(spikes, candidate, elapsed_map)
            return spikes
        neuron.forward = forward

    def metric(prediction):
        confusion = torch.bincount(target[valid].long() * 6 + prediction[valid].long(),
                                   minlength=36).reshape(6, 6)
        intersection = confusion.diagonal()
        union = confusion.sum(0) + confusion.sum(1) - intersection
        return float((intersection[union > 0] / union[union > 0]).float().mean()), confusion.tolist()

    rows = []
    baseline = None
    cases = [(0.0, None)] + [(float(sigma), int(seed)) for sigma in args.noise_uv.split(',')
                            for seed in args.seeds.split(',')]
    for sigma, seed in cases:
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
            row = {'comparator_error_sigma_uv': sigma, 'seed': seed,
                   'mean_iou': iou, 'pixel_change_fraction': float((prediction != baseline).float().mean()),
                   'confusion': confusion, 'runtime_seconds': time.monotonic() - started,
                   'prediction_sha256': tensor_digest(prediction)}
            rows.append(row)
            print(json.dumps(row), flush=True)
            del output
    source = Path(__file__)
    snapshot = BASE / 'tools/source_snapshots' / ('gf180_float_comparator_zero_control_' + digest(source) + '.py')
    snapshot.write_bytes(source.read_bytes())
    files = [checkpoint, source, snapshot, *sorted((ROOT / 'src/eventspikeseg').rglob('*.py'))]
    report = {'simulation_completed': True, 'checkpoint_sha256': EXPECTED, 'checkpoint_epoch': 58,
              'record': {'sequence_id': sequence, 'frame_index': frame, 'validation_record_index': args.record_index},
              'input_sequence_sha256': tensor_digest(inputs), 'target_sha256': tensor_digest(target),
              'full_frame_shape': [440, 640], 'update_count': 10, 'bin_us': 5000, 'actor_count': 25,
              'channel_oracle_candidate_absmax': {name: value.flatten().tolist() for name, value in maxima.items()}, 'physical_half_range_v': args.headroom_v, 'results': rows,
              'scope': 'Conditional independent Gaussian error ONLY in spike and competition comparison at every update; candidate accumulation, stored membrane, subtractive reset amplitude and adaptation-energy input remain noiseless. Noise changes spike decisions and thereby future recurrence/adaptation. Custom float forward preserves repository order and uses ordinary baseline forward when sigma0. This tests a direct charge-domain comparison hypothesis with ideal analog state arithmetic, not a complete circuit. Original float checkpoint, no QAT, no quantization, no retraining or clipping. Per-record baseline channel maxima define an optimistic oracle voltage scale; NOT implemented calibration. Hypothetical input error sigma is NOT measured device distribution: continuous buffer spectra/ideal boxcar averaging do not establish sampled or independent read error. Excludes bias/nonlinearity/weight/storage/sampling/reference noise/PVT/correlations/service. Two records or three seeds do not qualify full validation accuracy or accepted tolerance. Perfect other operations. Software model replay, not full-model SPICE.',
              'qat_or_quantized_reference_used': False, 'original_float_accuracy_accepted': False,
              'complete_PLIF_accepted': False, 'full_5ms_population_service_accepted': False,
              'full_chip_accepted': False,
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in files}}
    destination = BASE / 'results' / (f'gf180_float_comparator_zero_control_record{args.record_index}_src{digest(source)[:12]}.json')
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('REPORT ' + str(destination), flush=True)


if __name__ == '__main__':
    main()
