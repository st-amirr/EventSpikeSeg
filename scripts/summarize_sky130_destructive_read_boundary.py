"""Source-hashed signed read, noise, and original-float sensitivity screen."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
BASE = "sky130_min_mim_offswitch_leakage_"
SUFFIX = "_sourcevcm_physicalmoscap_sharedread_inputw0.42um"


def load(name: str) -> tuple[dict, dict]:
    path = RESULTS / f"{name}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not value.get("simulation_completed", False) and "float_state_saturation" not in name:
        raise RuntimeError(f"incomplete source: {path}")
    return value, {"path": path.relative_to(ROOT).as_posix(),
                   "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def read_case(stem: str, label: str) -> dict:
    case, source = load(BASE + stem)
    rv = case["shared_read_values_v"]
    return {
        "label": label,
        "source": source,
        "corner": case["corner"],
        "temperature_c": case["temperature_c"],
        "commanded_rail_offset_mv": case["commanded_state_offset_from_vcm_mv"]
            * (-1 if case.get("reversed_state_polarity", False) else 1),
        "read_output_differential_mv": (rv["read_outn_end"] - rv["read_outp_end"]) * 1e3,
        "state_preconnect_differential_mv": (rv["read_high_before"] - rv["read_low_before"]) * 1e3,
        "state_end_differential_mv": (rv["read_high_end"] - rv["read_low_end"]) * 1e3,
        "state_common_mode_step_mv": ((rv["read_high_end"] + rv["read_low_end"])
                                      - (rv["read_high_before"] + rv["read_low_before"])) * 500,
    }


def main() -> None:
    transfer = [
        read_case("tt_temp27_offset0mv" + SUFFIX, "tt_zero"),
        read_case("tt_temp27_offset1mv" + SUFFIX, "tt_plus_1mv"),
        read_case("tt_temp27_offset1mv_reversed" + SUFFIX, "tt_minus_1mv"),
        read_case("tt_temp27_offset10mv" + SUFFIX, "tt_plus_10mv"),
        read_case("tt_temp27" + SUFFIX, "tt_plus_300mv"),
        read_case("tt_temp27_offset450mv" + SUFFIX, "tt_plus_450mv"),
        read_case("tt_temp27_offset750mv" + SUFFIX, "tt_plus_750mv"),
        read_case("tt_temp27_offset900mv" + SUFFIX, "tt_plus_900mv"),
        read_case("ss_temp0_offset1mv" + SUFFIX, "ss_plus_1mv"),
        read_case("ff_temp85_offset1mv" + SUFFIX, "ff_plus_1mv"),
    ]
    by_label = {row["label"]: row for row in transfer}
    zero = by_label["tt_zero"]["read_output_differential_mv"]
    plus = by_label["tt_plus_1mv"]["read_output_differential_mv"]
    minus = by_label["tt_minus_1mv"]["read_output_differential_mv"]
    sensor_noise, sensor_noise_source = load("sky130_diff_sensor_noise_tt_100k_size1_inputw0.42um")
    large_noise, large_noise_source = load("sky130_diff_sensor_noise_tt_100k_size1")
    output_per_rail_offset = (plus - minus) / 2
    high_range_output_gain = (by_label["tt_plus_900mv"]["read_output_differential_mv"]
                              - by_label["tt_plus_750mv"]["read_output_differential_mv"]) / 150
    inferred_rail_noise_uv = sensor_noise["integrated_output_noise_v_rms"] / (output_per_rail_offset * 1e-3) * 1000
    replays = []
    for index in (0, 1):
        replay, replay_source = load(
            f"sky130_float_state_saturation_validation_{index}_all_neurons_full_threshold_only_g1000_piecewise6_ideal_n165uv")
        replays.append({
            "source": replay_source, "record_index": index,
            "checkpoint_sha256": replay["checkpoint_sha256"],
            "qat_or_quantized_reference_used": replay["qat_or_quantized_reference_used"],
            "baseline_mean_iou": replay["baseline_present_class_mean_iou"],
            "noise_trial_mean_iou": [row["present_class_mean_iou"] for row in replay["trials"]],
            "noise_trial_pixel_agreement": [row["segmentation_pixel_agreement_with_float"] for row in replay["trials"]],
            "noise_trial_final_fuse_spike_mismatch": [row["final_fuse_spike_mismatch"] for row in replay["trials"]],
        })
    report = {
        "test": "sky130_prebiased_destructive_read_signed_transfer_and_float_noise_boundary",
        "transfer": transfer,
        "tt_zero_output_mv": zero,
        "tt_signed_plus_minus_output_mv": [plus, minus],
        "tt_signed_symmetry_error_mv": plus + minus - 2 * zero,
        "tt_output_mv_per_rail_offset_mv_near_zero": output_per_rail_offset,
        "tt_output_mv_per_rail_offset_mv_750_to_900": high_range_output_gain,
        "tt_near_zero_to_high_range_gain_ratio": output_per_rail_offset / high_range_output_gain,
        "small_sensor_noise_source": sensor_noise_source,
        "large_sensor_noise_source": large_noise_source,
        "small_sensor_stationary_output_noise_mv_rms_10hz_100khz":
            sensor_noise["integrated_output_noise_v_rms"] * 1e3,
        "small_sensor_illustrative_read_rail_noise_uv_rms": inferred_rail_noise_uv,
        "large_sensor_stationary_input_noise_uv_rms_10hz_100khz":
            large_noise["integrated_input_noise_v_rms"] * 1e6,
        "two_full_frame_original_float_165uv_threshold_noise_sensitivity": replays,
        "decision": "The deterministic signed read is monotone at the tested TT offsets and keeps the correct sign at SS/FF near 1mV. Because boundary writeback is required anyway, read disturbance may be calibrated if pre-read state is recoverable with sufficient noise/offset accuracy. The output is nearly saturated by the 750-900mV rail-offset range, with far lower local gain than near zero, so the direct sensor cannot cover the full rail-safe state range at uniform accuracy; a physical range-selection/readout method is required. The ideal encoding replay and stationary noise estimate do not establish accuracy or 5ms population service. The minimum schematic TG width barely improves read disturbance, so no minimum-TG layout is selected yet.",
        "limitations": "Physical state MIM/MOSCAP and existing access/read TG are separately extracted; combined cell is not routed. Shared differential sensor and ideal precharge/clock are schematic. Noise PSD is stationary open-loop at VCM, not the switched complete-path noise; the 165uV replay input is an illustrative rounded rail-equivalent transfer estimate, with ideal six-range encoding and no measured hold/read/write error. Only two full validation frames, not dataset-wide accuracy. No mismatch, calibration, writeback, event bucket, 5ms service or full-chip area proof.",
    }
    out = RESULTS / "sky130_destructive_read_boundary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "signed_output_mv": [minus, zero, plus],
                      "illustrative_rail_noise_uv": inferred_rail_noise_uv,
                      "replay_mean_iou_ranges": [[min(r["noise_trial_mean_iou"]), max(r["noise_trial_mean_iou"])] for r in replays]}, indent=2))


if __name__ == "__main__":
    main()
