"""Measure original-float accuracy effects of current per-8x8 capacitor rails."""
import hashlib
import json
from pathlib import Path

import torch

from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def load_model(checkpoint):
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=10)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.set_mechanism_scale(float(checkpoint.get("mechanism_scale", 1.0)))
    for module in model.modules():
        disable = getattr(module, "set_asic_qat_enabled", None)
        if callable(disable):
            disable(False)
    model.eval()
    return model


def metrics(pred, target):
    valid = target != 255
    confusion = torch.bincount(target[valid].long() * 6 + pred[valid].long(), minlength=36).reshape(6, 6)
    intersection = confusion.diagonal()
    union = confusion.sum(0) + confusion.sum(1) - intersection
    present = union > 0
    return {
        "labeled_pixel_accuracy": float((pred[valid] == target[valid]).float().mean()),
        "present_class_mean_iou": float((intersection[present] / union[present]).float().mean()),
        "valid_pixels": int(valid.sum()),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--training-record-index", type=int, default=0)
    args = parser.parse_args()
    torch.set_num_threads(2)
    checkpoint_path = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
    checkpoint_sha = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    if checkpoint_sha != EXPECTED:
        raise RuntimeError("active full-float checkpoint hash mismatch")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    training_ids = checkpoint["temporal_protocol"]["training_record_ids"]
    sequence_id, frame_index = training_ids[args.training_record_index]
    records = [r for r in discover_dsec_records(args.dataset_root, "train")
               if r.sequence_id == sequence_id and r.frame_index == frame_index]
    if len(records) != 1:
        raise RuntimeError(f"expected one record, found {len(records)}")
    dataset = DSECRawEventDataset(args.dataset_root, split="train", output_size=(440, 640),
                                  internal_updates=10, class_count=6, records=records)
    events, target, _ = dataset[0]
    sequence = events.unsqueeze(1)
    calibration_path = ROOT / "artifacts/analog_asic/results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json"
    calibration = json.loads(calibration_path.read_text(encoding="utf8"))
    named = dict(load_model(checkpoint).named_modules())
    ranges = {}
    for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        bank = torch.tensor(calibration["state_tile8_ranges"][name][0], dtype=torch.float32).squeeze(0)
        ranges[name] = bank.repeat_interleave(8, 1).repeat_interleave(8, 2)

    outputs = {}
    clip_stats = {"candidate": {}, "stored_state": {}}
    for mode in ("baseline", "candidate_clip", "stored_state_clip"):
        model = load_model(checkpoint)
        actors = dict(model.named_modules())
        restores = []
        if mode != "baseline":
            for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
                neuron = actors[name].neuron
                bound = ranges[name]
                original_candidate = neuron._candidate_membrane
                original_forward = neuron.forward
                stats = {"clipped": 0, "total": 0}
                if mode == "candidate_clip":
                    def candidate(current, elapsed, *, _orig=original_candidate, _bound=bound, _stats=stats):
                        value = _orig(current, elapsed)
                        b = _bound.to(value)[None, :value.shape[1], :value.shape[2], :value.shape[3]]
                        clipped = value.clamp(min=-b, max=b)
                        _stats["clipped"] += int((clipped != value).sum())
                        _stats["total"] += value.numel()
                        return clipped
                    neuron._candidate_membrane = candidate
                    restores.append((neuron, "_candidate_membrane", original_candidate))
                    clip_stats["candidate"][name] = stats
                else:
                    def forward(current, *fargs, _orig=original_forward, _bound=bound, _stats=stats, _neuron=neuron, **kwargs):
                        spikes = _orig(current, *fargs, **kwargs)
                        state = _neuron.membrane
                        b = _bound.to(state)[None, :state.shape[1], :state.shape[2], :state.shape[3]]
                        clipped = state.clamp(min=-b, max=b)
                        _stats["clipped"] += int((clipped != state).sum())
                        _stats["total"] += state.numel()
                        _neuron.membrane = clipped
                        return spikes
                    neuron.forward = forward
                    restores.append((neuron, "forward", original_forward))
                    clip_stats["stored_state"][name] = stats
        with torch.inference_mode():
            output = model(sequence)
        for obj, attr, original in restores:
            setattr(obj, attr, original)
        outputs[mode] = output["segmentation_logits"].argmax(dim=1).squeeze(0).cpu()

    baseline = outputs["baseline"]
    report = {
        "simulation_completed": True,
        "checkpoint_sha256": checkpoint_sha,
        "qat_or_quantized_reference_used": False,
        "record": {"sequence_id": sequence_id, "frame_index": frame_index},
        "range_source": str(calibration_path.relative_to(ROOT)).replace("\\", "/"),
        "baseline": metrics(baseline, target),
        "modes": {},
        "scope": "One full training frame, original epoch58 float inference. candidate_clip clamps pre-threshold candidate; stored_state_clip clamps post-reset capacitor state before the next update. Ideal clipping surrogates, not transistor-level accuracy or noise results.",
    }
    for mode in ("candidate_clip", "stored_state_clip"):
        pred = outputs[mode]
        m = metrics(pred, target)
        m["delta_present_class_mean_iou"] = m["present_class_mean_iou"] - report["baseline"]["present_class_mean_iou"]
        m["prediction_pixel_change_fraction"] = float((pred != baseline).float().mean())
        report["modes"][mode] = m
    report["clipping"] = {
        mode: {name: {"fraction": row["clipped"] / max(row["total"], 1), **row}
               for name, row in actors.items()}
        for mode, actors in clip_stats.items()
    }
    out = ROOT / f"artifacts/analog_asic/results/gf180_train_record_voltage_range_saturation_v1_record{args.training_record_index}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"report": str(out), "record": report["record"],
                      "baseline": report["baseline"], "modes": report["modes"]}, indent=2))


if __name__ == "__main__":
    main()
