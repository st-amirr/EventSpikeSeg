"""Collect physical first-segment float fan-in evidence without macro acceptance."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
BASE = "sky130_ms_first_touch_float_fanin_ss0"
TAIL = "stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_piecewise1"


def read(name: str) -> dict:
    row = json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))
    if (not row["simulation_completed"] or row["qat_or_quantized_reference_used"] or
            not row["piecewise_first_range"] or row["requested_above_measured_ceiling_count"] or
            row["requested_below_measured_floor_count"]):
        raise RuntimeError(f"invalid physical first-range fan-in: {name}")
    return row


def main() -> int:
    near_name = f"{BASE}_near_threshold_scale_{TAIL}_slot50p253n"
    high_name = f"{BASE}_high_cancellation_{TAIL}_slot55n"
    corrected_name = f"{BASE}_high_cancellation_{TAIL}_statebiasideal_slot55n"
    near = read(near_name)
    high = read(high_name)
    corrected = read(corrected_name)
    if (near["checkpoint_sha256"] != high["checkpoint_sha256"] or
            corrected["checkpoint_sha256"] != high["checkpoint_sha256"] or
            near["event_count"] != 329 or high["event_count"] != 322 or
            corrected["event_count"] != high["event_count"] or
            near["volts_per_model_unit"] != high["volts_per_model_unit"] or
            high.get("ideal_state_polarity_correction", False) or
            not corrected["ideal_state_polarity_correction"] or
            set(near["event_orders"]) != {"forward", "reverse", "shuffle"} or
            set(high["event_orders"]) != {"forward", "reverse", "shuffle"}):
        raise RuntimeError("physical first-range site records differ")
    def summarize(source: dict, source_name: str) -> dict:
        return {
            "source_result": f"{source_name}.json",
            "event_count": source["event_count"],
            "event_slot_ns": source["period_ns"],
            "ideal_signed_sum_uv": source["ideal_event_sum_v"] * 1e6,
            "physical_signed_sum_uv_by_order": {
                order: value * 1e6 for order, value in
                source["physical_final_minus_reference_v"].items()},
            "error_uv_by_order": {order: value * 1e6 for order, value in
                                  source["error_v_by_order"].items()},
            "maximum_order_spread_uv": source["max_order_spread_v"] * 1e6,
        }
    failed_name = f"{BASE}_high_cancellation_{TAIL}_slot50p253n"
    failed_log = (RES / f"{failed_name}.log").read_text(encoding="utf-8", errors="replace")
    if "Timestep too small" not in failed_log or "ngspice-36 done" not in failed_log:
        raise RuntimeError("expected failed 50.253ns high-cancellation solver screen")
    report = {
        "test": "sky130_first_piecewise_segment_actual_float_fanin_physical_boundary",
        "checkpoint_sha256": near["checkpoint_sha256"],
        "qat_or_quantized_reference_used": False,
        "segment_slope_v_per_model_unit": near["volts_per_model_unit"],
        "first_segment_limit_model_units": near["piecewise_first_range_limit_model_units"],
        "near_threshold_scale": summarize(near, near_name),
        "high_cancellation": summarize(high, high_name),
        "high_cancellation_with_ideal_state_polarity_command": summarize(corrected, corrected_name),
        "high_cancellation_shuffle_prefix_error_result":
            "sky130_piecewise_first_range_highcancel_prefix40.json",
        "high_cancellation_50p253ns_slot_solver_failed": True,
        "failed_solver_log": f"{failed_name}.log",
        "full_eight_range_physical_update_qualified": False,
        "physical_state_aware_polarity_control_implemented": False,
        "ideal_state_polarity_command_qualifies_mixed_weight_cancellation": False,
        "full_analog_architecture_ready": False,
        "scope": "Two saved final-fuse sites from the original float checkpoint, each fully inside the ideal eight-range map's first segment. A shared physical SKY130 13-geometry MOS bank, TG and 10um differential MIM receive ideal effective gate PWL commands derived from a zero-state measured transfer map. One high-cancellation variant adds an ideal per-event state estimate and a one-geometry polarity correction coefficient across all weights; it reduces some order errors but does not qualify the signed sum. No actual resistor ladder, state sensor, polarity feedback, range transition, threshold/beta/reset, noise/mismatch, 5ms hold or layout. The high-cancellation 50.253ns all-order deck failed transient convergence; the 55ns all-order deck completed, so slot-specific outcomes must stay separate."
    }
    path = RES / "sky130_piecewise_first_range_physical_boundary.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({site: report[site] for site in ("near_threshold_scale", "high_cancellation",
                                                   "high_cancellation_with_ideal_state_polarity_command")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
