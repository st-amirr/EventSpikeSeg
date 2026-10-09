"""Bound the present sampled readout using extracted area and existing noise data.

This is an analytic architecture gate, not a switched-noise or yield simulation.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
LAYOUT = ROOT / "artifacts/analog_asic/layout"
SOURCES = {
    "settled_readout": RESULTS / "sky130_readout_settled_pvt_population_gate.json",
    "sample_bank": LAYOUT / "sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30_qualification.json",
    "trim_pair": LAYOUT / "sky130_differential_trim_cap_pair/qualification.json",
    "ota_noise": RESULTS / "sky130_ms_diff_ota_noise_tt_temp27_w4_cc20_f1-1e+07_unity.json",
    "float_margins": RESULTS / "sky130_float_threshold_margin_distribution.json",
}
OUT = RESULTS / "sky130_readout_sample_noise_service_gate.json"
K_B = 1.380649e-23
T_K = 300.0


def main() -> None:
    data = {key: json.loads(path.read_text(encoding="utf-8")) for key, path in SOURCES.items()}
    checksums = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in SOURCES.items()}
    readout = data["settled_readout"]
    sample = data["sample_bank"]
    trim = data["trim_pair"]
    ota = data["ota_noise"]
    margin = data["float_margins"]
    assert sample["drc_zero_errors"] and sample["netgen_unique_match"]
    assert trim["magic_drc_zero"] and trim["netgen_unique_match"]
    assert ota["simulation_completed"]
    assert len(readout["cases"]) == 6 and all(row["completed"] for row in readout["cases"])
    n_state = readout["population_replication_bound"]["logical_state_count"]
    n_channels = readout["population_replication_bound"]["minimum_parallel_channels"]
    c_leg_f = sample["extracted_bank_ceff_f"]
    sample_pair_bbox_mm2 = 2 * math.prod(sample["gds_bbox_um"]) / 1e6
    trim_bbox_mm2 = math.prod(trim["gds_bbox_um"]) / 1e6
    sample_diff_uv = math.sqrt(2 * K_B * T_K / c_leg_f) * 1e6
    # The two-swap chopper signal gain is G - 0.5 = 9.6 for G=10.1.
    signal_gain = 9.6
    # The sampled phase difference is twice the demodulated output. A differential
    # sample-cap noise term therefore refers to the input through 2*(G-0.5).
    sampled_phase_gain = 2 * signal_gain
    sample_input_uv = sample_diff_uv / sampled_phase_gain
    ota_diff_uv = ota["ideal_boxcar_sample_aperture_noise_v_rms"]["1us"]["two_independent_buffers_differential_v_rms"] * 1e6
    q01_uv = margin["all"]["absolute_margin_quantiles_mapped_uv"]["0.1"]
    measured_max_error_uv = readout["max_abs_input_referred_error_uv"]
    report = {
        "test": "sky130_current_sampled_readout_noise_and_service_gate",
        "source_files_and_sha256": {key: {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": checksums[key]}
                                    for key, path in SOURCES.items()},
        "full_float_checkpoint_sha256": margin["checkpoint_sha256"],
        "qat_or_quantized_reference_used": False,
        "current_readout": {
            "deterministic_signed_5ms_cases": len(readout["cases"]),
            "all_selected_corner_codes_pass": all(row["latch_decision_correct"] for row in readout["cases"]),
            "selected_codes_are_external": readout["selected_corner_codes_are_calibrated_externally"],
            "maximum_input_referred_deterministic_error_uv": measured_max_error_uv,
            "one_channel_sequential_decision_us": 30,
            "one_us_sampling_aperture": True,
            "demodulated_signal_gain": signal_gain,
            "sampled_phase_difference_signal_gain": sampled_phase_gain,
        },
        "extracted_sample_bank": {
            "capacitance_per_leg_f": c_leg_f,
            "bbox_per_leg_um": sample["gds_bbox_um"],
            "two_leg_bbox_area_mm2_per_channel": sample_pair_bbox_mm2,
            "two_leg_bbox_area_mm2_at_minimum_parallel_channels": sample_pair_bbox_mm2 * n_channels,
            "independent_sampling_thermal_differential_uv_rms_at_300k": sample_diff_uv,
            "independent_sampling_thermal_input_equivalent_uv_rms_at_phase_gain_19p2": sample_input_uv,
        },
        "compact_trim_pair": {
            "bbox_um": trim["gds_bbox_um"],
            "bbox_area_mm2_per_channel": trim_bbox_mm2,
            "bbox_area_mm2_at_minimum_parallel_channels": trim_bbox_mm2 * n_channels,
            "note": "Two small MIM units only; no demonstrated full offset range, selector, calibration or readout integration.",
        },
        "ota_small_signal_noise_estimate": {
            "source_corner": ota["mos_corner"],
            "source_temperature_c": ota["temperature_c"],
            "integration_band_hz": ota["integration_band_hz"],
            "ideal_one_us_two_independent_buffer_boxcar_differential_uv_rms": ota_diff_uv,
            "q0p1_buffer_input_differential_signal_uv": q01_uv,
            "raw_buffer_noise_to_q0p1_input_signal_ratio": ota_diff_uv / q01_uv,
            "scope": ota["correlation_model_scope"],
        },
        "conditional_comparison": {
            "full_float_exploratory_mapping_q0p1_absolute_margin_uv": q01_uv,
            "sample_thermal_to_margin_ratio": sample_input_uv / q01_uv,
            "deterministic_error_to_margin_ratio": measured_max_error_uv / q01_uv,
            "interpretation": "The q0.1 voltage is one exploratory original-float state mapping, not an established required noise specification. OTA buffer noise is before the chopper gain; no direct input-equivalent or combined noise is assigned without a complete transfer/noise simulation. Ratios are screening comparisons, not predicted task error rates.",
        },
        "service": {
            "logical_resident_states": n_state,
            "semantic_bin_us": 5000,
            "zero_overhead_minimum_parallel_channels": n_channels,
            "sample_bank_bbox_only_floor_mm2": sample_pair_bbox_mm2 * n_channels,
            "trim_pair_bbox_only_floor_mm2": trim_bbox_mm2 * n_channels,
            "excludes": ["state storage", "OTA/chopper", "latch", "switches", "calibration", "bias", "clock", "spacing", "routing", "DAG dependency and contention"],
        },
        "decision": "The present 30us, two-large-sample-bank readout is a deterministic module demonstrator, not a scalable or noise-qualified full-chip readout. Replacing only the trim macro cannot remove the sample-bank area or the upstream OTA noise concern. Evaluate a different analog sensing/state organization and require switched-noise, mismatch, full-float replay and actual service evidence before layout promotion.",
        "limitations": "Thermal kT/C assumes two independent equilibrium sampled capacitors; actual switching and correlations are unknown. OTA estimate is ideal small-signal boxcar under ideal bias, not switched transient noise. Bounding-box replication is an area floor for this direct channel mapping only. No full validation-set accuracy or yield inference is made.",
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(OUT), "sample_bank_floor_mm2": report["service"]["sample_bank_bbox_only_floor_mm2"],
                      "sample_noise_input_uv": sample_input_uv, "ota_buffer_noise_uv": ota_diff_uv,
                      "q0p1_margin_uv": q01_uv}, indent=2))


if __name__ == "__main__":
    main()
