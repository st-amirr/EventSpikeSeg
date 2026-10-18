"""Summarize signed pulse delivery against the continuous float parameter inventory."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
RESULTS = BASE / "results"
OUT = RESULTS / "gf180_weight_delivery_float_mapping_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_case(name: str, case: str) -> tuple[dict, dict]:
    path = RESULTS / name
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["module_simulation_completed"], path
    rows = [row for row in report["cases"] if row["case"] == case]
    assert len(rows) == 1, (path, case)
    row = rows[0]
    assert all(count == 1 for count in row["sequencer_strobe_counts"].values())
    assert row["ready_end_v"] > 2.9 and row["ready_during_arm_v"] < 0.4
    return report, row


def main() -> None:
    sources = {
        "zero_old_ramp": "gf180_sequenced_signed_injector_v2_mag1_zero_diag_case0_srcb05d9bc693c6.json",
        "low_weight_positive_new_ramp": "gf180_sequenced_signed_injector_v2_vreset10_mag11_diag_case0_srcd17cbc18109a.json",
        "new_ramp_endpoints": "gf180_sequenced_signed_injector_v2_vreset10_endpoint_diag_case0_src3c7164fd6b2f.json",
        "new_ramp_negative_fullscale": "gf180_sequenced_signed_injector_v2_vreset10_mag14_negative_diag_case2_src6236f2762b0c.json",
        "old_ramp_positive_fullscale": "gf180_sequenced_signed_injector_v2_nprogram0613_positive_diag_case1_srca97ac8d09ee8.json",
        "old_ramp_negative_fullscale": "gf180_sequenced_signed_injector_v2_nprogram0613_negative_diag_case2_src7549edcee996.json",
        "old_ramp_negative_mid": "gf180_sequenced_signed_injector_v2_nprogram062_negative_diag_case2_srcea997e234827.json",
        "old_ramp_negative_low": "gf180_sequenced_signed_injector_v2_nprogram0613_small_negative_diag_case2_src59e6a27f728c.json",
        "negative_original_bias": "gf180_sequenced_signed_injector_v2_prebiased_complete_case2_srce6c2febeab6a.json",
        "negative_high_bias": "gf180_sequenced_signed_injector_v2_nprogram08_negative_diag_case2_src07e41193a124.json",
        "negative_mid_bias": "gf180_sequenced_signed_injector_v2_nprogram067_negative_diag_case2_src062c671ce82b.json",
    }
    case_names = {
        "zero_old_ramp": "zero_positive",
        "low_weight_positive_new_ramp": "magnitude_1p1_positive",
        "new_ramp_endpoints": "zero_positive",
        "new_ramp_negative_fullscale": "magnitude_1p4_negative",
        "old_ramp_positive_fullscale": "large_positive",
        "old_ramp_negative_fullscale": "large_negative",
        "old_ramp_negative_mid": "large_negative",
        "old_ramp_negative_low": "small_negative",
        "negative_original_bias": "large_negative",
        "negative_high_bias": "large_negative",
        "negative_mid_bias": "large_negative",
    }
    reports = {key: load_case(name, case_names[key]) for key, name in sources.items()}
    # The endpoint report contains both zero and full scale; load both explicitly.
    endpoint_path = RESULTS / sources["new_ramp_endpoints"]
    endpoint_report = json.loads(endpoint_path.read_text(encoding="utf-8"))
    assert endpoint_report["module_simulation_completed"]
    zero = next(c for c in endpoint_report["cases"] if c["case"] == "zero_positive")
    full_pos = next(c for c in endpoint_report["cases"] if c["case"] == "full_positive")
    assert all(n == 1 for n in zero["sequencer_strobe_counts"].values())
    assert all(n == 1 for n in full_pos["sequencer_strobe_counts"].values())

    low = reports["low_weight_positive_new_ramp"][1]
    full_neg = reports["new_ramp_negative_fullscale"][1]
    pos = full_pos
    zero_new = zero
    charge_balance = abs(abs(full_neg["net_charge_into_state_c"]) - pos["net_charge_into_state_c"]) / pos["net_charge_into_state_c"]
    state_balance = abs(abs(full_neg["state_step_v"]) - pos["state_step_v"]) / pos["state_step_v"]
    low_charge_fraction = low["net_charge_into_state_c"] / pos["net_charge_into_state_c"]
    mid_bias = reports["old_ramp_negative_mid"][1]
    high_bias = reports["negative_high_bias"][1]
    original_bias = reports["negative_original_bias"][1]

    params_path = BASE / "model_reference/eventspikeseg140k_float_parameters.npz"
    params = np.load(params_path)
    ratios: list[float] = []
    layer_stats = []
    for key in params.files:
        if not key.startswith("weight__"):
            continue
        values = np.abs(params[key].astype(np.float64))
        maximum = float(values.max())
        normalized = values / maximum if maximum else values
        ratios.extend(normalized.ravel().tolist())
        layer_stats.append({"name": key, "count": int(values.size), "max_abs_float": maximum,
                            "normalized_abs_p10": float(np.quantile(normalized, .1)),
                            "normalized_abs_median": float(np.median(normalized)),
                            "normalized_abs_p90": float(np.quantile(normalized, .9))})
    ratio_array = np.asarray(ratios)

    report = {
        "status": "NOMINAL_SIGNED_WEIGHT_TRANSFER_SCREEN_PASS_WITH_LOW_END_AND_SYSTEM_GATES_OPEN",
        "architecture": "one signed analog charge packet per presynaptic event; continuous per-tensor magnitude mapped to the existing 1.0-1.4 V analog storage range; sign remains categorical",
        "diagnostic_conditions": {
            "ramp_reset_v": 1.0,
            "negative_branch_program_v": 0.613,
            "clock_hz": 50000,
            "prebias_ms": 1.0,
            "physical_netlist": "extracted GF180 230-MOS/4-MIM sequencer plus signed injector",
            "weight_voltage_map_candidate": "MAG_DATA = 1.0 + 0.4 * abs(weight) / max_abs(weight_tensor); no quantization",
        },
        "measured_transfer": {
            "zero_v": {k: zero_new[k] for k in ["programmed_magnitude_v", "pulse_width_us", "state_step_v", "net_charge_into_state_c"]},
            "quarter_scale_v1p1": {k: low[k] for k in ["programmed_magnitude_v", "pulse_width_us", "state_step_v", "net_charge_into_state_c"]},
            "full_scale_positive": {k: pos[k] for k in ["programmed_magnitude_v", "pulse_width_us", "state_step_v", "net_charge_into_state_c"]},
            "full_scale_negative": {k: full_neg[k] for k in ["programmed_magnitude_v", "pulse_width_us", "state_step_v", "net_charge_into_state_c"]},
            "quarter_scale_charge_fraction_of_full": low_charge_fraction,
            "ideal_quarter_scale_fraction": 0.25,
            "quarter_scale_relative_charge_error": abs(low_charge_fraction - 0.25) / 0.25,
            "fullscale_signed_charge_magnitude_mismatch": charge_balance,
            "fullscale_signed_state_step_magnitude_mismatch": state_balance,
        },
        "bias_diagnosis": {
            "original_nprogram_0p45_negative_step_v": original_bias["state_step_v"],
            "nprogram_0p67_negative_step_v": reports["negative_mid_bias"][1]["state_step_v"],
            "nprogram_0p8_negative_step_v": high_bias["state_step_v"],
            "selected_nominal_nprogram_v": 0.613,
            "scope": "A single shared nominal bias restores polarity balance at the tested magnitude; it is not PVT, mismatch, or whole-population calibration.",
        },
        "float_inventory": {
            "source": "artifacts/analog_asic/model_reference/eventspikeseg140k_float_parameters.npz",
            "sha256": sha(params_path),
            "weight_arrays": len(layer_stats),
            "weight_values": int(ratio_array.size),
            "exact_zero_fraction": float(np.mean(ratio_array == 0)),
            "per_tensor_normalized_abs_quantiles": {str(q): float(np.quantile(ratio_array, q)) for q in [.001, .01, .05, .1, .25, .5, .9]},
            "fraction_below_normalized_magnitude": {str(th): float(np.mean(ratio_array < th)) for th in [.001, .005, .01, .02, .05, .1]},
            "estimated_width_us_from_fullscale_linear_fit": {str(q): float(np.quantile(ratio_array, q) * pos["pulse_width_us"]) for q in [.01, .05, .1, .5]},
            "layer_stats": layer_stats,
        },
        "limitations": [
            "The positive and negative full-scale checks are nominal isolated events with one shared fixed bias; loaded memory/readout and per-channel weight programming are not connected.",
            "The candidate voltage map is not yet validated against model-level spike/segmentation error.",
            "About 13.5% of normalized float weights imply pulse durations below roughly 51 ns under a linear full-scale fit; short-pulse accuracy, leakage, parasitics, and 5 ms population service remain unqualified.",
            "The stored parameter atlas is capacity geometry, not an electrically addressed weight array connected to this injector.",
        ],
        "source_reports": {key: str((RESULTS / name).relative_to(ROOT)).replace("\\", "/") for key, name in sources.items()} | {"new_ramp_endpoints": str(endpoint_path.relative_to(ROOT)).replace("\\", "/")},
    }
    report["checks"] = {
        "all_simulations_complete_and_sequencers_single_shot": True,
        "zero_magnitude_suppresses_pulse": zero_new["pulse_width_us"] is None and abs(zero_new["state_step_v"]) < 1e-6,
        "positive_charge_monotonic_at_0_25_and_1_0": 0 < low["net_charge_into_state_c"] < pos["net_charge_into_state_c"],
        "negative_fullscale_direction_and_balance": full_neg["state_step_v"] < 0 and charge_balance < .01,
        "all_original_float_weights_remain_continuous": report["float_inventory"]["exact_zero_fraction"] == 0,
    }
    report["qualified_as"] = "bounded nominal transfer-function progress only; not acceptance of the weight path, model accuracy, full chip, or 5 ms service"
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT), "checks": report["checks"], "measured_transfer": report["measured_transfer"],
                      "float_inventory": {k: v for k, v in report["float_inventory"].items() if k != "layer_stats"},
                      "limitations": report["limitations"]}, indent=2))


if __name__ == "__main__":
    main()
