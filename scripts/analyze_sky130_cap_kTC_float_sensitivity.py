"""Screen sampled full-float PLIF spikes against a MIM kT/C noise scale.

This is a software sensitivity bound, not a transistor transient-noise simulation.
The candidate/state voltage scale is varied while the ordinary float checkpoint
and the captured full-float input currents remain fixed.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RESULTS = ROOT / "artifacts/analog_asic/results"
TRACE_META = REF / "float_patch_trace.json"
TRACE_NPZ = REF / "float_patch_trace.npz"
PARAM_NPZ = REF / "eventspikeseg140k_float_parameters.npz"
STAGE = "final_fuse__standard"
SEED = 1729
TRIALS = 8
HEADROOMS_V = (0.30, 0.60)


def replay(current: np.ndarray, beta: np.ndarray, threshold: np.ndarray,
           noise: np.ndarray | None = None,
           reset_noise: np.ndarray | None = None,
           initial_noise: np.ndarray | None = None) -> np.ndarray:
    state = (np.zeros_like(current[0], dtype=np.float64) if initial_noise is None
             else initial_noise.astype(np.float64, copy=True))
    spikes = []
    for tick in range(current.shape[0]):
        candidate = beta * state + current[tick]
        if noise is not None:
            candidate = candidate + noise[tick]
        fired = candidate >= threshold[tick]
        spikes.append(fired)
        state = candidate - fired * threshold[tick]
        if reset_noise is not None:
            state = np.where(fired, reset_noise[tick], state)
    return np.stack(spikes)


def main() -> int:
    meta = json.loads(TRACE_META.read_text(encoding="utf-8"))
    trace = np.load(TRACE_NPZ)
    params = np.load(PARAM_NPZ)
    current = trace[f"current__{STAGE}"].astype(np.float64)
    candidate_ref = trace[f"candidate__{STAGE}"].astype(np.float64)
    threshold = trace[f"threshold__{STAGE}"].astype(np.float64)
    expected = trace[f"spikes__{STAGE}"].astype(bool)
    beta = params[f"beta__{STAGE}"].astype(np.float64).reshape(1, -1, 1, 1)

    replayed = replay(current, beta, threshold)
    baseline_mismatch = float(np.mean(replayed != expected))

    # Estimate membrane-cap value from the measured 10um MIM capacitor report.
    # Sweep geometry explicitly: 100um is the SPICE bench cap, not a proposed
    # per-state size. Assumes area scaling and 300K; excludes circuit noise.
    c10_f = 203.8e-15
    k_b = 1.380649e-23
    temp_k = 300.0
    membrane_count = 30_976_000
    area_cap_f_per_um2 = 2.00e-15
    perimeter_cap_f_per_um = 0.19e-15
    widths_um = (1.0, 2.0, 5.0, 10.0, 20.0, 100.0)
    geometry_sweep = []
    for width_um in widths_um:
        cap_f = area_cap_f_per_um2 * width_um ** 2 + perimeter_cap_f_per_um * 4.0 * width_um
        one_sigma_uv = float(np.sqrt(k_b * temp_k / cap_f) * 1e6)
        geometry_sweep.append({
            "square_width_um": width_um,
            "capacitance_f_area_scaled": cap_f,
            "single_cap_kTC_sigma_uv": one_sigma_uv,
            "independent_differential_pair_sigma_uv": float(np.sqrt(2.0) * one_sigma_uv),
            "area_per_state_um2": width_um ** 2,
            "aggregate_area_mm2": width_um ** 2 * membrane_count / 1e6,
            "aggregate_capacitance_f": cap_f * membrane_count,
        })
    sigma_100um_uv = geometry_sweep[-1]["single_cap_kTC_sigma_uv"]
    sigma_diff_100um_uv = geometry_sweep[-1]["independent_differential_pair_sigma_uv"]
    sigma_cases = (0.0, 0.18,
                   geometry_sweep[2]["single_cap_kTC_sigma_uv"],
                   geometry_sweep[3]["single_cap_kTC_sigma_uv"],
                   geometry_sweep[0]["single_cap_kTC_sigma_uv"])

    cases = []
    rng = np.random.default_rng(SEED)
    for headroom in HEADROOMS_V:
        units_per_v = float(np.max(np.abs(candidate_ref)) / headroom)
        for sigma_uv in sigma_cases:
            sigma_units = sigma_uv * 1e-6 * units_per_v
            for noise_kind in ("independent_per_update", "static_per_neuron", "kTC_on_cap_reset"):
                mismatch = []
                for _ in range(TRIALS):
                    if sigma_uv == 0.0:
                        noise = None
                        reset_noise = None
                        initial_noise = None
                    elif noise_kind == "independent_per_update":
                        noise = rng.normal(0.0, sigma_units, size=current.shape)
                        reset_noise = None
                        initial_noise = None
                    elif noise_kind == "kTC_on_cap_reset":
                        noise = None
                        reset_noise = rng.normal(0.0, sigma_units, size=current.shape)
                        initial_noise = rng.normal(0.0, sigma_units, size=current.shape[1:])
                    else:
                        one = rng.normal(0.0, sigma_units, size=current.shape[1:])
                        noise = np.broadcast_to(one, current.shape)
                        reset_noise = None
                        initial_noise = None
                    got = replay(current, beta, threshold, noise, reset_noise, initial_noise)
                    mismatch.append(float(np.mean(got != expected)))
                cases.append({
                    "candidate_headroom_v": headroom,
                    "noise_model": noise_kind,
                    "injected_state_noise_sigma_uv": sigma_uv,
                    "injected_state_noise_sigma_model_units": sigma_units,
                    "equivalent_mim_width_um_for_one_cap_kTC": (
                        None if sigma_uv == 0.0 else sigma_100um_uv * 100.0 / sigma_uv
                    ),
                    "trial_count": TRIALS,
                    "spike_mismatch_mean": float(np.mean(mismatch)),
                    "spike_mismatch_p05_p50_p95": [float(x) for x in np.quantile(mismatch, [0.05, 0.5, 0.95])],
                })

    out = {
        "test": "sky130_mim_kTC_scale_fullfloat_spike_sensitivity",
        "checkpoint_sha256": meta["checkpoint_sha256"],
        "float_path": meta["float_path"],
        "qat_or_quantized_reference_used": False,
        "stage": STAGE,
        "trace_archive": str(TRACE_NPZ.relative_to(ROOT)).replace("\\", "/"),
        "captured_spike_count": int(expected.size),
        "baseline_replay_mismatch_vs_recorded": baseline_mismatch,
        "thermal_estimate": {
            "temperature_k": temp_k,
            "c10um_from_existing_report_f": c10_f,
            "pdk_typical_area_cap_f_per_um2": area_cap_f_per_um2,
            "pdk_typical_perimeter_cap_f_per_um": perimeter_cap_f_per_um,
            "bench_100um_cap_single_kTC_sigma_uv": sigma_100um_uv,
            "bench_100um_cap_independent_pair_sigma_uv": sigma_diff_100um_uv,
            "geometry_sweep": geometry_sweep,
            "notes": "Uses local SKY130 typical MIM area/perimeter model terms and 300K. Width points are scenarios, not selected design dimensions. Not transient-noise evidence for the OTA/circuit.",
        },
        "one_cap_per_PLIF_geometry_scenarios": {
            "logical_membrane_count": membrane_count,
            "selected_design_size": False,
            "sensitivity_threshold_0_18uv_is_cap_requirement": False,
            "scope": "Geometric scenarios only: one MIM capacitor per logical PLIF state; excludes switches, buffers, synapses, routing and spacing. 100um was the circuit bench capacitor, not an area recommendation. 0.18uV was a local sensitivity threshold, not a specified kT/C design requirement.",
        },
        "headroom_cases": cases,
        "scope": "64 deterministic Monte Carlo replays of one sampled final-fusion PLIF layer on three 64x64 patches from the best-validation full-float checkpoint; captured baseline currents are fixed, beta is applied once per update, and noise is injected into candidate state before threshold/reset. Upstream spikes are not re-simulated. This is a local sensitivity screen, not task accuracy or circuit noise characterization.",
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS / "sky130_cap_kTC_float_sensitivity.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out_path), "baseline_replay_mismatch": baseline_mismatch,
                      "thermal_estimate": out["thermal_estimate"], "headroom_cases": cases}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
