"""Compare tight single-event PVT charge range with original full-float weights."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RES = ROOT / "artifacts/analog_asic/results"


def main() -> int:
    trace = json.loads((REF / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    curve = json.loads((RES / "sky130_ms_first_event_pvt_transfer_curve_tight.json").read_text(encoding="utf-8"))
    if trace["checkpoint_sha256"] != "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7" or not curve["simulation_completed"]:
        raise RuntimeError("unexpected full-float or PVT curve reference")
    by_fraction = [{row["gate_fraction"]: row["event_step_uv"] for row in condition["points"]}
                   for condition in curve["conditions"]]
    ranges = []
    for low_fraction, high_fraction in ((0.4, 0.8), (0.1, 0.95)):
        ranges.append({"gate_fraction_range": [low_fraction, high_fraction],
                       "common_min_event_uv": max(row[low_fraction] for row in by_fraction),
                       "common_max_event_uv": min(row[high_fraction] for row in by_fraction)})
    arrays = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    trace_arrays = np.load(REF / trace["trace_archive"])
    metadata = json.loads((REF / "eventspikeseg140k_float_reference.json").read_text(encoding="utf-8"))
    conv_meta = {row["name"]: row for row in metadata["effective_folded_weight_and_neuron_parameters"]}
    conv2d = runpy.run_path(str(ROOT / "scripts/analyze_sky130_passive_float_mapping.py"))["conv2d"]
    stages = []
    for stage in trace["sampled_stages"]:
        name = stage["name"]
        c = stage["candidate_before_threshold_and_reset"]
        candidate_max = max(abs(float(c["min"])), abs(float(c["max"])))
        weights = np.abs(arrays[f"weight__{name.replace('.', '__')}"].astype(np.float64).ravel())
        required_uv = weights * (0.9 / candidate_max) * 1e6
        row = {"stage": name, "weight_count": int(weights.size),
               "candidate_abs_max_model_units_on_three_patches": candidate_max,
               "volts_per_model_unit_at_0p9v_headroom": 0.9 / candidate_max,
               "required_abs_event_uv_quantiles_p0_p1_p50_p99_max": [float(v) for v in np.quantile(required_uv, [0, .01, .5, .99, 1])],
               "range_coverage": []}
        safe = name.replace(".", "__")
        inputs = trace_arrays[f"presynaptic_input__{safe}"].astype(np.float32)
        candidate = trace_arrays[f"candidate__{safe}"]
        meta = conv_meta[name]
        weight_shape = arrays[f"weight__{safe}"].shape
        fanin = conv2d(inputs, np.ones(weight_shape, dtype=np.float32), candidate.shape[-2:],
                       groups=meta["conv_groups"], dilation=tuple(meta["conv_dilation"]),
                       padding=tuple(meta["conv_padding"])).ravel()
        active_fanin = fanin[fanin > 0]
        required_width_ns = max(10.5, 10.5 * required_uv.max() / ranges[1]["common_max_event_uv"])
        row["illustrative_worst_corner_width_ns_to_cover_max_weight"] = float(required_width_ns)
        illustrative_low_floor_uv = ranges[1]["common_min_event_uv"] * required_width_ns / 10.5
        row["illustrative_low_event_floor_uv_at_that_width"] = float(illustrative_low_floor_uv)
        row["illustrative_static_weights_below_that_floor_fraction"] = float(np.mean(required_uv < illustrative_low_floor_uv))
        row["sampled_active_destination_fanin_p50_p90_p99_max"] = [float(v) for v in np.quantile(active_fanin, [.5, .9, .99, 1])]
        row["optimistic_serial_pulse_service_us_p99_max"] = [
            float(v * required_width_ns / 1000) for v in np.quantile(active_fanin, [.99, 1])]
        for charge_range in ranges:
            lo, hi = charge_range["common_min_event_uv"], charge_range["common_max_event_uv"]
            row["range_coverage"].append({"gate_fraction_range": charge_range["gate_fraction_range"],
                                           "below_common_min_fraction": float(np.mean(required_uv < lo)),
                                           "above_common_max_fraction": float(np.mean(required_uv > hi)),
                                           "inside_common_range_fraction": float(np.mean((required_uv >= lo) & (required_uv <= hi)))})
        stages.append(row)
    report = {"test": "sky130_full_float_static_weight_charge_PVT_range_screen",
              "checkpoint_sha256": trace["checkpoint_sha256"],
              "qat_or_quantized_reference_used": False,
              "candidate_headroom_v": 0.9,
              "common_charge_ranges": ranges,
              "stages": stages,
              "scope": "Original folded float static weights on 25 deployed PLIF stages. Per-stage candidate maximum and active fan-in are from three sampled 64x64 patches, not guaranteed full-frame ranges. Illustrative fixed per-stage pulse width assumes linear SS/0C fraction0.95 charge out to the width needed for the largest static weight; only selected widths through450ns have been tested. Serial service assumes one lane per output and excludes switch setup, calibration, reset/readout, graph scheduling, routing and contention. Charge curve uses one positive event on 10um MIM with ideal gate source and selected PVT; negative transfer, cumulative fan-in, drift, mismatch, DAC resolution, noise and physical calibration are absent. Static-weight fraction is not event-weighted task error."}
    out = RES / "sky130_ms_pvt_float_weight_charge_coverage.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"common_charge_ranges": ranges,
                      "selected_stages": [row for row in stages if row["stage"] in
                                          ("stem", "enc1.standard", "final_fuse.standard")]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
