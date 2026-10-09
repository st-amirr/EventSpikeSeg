#!/usr/bin/env python3
"""Summarize matched-corner full-float companding/noise replay reports."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
CHECKPOINT_SHA256 = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
RETENTION_TOKEN = "mos_gate_bank_hold_vcm_loaded_injisolate_pextg_ss_temp0_mos_gate_state_pair_100x10_nf10_5ms"


def load_match(pattern: str) -> dict:
    paths = list(RESULTS.glob(pattern))
    if len(paths) != 1:
        raise RuntimeError(f"expected one report for {pattern!r}, got {len(paths)}")
    report = json.loads(paths[0].read_text(encoding="utf-8"))
    if (report.get("checkpoint_sha256") != CHECKPOINT_SHA256
            or report.get("qat_or_quantized_reference_used") is not False
            or report.get("full_frame") is not True
            or report.get("scope") != "all-neurons"
            or report.get("noise_mode") != "reset-only"
            or report.get("injected_state_noise_sigma_uv_rms") != 24.0
            or report.get("retention_law") != "measured-vcm-differential"
            or report.get("retention_profile_metadata", {}).get("mos_corner") != "ss"
            or report.get("retention_profile_metadata", {}).get("temperature_c") != 0
            or report.get("retention_profile_metadata", {}).get("simulation_completed") is not True):
        raise RuntimeError(f"report does not match the full-float, SS/0C, 24uV replay contract: {paths[0]}")
    report["_source_path"] = str(paths[0].relative_to(ROOT))
    return report


def selected_trials(report: dict, gain: float) -> list[dict]:
    rows = [row for row in report["trials"]
            if math.isclose(row["linear_gain_relative_to_max_fitting_range"], gain)]
    if len(rows) != 3:
        raise RuntimeError(f"expected three seeds at gain {gain:g}, got {len(rows)}")
    return rows


def summarize(report: dict, gain: float) -> dict:
    trials = selected_trials(report, gain)
    keys = ("final_fuse_spike_mismatch", "segmentation_pixel_agreement_with_float",
            "labeled_pixel_accuracy", "present_class_mean_iou")
    return {
        "record_index": report["record_index"],
        "sequence_id": report["sequence_id"],
        "baseline_labeled_pixel_accuracy": report["baseline_labeled_pixel_accuracy"],
        "baseline_present_class_mean_iou": report["baseline_present_class_mean_iou"],
        "gain": gain,
        "segment_count": report["piecewise_segment_count"],
        "near_zero_voltage_gain_relative_to_linear": trials[0]["near_zero_voltage_gain_relative_to_linear"],
        "trials": [{"seed": row["seed"], **{key: row[key] for key in keys}} for row in trials],
        "mean": {key: sum(row[key] for row in trials) / len(trials) for key in keys},
        "measured_retention_window_state_accesses": trials[0]["measured_retention_window_state_accesses"],
        "source_retention_profile": report["retention_source"],
        "source_report": report["_source_path"],
    }


def main() -> int:
    reports = []
    for segments in (2, 4, 6):
        pattern = (f"sky130_float_state_saturation_validation_0_all_neurons_full_reset_only_"
                   f"g1000_piecewise{segments}_ideal_n24uv_mos_vcm_diff_profile*{RETENTION_TOKEN}.json")
        reports.append(summarize(load_match(pattern), 1000))
    pattern = (f"sky130_float_state_saturation_validation_0_all_neurons_full_reset_only_"
               f"g10-100-1000_piecewise8_ideal_n24uv_mos_vcm_diff_profile*{RETENTION_TOKEN}.json")
    reports.append(summarize(load_match(pattern), 1000))
    pattern = (f"sky130_float_state_saturation_validation_1_all_neurons_full_reset_only_"
               f"g1000_piecewise6_ideal_n24uv_mos_vcm_diff_profile*{RETENTION_TOKEN}.json")
    reports.append(summarize(load_match(pattern), 1000))
    slope_spans = {}
    for count in (2, 4, 6, 8):
        gain = 1000.0
        arc = math.asinh(gain)
        scale = 1.0 / gain
        knots = [scale * math.sinh(arc * i / count) for i in range(count + 1)]
        slopes = [(0.9 / count) / (knots[i + 1] - knots[i]) for i in range(count)]
        slope_spans[str(count)] = {"voltage_gain_by_segment": slopes,
                                   "max_to_min_update_gain_ratio": max(slopes) / min(slopes)}
    output = {
        "test": "matched_corner_full_float_analog_state_companding_sensitivity",
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "qat_or_quantized_reference_used": False,
        "full_frame_scope": "all-neurons, DSEC validation records0 and1",
        "state_noise_sigma_uv_rms": 24.0,
        "noise_mode": "independent noise at initialization and after each subtractive spike reset, preserving reset state",
        "retention": "measured SKY130 SS/0C differential MOS gate-bank + extracted TG 5ms profile; all counted accesses in profile window",
        "gain": 1000,
        "segment_slope_frontier": slope_spans,
        "cases": reports,
        "physical_encoder_or_update_circuit_implemented": False,
        "accuracy_interpretation": "Ideal per-record piecewise encoder/inverse, ideal weights/updates/readout/threshold, noise proxy rather than transient PDK noise. Results are model sensitivity bounds, not circuit acceptance or validation-set qualification.",
    }
    path = RESULTS / "sky130_companded_fullfloat_replay_summary.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
