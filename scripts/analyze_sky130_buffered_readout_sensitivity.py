"""Replay a bounded full-float spike trace under measured readout error bounds."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RESULTS = ROOT / "artifacts/analog_asic/results"
TRACE_META = REF / "float_patch_trace.json"
TRACE = REF / "float_patch_trace.npz"
STAGE = "final_fuse__standard"
HEADROOM_V = (0.15, 0.30, 0.60)
ERROR_UV = 0.145


def main() -> int:
    error_uv = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--error-uv=")), str(ERROR_UV)))
    error_tag = f"_e{error_uv:g}uv" if error_uv != ERROR_UV else ""
    out_path = RESULTS / f"sky130_buffered_readout_float_sensitivity{error_tag}.json"
    meta = json.loads(TRACE_META.read_text(encoding="utf-8"))
    archive = np.load(TRACE)
    candidate = archive[f"candidate__{STAGE}"].astype(np.float64)
    threshold = archive[f"threshold__{STAGE}"].astype(np.float64)
    spikes = archive[f"spikes__{STAGE}"].astype(bool)
    candidate_max = float(np.max(np.abs(candidate)))
    threshold_min = float(np.min(threshold))
    threshold_median = float(np.median(threshold))
    threshold_max = float(np.max(threshold))
    cases = []
    for headroom in HEADROOM_V:
        units_per_v = candidate_max / headroom
        offset_units = error_uv * 1e-6 * units_per_v
        plus = candidate >= threshold + offset_units
        minus = candidate >= threshold - offset_units
        cases.append({
            "candidate_headroom_v": headroom,
            "candidate_absmax_model_units": candidate_max,
            "float_threshold_voltage_range_uv_at_candidate_headroom": {
                "min": threshold_min / candidate_max * headroom * 1e6,
                "median": threshold_median / candidate_max * headroom * 1e6,
                "max": threshold_max / candidate_max * headroom * 1e6,
            },
            "threshold_offset_model_units": offset_units,
            "spike_bit_mismatch_fraction_offset_positive": float(np.mean(plus != spikes)),
            "spike_bit_mismatch_fraction_offset_negative": float(np.mean(minus != spikes)),
        })
    report = {
        "test": "sky130_buffered_readout_float_spike_sensitivity",
        "checkpoint_sha256": meta["checkpoint_sha256"],
        "float_path": meta["float_path"],
        "qat_or_quantized_reference_used": meta["qat_or_quantized_reference_used"],
        "trace_archive": str(TRACE.relative_to(ROOT)).replace("\\", "/"),
        "stage": STAGE,
        "spike_bit_count": int(spikes.size),
        "measured_combined_readout_error_bound_uv": error_uv,
        "candidate_headroom_sensitivity": cases,
        "scope": "uniform static threshold perturbation applied to recorded float candidate/threshold tensors for three 64x64 patches from one DSEC training frame; transfer-error bound is the measured mixed-order state-shift plus readout-relation envelope; no analog-noise, PVT, mismatch, full-network replay, or segmentation metric",
    }
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
