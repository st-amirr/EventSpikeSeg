"""Count exact nonzero PLIF states in full-frame original float inference."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch

from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
OUT = ROOT / "artifacts/analog_asic/results"
EXPECTED_SHA256 = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
EXPECTED_RESIDENT = 30_976_000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--record-indices", default="0,1")
    args = parser.parse_args()
    indices = [int(value) for value in args.record_indices.split(",")]
    if not indices or any(value < 0 for value in indices):
        raise ValueError("record indices must be nonnegative")
    torch.set_num_threads(2)
    digest = hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError("full-float checkpoint hash differs from active reference")
    checkpoint = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    if checkpoint["architecture"] != "EventSpikeSeg140k":
        raise RuntimeError("unexpected model")
    updates = int(checkpoint["temporal_protocol"]["internal_updates"])
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=updates)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.set_mechanism_scale(float(checkpoint.get("mechanism_scale", 1.0)))
    for module in model.modules():
        disable = getattr(module, "set_asic_qat_enabled", None)
        if callable(disable):
            disable(False)
    model.eval()
    neurons = [(name, module.neuron) for name, module in model.named_modules()
               if hasattr(module, "neuron") and hasattr(module.neuron, "_candidate_membrane")]
    if len(neurons) < 25:
        raise RuntimeError(f"fewer than 25 registered PLIF actors: {len(neurons)}")
    records = discover_dsec_records(args.dataset_root, "train")
    report_records = []
    for record_index in indices:
        sequence_id, frame_index = checkpoint["temporal_protocol"]["validation_record_ids"][record_index]
        matched = [row for row in records if row.sequence_id == sequence_id and row.frame_index == frame_index]
        if len(matched) != 1:
            raise RuntimeError(f"selected record unavailable: {sequence_id} frame {frame_index}")
        dataset = DSECRawEventDataset(args.dataset_root, split="train", output_size=(440, 640),
                                     internal_updates=updates, class_count=6, records=matched)
        events, _, _ = dataset[0]
        counts: dict[str, dict] = {}
        ever: dict[str, torch.Tensor] = {}
        handles = []

        def make_hook(actor_name: str):
            def observe(module, _inputs, _output):
                membrane = module.membrane.detach()
                active = membrane != 0
                if actor_name not in counts:
                    counts[actor_name] = {"shape": list(membrane.shape), "resident": membrane.numel(),
                                          "per_update_nonzero": []}
                    ever[actor_name] = torch.zeros_like(active, dtype=torch.bool)
                elif membrane.numel() != counts[actor_name]["resident"]:
                    raise RuntimeError(f"actor shape changed: {actor_name}")
                counts[actor_name]["per_update_nonzero"].append(int(active.sum().item()))
                ever[actor_name] |= active
            return observe

        for name, neuron in neurons:
            handles.append(neuron.register_forward_hook(make_hook(name)))
        try:
            with torch.inference_mode():
                model.reset()
                model(events.unsqueeze(1))
        finally:
            for handle in handles:
                handle.remove()
        if len(counts) != 25:
            raise RuntimeError(f"expected 25 executed PLIF actors, observed {len(counts)}")
        if any(len(row["per_update_nonzero"]) != updates for row in counts.values()):
            raise RuntimeError("actor update count differs from full temporal protocol")
        for name, row in counts.items():
            row["ever_nonzero"] = int(ever[name].sum().item())
            row["nonzero_fraction_by_update"] = [value / row["resident"] for value in row["per_update_nonzero"]]
            row["ever_nonzero_fraction"] = row["ever_nonzero"] / row["resident"]
        resident = sum(row["resident"] for row in counts.values())
        if resident != EXPECTED_RESIDENT:
            raise RuntimeError(f"full-frame resident inventory mismatch: {resident}")
        totals = [sum(row["per_update_nonzero"][t] for row in counts.values()) for t in range(updates)]
        report_records.append({
            "record_index": record_index, "sequence_id": sequence_id, "frame_index": frame_index,
            "resident_states": resident, "nonzero_by_update": totals,
            "nonzero_fraction_by_update": [value / resident for value in totals],
            "ever_nonzero_states": sum(row["ever_nonzero"] for row in counts.values()),
            "actors": counts,
        })
        print(json.dumps({"record_index": record_index,
                          "nonzero_fraction_by_update": report_records[-1]["nonzero_fraction_by_update"],
                          "ever_nonzero_states": report_records[-1]["ever_nonzero_states"]}))
    report = {
        "test": "eventspikeseg140k_original_float_full_frame_plif_state_occupancy",
        "checkpoint_sha256": digest, "checkpoint_epoch": checkpoint.get("epoch"),
        "qat_enabled": False, "full_frame": True, "update_count": updates,
        "inventory_states": EXPECTED_RESIDENT, "records": report_records,
        "registered_plif_modules": len(neurons), "executed_plif_actors": 25,
        "source_sha256": {str(CHECKPOINT.relative_to(ROOT)).replace("\\", "/"): digest,
                          str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"):
                              hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "limitations": "Only specified validation records. Exact-zero state is a software property, not a physical circuit state or safe sparse encoding. A sparse analog store would need lossless addressing, allocation, concurrent event service, per-actor isolation, read/write/reset/beta order and power/area qualification. This report does not validate such an architecture.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "sky130_float_fullframe_state_occupancy.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "records": len(report_records)}))


if __name__ == "__main__":
    main()
