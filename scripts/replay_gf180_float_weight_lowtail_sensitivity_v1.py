"""One-record float-model sensitivity to the measured analog low-tail gain error."""
import hashlib
import json
import time
from pathlib import Path

import torch
from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
from eventspikeseg.model_components import ChannelAffine, SpikingStage

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
EXPECTED = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tensor_digest(value: torch.Tensor) -> str:
    return hashlib.sha256(value.detach().contiguous().cpu().numpy().tobytes()).hexdigest()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--record-index", type=int, default=0)
    parser.add_argument("--normalized-cut", type=float, default=1e-3)
    parser.add_argument("--measured-lowtail-gain", type=float, default=1.2910798122074047)
    args = parser.parse_args()
    torch.set_num_threads(2)

    checkpoint = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
    assert digest(checkpoint) == EXPECTED
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    assert state["architecture"] == "EventSpikeSeg140k" and state["epoch"] == 58
    sequence, frame = state["temporal_protocol"]["validation_record_ids"][args.record_index]
    records = [r for r in discover_dsec_records(args.dataset_root, "train") if r.sequence_id == sequence and r.frame_index == frame]
    assert len(records) == 1
    dataset = DSECRawEventDataset(
        args.dataset_root,
        split="train",
        output_size=(440, 640),
        internal_updates=10,
        class_count=6,
        records=records,
    )
    events, target, _ = dataset[0]
    inputs = events.unsqueeze(1)
    valid = target != 255

    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=10)
    model.load_state_dict(state["model_state_dict"], strict=True)
    model.set_mechanism_scale(float(state.get("mechanism_scale", 1)))
    for module in model.modules():
        disable_qat = getattr(module, "set_asic_qat_enabled", None)
        if callable(disable_qat):
            disable_qat(False)
    model.eval()
    named = dict(model.named_modules())
    actors = [(name, named[name]) for name in EVENTSPIKESEG140K_INFERENCE_STAGES]
    assert len(actors) == 25 and all(isinstance(module, SpikingStage) for _, module in actors)
    original = {name: module.conv.weight.detach().clone() for name, module in actors}

    def score(prediction: torch.Tensor):
        truth = target[valid].long()
        pred = prediction[valid].long()
        confusion = torch.bincount(truth * 6 + pred, minlength=36).reshape(6, 6)
        intersection = confusion.diagonal()
        union = confusion.sum(0) + confusion.sum(1) - intersection
        present = union > 0
        return float((intersection[present] / union[present]).float().mean()), confusion.tolist()

    def infer():
        start = time.monotonic()
        with torch.inference_mode():
            model.reset()
            output = model(inputs)
        prediction = output["segmentation_logits"].argmax(1)[0].cpu()
        metric, confusion = score(prediction)
        runtime = time.monotonic() - start
        del output
        return prediction, metric, confusion, runtime

    baseline, baseline_iou, baseline_confusion, baseline_seconds = infer()
    affected_count = 0
    affected_tensors = 0
    for name, module in actors:
        weights = original[name]
        maximum = weights.abs().amax()
        low = (weights.abs() / maximum) < args.normalized_cut
        affected_count += int(low.sum())
        affected_tensors += int(bool(low.any()))
        # Keep every float coefficient nonzero and preserve sign. This perturbation
        # models the measured +29.1% q0.1 response as a continuous low-tail gain;
        # it is a sensitivity screen, not a source-cell transfer/noise model.
        with torch.no_grad():
            module.conv.weight.copy_(weights * torch.where(low, args.measured_lowtail_gain, 1.0))
    perturbed, perturbed_iou, perturbed_confusion, perturbed_seconds = infer()

    report = {
        "simulation_completed": True,
        "checkpoint_sha256": EXPECTED,
        "checkpoint_epoch": 58,
        "record": {"sequence_id": sequence, "frame_index": frame, "validation_record_index": args.record_index},
        "full_frame_shape": [440, 640],
        "update_count": 10,
        "bin_us": 5000,
        "actor_count": 25,
        "normalized_weight_cut_for_sensitivity_only": args.normalized_cut,
        "weights_perturbed": affected_count,
        "weight_count": sum(weight.numel() for weight in original.values()),
        "affected_tensors": affected_tensors,
        "continuous_lowtail_gain": args.measured_lowtail_gain,
        "original_float_weights_preserved_nonzero_and_signed": True,
        "baseline": {
            "mean_iou": baseline_iou,
            "confusion": baseline_confusion,
            "prediction_sha256": tensor_digest(baseline),
            "runtime_seconds": baseline_seconds,
        },
        "lowtail_analog_gain_sensitivity": {
            "mean_iou": perturbed_iou,
            "mean_iou_delta": perturbed_iou - baseline_iou,
            "pixel_change_fraction": float((perturbed != baseline).float().mean()),
            "confusion": perturbed_confusion,
            "prediction_sha256": tensor_digest(perturbed),
            "runtime_seconds": perturbed_seconds,
        },
        "qat_or_quantized_reference_used": False,
        "readout_weights_modified": False,
        "scope": "One validation-listed full-frame record, all25 original-float actors and10 temporal updates. Only weights below the per-tensor normalized cut receive the measured q0.1 analog transfer gain error (+29.1%); all remain continuous, nonzero and signed. This isolates low-tail sensitivity but extrapolates one measured point uniformly below the cut and is not a measured device transfer, cross-record accuracy, noise/PVT, addressed storage, full physical service, or acceptance result.",
        "original_float_accuracy_accepted": False,
        "full_5ms_population_service_accepted": False,
        "full_chip_accepted": False,
    }
    src = Path(__file__)
    snapshots = BASE / "tools/source_snapshots"
    snapshots.mkdir(parents=True, exist_ok=True)
    snap = snapshots / ("gf180_float_lowtail_sensitivity_" + digest(src) + ".py")
    snap.write_bytes(src.read_bytes())
    sources = [checkpoint, src, snap, *sorted((ROOT / "src/eventspikeseg").rglob("*.py"))]
    report["sha256"] = {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}
    dest = BASE / "results" / f"gf180_float_weight_lowtail_sensitivity_record{args.record_index}_src{digest(src)[:12]}.json"
    dest.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(dest), "weights_perturbed": affected_count, "baseline_mean_iou": baseline_iou, "sensitivity_mean_iou": perturbed_iou, "mean_iou_delta": perturbed_iou - baseline_iou, "pixel_change_fraction": report["lowtail_analog_gain_sensitivity"]["pixel_change_fraction"]}, indent=2))


if __name__ == "__main__":
    main()
