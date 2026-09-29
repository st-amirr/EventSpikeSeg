"""Run one bounded real-DSEC float-model patch trace for analog sensitivity work."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.model_components import SpikingStage


def tensor_summary(value: torch.Tensor) -> dict[str, object]:
    x = value.detach().cpu().float().numpy().astype(np.float64, copy=False).ravel()
    absolute = np.abs(x)
    qs = np.percentile(absolute, [50, 90, 99, 99.9]).tolist() if x.size else [0.0] * 4
    return {
        "count": int(x.size),
        "min": float(x.min()) if x.size else 0.0,
        "max": float(x.max()) if x.size else 0.0,
        "abs_p50_p90_p99_p999": [float(v) for v in qs],
        "nonzero_fraction": float(np.count_nonzero(x) / x.size) if x.size else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--patch-size", type=int, default=64)
    parser.add_argument("--all-stages", action="store_true",
                        help="capture every inference SpikingStage for physical analog mapping")
    parser.add_argument("--differential-readout-calibration", action="store_true",
                        help="anchor the 1um packet point to half the measured two-packet transistor-readout swing")
    parser.add_argument("--sampled-differential-readout-calibration", action="store_true",
                        help="use per-sequence late-switched readout reports as the physical 1um calibration")
    args = parser.parse_args()
    torch.set_num_threads(2)
    checkpoint_path = args.checkpoint.resolve()
    raw = checkpoint_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint.get("architecture") != "EventSpikeSeg140k":
        raise ValueError("expected EventSpikeSeg140k float checkpoint")
    protocol = checkpoint.get("temporal_protocol", {})
    updates = int(protocol.get("internal_updates", 0))
    if updates != 10:
        raise ValueError(f"expected 10 trained updates per 50ms input window, got {updates}")
    record_ids = protocol.get("training_record_ids")
    if not record_ids:
        raise ValueError("checkpoint temporal protocol has no training record ids")
    sequence_id, frame_index = record_ids[0]
    records = [
        record
        for record in discover_dsec_records(args.dataset_root, "train")
        if record.sequence_id == sequence_id and record.frame_index == frame_index
    ]
    if len(records) != 1:
        raise ValueError(f"expected one checkpoint training record match, got {len(records)}")
    dataset = DSECRawEventDataset(
        args.dataset_root,
        split="train",
        output_size=(440, 640),
        internal_updates=updates,
        class_count=6,
        records=records,
    )
    events, _, _ = dataset[0]
    size = args.patch_size
    if size < 32 or size > 128:
        raise ValueError("bounded patch size must be between 32 and 128")
    tiles: list[tuple[float, int, int]] = []
    for y in range(0, events.shape[-2] - size + 1, size):
        for x in range(0, events.shape[-1] - size + 1, size):
            tiles.append((float(events[:, :, y:y + size, x:x + size].sum()), y, x))
    tiles.sort()
    selected = [tiles[0], tiles[len(tiles) // 2], tiles[-1]]
    input_sequence = torch.stack(
        [events[:, :, y:y + size, x:x + size] for _, y, x in selected], dim=1
    )

    model = EventSpikeSeg140k(
        class_count=6,
        input_channels=2,
        internal_updates=updates,
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.set_mechanism_scale(float(checkpoint.get("mechanism_scale", 1.0)))
    for module in model.modules():
        disable_qat = getattr(module, "set_asic_qat_enabled", None)
        if callable(disable_qat):
            disable_qat(False)
    model.eval()
    names = dict(model.named_modules())
    layers = (tuple(EVENTSPIKESEG140K_INFERENCE_STAGES) if args.all_stages
              else ("stem", "enc1.standard", "final_fuse.standard"))
    traces: dict[str, dict[str, list[torch.Tensor]]] = {}
    restore_methods: list[tuple[object, str, object]] = []
    handles = []
    for layer_name in layers:
        stage = names[layer_name]
        if not isinstance(stage, SpikingStage):
            raise TypeError(f"{layer_name} is not a SpikingStage")
        traces[layer_name] = {"presynaptic_input": [], "current": [], "candidate": [], "threshold": [], "spikes": [], "membrane": []}

        def conv_input_hook(_module, inputs, key=layer_name):
            traces[key]["presynaptic_input"].append(inputs[0].detach().cpu().clone())

        def pre_hook(_module, inputs, key=layer_name):
            traces[key]["current"].append(inputs[0].detach().cpu().clone())

        def out_hook(_module, _inputs, output, key=layer_name):
            traces[key]["spikes"].append(output.detach().cpu().clone())

        neuron = stage.neuron
        original_candidate = neuron._candidate_membrane
        original_threshold = neuron._threshold_tensor

        def capture_candidate(current, elapsed, original=original_candidate, key=layer_name):
            result = original(current, elapsed)
            traces[key]["candidate"].append(result.detach().cpu().clone())
            return result

        def capture_threshold(current, original=original_threshold, key=layer_name):
            result = original(current)
            traces[key]["threshold"].append(result.detach().cpu().clone())
            return result

        neuron._candidate_membrane = capture_candidate
        neuron._threshold_tensor = capture_threshold
        restore_methods.extend(((neuron, "_candidate_membrane", original_candidate),
                                (neuron, "_threshold_tensor", original_threshold)))
        def state_hook(module, _inputs, _output, key=layer_name):
            traces[key]["membrane"].append(module.membrane.detach().cpu().clone())

        handles.extend((
            stage.conv.register_forward_pre_hook(conv_input_hook),
            neuron.register_forward_pre_hook(pre_hook),
            neuron.register_forward_hook(out_hook),
            neuron.register_forward_hook(state_hook),
        ))
    with torch.inference_mode():
        outputs = model(input_sequence)
    for handle in handles:
        handle.remove()
    for module, name, original in restore_methods:
        setattr(module, name, original)

    # Bounded software sensitivity replay: map only final_fuse's full-float
    # effective weights onto the measured 1um-minimum MIM packet curve, then run
    # the same three-patch input through the full software graph. This is an
    # analog geometry-floor approximation, not QAT or a new trained reference.
    final_candidate = torch.stack(traces["final_fuse.standard"]["candidate"])
    reference_stage_spikes = torch.stack(traces["final_fuse.standard"]["spikes"]).bool()
    candidate_max = float(torch.max(torch.abs(final_candidate)))
    sc_report = json.loads((Path(__file__).resolve().parents[1] /
                            "artifacts/analog_asic/results/sky130_sc_small_cap_geometry.json").read_text(encoding="utf-8"))
    physical_packet_report = json.loads((Path(__file__).resolve().parents[1] /
                            "artifacts/analog_asic/results/sky130_sc_physical_retention_packet_sweep.json").read_text(encoding="utf-8"))
    cap_curves: dict[str, tuple[float, float, float]] = {}
    physical_one_um: dict[str, float] = {}
    for polarity in ("positive", "negative"):
        areas, deltas = [], []
        for width_um in (1.0, 3.0, 10.0):
            points = [item for item in sc_report["cases"]
                      if float(item["packet_size_um"]) == width_um and item["polarity"] == polarity]
            if width_um == 1.0:
                physical_points = [item for item in physical_packet_report["cases"]
                                   if float(item["packet_size_um"]) == 1.0 and item["polarity"] == polarity]
                physical_one_um[polarity] = float(np.mean([abs(float(item["state_change_v"]))
                                                            for item in physical_points]))
            areas.append(width_um * width_um)
            deltas.append(physical_one_um[polarity] if width_um == 1.0 else
                          float(np.mean([abs(float(item["state_change_v"])) for item in points])))
        slope, intercept = np.polyfit(areas, deltas, 1)
        cap_curves[polarity] = (float(slope), float(intercept), float(min(deltas)))
    if args.differential_readout_calibration or args.sampled_differential_readout_calibration:
        results_dir = Path(__file__).resolve().parents[1] / "artifacts/analog_asic/results"
        if args.sampled_differential_readout_calibration:
            readout_cases = {}
            for seq in ("pp", "nn", "pn", "np"):
                item = json.loads((results_dir / f"sky130_sc_differential_reference_sampled_{seq}.json").read_text(encoding="utf-8"))
                if not item.get("simulation_completed"):
                    raise ValueError(f"sampled differential readout report {seq} is incomplete")
                readout_cases[seq] = item["cases"][0]
        else:
            readout_report = json.loads((results_dir / "sky130_sc_differential_reference.json").read_text(encoding="utf-8"))
            if not readout_report.get("simulation_completed"):
                raise ValueError("differential readout report is incomplete")
            readout_cases = {item["sequence"]: item for item in readout_report["cases"]}
        physical_one_um["positive"] = abs(float(readout_cases["pp"]["readout_change_uv"])) * 0.5e-6
        physical_one_um["negative"] = abs(float(readout_cases["nn"]["readout_change_uv"])) * 0.5e-6
        # Rebuild the 1um-anchored polarity curves with the loaded-readout points.
        for polarity in ("positive", "negative"):
            area_values = [1.0]
            delta_values = [physical_one_um[polarity]]
            for width_um in (3.0, 10.0):
                points = [item for item in sc_report["cases"]
                          if float(item["packet_size_um"]) == width_um and item["polarity"] == polarity]
                area_values.append(width_um * width_um)
                delta_values.append(float(np.mean([abs(float(item["state_change_v"])) for item in points])))
            slope, intercept = np.polyfit(area_values, delta_values, 1)
            cap_curves[polarity] = (float(slope), float(intercept), float(min(delta_values)))
    cap_floor_model_replay = []
    base_logits = outputs["segmentation_logits"].detach().cpu().float()
    base_mask = base_logits.argmax(dim=1)
    base_scores = outputs.get("class_scores")
    base_scores = base_scores.detach().cpu().float() if base_scores is not None else None
    for swing in (0.15, 0.30, 0.60):
        v_per_unit = swing / candidate_max
        mapped_model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=updates)
        mapped_model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        mapped_model.set_mechanism_scale(float(checkpoint.get("mechanism_scale", 1.0)))
        for module in mapped_model.modules():
            disable_qat = getattr(module, "set_asic_qat_enabled", None)
            if callable(disable_qat):
                disable_qat(False)
        mapped_model.eval()
        mapped_stage = dict(mapped_model.named_modules())["final_fuse.standard"]
        mapped_weight = mapped_stage.conv.weight.detach().clone()
        affine = getattr(mapped_stage.transform.op, "gain", None)
        gain = affine.detach().clone() if affine is not None else torch.ones(mapped_weight.shape[0])
        effective_weight = mapped_weight * gain.view(-1, 1, 1, 1)
        target_v = effective_weight.abs() * v_per_unit
        use_negative_packet = effective_weight > 0
        slope_neg, intercept_neg, min_neg = cap_curves["negative"]
        slope_pos, intercept_pos, min_pos = cap_curves["positive"]
        slope = torch.where(use_negative_packet, slope_neg, slope_pos)
        intercept = torch.where(use_negative_packet, intercept_neg, intercept_pos)
        min_packet = torch.where(use_negative_packet, min_neg, min_pos)
        representable = target_v >= min_packet
        area = ((target_v - intercept) / slope).clamp_min(1.0)
        delivered_v = torch.where(representable, intercept + slope * area, torch.zeros_like(target_v))
        analog_effective_weight = torch.sign(effective_weight) * delivered_v / v_per_unit
        if affine is not None:
            mapped_stage.conv.weight.data.copy_(analog_effective_weight / gain.view(-1, 1, 1, 1))
        else:
            mapped_stage.conv.weight.data.copy_(analog_effective_weight)
        mapped_stage_spikes: list[torch.Tensor] = []
        spike_handle = mapped_stage.neuron.register_forward_hook(
            lambda _module, _inputs, output: mapped_stage_spikes.append(output.detach().cpu().clone())
        )
        with torch.inference_mode():
            mapped_output = mapped_model(input_sequence)
        spike_handle.remove()
        mapped_logits = mapped_output["segmentation_logits"].detach().cpu().float()
        mapped_mask = mapped_logits.argmax(dim=1)
        diff = (mapped_logits - base_logits).abs().flatten()
        row = {
            "candidate_headroom_v": swing,
            "volts_per_model_unit_from_sample_candidate_max": v_per_unit,
            "median_final_fuse_threshold_uv": float(torch.median(names["final_fuse.standard"].neuron.learned_threshold).detach().cpu()) * v_per_unit * 1e6,
            "fraction_final_fuse_static_coefficients_zeroed_below_smallest_tested_cap": float((~representable).float().mean()),
            "required_square_cap_width_um_median_max_for_retained_coefficients": [float(torch.median(torch.sqrt(area[representable]))), float(torch.max(torch.sqrt(area[representable])))],
            "full_float_vs_cap_floor_output_pixel_argmax_agreement": float((mapped_mask == base_mask).float().mean()),
            "segmentation_logit_abs_difference_p50_p90_p99_max": [float(v) for v in torch.quantile(diff, torch.tensor([0.5, 0.9, 0.99, 1.0]))],
            "spike_trace_final_fuse_mismatch_fraction": float((torch.stack(mapped_stage_spikes).bool() != reference_stage_spikes).float().mean()),
        }
        if base_scores is not None and "class_scores" in mapped_output:
            score_diff = (mapped_output["class_scores"].detach().cpu().float() - base_scores).abs().flatten()
            row["class_score_abs_difference_p50_p90_p99_max"] = [float(v) for v in torch.quantile(score_diff, torch.tensor([0.5, 0.9, 0.99, 1.0]))]
        cap_floor_model_replay.append(row)

    arrays: dict[str, np.ndarray] = {}
    report_layers = []
    for layer_name in layers:
        current = torch.stack(traces[layer_name]["current"])
        spikes = torch.stack(traces[layer_name]["spikes"])
        candidate = torch.stack(traces[layer_name]["candidate"])
        threshold = torch.stack(traces[layer_name]["threshold"])
        membrane = torch.stack(traces[layer_name]["membrane"])
        arrays[f"current__{layer_name.replace('.', '__')}"] = current.numpy()
        presynaptic_input = torch.cat(traces[layer_name]["presynaptic_input"], dim=0)
        arrays[f"presynaptic_input__{layer_name.replace('.', '__')}"] = presynaptic_input.numpy()
        arrays[f"candidate__{layer_name.replace('.', '__')}"] = candidate.numpy()
        arrays[f"threshold__{layer_name.replace('.', '__')}"] = threshold.numpy()
        arrays[f"spikes__{layer_name.replace('.', '__')}"] = spikes.numpy()
        arrays[f"membrane__{layer_name.replace('.', '__')}"] = membrane.numpy()
        neuron = names[layer_name].neuron
        threshold_margin = candidate - threshold
        margin_abs = threshold_margin.abs().flatten()
        report_layers.append({
            "name": layer_name,
            "current": tensor_summary(current),
            "candidate_before_threshold_and_reset": tensor_summary(candidate),
            "effective_threshold": tensor_summary(threshold),
            "candidate_minus_threshold_margin_model_units": {
                "min": float(threshold_margin.min()),
                "max": float(threshold_margin.max()),
                "abs_percentiles_0p1_1_10_50_90": [
                    float(v) for v in torch.quantile(
                        margin_abs,
                        torch.tensor([0.001, 0.01, 0.10, 0.50, 0.90]),
                    )
                ],
                "abs_le_0p01_fraction": float((margin_abs <= 0.01).float().mean()),
                "abs_le_0p05_fraction": float((margin_abs <= 0.05).float().mean()),
                "scope": "raw beta*prior+current candidate before update-mask, competition, reset and peer inhibition; exact for unmasked final_fuse candidate only",
            },
            "spikes": tensor_summary(spikes),
            "post_reset_membrane": tensor_summary(membrane),
            "spike_rate": float(spikes.mean()),
            "beta": tensor_summary(neuron.beta),
            "threshold": tensor_summary(neuron.learned_threshold),
            "inhibition_enabled": bool(neuron.config.inhibition_enabled),
            "threshold_adaptation_enabled": bool(neuron.config.threshold_adaptation_enabled),
        })

    # Compare the model's subtractive reset with a physical reset-to-VCM switch
    # using the same captured final-stage input-current sequence. This layer has
    # no peer inhibition or threshold adaptation, isolating reset semantics.
    reset_layer = "final_fuse.standard"
    key = reset_layer.replace(".", "__")
    current = arrays[f"current__{key}"]
    reference_spikes = arrays[f"spikes__{key}"]
    thresholds = arrays[f"threshold__{key}"]
    beta = names[reset_layer].neuron.beta.detach().cpu().float().numpy().copy().reshape(1, -1, 1, 1)
    soft_state = np.zeros_like(current[0])
    hard_state = np.zeros_like(current[0])
    soft_spikes = []
    hard_spikes = []
    for timestep in range(current.shape[0]):
        threshold = thresholds[timestep]
        candidate_soft = beta * soft_state + current[timestep]
        candidate_hard = beta * hard_state + current[timestep]
        spike_soft = (candidate_soft >= threshold).astype(np.float32)
        spike_hard = (candidate_hard >= threshold).astype(np.float32)
        soft_spikes.append(spike_soft)
        hard_spikes.append(spike_hard)
        soft_state = candidate_soft - spike_soft * threshold
        hard_state = np.where(spike_hard > 0, 0.0, candidate_hard)
    soft_spikes_array = np.stack(soft_spikes)
    hard_spikes_array = np.stack(hard_spikes)
    reset_screen = {
        "layer": reset_layer,
        "comparison": "replay captured float input currents; soft reset subtracts threshold; hard reset returns membrane to zero/VCM",
        "soft_reset_spike_bit_mismatches_vs_float": int(np.count_nonzero(soft_spikes_array != reference_spikes)),
        "hard_reset_spike_bit_mismatches_vs_float": int(np.count_nonzero(hard_spikes_array != reference_spikes)),
        "hard_vs_soft_spike_bit_mismatches": int(np.count_nonzero(hard_spikes_array != soft_spikes_array)),
        "spike_bit_count": int(reference_spikes.size),
        "hard_reset_is_model_equivalent": bool(np.array_equal(hard_spikes_array, reference_spikes)),
        "soft_reset_replay_matches_float": bool(np.array_equal(soft_spikes_array, reference_spikes)),
        "inhibition_enabled": bool(names[reset_layer].neuron.config.inhibition_enabled),
        "threshold_adaptation_enabled": bool(names[reset_layer].neuron.config.threshold_adaptation_enabled),
    }
    arrays["soft_reset_spikes__final_fuse__standard"] = soft_spikes_array
    arrays["hard_reset_spikes__final_fuse__standard"] = hard_spikes_array

    args.output.parent.mkdir(parents=True, exist_ok=True)
    archive_path = args.output.with_suffix(".npz")
    np.savez_compressed(archive_path, **arrays)
    report = {
        "test": "sky130_float_model_real_dsec_patch_trace",
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": digest,
        "checkpoint_epoch": checkpoint.get("epoch"),
        "checkpoint_best_epoch": checkpoint.get("best_epoch"),
        "float_path": True,
        "qat_or_quantized_reference_used": False,
        "dataset_root": str(args.dataset_root.resolve()),
        "split": "train",
        "record": {"sequence_id": sequence_id, "frame_index": frame_index},
        "input_window_us": int(protocol["integration_window_us"]),
        "update_count": updates,
        "update_interval_us": int(protocol["event_clock_us"]),
        "patch_size": size,
        "patches_low_median_high_total_events_and_xy": [
            {"event_count": int(score), "y": int(y), "x": int(x)}
            for score, y, x in selected
        ],
        "input_shape_t_n_c_h_w": list(input_sequence.shape),
        "input_event_summary": tensor_summary(input_sequence),
        "sampled_stages": report_layers,
        "reset_semantics_screen": reset_screen,
        "segmentation_logits": tensor_summary(outputs["segmentation_logits"]),
        "measured_mim_cap_floor_software_replay": {
            "cases": cap_floor_model_replay,
            "physical_1um_packet_calibration_by_polarity_v": physical_one_um,
            "calibration_source": "sky130_sc_differential_reference_sampled_{pp,nn}.json; half the late-switched transistor-readout same-sign two-packet output swing per event" if args.sampled_differential_readout_calibration else ("sky130_sc_differential_reference.json; half the continuously loaded transistor-readout same-sign two-packet output swing per event" if args.differential_readout_calibration else "sky130_sc_physical_retention_packet_sweep.json; 5ms physical init/hold then phase-ordered packet and matched no-event subtraction"),
            "scope": "full software inference on the same three real-DSEC patches, with only final_fuse effective float weights remapped through a 1/3/10um cap-area fit anchored at the physically initialized/held 1um packet response and coefficients below that measured packet omitted; no QAT, training, task accuracy, PVT/mismatch/noise or physical layout",
        },
        "trace_archive": archive_path.name,
        "scope": "three spatial patches from one real training record; full float software forward obtains local PLIF currents/spikes; a separate single-layer cap-floor sensitivity replay maps final_fuse using measured 1/3/10um capacitor responses, with the 1um point anchored to the physical init/hold/packet sequence; this is not task accuracy, full analog inference, hardware throughput or a population claim.",
    }
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(args.output.resolve()),
        "trace_archive": str(archive_path.resolve()),
        "record": report["record"],
        "sampled_stages": [
            {"name": row["name"], "current_abs_quantiles": row["current"]["abs_p50_p90_p99_p999"],
             "spike_rate": row["spike_rate"]} for row in report_layers
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
