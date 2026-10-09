"""Collect fixed analog channel ranges from independent float calibration records."""
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
    parser.add_argument('--record-indices', default='0,1,2,3,4,5,6,7')
    parser.add_argument('--range-margin', type=float, default=1.25)
    parser.add_argument('--threshold-floor-multiple', type=float, default=4)
    args = parser.parse_args()
    indices = [int(value) for value in args.record_indices.split(',')]
    assert len(set(indices)) == len(indices) and args.range_margin >= 1 and args.threshold_floor_multiple > 0
    torch.set_num_threads(2)
    checkpoint = ROOT / 'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    assert digest(checkpoint) == EXPECTED
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    assert saved['architecture'] == 'EventSpikeSeg140k' and saved['epoch'] == 58
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
    maxima = {name: None for name in neurons}
    counts = {}
    thresholds = {}
    for name, neuron in neurons.items():
        thresholds[name] = neuron._base_threshold(torch.zeros(1, neuron.channels, 1, 1)).detach().flatten()
        original = neuron._candidate_membrane
        def capture(current, elapsed, _name=name, _original=original):
            result = _original(current, elapsed)
            counts[_name] = result.numel()
            observed = result.abs().amax(dim=(0, 2, 3), keepdim=True)
            maxima[_name] = observed if maxima[_name] is None else torch.maximum(maxima[_name], observed)
            return result
        neuron._candidate_membrane = capture
    all_records = discover_dsec_records(args.dataset_root, 'train')
    results = []
    for index in indices:
        sequence, frame = saved['temporal_protocol']['validation_record_ids'][index]
        records = [record for record in all_records if record.sequence_id == sequence and record.frame_index == frame]
        assert len(records) == 1
        dataset = DSECRawEventDataset(args.dataset_root, split='train', output_size=(440, 640),
                                    internal_updates=10, class_count=6, records=records)
        events, target, _ = dataset[0]
        inputs = events.unsqueeze(1)
        with torch.inference_mode():
            model.reset()
            started = time.monotonic()
            output = model(inputs)
            prediction = output['segmentation_logits'].argmax(1)[0].cpu()
            row = {'validation_record_index': index, 'sequence_id': sequence, 'frame_index': frame,
                   'input_sequence_sha256': tensor_digest(inputs), 'target_sha256': tensor_digest(target),
                   'prediction_sha256': tensor_digest(prediction), 'runtime_seconds': time.monotonic() - started}
            results.append(row)
            print(json.dumps(row), flush=True)
            del output
    ranges = {name: torch.maximum(maxima[name].flatten(), args.threshold_floor_multiple * thresholds[name]) * args.range_margin
              for name in neurons}
    assert all(torch.all(value > 0) for value in ranges.values())
    assert sum(counts.values()) == 30976000
    source = Path(__file__)
    configuration = {k: v for k, v in vars(args).items() if k != 'dataset_root'}
    stem = 'gf180_float_channel_calibration_' + hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()[:10] + '_src' + digest(source)[:12]
    snapshot = BASE / 'tools/source_snapshots' / (stem + '.py')
    snapshot.write_bytes(source.read_bytes())
    files = [checkpoint, source, snapshot, *sorted((ROOT / 'src/eventspikeseg').rglob('*.py'))]
    report = {'simulation_completed': True, 'checkpoint_sha256': EXPECTED, 'checkpoint_epoch': 58,
              'settings': configuration, 'records': results, 'actor_count': 25, 'actor_state_counts': counts,
              'channel_count': sum(value.numel() for value in ranges.values()),
              'channel_base_thresholds': {name: value.tolist() for name, value in thresholds.items()},
              'channel_observed_calibration_absmax': {name: value.flatten().tolist() for name, value in maxima.items()},
              'channel_fixed_calibration_absmax': {name: value.tolist() for name, value in ranges.items()},
              'scope': 'Original unmodified float model, no QAT/no retraining. Fixed channel ranges from listed calibration records only; max(abs candidate) and four-times-base-threshold floor, multiplied by fixed25percent guard margin. Floor prevents zero ranges, not global range certification. These records belong to validation-listed sequence IDs and are now used for calibration; separate records required for evaluation. Target-record ranges must not modify calibration. No physical reference/range-gain delivery, no rail/noise/service/accuracy acceptance.',
              'original_float_accuracy_accepted': False, 'complete_PLIF_accepted': False,
              'full_chip_accepted': False,
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in files}}
    destination = BASE / 'results' / (stem + '.json')
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('REPORT ' + str(destination), flush=True)


if __name__ == '__main__':
    main()
