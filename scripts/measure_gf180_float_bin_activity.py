"""Measure actual per-bin connectivity demand without changing float inference."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
EXPECTED = 'c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tsha(tensor):
    return hashlib.sha256(tensor.detach().cpu().contiguous().numpy().tobytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(2)
    checkpoint = ROOT / 'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    assert sha(checkpoint) == EXPECTED
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    assert saved['epoch'] == 58
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=10)
    model.load_state_dict(saved['model_state_dict'], strict=True)
    model.set_mechanism_scale(float(saved.get('mechanism_scale', 1)))
    model.eval()
    for module in model.modules():
        toggle = getattr(module, 'set_asic_qat_enabled', None)
        if callable(toggle):
            toggle(False)
    named = dict(model.named_modules())
    activity = {}
    for name in [*EVENTSPIKESEG140K_INFERENCE_STAGES, 'head']:
        def before(module, inputs, name=name):
            seq = inputs[0]
            t, n = seq.shape[:2]
            assert t == 10 and n == 1
            flat = seq.reshape(t*n, *seq.shape[2:]).float()
            assert bool((flat >= 0).all()) and torch.equal(flat, flat.round())
            conv = module.synapse if name == 'head' else module.conv
            counts = F.conv2d(flat, torch.ones((conv.groups, conv.in_channels//conv.groups, *conv.kernel_size)),
                              stride=conv.stride, padding=conv.padding, dilation=conv.dilation,
                              groups=conv.groups).reshape(t, n, conv.groups, -1)
            per_group = conv.out_channels // conv.groups
            per_bin = [int(value) * per_group for value in counts.sum(dim=(1,2,3), dtype=torch.float64).tolist()]
            destinations = counts[0].numel() * per_group
            activity[name] = {
                'weighted_deliveries_by_bin': per_bin,
                'weighted_event_deliveries': sum(per_bin),
                'peak_bin_weighted_deliveries': max(per_bin),
                'max_events_per_destination_per_bin': int(counts.max()),
                'destinations': destinations,
                'is_PLIF_population': name != 'head',
            }
        named[name].register_forward_pre_hook(before)
    source = Path(__file__)
    source_hash = sha(source)
    all_records = discover_dsec_records(args.dataset_root, 'train')
    for index in [8, 64]:
        stem = f'gf180_float_bin_activity_record{index}_src{source_hash[:12]}'
        target_report = BASE / 'results' / (stem + '.json')
        assert not target_report.exists(), 'Preserve prior evidence; do not overwrite'
        sequence, frame = saved['temporal_protocol']['validation_record_ids'][index]
        records = [r for r in all_records if r.sequence_id == sequence and r.frame_index == frame]
        assert len(records) == 1
        dataset = DSECRawEventDataset(args.dataset_root, split='train', output_size=(440,640),
                                     internal_updates=10, class_count=6, records=records)
        events, target, _ = dataset[0]
        inputs = events.unsqueeze(1)
        activity.clear()
        start = time.monotonic()
        with torch.inference_mode():
            model.reset()
            output = model(inputs)
            prediction = output['segmentation_logits'].argmax(1)[0].cpu()
        assert len(activity) == 26
        prior_path = BASE / 'results' / f'replay_gf180_packet_state_bias_record{index}_srcfc94fbe1c2da.json'
        prior = json.loads(prior_path.read_text(encoding='utf-8'))
        assert tsha(inputs) == prior['input_sequence_sha256']
        assert tsha(target) == prior['target_sha256']
        assert tsha(prediction) == prior['results'][0]['prediction_sha256']
        for name, row in prior['results'][0]['activity'].items():
            assert activity[name]['weighted_event_deliveries'] == row['weighted_event_deliveries']
            assert activity[name]['destinations'] * 10 == row['state_updates']
        total = [sum(row['weighted_deliveries_by_bin'][i] for row in activity.values()) for i in range(10)]
        snap = BASE / 'tools/source_snapshots' / (stem + '.py')
        snap.write_bytes(source.read_bytes())
        files = [source, snap, checkpoint, prior_path, *sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]
        report = {
            'measurement_completed': True, 'checkpoint_sha256': EXPECTED,
            'record_index': index, 'sequence': sequence, 'frame': frame,
            'input_sequence_sha256': tsha(inputs), 'target_sha256': tsha(target),
            'prediction_sha256': tsha(prediction), 'prior_baseline_reproduced': True,
            'runtime_seconds': time.monotonic()-start,
            'activity': dict(activity), 'total_weighted_deliveries_by_bin_including_readout': total,
            'peak_bin_weighted_deliveries_including_readout': max(total),
            'scope': 'Original-float unchanged inference, QAT off. Integer connectivity deliveries include raw and skip multiplicity and all connections, including zero weights; no pruning assumed. Includes continuous current head, absent from earlier 25-actor totals. Two same-sequence records only; not worst-case dataset activity. Per-bin workload is not a schedule or proof of 5ms DAG service. No physical simulation or noise qualification.',
            'qat_or_quantized_reference_used': False, 'full_5ms_population_service_accepted': False,
            'full_chip_accepted': False,
            'sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in files},
        }
        target_report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'report': str(target_report), 'peak_bin_deliveries': max(total),
                          'baseline_reproduced': True}), flush=True)
        del output

if __name__ == '__main__':
    main()
