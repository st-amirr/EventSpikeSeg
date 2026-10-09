"""Summarize original-float full-frame MOS retention sensitivity with coverage."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
EXPECTED_SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def load(record: int, *, noise: bool, retention: str, mapping: str = "piecewise") -> dict:
    stem = (f"sky130_float_state_saturation_validation_{record}_all_neurons_full_"
            f"{'reset_only' if noise else 'none'}_"
            f"{'g10000_piecewise8_ideal' if mapping == 'piecewise' else 'g1'}"
            f"{'_n113uv' if noise else ''}"
            f"{'_mos_tt_retention_window' if retention == 'narrow' else ''}"
            f"{'_mos_tt_rail_window' if retention == 'rail' else ''}")
    report = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
    law = {"none": "none", "narrow": "mos-tt-measured-window", "rail": "mos-tt-rail-window"}[retention]
    if (report["checkpoint_sha256"] != EXPECTED_SHA or
            report["qat_or_quantized_reference_used"] or
            report["retention_law"] != law or
            report["noise_mode"] != ("reset-only" if noise else "none") or
            report["encoding"] != ("piecewise-ideal" if mapping == "piecewise" else "linear-clipped") or
            report["scope"] != "all-neurons" or not report["full_frame"] or
            report["gains"] != ([10000.0] if mapping == "piecewise" else [1.0]) or
            len(report["trials"]) != (3 if noise else 1) or
            report.get("injected_state_noise_sigma_uv_rms", 0.0) != (113.0 if noise else 0.0)):
        raise RuntimeError(f"wrong float replay provenance for record{record} {noise=} {retention=}")
    return report


def summarize(report: dict) -> dict:
    trials = report["trials"]
    if len(trials) == 3 and [row["seed"] for row in trials] != [1729, 1730, 1731]:
        raise RuntimeError("unexpected noise seeds")
    counts = [row["measured_retention_window_state_accesses"] for row in trials]
    coverage = ([item["inside"] / (item["inside"] + item["outside"]) for item in counts]
                if report["retention_law"] != "none" else [])
    return {
        "trial_count": len(trials),
        "mean_measured_voltage_window_fraction": statistics.mean(coverage) if coverage else None,
        "mean_final_fuse_spike_mismatch": statistics.mean(
            row["final_fuse_spike_mismatch"] for row in trials),
        "mean_pixel_agreement_with_float": statistics.mean(
            row["segmentation_pixel_agreement_with_float"] for row in trials),
        "mean_labeled_accuracy": statistics.mean(
            row["labeled_pixel_accuracy"] for row in trials),
        "mean_present_class_mean_iou": statistics.mean(
            row["present_class_mean_iou"] for row in trials),
    }


def main() -> int:
    rows = []
    for record in (0, 1):
        control = load(record, noise=False, retention="none")
        narrow = load(record, noise=False, retention="narrow")
        rail = load(record, noise=False, retention="rail")
        noise_only = load(record, noise=True, retention="none")
        combined = load(record, noise=True, retention="rail")
        linear_control = load(record, noise=False, retention="none", mapping="linear")
        linear_rail = load(record, noise=False, retention="rail", mapping="linear")
        linear_noise_only = load(record, noise=True, retention="none", mapping="linear")
        linear_combined = load(record, noise=True, retention="rail", mapping="linear")
        base = summarize(control)
        if base["mean_final_fuse_spike_mismatch"] != 0 or base["mean_pixel_agreement_with_float"] != 1:
            raise RuntimeError("zero-drift control differs from original full float")
        linear_base = summarize(linear_control)
        if linear_base["mean_final_fuse_spike_mismatch"] != 0 or linear_base["mean_pixel_agreement_with_float"] != 1:
            raise RuntimeError("linear zero-drift control differs from original full float")
        if (narrow["retention_source"] != "sky130_mos_decay_prediction_boundary.json" or
                rail["retention_source"] != "sky130_mos_fullrail_hold_boundary.json" or
                combined["retention_source"] != rail["retention_source"]):
            raise RuntimeError("wrong physical hold source")
        rows.append({
            "record_index": record,
            "baseline_labeled_accuracy": control["baseline_labeled_pixel_accuracy"],
            "baseline_present_class_mean_iou": control["baseline_present_class_mean_iou"],
            "zero_drift_zero_noise": base,
            "narrow_window_drift_only": summarize(narrow),
            "rail_window_drift_only": summarize(rail),
            "noise_113uv_only": summarize(noise_only),
            "rail_window_drift_plus_noise_113uv": summarize(combined),
            "linear_zero_drift_zero_noise": linear_base,
            "linear_rail_window_drift_only": summarize(linear_rail),
            "linear_noise_113uv_only": summarize(linear_noise_only),
            "linear_rail_window_drift_plus_noise_113uv": summarize(linear_combined),
        })
    report = {
        "checkpoint_sha256": EXPECTED_SHA,
        "qat_or_quantized_reference_used": False,
        "encoding": "ideal_8_segment_piecewise_R10000_per_actor_per_record_maximum",
        "physical_retention_sources": ["sky130_mos_decay_prediction_boundary.json",
                                       "sky130_mos_fullrail_hold_boundary.json"],
        "scope": "Two complete DSEC validation records and all 25 float PLIF actors. Ideal per-record normalized linear and eight-segment piecewise state encodings. Measured SKY130 TT MOS-gate/TG 5ms drift is interpolated inside physical voltage windows before each semantic update; outside states remain ideal. The rail profile excludes 0V programming because its sampled gate was below the documented MOS model voltage range. Three seeded 113uV Gaussian differential reset-noise trials are an optimistic kT/C-scale proxy, not physical switched noise. Ideal per-record gain/programming and ideal nonlinear event encoding/inverse; no physical readout, PVT/mismatch, injector error, beta/threshold circuit, layout or service. Not dataset-wide accuracy or an accepted architecture.",
        "rows": rows,
        "analog_architecture_ready": False,
    }
    (RES / "sky130_mos_retention_float_boundary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
