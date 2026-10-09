"""Bound local float spike sensitivity to measured static MOS geometry range."""

from __future__ import annotations

import hashlib
import json
import runpy
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RESULTS = ROOT / "artifacts/analog_asic/results"
CHECKPOINT = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
EXPECTED_SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
STAGES = ("final_fuse.standard", "enc1.standard", "context2.depthwise")
ANCHORS = (0.5, 0.75, 0.9, 0.95, 0.99, 1.0)
WIDTHS = (0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0)
BIAS_FRACTIONS = (0.4, 0.5, 0.6, 0.7, 0.8)
EXTENDED_BIAS_FRACTIONS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)
GEOMETRY_CASE = "before_0p2ns"
GEOMETRY_GATE_SLEW_NS = 0.1
EVENT_WIDTH_NS = 10.5
SHARED_BANK_LOAD = False
R2R_CURVE_REPORTS = {
    0.4: "sky130_ms_static_bias_r2r_b12_event_biases0p4-0p6-0p7_geom4_slew0p5n_clamp1n_tt_temp27_reuse_tt_trim.json",
    0.5: "sky130_ms_static_bias_r2r_b12_event_biases0p5_geom4_slew0p5n_clamp1n_tt_temp27_reuse_tt_trim.json",
    0.6: "sky130_ms_static_bias_r2r_b12_event_biases0p4-0p6-0p7_geom4_slew0p5n_clamp1n_tt_temp27_reuse_tt_trim.json",
    0.7: "sky130_ms_static_bias_r2r_b12_event_biases0p4-0p6-0p7_geom4_slew0p5n_clamp1n_tt_temp27_reuse_tt_trim.json",
    0.8: "sky130_ms_static_bias_r2r_b12_event_biases0p8_geom4_slew0p5n_clamp1n_tt_temp27_reuse_tt_trim.json",
}


def geometry_result_path(width: float, fraction: float) -> Path:
    tag = "" if fraction == .6 else f"_g{fraction:g}".replace(".", "p")
    tag += "" if width == 1 else f"_geom{width:g}".replace(".", "p")
    width_tag = "" if EVENT_WIDTH_NS == 10.5 else f"_w{EVENT_WIDTH_NS:g}n".replace(".", "p")
    if EVENT_WIDTH_NS != 10.5:
        width_tag += "_post20n"
    if GEOMETRY_GATE_SLEW_NS != 0.1:
        width_tag += f"_rise{GEOMETRY_GATE_SLEW_NS:g}n".replace(".", "p")
    if SHARED_BANK_LOAD:
        width_tag += "_banked"
    case_tag = ("onlyreference-before_0p2ns" if EVENT_WIDTH_NS == 10.5
                else f"only{GEOMETRY_CASE}")
    stem = "sky130_ms_first_event_clamp_ss_temp0" + tag + f"_tight_s0p1n{width_tag}"
    expected = RESULTS / f"{stem}_{case_tag}.json"
    if expected.exists() or EVENT_WIDTH_NS == 10.5:
        return expected
    # Earlier completed width-grid runs retained every timing case in one
    # report; accept that report when it contains the required case row.
    return RESULTS / f"{stem}.json"


def load_curve(fraction: float) -> tuple[np.ndarray, list[str]]:
    charges = []
    sources = []
    for width in WIDTHS:
        path = geometry_result_path(width, fraction)
        row = json.loads(path.read_text(encoding="utf-8"))
        if not row["simulation_completed"] or row["mos_corner"] != "ss" or row["temperature_c"] != 0:
            raise ValueError(f"invalid physical geometry row: {path}")
        if row["gate_fraction"] != fraction or abs(row["event_width_ns"] - EVENT_WIDTH_NS) > 0.001:
            raise ValueError(f"incompatible physical geometry point: {path}")
        point = next(case for case in row["cases"] if case["case"] == GEOMETRY_CASE)
        charges.append(float(point["post_event_minus_no_event_uv"]))
        sources.append(path.name)
    return np.asarray(charges, dtype=np.float64), sources


def load_r2r_factors() -> tuple[dict[float, float], dict[str, str]]:
    factors, sources = {}, {}
    candidates = []
    for path in RESULTS.glob("sky130_ms_static_bias_r2r_b12_event*.json"):
        report = json.loads(path.read_text(encoding="utf-8"))
        if (report.get("simulation_completed") and report.get("event_width_ns") is not None
                and abs(report["event_width_ns"] - EVENT_WIDTH_NS) <= 0.001
                and report.get("mos_corner") == "tt" and report.get("temperature_c") == 27
                and report.get("gate_selection_slew_ns") == (0.5 if EVENT_WIDTH_NS == 10.5 else GEOMETRY_GATE_SLEW_NS)
                and report.get("clamp_release_slew_ns") == 1.0):
            candidates.append((path.name, report))
    for fraction in BIAS_FRACTIONS:
        if EVENT_WIDTH_NS == 10.5:
            filename = R2R_CURVE_REPORTS[fraction]
            report = json.loads((RESULTS / filename).read_text(encoding="utf-8"))
            match = (filename, report)
        else:
            match = next(((name, report) for name, report in candidates
                      if any(row["gate_fraction"] == fraction and row["injector_geometry_scale"] == 4
                             for row in report["event_transfer_rows"])), None)
        if match is None:
            raise ValueError(f"missing TT/27C geometry4 R-2R event correction at {EVENT_WIDTH_NS:g}ns, bias {fraction}")
        filename, report = match
        if report.get("r2r_bits") != 12:
            raise ValueError(f"invalid R-2R calibration row: {filename}")
        point = next(row for row in report["event_transfer_rows"]
                     if row["gate_fraction"] == fraction)
        if point["injector_geometry_scale"] != 4 or point["ideal_event_delta_uv"] == 0:
            raise ValueError(f"incompatible R-2R geometry/bias point: {path}")
        factors[fraction] = float(point["r2r_event_delta_uv"] / point["ideal_event_delta_uv"])
        sources[fraction] = filename
    return factors, sources


def representable_charge(desired_uv: np.ndarray, abs_weight: np.ndarray,
                         curves: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ranges = sorted((float(np.min(curve)), float(np.max(curve))) for curve in curves)
    qmin, qmax = ranges[0][0], max(end for _, end in ranges)
    low = (desired_uv < qmin) & (abs_weight > 0)
    high = desired_uv > qmax
    covered = np.zeros_like(low)
    for begin, end in ranges:
        covered |= (desired_uv >= begin) & (desired_uv <= end)
    gap = (~covered) & (~low) & (~high) & (abs_weight > 0)
    realized = np.where(low, 0.0, np.minimum(desired_uv, qmax))
    if np.any(gap):
        endpoints = np.asarray([edge for pair in ranges for edge in pair])
        realized[gap] = endpoints[np.abs(desired_uv[gap, None] - endpoints).argmin(axis=1)]
    return realized, low, high, gap


def main() -> int:
    global EVENT_WIDTH_NS, BIAS_FRACTIONS, GEOMETRY_CASE, GEOMETRY_GATE_SLEW_NS, SHARED_BANK_LOAD
    EVENT_WIDTH_NS = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                 if arg.startswith("--event-width-ns=")), "10.5"))
    if EVENT_WIDTH_NS != 10.5:
        BIAS_FRACTIONS = EXTENDED_BIAS_FRACTIONS
        GEOMETRY_CASE = "before_10ns"
        GEOMETRY_GATE_SLEW_NS = 2.0
    SHARED_BANK_LOAD = "--shared-bank-load" in sys.argv[1:]
    hasher = hashlib.sha256()
    with CHECKPOINT.open("rb") as checkpoint_file:
        for chunk in iter(lambda: checkpoint_file.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError("best full-float checkpoint hash changed")
    trace_path = REF / "float_patch_trace_all.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    if trace["checkpoint_sha256"] != EXPECTED_SHA or trace.get("checkpoint_epoch") != 58:
        raise ValueError("trace does not match the best full-float checkpoint")
    arrays = np.load(REF / trace["trace_archive"])
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    reference = json.loads((REF / "eventspikeseg140k_float_reference.json").read_text(encoding="utf-8"))
    meta = {row["name"]: row for row in reference["effective_folded_weight_and_neuron_parameters"]}
    tools = runpy.run_path(str(ROOT / "scripts/analyze_sky130_passive_float_mapping.py"))
    conv2d, replay = tools["conv2d"], tools["replay"]
    curves = {fraction: load_curve(fraction) for fraction in BIAS_FRACTIONS}
    use_r2r_correction = "--r2r-bias-correction" in sys.argv[1:]
    r2r_factors, r2r_sources = load_r2r_factors() if use_r2r_correction else ({}, {})
    if use_r2r_correction:
        curves = {fraction: (curve * r2r_factors[fraction], sources + [r2r_sources[fraction]])
                  for fraction, (curve, sources) in curves.items()}
    stages = []
    nearest_mode = ("five_bias_thirteen_geometry_nearest" if len(BIAS_FRACTIONS) == 5
                    else "eight_bias_thirteen_geometry_nearest")
    for stage in STAGES:
        key = stage.replace(".", "__")
        weight = params[f"weight__{key}"].astype(np.float32)
        abs_weight = np.abs(weight.astype(np.float64))
        inputs = arrays[f"presynaptic_input__{key}"].astype(np.float32)
        reference_current = arrays[f"current__{key}"].astype(np.float32)
        reference_spikes = arrays[f"spikes__{key}"].astype(bool)
        thresholds = arrays[f"threshold__{key}"].astype(np.float32)
        beta = params[f"beta__{key}"].astype(np.float32).reshape(1, -1, 1, 1)
        info = meta[stage]
        conv_args = {"groups": info["conv_groups"],
                     "dilation": tuple(info["conv_dilation"]),
                     "padding": tuple(info["conv_padding"])}
        baseline_spikes, _ = replay(reference_current, beta, thresholds)
        stage_rows = []
        for mode, fractions, finite_levels in (("geometry_only", (.6,), False),
                                               ("shared_bias_continuous_geometry", BIAS_FRACTIONS, False),
                                               (nearest_mode, BIAS_FRACTIONS, True)):
            selected = [curves[f][0] for f in fractions]
            qmax = max(float(np.max(curve)) for curve in selected)
            for anchor in ANCHORS:
                anchor_weight = float(np.quantile(abs_weight, anchor))
                if anchor_weight <= 0:
                    continue
                uv_per_model_unit = qmax / anchor_weight
                desired_uv = abs_weight * uv_per_model_unit
                unfiltered_uv, low, high, gap = representable_charge(desired_uv, abs_weight, selected)
                if finite_levels:
                    levels = np.sort(np.concatenate(selected))
                    clipped = np.clip(desired_uv, levels[0], levels[-1])
                    nearest = np.abs(clipped[..., None] - levels).argmin(axis=-1)
                    unfiltered_uv = np.where(low, 0.0, levels[nearest])
                floors = ((0.0, 1.0, 10.0, 100.0) if mode in ("shared_bias_continuous_geometry", nearest_mode)
                          and anchor in (.99, 1.0) else (0.0,))
                for floor_uv in floors:
                    floor_mask = (unfiltered_uv < floor_uv) & (abs_weight > 0)
                    realized_uv = np.where(floor_mask, 0.0, unfiltered_uv)
                    mapped = np.sign(weight) * (realized_uv / uv_per_model_unit)
                    current = conv2d(inputs, mapped.astype(np.float32), reference_current.shape[-2:],
                                     **conv_args).reshape(reference_current.shape)
                    spikes, _ = replay(current, beta, thresholds)
                    stage_rows.append({
                        "mode": mode,
                        "weight_anchor_quantile_mapped_to_max_geometry": anchor,
                        "microvolts_per_model_weight_unit": uv_per_model_unit,
                        "illustrative_minimum_event_uv": floor_uv,
                        "fraction_static_weights_suppressed_below_min_geometry": float(np.mean(low)),
                        "fraction_static_weights_suppressed_by_event_floor": float(np.mean(floor_mask)),
                        "fraction_static_weights_clipped_above_max_geometry": float(np.mean(high)),
                        "fraction_static_weights_rounded_at_charge_gap": float(np.mean(gap)),
                        "fraction_absolute_weight_mass_suppressed": float(
                            abs_weight[(realized_uv == 0) & (abs_weight > 0)].sum() / abs_weight.sum()),
                        "fraction_absolute_weight_mass_clipped_excess": float(
                            np.maximum(abs_weight - qmax / uv_per_model_unit, 0).sum() / abs_weight.sum()),
                        "local_spike_mismatch_vs_float_trace": float(np.mean(spikes != reference_spikes)),
                        "local_spike_mismatch_vs_replayed_float_current": float(np.mean(spikes != baseline_spikes)),
                        "local_spike_rate": float(spikes.mean()),
                        "current_abs_error_model_units_p50_p90_p99": [float(v) for v in np.quantile(
                            np.abs(current - reference_current), (.5, .9, .99))],
                    })
        stages.append({"stage": stage, "weight_count": int(weight.size),
                       "trace_shape": list(reference_current.shape),
                       "baseline_spike_rate": float(reference_spikes.mean()),
                       "baseline_replay_spike_mismatch": float(np.mean(baseline_spikes != reference_spikes)),
                       "absolute_weight_quantiles_p1_p50_p99_max": [float(v) for v in np.quantile(
                           abs_weight, (.01, .5, .99, 1.0))],
                       "screens": stage_rows})
    report = {"test": "sky130_static_mos_geometry_full_float_local_mapping_r2r_corrected" if use_r2r_correction else "sky130_static_mos_geometry_full_float_local_mapping",
              "checkpoint_sha256": digest, "checkpoint_epoch": 58,
              "qat_or_quantized_reference_used": False,
              "physical_condition": f"SS/0C; 10um differential MIM state; gate fractions 0.4-0.8; {EVENT_WIDTH_NS:g}ns positive event; physical MOS/TG",
              "geometry_scale_factors": list(WIDTHS),
              "geometry_transfer_monotone_by_bias": {
                  str(f): bool(np.all(np.diff(curves[f][0]) > 0)) for f in BIAS_FRACTIONS},
              "measured_positive_event_uv_by_gate_fraction": {
                  str(f): {"charge_uv": curves[f][0].tolist(), "source_results": curves[f][1]}
                  for f in BIAS_FRACTIONS},
              "shared_r2r_bias_transfer_correction": ({"bits": 12, "corner": "TT/27C",
                    "geometry_scale": 4, "gate_selection_slew_ns": 0.5,
                    "clamp_release_slew_ns": 1.0,
                    "measured_event_charge_ratio_to_ideal": {str(f): r2r_factors[f] for f in BIAS_FRACTIONS},
                    "source_reports": {str(f): r2r_sources[f] for f in BIAS_FRACTIONS},
                    "application_assumption": "apply each measured TT/27C geometry4 gain ratio uniformly to the four SS/0C geometry-width points for its gate bias; width/corner interaction is unmeasured"}
                    if use_r2r_correction else None),
              "stage_screens": stages,
              "scope": (f"Local replay of three frozen 64x64 full-float patch traces; source weight reference remains float32, no QAT/quantized weights. The {len(BIAS_FRACTIONS)}-bias/thirteen-geometry nearest-level mode selects among {len(BIAS_FRACTIONS)*len(WIDTHS)} measured event-charge levels rather than continuously interpolating weights. With R2R correction, measured TT/27C geometry4 charge ratios are applied uniformly to each SS/0C width curve by bias; width/corner independence is an unverified assumption. Each stage uses a freely chosen scale; frozen presynaptic inputs, learned beta and recorded thresholds are used with one subtractive reset per bin. This remains a simplified positive-event local replay without the physical R2R transient in the fan-in deck, polarity asymmetry, state-dependent transfer, mismatch/noise, inter-actor feedback, full-frame task accuracy, layout or population service."
                        if use_r2r_correction else
                        "Optimistic local replay of three frozen 64x64 full-float patch traces: weights whose desired single-event charge lies within a measured geometry/bias interval are represented continuously and exactly; sub-minimum weights are suppressed, over-maximum weights clipped and gap weights rounded to the nearest interval edge. Additional illustrative 1/10/100uV contribution floors omit small weights for sensitivity only; these are not measured physical noise thresholds. Each stage uses its own freely chosen scale. Frozen presynaptic inputs, learned beta and recorded thresholds are used with one subtractive reset per bin. Does not implement geometry personalization, five calibrated physical bias rails, negative polarity, full weighted physical event sequence, local mismatch/PVT, state-dependent transfer, feedback across actors, complete-frame task accuracy, noise, layout or population service."),
              }
    width_suffix = "" if EVENT_WIDTH_NS == 10.5 else f"_w{EVENT_WIDTH_NS:g}n".replace(".", "p")
    if SHARED_BANK_LOAD:
        width_suffix += "_banked"
    dest = RESULTS / (("sky130_ms_static_geometry_float_mapping_r2r_transfer_screen" if use_r2r_correction else "sky130_ms_static_geometry_float_mapping_screen") + width_suffix + ".json")
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(dest),
                      "stages": [{"stage": row["stage"],
                                  "best_local_spike_mismatch_by_mode": {
                                  mode: min(screen["local_spike_mismatch_vs_float_trace"]
                                                for screen in row["screens"] if screen["mode"] == mode
                                                and screen["illustrative_minimum_event_uv"] == 0)
                                      for mode in ("geometry_only", "shared_bias_continuous_geometry", nearest_mode)},
                                  "baseline_replay_spike_mismatch": row["baseline_replay_spike_mismatch"]}
                                 for row in stages]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
