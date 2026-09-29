"""Replay bounded state/reset and comparator-noise proxies through the full-float model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
TRACE = ROOT / "artifacts/analog_asic/model_reference/float_patch_trace.npz"
OUT = ROOT / "artifacts/analog_asic/results/sky130_ms_diff_task_sensitivity.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--record-source', choices=('training', 'validation'), default='training')
    parser.add_argument('--record-index', type=int, default=0)
    parser.add_argument('--noise-mode', choices=('init-only', 'first-event', 'reset-only', 'comparator-only', 'both'),
                        default='reset-only')
    parser.add_argument('--mim-width-um', type=float, default=20.0)
    parser.add_argument('--headroom-v', type=float, default=0.15)
    parser.add_argument('--noise-topology', choices=('independent_pair', 'single_differential_cap'),
                        default='independent_pair')
    parser.add_argument('--full-frame', action='store_true',
                        help='evaluate the complete selected 440x640 record once')
    parser.add_argument('--noise-scope', choices=('final-fuse', 'all-neurons'),
                        default='final-fuse')
    parser.add_argument('--noise-sigma-uv', type=float, default=0.0,
                        help='optional injected noise override; 0 uses the selected MIM kT/C model')
    parser.add_argument('--zero-noise', action='store_true',
                        help='verify that the replay preserves the original float trajectory')
    args = parser.parse_args()
    torch.set_num_threads(2)
    digest = hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()
    checkpoint = torch.load(CHECKPOINT, map_location='cpu', weights_only=True)
    if checkpoint.get('architecture') != 'EventSpikeSeg140k':
        raise ValueError('unexpected checkpoint architecture')
    updates = int(checkpoint['temporal_protocol']['internal_updates'])
    record_ids = checkpoint['temporal_protocol'][f'{args.record_source}_record_ids']
    if not 0 <= args.record_index < len(record_ids):
        raise ValueError('record index outside checkpoint record list')
    sequence_id, frame_index = record_ids[args.record_index]
    records = [record for record in discover_dsec_records(args.dataset_root, 'train')
               if record.sequence_id == sequence_id and record.frame_index == frame_index]
    if len(records) != 1:
        raise ValueError(f'expected one selected DSEC record, got {len(records)}')
    dataset = DSECRawEventDataset(args.dataset_root, split='train', output_size=(440, 640),
                                 internal_updates=updates, class_count=6, records=records)
    events, target_mask, _ = dataset[0]
    if args.full_frame:
        selected = [(float(events.sum()), 0, 0)]
        input_sequence = events.unsqueeze(1)
        selected_target = target_mask.unsqueeze(0)
    else:
        size = 64
        tiles = [(float(events[:, :, y:y+size, x:x+size].sum()), y, x)
                 for y in range(0, events.shape[-2]-size+1, size)
                 for x in range(0, events.shape[-1]-size+1, size)]
        tiles.sort()
        selected = [tiles[0], tiles[len(tiles)//2], tiles[-1]]
        input_sequence = torch.stack([events[:, :, y:y+size, x:x+size] for _, y, x in selected], dim=1)
        selected_target = torch.stack([target_mask[y:y+size, x:x+size] for _, y, x in selected])
    valid = selected_target != 255
    def class_iou(prediction: torch.Tensor) -> tuple[list[float | None], float]:
        class_count = 6
        target = selected_target[valid].to(torch.int64)
        predicted = prediction[valid].to(torch.int64)
        confusion = torch.bincount(target * class_count + predicted,
                                   minlength=class_count * class_count).reshape(class_count, class_count)
        intersection = confusion.diagonal()
        union = confusion.sum(dim=0) + confusion.sum(dim=1) - intersection
        values = [float(intersection[index] / union[index]) if union[index] else None
                  for index in range(class_count)]
        present = [value for value in values if value is not None]
        return values, float(np.mean(present)) if present else float('nan')
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=updates)
    model.load_state_dict(checkpoint['model_state_dict'], strict=True)
    model.set_mechanism_scale(float(checkpoint.get('mechanism_scale', 1.0)))
    for module in model.modules():
        disable = getattr(module, 'set_asic_qat_enabled', None)
        if callable(disable):
            disable(False)
    model.eval()
    stage = dict(model.named_modules())['final_fuse.standard']
    neuron_modules = [(name, module.neuron) for name, module in model.named_modules()
                      if hasattr(module, 'neuron') and hasattr(module.neuron, '_candidate_membrane')]
    noise_modules = ([(name, neuron) for name, neuron in neuron_modules
                      if name == 'final_fuse.standard'] if args.noise_scope == 'final-fuse'
                     else neuron_modules)
    candidate_max_by_name: dict[str, float] = {}
    saved_candidates = {}
    for name, neuron in noise_modules:
        original_candidate = neuron._candidate_membrane
        saved_candidates[name] = original_candidate
        def capture_candidate(current, elapsed, *, _name=name, _original=original_candidate):
            candidate = _original(current, elapsed)
            value = float(candidate.detach().abs().max().cpu())
            candidate_max_by_name[_name] = max(candidate_max_by_name.get(_name, 0.0), value)
            return candidate
        neuron._candidate_membrane = capture_candidate
    reference_spikes = []
    handle = stage.neuron.register_forward_hook(
        lambda _m, _i, out: reference_spikes.append(out.detach().cpu().bool().clone()))
    with torch.inference_mode():
        model.reset()
        base = model(input_sequence)
    for name, neuron in noise_modules:
        neuron._candidate_membrane = saved_candidates[name]
    handle.remove()
    noise_modules = [(name, neuron) for name, neuron in noise_modules
                     if candidate_max_by_name.get(name, 0.0) > 0.0]
    base_mask = base['segmentation_logits'].argmax(dim=1).detach().cpu()
    base_valid_accuracy = float((base_mask[valid] == selected_target[valid]).float().mean())
    baseline_per_class_iou, baseline_mean_iou = class_iou(base_mask)
    base_spikes = torch.stack(reference_spikes)
    trace = np.load(TRACE)
    headroom_v = args.headroom_v
    if headroom_v <= 0:
        raise ValueError('headroom must be positive')
    if args.mim_width_um <= 0:
        raise ValueError('MIM width must be positive')
    cap_f = (2.0*args.mim_width_um**2 + 0.19*4*args.mim_width_um)*1e-15
    cap_noise_factor = 2.0 if args.noise_topology == 'independent_pair' else 1.0
    sigma_v = (0.0 if args.zero_noise else args.noise_sigma_uv*1e-6 if args.noise_sigma_uv > 0 else
               float(np.sqrt(cap_noise_factor*1.380649e-23*300/cap_f)))
    sigma_units_by_name = {name: sigma_v / (headroom_v / candidate_max_by_name[name])
                           for name, _ in noise_modules if candidate_max_by_name.get(name, 0) > 0}
    original_forwards = {name: neuron.forward for name, neuron in noise_modules}
    original_thresholds = {name:neuron._threshold_tensor for name, neuron in noise_modules}
    cases = []
    for seed in (1729, 1730, 1731):
        torch.manual_seed(seed)
        first = [True]
        captured = []
        touch_masks = []

        for name, neuron in noise_modules:
            first = [True]
            touched = [None]
            touch_masks.append(touched)
            original_forward = original_forwards[name]
            sigma_units = sigma_units_by_name[name]
            def noisy_forward(current, *forward_args, _neuron=neuron, _first=first,
                              _touched=touched, _original=original_forward,
                              _sigma=sigma_units, **forward_kwargs):
                if _first[0]:
                    _neuron._ensure_state(current)
                    if args.noise_mode in ('init-only', 'reset-only', 'both'):
                        _neuron.membrane = _neuron.membrane + torch.randn_like(current)*_sigma
                    if args.noise_mode == 'first-event':
                        _touched[0] = torch.zeros_like(current, dtype=torch.bool)
                    _first[0] = False
                if args.noise_mode == 'first-event':
                    active = current != 0
                    update_mask = forward_kwargs.get('update_mask')
                    if update_mask is not None:
                        active = active & update_mask.to(dtype=torch.bool, device=current.device)
                    newly_touched = active & ~_touched[0]
                    _neuron.membrane = _neuron.membrane + torch.randn_like(current)*_sigma*newly_touched
                    _touched[0] = _touched[0] | active
                spikes = _original(current, *forward_args, **forward_kwargs)
                if args.noise_mode in ('reset-only', 'both'):
                    reset_noise = torch.randn_like(current)*_sigma
                    # The float PLIF uses subtractive reset. Preserve its actual
                    # post-reset state and add capacitor noise to that state.
                    _neuron.membrane = torch.where(spikes.bool(), _neuron.membrane + reset_noise,
                                                   _neuron.membrane)
                return spikes
            neuron.forward = noisy_forward
        def capture_noisy_final(_module, _inputs, output):
            captured.append(output.detach().cpu().bool().clone())
        noisy_handle = stage.neuron.register_forward_hook(capture_noisy_final)
        if args.noise_mode in ('comparator-only', 'both'):
            for name, neuron in noise_modules:
                original_threshold = original_thresholds[name]
                sigma_units = sigma_units_by_name[name]
                neuron._threshold_tensor = lambda current, _original=original_threshold, _sigma=sigma_units: (
                    _original(current) + torch.randn_like(current)*_sigma)
        with torch.inference_mode():
            model.reset()
            got = model(input_sequence)
        got_mask = got['segmentation_logits'].argmax(dim=1).detach().cpu()
        got_spikes = torch.stack(captured)
        per_class_iou, present_class_mean_iou = class_iou(got_mask)
        cases.append({'seed': seed,
                      'first_event_touched_fraction': (
                          sum(mask[0].sum().item() for mask in touch_masks) /
                          sum(mask[0].numel() for mask in touch_masks)
                          if args.noise_mode == 'first-event' else None),
                      'final_fuse_spike_mismatch': float((got_spikes != base_spikes).float().mean()),
                      'segmentation_pixel_argmax_agreement': float((got_mask == base_mask).float().mean()),
                      'labeled_pixel_accuracy': float((got_mask[valid] == selected_target[valid]).float().mean()),
                      'per_class_iou': per_class_iou,
                      'present_class_mean_iou': present_class_mean_iou,
                      'segmentation_logit_abs_diff_p99': float(torch.quantile(
                          (got['segmentation_logits'].detach().cpu()-base['segmentation_logits'].detach().cpu()).abs().flatten(),
                          torch.tensor(0.99)))})
        noisy_handle.remove()
        for name, neuron in noise_modules:
            neuron.forward = original_forwards[name]
        for name, neuron in noise_modules:
            neuron._threshold_tensor = original_thresholds[name]
    if args.zero_noise and any(trial['final_fuse_spike_mismatch'] != 0.0 or
                               trial['segmentation_pixel_argmax_agreement'] != 1.0 or
                               trial['segmentation_logit_abs_diff_p99'] != 0.0 for trial in cases):
        raise RuntimeError('zero-noise replay changed the float trajectory')
    report = {'test':'sky130_mim_ota_noise_full_float_task_sensitivity',
              'checkpoint_sha256': digest, 'qat_or_quantized_reference_used': False,
              'record_source': args.record_source, 'record_index': args.record_index,
              'noise_mode': args.noise_mode,
              'noise_scope':args.noise_scope,
              'noise_neuron_count':len(noise_modules),
              'injected_noise_sigma_uv':sigma_v*1e6,
              'full_frame':args.full_frame,
              'mim_width_um':args.mim_width_um,
              'noise_topology':args.noise_topology,
              'reset_noise_preserves_subtractive_state':True,
              'sequence_id': sequence_id, 'frame_index': frame_index,
              'selected_patch_yx': [[int(y), int(x)] for _, y, x in selected],
              'valid_labeled_pixel_count': int(valid.sum()),
              'baseline_labeled_pixel_accuracy': base_valid_accuracy,
              'baseline_per_class_iou': baseline_per_class_iou,
              'baseline_present_class_mean_iou': baseline_mean_iou,
              'headroom_v': headroom_v, 'pair_kTC_sigma_uv': sigma_v*1e6,
              'noise_source':'zero-noise control' if args.zero_noise else
                             'explicit noise override' if args.noise_sigma_uv > 0 else
                             'independent MIM pair kT/C proxy',
              'trials': cases,
              'scope':('Full original float model on one complete 440x640 DSEC record.' if args.full_frame
                       else 'Full original float model on three selected64x64 patches from one DSEC record.')
                      + (' Independent Gaussian state kT/C is applied at initialization and post-spike reset to all active PLIF populations.'
                         if args.noise_scope == 'all-neurons' and args.noise_mode in ('reset-only', 'both')
                         else ' Independent Gaussian state perturbation is applied only on each location\'s first nonzero current with an active update mask; untouched locations remain clamped to the model zero state. Exact-zero cancellation of nonzero physical events is not represented.'
                         if args.noise_mode == 'first-event'
                         else ' Independent Gaussian state perturbation is applied once at initialization to all active PLIF populations; subtractive spike reset adds no fresh perturbation.'
                         if args.noise_scope == 'all-neurons' and args.noise_mode == 'init-only'
                         else ' Independent Gaussian state kT/C is applied at final_fuse.standard initialization and post-spike reset.'
                         if args.noise_mode in ('reset-only', 'both')
                         else ' Independent Gaussian state perturbation is applied once at final_fuse.standard initialization.'
                         if args.noise_mode == 'init-only' else '')
                      + ((' Per-update Gaussian threshold noise is applied at all active PLIF populations.'
                          if args.noise_scope == 'all-neurons' else
                          ' Per-update Gaussian threshold noise is applied at final_fuse.standard.')
                         if args.noise_mode in ('comparator-only', 'both') else '')
                      + (' The explicit noise override is a software proxy; temporal sampling/correlation and closed-loop effects are not modeled.'
                         if args.noise_sigma_uv > 0 else
                         ' Noise is an ideal Gaussian MIM kT/C proxy, not extracted transistor transient noise.')
                      + ' Spatial/temporal correlations, PVT and mismatch are excluded.'}
    output = OUT.with_name(f'{OUT.stem}_{args.record_source}_{args.record_index}_'
                           f'{args.noise_mode.replace("-", "_")}_{args.noise_topology}_mim{args.mim_width_um:g}um_'
                           f'{"full" if args.full_frame else "patches"}_'
                           f'{args.noise_scope.replace("-", "_")}_'
                           f'n{sigma_v*1e6:g}uv_h{args.headroom_v:g}v_corrected_subtractive_reset{OUT.suffix}')
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
