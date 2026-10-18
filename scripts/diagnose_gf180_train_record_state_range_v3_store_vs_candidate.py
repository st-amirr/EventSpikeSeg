"""Compare full-frame training-record PLIF ranges with the GF180 8x8 scale map."""
import hashlib
import json
import argparse
from pathlib import Path

import torch
import torch.nn.functional as F
import numpy as np

from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
EXPECTED = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pool8(value):
    return value.abs()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-record-index", type=int, default=0)
    args = parser.parse_args()
    torch.set_num_threads(2)
    checkpoint_path = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
    if digest(checkpoint_path) != EXPECTED:
        raise ValueError("checkpoint hash mismatch")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint.get("architecture") != "EventSpikeSeg140k" or checkpoint.get("epoch") != 58:
        raise ValueError("unexpected checkpoint metadata")
    training_ids = checkpoint["temporal_protocol"]["training_record_ids"]
    if not 0 <= args.training_record_index < len(training_ids):
        raise ValueError(f"training record index outside 0..{len(training_ids)-1}")
    sequence_id, frame_index = training_ids[args.training_record_index]
    dataset_root = Path("/workspace/DSEC")
    records = [r for r in discover_dsec_records(dataset_root, "train")
               if r.sequence_id == sequence_id and r.frame_index == frame_index]
    if len(records) != 1:
        raise ValueError(f"expected one training record, got {len(records)}")
    dataset = DSECRawEventDataset(dataset_root, split="train", output_size=(440, 640),
                                  internal_updates=10, class_count=6, records=records)
    events, _, _ = dataset[0]
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=10)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.set_mechanism_scale(float(checkpoint.get("mechanism_scale", 1.0)))
    for module in model.modules():
        toggle = getattr(module, "set_asic_qat_enabled", None)
        if callable(toggle):
            toggle(False)
    model.eval()
    named = dict(model.named_modules())
    observations = {}
    restores = []
    for stage_name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        neuron = named[stage_name].neuron
        observations[stage_name] = {"postreset": None, "candidate": None, "updates": 0}
        original_forward = neuron.forward
        original_candidate = neuron._candidate_membrane

        def capture_candidate(current, elapsed_steps=1.0, *, _name=stage_name,
                              _original=original_candidate):
            value = _original(current, elapsed_steps)
            pooled = pool8(value).detach()
            obs = observations[_name]
            obs["candidate"] = pooled if obs["candidate"] is None else torch.maximum(obs["candidate"], pooled)
            return value

        def capture_forward(current, elapsed_steps=1.0, update_mask=None, *,
                            _name=stage_name, _original=original_forward, _neuron=neuron):
            spikes = _original(current, elapsed_steps, update_mask)
            pooled = pool8(_neuron.membrane).detach()
            obs = observations[_name]
            obs["postreset"] = pooled if obs["postreset"] is None else torch.maximum(obs["postreset"], pooled)
            obs["updates"] += 1
            return spikes

        neuron._candidate_membrane = capture_candidate
        neuron.forward = capture_forward
        restores.extend(((neuron, "forward", original_forward),
                         (neuron, "_candidate_membrane", original_candidate)))

    with torch.inference_mode():
        output = model(events.unsqueeze(1))
    for neuron, name, original in restores:
        setattr(neuron, name, original)

    calibration_path = BASE / "results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json"
    calibration = json.loads(calibration_path.read_text(encoding="utf8"))
    results = {}
    all_factors = []
    all_postreset_factors = []
    all_candidate_factors = []
    all_candidate_v = []
    all_threshold_mv = []
    for stage_name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        obs = observations[stage_name]
        if obs["candidate"] is None or obs["postreset"] is None or obs["updates"] != 10:
            raise ValueError(f"incomplete stage observation: {stage_name}")
        candidate = obs["candidate"].squeeze(0)
        postreset = obs["postreset"].squeeze(0)
        thresholds = named[stage_name].neuron._base_threshold(
            torch.zeros(1, named[stage_name].neuron.channels, 1, 1)
        ).detach().cpu().flatten()
        floor = (4.0 * thresholds).view(-1, 1, 1)
        old_bank = torch.tensor(calibration["state_tile8_ranges"][stage_name][0], dtype=torch.float32).squeeze(0)
        old = old_bank.repeat_interleave(8, dim=1).repeat_interleave(8, dim=2)[:, :candidate.shape[1], :candidate.shape[2]]
        required_postreset = torch.maximum(postreset, floor) * 1.25
        required_candidate = torch.maximum(candidate, floor) * 1.25
        required = torch.maximum(required_candidate, required_postreset)
        factor = required / old
        postreset_factor = required_postreset / old
        candidate_factor = required_candidate / old
        candidate_v = 0.9 * candidate / old
        threshold_mv = 900.0 * thresholds.view(-1, 1, 1) / required
        f = factor.flatten().cpu()
        cv = candidate_v.flatten().cpu()
        tmv = threshold_mv.flatten().cpu()
        all_factors.append(f)
        all_postreset_factors.append(postreset_factor.flatten().cpu())
        all_candidate_factors.append(candidate_factor.flatten().cpu())
        all_candidate_v.append(cv)
        all_threshold_mv.append(tmv)
        results[stage_name] = {
            "state_cell_count": int(f.numel()),
            "existing_validation_range_abs_model_units_p10_p50_p90_max": [
                float(x) for x in torch.quantile(old.flatten(), torch.tensor([.1, .5, .9, 1.0]))
            ],
            "required_range_expansion_factor_p50_p90_p99_p999_max": [
                float(x) for x in torch.quantile(f, torch.tensor([.5, .9, .99, .999, 1.0]))
            ],
            "stored_postreset_range_expansion_factor_p50_p90_p99_p999_max": [
                float(x) for x in torch.quantile(postreset_factor.flatten(), torch.tensor([.5, .9, .99, .999, 1.0]))
            ],
            "transient_candidate_range_expansion_factor_p50_p90_p99_p999_max": [
                float(x) for x in torch.quantile(candidate_factor.flatten(), torch.tensor([.5, .9, .99, .999, 1.0]))
            ],
            "fraction_banks_requiring_over_2x_10x_100x": [
                float((f > limit).float().mean()) for limit in (2, 10, 100)
            ],
            "candidate_mapped_to_existing_range_abs_v_p50_p90_p99_p999_max": [
                float(x) for x in torch.quantile(cv, torch.tensor([.5, .9, .99, .999, 1.0]))
            ],
            "threshold_under_expanded_range_mv_p10_p50_p90_min": [
                float(x) for x in torch.quantile(tmv, torch.tensor([.1, .5, .9, 0.0]))
            ],
        }
    factors = torch.cat(all_factors).contiguous()
    postreset_factors = torch.cat(all_postreset_factors).contiguous()
    candidate_factors = torch.cat(all_candidate_factors).contiguous()
    candidates_v = torch.cat(all_candidate_v).contiguous()
    threshold_mv = torch.cat(all_threshold_mv).contiguous()
    def global_quantiles(value, q):
        return [float(x) for x in np.percentile(value.numpy(), q)]
    report = {
        "diagnostic_completed": True,
        "checkpoint_sha256": EXPECTED,
        "checkpoint_epoch": 58,
        "qat_or_quantized_reference_used": False,
        "record": {"sequence_id": sequence_id, "frame_index": frame_index},
        "input_shape_t_n_c_h_w": list(events.unsqueeze(1).shape),
        "updates_per_stage": 10,
        "calibration_records": calibration["settings"]["record_indices"],
        "actor_count": len(results),
        "state_cell_count": int(factors.numel()),
        "aggregate": {
            "required_range_expansion_factor_p50_p90_p99_p999_max": global_quantiles(factors, [50, 90, 99, 99.9, 100]),
            "stored_postreset_range_expansion_factor_p50_p90_p99_p999_max": global_quantiles(postreset_factors, [50, 90, 99, 99.9, 100]),
            "transient_candidate_range_expansion_factor_p50_p90_p99_p999_max": global_quantiles(candidate_factors, [50, 90, 99, 99.9, 100]),
            "fraction_stored_postreset_needing_over_2x_10x_100x": [float((postreset_factors > x).float().mean()) for x in (2, 10, 100)],
            "fraction_transient_candidate_needing_over_2x_10x_100x": [float((candidate_factors > x).float().mean()) for x in (2, 10, 100)],
            "fraction_banks_requiring_over_2x_10x_100x": [
                float((factors > limit).float().mean()) for limit in (2, 10, 100)
            ],
            "candidate_mapped_to_existing_range_abs_v_p50_p90_p99_p999_max": global_quantiles(candidates_v, [50, 90, 99, 99.9, 100]),
            "threshold_under_expanded_range_mv_p10_p50_p90_min": global_quantiles(threshold_mv, [10, 50, 90, 0]),
        },
        "actors": results,
        "scope": "One full 440x640 training frame, original epoch58 float checkpoint, ten updates, all25 actors. Separately compares transient pre-threshold candidate and stored post-reset state ranges with the existing 8-record validation post-reset range map. Candidate may require summing/comparator headroom but does not automatically set the storage capacitor range. Diagnostic only: does not change model or assert model accuracy, analog update accuracy, noise/PVT, 5ms physical service, or full-chip acceptance.",
        "sha256": {
            str(p.relative_to(ROOT)).replace("\\", "/"): digest(p)
            for p in [checkpoint_path, calibration_path, Path(__file__),
                      ROOT / "src/eventspikeseg/model.py", ROOT / "src/eventspikeseg/model_components.py"]
        },
    }
    out = BASE / f"results/gf180_train_record_state_range_diagnostic_v3_record{args.training_record_index}_store_vs_candidate.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"report": str(out), "record": report["record"],
                      "aggregate": report["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()
