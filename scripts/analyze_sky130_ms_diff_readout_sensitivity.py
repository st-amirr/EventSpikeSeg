"""Bound physical threshold and 20um-pair noise against frozen full-float PLIF spikes."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from analyze_sky130_cap_kTC_float_sensitivity import replay

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
OUT = ROOT / "artifacts/analog_asic/results/sky130_ms_diff_readout_float_sensitivity.json"
STAGE = "final_fuse__standard"


def main() -> int:
    trace = np.load(REF / "float_patch_trace.npz")
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    current = trace[f"current__{STAGE}"].astype(np.float64)
    candidate = trace[f"candidate__{STAGE}"].astype(np.float64)
    threshold = trace[f"threshold__{STAGE}"].astype(np.float64)
    captured = trace[f"spikes__{STAGE}"].astype(bool)
    beta = params[f"beta__{STAGE}"].astype(np.float64).reshape(1, -1, 1, 1)
    headroom_v = 0.15
    v_per_unit = headroom_v / float(np.max(np.abs(candidate)))
    baseline = replay(current, beta, threshold)
    offset_rows = []
    for offset_uv in (-10, -3, -1, -0.1, 0.1, 1, 3, 10):
        shifted = threshold + offset_uv * 1e-6 / v_per_unit
        got = replay(current, beta, shifted)
        offset_rows.append({"threshold_offset_uv": offset_uv,
                            "spike_mismatch_vs_baseline": float(np.mean(got != baseline))})
    k_b = 1.380649e-23
    c_one_f = (2.0 * 20 * 20 + 0.19 * 4 * 20) * 1e-15
    sigma_pair_v = float(np.sqrt(2 * k_b * 300 / c_one_f))
    sigma_units = sigma_pair_v / v_per_unit
    rng = np.random.default_rng(1729)
    mismatch = []
    for _ in range(8):
        initial = rng.normal(0, sigma_units, size=current.shape[1:])
        reset_noise = rng.normal(0, sigma_units, size=current.shape)
        got = replay(current, beta, threshold, reset_noise=reset_noise, initial_noise=initial)
        mismatch.append(float(np.mean(got != baseline)))
    out = {
        "test": "sky130_20um_diff_mim_threshold_offset_and_kTC_float_sensitivity",
        "stage": STAGE, "headroom_v": headroom_v, "volts_per_model_unit": v_per_unit,
        "baseline_replay_mismatch_vs_captured": float(np.mean(baseline != captured)),
        "learned_threshold_voltage_uv_min_max": [float(np.min(threshold) * v_per_unit * 1e6),
                                                   float(np.max(threshold) * v_per_unit * 1e6)],
        "threshold_offset_cases": offset_rows,
        "mim_width_um": 20, "mim_capacitance_one_f": c_one_f,
        "independent_pair_kTC_sigma_uv": sigma_pair_v * 1e6,
        "reset_only_kTC_trials": mismatch,
        "reset_only_kTC_mean_spike_mismatch": float(np.mean(mismatch)),
        "scope": "Three frozen 64x64 patches of one final-fusion PLIF stage from the best-validation float checkpoint. Captured upstream currents are fixed. A deterministic threshold shift and independent Gaussian MIM kT/C at initial state and post-spike reset are software sensitivity proxies, not measured comparator offset/noise, transistor transient noise, closed-loop network behavior, or segmentation accuracy.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "threshold_voltage_uv": out["learned_threshold_voltage_uv_min_max"],
                      "pair_kTC_sigma_uv": out["independent_pair_kTC_sigma_uv"],
                      "kTC_mean_spike_mismatch": out["reset_only_kTC_mean_spike_mismatch"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
