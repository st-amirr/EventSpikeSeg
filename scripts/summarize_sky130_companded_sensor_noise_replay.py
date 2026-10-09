"""Summarize two original-float full-frame sensor-noise sensitivity replays."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
NOISE = RESULTS / "sky130_diff_sensor_noise_ss_1meg_size100.json"
SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def main() -> None:
    sensor = json.loads(NOISE.read_text(encoding="utf-8"))
    assert sensor["simulation_completed"] and sensor["corner"] == "ss"
    sigma_uv = sensor["integrated_input_noise_v_rms"] * 1e6
    records = []
    for index in (0, 1):
        matches = list(RESULTS.glob(
            f"sky130_float_state_saturation_validation_{index}_all_neurons_full_"
            "threshold_only_g1000_piecewise6_ideal_n24.8009uv_mos_vcm_diff_profile_"
            "sky130_mos_gate_bank_hold_vcm_loaded_injisolate_pextg_ss_temp0_"
            "mos_gate_state_pair_100x10_nf10_5ms.json"))
        if len(matches) != 1:
            raise RuntimeError(f"record {index}: expected one replay, got {len(matches)}")
        path = matches[0]
        source = json.loads(path.read_text(encoding="utf-8"))
        if (source["checkpoint_sha256"] != SHA or source["qat_or_quantized_reference_used"] is not False
                or source["noise_mode"] != "threshold-only" or source["encoding"] != "piecewise-ideal"
                or source["piecewise_segment_count"] != 6 or source["full_frame"] is not True
                or source["scope"] != "all-neurons" or source["retention_law"] != "measured-vcm-differential"
                or abs(source["injected_threshold_noise_sigma_uv_rms"] - sigma_uv) > 1e-8):
            raise RuntimeError(f"record {index}: replay contract mismatch")
        trials = [row for row in source["trials"] if row["linear_gain_relative_to_max_fitting_range"] == 1000]
        if len(trials) != 3 or any(row["measured_retention_window_state_accesses"]["outside"] for row in trials):
            raise RuntimeError(f"record {index}: trial/retention coverage mismatch")
        metrics = ("final_fuse_spike_mismatch", "segmentation_pixel_agreement_with_float",
                   "labeled_pixel_accuracy", "present_class_mean_iou")
        records.append({
            "record_index": index,
            "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "baseline_labeled_pixel_accuracy": source["baseline_labeled_pixel_accuracy"],
            "baseline_present_class_mean_iou": source["baseline_present_class_mean_iou"],
            "means": {key: sum(row[key] for row in trials) / len(trials) for key in metrics},
            "trial_seeds": [row["seed"] for row in trials],
            "measured_retention_window_state_accesses_per_trial": trials[0]["measured_retention_window_state_accesses"]["inside"],
        })
    report = {
        "test": "original_float_six_range_ideal_companding_threshold_noise_sensitivity",
        "checkpoint_sha256": SHA,
        "qat_or_quantized_reference_used": False,
        "source_sensor_noise_report": str(NOISE.relative_to(ROOT)).replace("\\", "/"),
        "source_sensor_noise_sha256": hashlib.sha256(NOISE.read_bytes()).hexdigest(),
        "sensor_ss_0c_small_signal_input_noise_uv_rms_10hz_to_1mhz": sigma_uv,
        "ideal_threshold_noise_proxy_uv_rms": sigma_uv,
        "piecewise_segments": 6,
        "ideal_per_actor_range_gain": 1000,
        "records": records,
        "interpretation": "Two DSEC frames and three independent noise seeds per frame preserve approximate mean IoU under this ideal full-float six-range/noise proxy, but alter many spikes and pixels. The physical range encoder, signed weighted event update, comparator transfer, switched noise/correlation, mismatch, layout and 5ms service are absent. This is a sensitivity screen, not accuracy qualification or evidence that the 100-device sensor is area-feasible.",
    }
    out = RESULTS / "sky130_companded_sensor_noise_replay_summary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "records": records}, indent=2))


if __name__ == "__main__":
    main()
