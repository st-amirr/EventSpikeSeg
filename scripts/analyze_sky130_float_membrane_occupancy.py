"""Count exact nonzero full-float PLIF membranes after each 5 ms update."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--record-index", type=int, default=0)
    args = parser.parse_args()
    torch.set_num_threads(2)
    digest = hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()
    expected = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
    if digest != expected:
        raise RuntimeError("unexpected float checkpoint hash")
    checkpoint = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    updates = int(checkpoint["temporal_protocol"]["internal_updates"])
    record_ids = checkpoint["temporal_protocol"]["validation_record_ids"]
    if not 0 <= args.record_index < len(record_ids):
        raise ValueError("record index outside validation list")
    sequence_id, frame_index = record_ids[args.record_index]
    records = [record for record in discover_dsec_records(args.dataset_root, "train")
               if record.sequence_id == sequence_id and record.frame_index == frame_index]
    if len(records) != 1:
        raise RuntimeError(f"expected one DSEC record, got {len(records)}")
    dataset = DSECRawEventDataset(args.dataset_root, split="train", output_size=(440, 640),
                                 internal_updates=updates, class_count=6, records=records)
    events, _, _ = dataset[0]
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
    observations: dict[str, list[dict]] = {name: [] for name, _ in neurons}
    handles = []
    for name, neuron in neurons:
        def capture(module, inputs, output, *, _name=name):
            current = inputs[0]
            membrane = module.membrane
            observations[_name].append({
                "states": membrane.numel(),
                "nonzero_membranes": int(torch.count_nonzero(membrane).item()),
                "nonzero_currents": int(torch.count_nonzero(current).item()),
                "spikes": int(torch.count_nonzero(output).item()),
            })
        handles.append(neuron.register_forward_hook(capture))
    with torch.inference_mode():
        model.reset()
        model(events.unsqueeze(1))
    for handle in handles:
        handle.remove()
    # The Python module tree also contains training-only aux_head.stage.
    neurons = [(name, neuron) for name, neuron in neurons if observations[name]]
    observations = {name: observations[name] for name, _ in neurons}
    calls = {name: len(rows) for name, rows in observations.items()}
    if len(neurons) != 25 or any(count != updates for count in calls.values()):
        raise RuntimeError(f"PLIF inventory or per-update observation count differs: "
                           f"actors={len(neurons)}, expected_updates={updates}, "
                           f"observed_calls={calls}")
    per_update = []
    for update in range(updates):
        rows = [observations[name][update] for name, _ in neurons]
        totals = {key: sum(row[key] for row in rows) for key in
                  ("states", "nonzero_membranes", "nonzero_currents", "spikes")}
        totals["update_index"] = update
        totals["nonzero_membrane_fraction"] = totals["nonzero_membranes"] / totals["states"]
        totals["nonzero_current_fraction"] = totals["nonzero_currents"] / totals["states"]
        per_update.append(totals)
    report = {
        "test": "sky130_float_exact_nonzero_membrane_occupancy",
        "checkpoint_sha256": digest, "qat_or_quantized_reference_used": False,
        "record_index": args.record_index, "sequence_id": sequence_id,
        "frame_index": frame_index, "actor_count": len(neurons),
        "logical_membrane_count": per_update[0]["states"],
        "per_update": per_update, "per_actor": observations,
        "scope": "One full 440x640 float validation record, ten 5ms updates. Exact software zero is a necessary condition for lossless sparse membrane storage, not a measured analog zero detector, compressibility proof, or complete adaptation-state inventory.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"sky130_float_membrane_occupancy_validation_{args.record_index}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("record_index", "actor_count", "logical_membrane_count", "per_update")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
