"""Relate measured Sky130 fan-in residuals to same-site float threshold margins."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
REF = OUT / "model_reference"
RES = OUT / "results"
SUFFIX = ("stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_"
          "slot50p253n")


def main() -> int:
    archive = np.load(REF / "float_patch_trace_all.npz")
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    reference = json.loads((REF / "eventspikeseg140k_float_reference.json").read_text(encoding="utf-8"))
    trace_meta = json.loads((REF / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    if trace_meta["qat_or_quantized_reference_used"]:
        raise RuntimeError("the reference trace must be full float, without QAT")
    actor = next(row for row in reference["effective_folded_weight_and_neuron_parameters"]
                 if row["name"] == "final_fuse.standard")
    weights = params["weight__final_fuse__standard"].astype(np.float32)
    inputs = archive["presynaptic_input__final_fuse__standard"].astype(np.float32)
    candidate = archive["candidate__final_fuse__standard"]
    current = archive["current__final_fuse__standard"]
    threshold = archive["threshold__final_fuse__standard"]
    spikes = archive["spikes__final_fuse__standard"]
    conv2d = runpy.run_path(str(ROOT / "scripts/analyze_sky130_passive_float_mapping.py"))["conv2d"]
    fanin = conv2d(inputs, np.ones_like(weights), candidate.shape[-2:],
                   groups=actor["conv_groups"], dilation=tuple(actor["conv_dilation"]),
                   padding=tuple(actor["conv_padding"]))
    volts_per_model_unit = 0.9 / float(np.max(np.abs(candidate)))
    cases = (("max_fanin", None), ("near_threshold_scale", 0.5), ("high_cancellation", 0.0))
    report_cases = {}
    for site, target in cases:
        if target is None:
            flat_index = int(np.argmax(fanin))
        else:
            eligible = fanin >= np.percentile(fanin[fanin > 0], 99)
            ranking = np.where(eligible,
                               np.abs(np.abs(current.reshape(fanin.shape)) - target), np.inf)
            flat_index = int(np.argmin(ranking))
        batch_index, output_channel, y, x = np.unravel_index(flat_index, fanin.shape)
        trace_step, member = divmod(batch_index, 3)
        theta = float(threshold[trace_step, 0, output_channel, 0, 0])
        float_candidate = float(candidate[trace_step, member, output_channel, y, x])
        float_current = float(current[trace_step, member, output_channel, y, x])
        float_spike = bool(spikes[trace_step, member, output_channel, y, x] >= 0.5)
        site_tag = "" if site == "max_fanin" else f"_{site}"
        base = (f"sky130_ms_first_touch_float_fanin_ss0{site_tag}_"
                "stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_"
                "slot50p253n")
        orders = {}
        for order in ("forward", "reverse", "shuffle"):
            path = RES / (f"{base}.json" if site == "max_fanin"
                          else f"{base}_{order}only.json")
            physical = json.loads(path.read_text(encoding="utf-8"))
            delivered = float(physical["physical_final_minus_reference_v"][order])
            ideal = float(physical["ideal_event_sum_v"])
            residual_v = delivered - ideal
            inferred_candidate = float_candidate + residual_v / volts_per_model_unit
            inferred_spike = inferred_candidate >= theta
            orders[order] = {
                "physical_event_sum_v": delivered,
                "ideal_event_sum_v": ideal,
                "event_sum_error_uv": residual_v * 1e6,
                "candidate_error_model_units": residual_v / volts_per_model_unit,
                "inferred_candidate_after_event_error": inferred_candidate,
                "float_threshold": theta,
                "float_candidate_margin_to_threshold": float_candidate - theta,
                "float_candidate_margin_mapped_to_uv": (float_candidate - theta) * volts_per_model_unit * 1e6,
                "float_spike": float_spike,
                "inferred_spike_from_measured_event_error": bool(inferred_spike),
                "decision_changed": bool(inferred_spike != float_spike),
            }
        report_cases[site] = {
            "trace_index": [int(trace_step), int(member), int(output_channel), int(y), int(x)],
            "fan_in": int(fanin[batch_index, output_channel, y, x]),
            "float_current": float_current,
            "float_candidate": float_candidate,
            "float_threshold": theta,
            "float_candidate_margin_mapped_to_uv": (float_candidate - theta) * volts_per_model_unit * 1e6,
            "float_spike": float_spike,
            "orders": orders,
        }
    report = {
        "test": "sky130_measured_fanin_residual_to_float_threshold_margin",
        "checkpoint_sha256": trace_meta["checkpoint_sha256"],
        "qat_or_quantized_reference_used": False,
        "volts_per_model_unit": volts_per_model_unit,
        "method": "Add each physical event-sum error to the same-site float candidate, converted through the fan-in map scale, and compare with the saved full-float threshold.",
        "scope": "Pointwise sensitivity only: presynaptic trace, prior state, threshold and beta are held at the float reference. Physical event-injection residual is measured from a matched no-event cell. No physical threshold comparator, state feedback, noise, mismatch or task-level replay is included.",
        "cases": report_cases,
    }
    path = RES / "sky130_ms_fanin_threshold_margin_screen.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: {"margin": row["float_candidate"] - row["float_threshold"],
                             "float_spike": row["float_spike"],
                             "analog_decisions": {order: item["inferred_spike_from_measured_event_error"]
                                                  for order, item in row["orders"].items()},
                             "decision_changes": {order: item["decision_changed"]
                                                  for order, item in row["orders"].items()}}
                      for name, row in report_cases.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
