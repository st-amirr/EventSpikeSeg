"""Bound per-actor analog voltage gain using the original float PLIF trace."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RESULT = ROOT / "artifacts/analog_asic/results/sky130_float_dynamic_range_noise_boundary.json"
HEADROOM_V = 0.9
CAP_EACH_F = 203.8e-15
KT_PAIR_UV_AT_0C = float(np.sqrt(2 * 1.380649e-23 * 273.15 / CAP_EACH_F) * 1e6)


def main() -> int:
    meta = json.loads((REF / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    if meta["qat_or_quantized_reference_used"]:
        raise RuntimeError("expected the original full-float trace")
    archive = np.load(REF / "float_patch_trace_all.npz")
    actors = {}
    for key in sorted(name for name in archive.files if name.startswith("candidate__")):
        actor = key.removeprefix("candidate__")
        candidate = archive[key].astype(np.float64)
        threshold = np.broadcast_to(archive[f"threshold__{actor}"], candidate.shape).astype(np.float64)
        if not np.isfinite(candidate).all() or not np.isfinite(threshold).all():
            raise RuntimeError(f"nonfinite trace: {actor}")
        maximum = float(np.max(np.abs(candidate)))
        if maximum <= 0:
            continue
        volts_per_unit = HEADROOM_V / maximum
        margin_uv = np.abs(candidate - threshold) * volts_per_unit * 1e6
        saturation = {str(gain): float(np.mean(np.abs(candidate) > maximum / gain))
                      for gain in (2, 4, 10, 32, 100)}
        actors[actor] = {
            "candidate_sample_count": int(candidate.size),
            "maximum_absolute_candidate_model_units": maximum,
            "candidate_absolute_percentiles_model_units": {
                str(p): float(np.percentile(np.abs(candidate), p))
                for p in (50, 90, 99, 99.9)
            },
            "volts_per_model_unit_at_0p9v_max_headroom": volts_per_unit,
            "threshold_margin_absolute_percentiles_uv": {
                str(p): float(np.percentile(margin_uv, p))
                for p in (0.1, 1, 5, 50)
            },
            "fraction_of_states_with_margin_below_independent_10um_pair_ktc_proxy":
                float(np.mean(margin_uv < KT_PAIR_UV_AT_0C)),
            "fraction_of_candidates_outside_headroom_if_linear_gain_multiplied": saturation,
        }
    total_samples = sum(row["candidate_sample_count"] for row in actors.values())
    weighted_below_noise = sum(
        row["candidate_sample_count"] *
        row["fraction_of_states_with_margin_below_independent_10um_pair_ktc_proxy"]
        for row in actors.values()) / total_samples
    overflow_by_gain = {
        str(gain): sum(
            row["candidate_sample_count"] *
            row["fraction_of_candidates_outside_headroom_if_linear_gain_multiplied"][str(gain)]
            for row in actors.values()) / total_samples
        for gain in (2, 4, 10, 32, 100)
    }
    report = {
        "test": "sky130_full_float_plif_dynamic_range_vs_independent_state_noise",
        "checkpoint_sha256": meta["checkpoint_sha256"],
        "qat_or_quantized_reference_used": False,
        "trace": "float_patch_trace_all.npz",
        "headroom_v_each_polarity": HEADROOM_V,
        "independent_10um_pair_ktc_proxy_uv_rms_at_0c": KT_PAIR_UV_AT_0C,
        "total_candidate_samples": total_samples,
        "sample_weighted_fraction_with_margin_below_independent_pair_proxy": weighted_below_noise,
        "sample_weighted_fraction_outside_headroom_if_linear_gain_multiplied": overflow_by_gain,
        "actors": actors,
        "interpretation": "Each actor is independently scaled so its largest absolute candidate reaches 0.9V; linear gain multipliers are compared with that same fixed range. A candidate outside the range is an overflow count, not a measured circuit failure. The kT/C comparison is a one-sigma independent-reset proxy, not a spike-error prediction, physical switched-noise result, or required per-site margin. Traces are frozen 64x64 patches; no recurrent replay with clipping, mismatch, adaptive gain circuit, physical store or network accuracy is included.",
    }
    RESULT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: row for name, row in actors.items()
                      if name in ("final_fuse__standard", "enc1__standard", "context2__pointwise")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
