"""Summarize original-float sensitivity to 20um and 2um MIM reset noise."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
QUAL = ROOT / "artifacts/analog_asic/layout/sky130_differential_trim_cap_pair/qualification.json"
SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
STATE_COUNT = 30_976_000


def main() -> None:
    qual = json.loads(QUAL.read_text(encoding="utf-8"))
    assert qual["magic_drc_zero"] and qual["netgen_unique_match"]
    c_min_f = qual["unit_capacitance_f"]
    cases = []
    for width_um in (20, 2):
        area_um2 = width_um**2
        c_f = c_min_f * area_um2 / 4
        sigma_uv = math.sqrt(1.380649e-23 * 300 / c_f) * 1e6
        reports = []
        for record in (0, 1):
            pattern = (f"sky130_float_state_saturation_validation_{record}_all_neurons_full_"
                       f"reset_only_g1000_piecewise6_ideal_n{sigma_uv:.6g}uv.json")
            paths = list(RESULTS.glob(pattern))
            if len(paths) != 1:
                raise RuntimeError(f"expected one replay for {pattern}, got {len(paths)}")
            path = paths[0]
            source = json.loads(path.read_text(encoding="utf-8"))
            if (source["checkpoint_sha256"] != SHA or source["qat_or_quantized_reference_used"] is not False
                    or source["noise_mode"] != "reset-only" or source["encoding"] != "piecewise-ideal"
                    or source["piecewise_segment_count"] != 6 or source["retention_law"] != "none"
                    or source["full_frame"] is not True or source["scope"] != "all-neurons"
                    or abs(source["injected_state_noise_sigma_uv_rms"] - sigma_uv) > 1e-4):
                raise RuntimeError(f"replay contract mismatch: {path}")
            trials = source["trials"]
            if len(trials) != 3:
                raise RuntimeError(f"expected three trials: {path}")
            keys = ("final_fuse_spike_mismatch", "segmentation_pixel_agreement_with_float",
                    "labeled_pixel_accuracy", "present_class_mean_iou")
            reports.append({
                "record_index": record,
                "source": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "baseline_present_class_mean_iou": source["baseline_present_class_mean_iou"],
                "mean": {key: sum(row[key] for row in trials) / 3 for key in keys},
                "seeds": [row["seed"] for row in trials],
            })
        cases.append({
            "mim_square_um": width_um,
            "capacitance_estimate_f_from_extracted_2um_density": c_f,
            "single_cap_kTC_300k_uv_rms": sigma_uv,
            "bare_mim_plate_area_mm2_per_30p976m_states": area_um2 * STATE_COUNT / 1e6,
            "records": reports,
        })
    report = {
        "test": "original_float_ideal_companded_mim_state_kTC_area_screen",
        "checkpoint_sha256": SHA,
        "qat_or_quantized_reference_used": False,
        "source_minimum_routed_mim_qualification": str(QUAL.relative_to(ROOT)).replace("\\", "/"),
        "source_minimum_routed_mim_sha256": hashlib.sha256(QUAL.read_bytes()).hexdigest(),
        "cases": cases,
        "interpretation": "Ideal six-range g1000 original-float replay on two full DSEC frames with independent Gaussian kT/C proxy at initialization and after subtractive reset. 20um capacitance is density-scaled from the extracted 2um unit, not measured 20um PEX. No retention, comparator noise, physical gain selection, weighted event error, mismatch or service. Bare drawn plate area omits enclosure, spacing, switch, routing and readout. These two frames do not qualify task accuracy or a physical analog cell.",
    }
    out = RESULTS / "sky130_mim_scale_companded_replay_summary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "cases": cases}, indent=2))


if __name__ == "__main__":
    main()
