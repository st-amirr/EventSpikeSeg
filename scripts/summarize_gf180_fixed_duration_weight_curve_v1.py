"""Summarize fixed-duration analog-current control for continuous float weights."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
RESULTS = BASE / "results"
OUT = RESULTS / "gf180_fixed_duration_weight_curve_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name: str) -> dict:
    obj = json.loads((RESULTS / name).read_text(encoding="utf-8"))
    assert obj["simulation_completed"], name
    return obj


def main() -> None:
    names = {
        "full_scale": "gf180_differential_weighted_charge_da6fcbce01_src97c7fd247a03.json",
        "linear_10_percent": "gf180_differential_weighted_charge_998885a84e_src97c7fd247a03.json",
        "linear_1_percent": "gf180_differential_weighted_charge_efd8926ed7_src97c7fd247a03.json",
        "gate_2p82": "gf180_differential_weighted_charge_bddc631074_src70626a4d14b7.json",
        "gate_2p85": "gf180_differential_weighted_charge_514b79b789_src70626a4d14b7.json",
        "gate_2p88": "gf180_differential_weighted_charge_b346e6b33a_src70626a4d14b7.json",
        "gate_2p90": "gf180_differential_weighted_charge_184a352097_src70626a4d14b7.json",
        "gate_3p00": "gf180_differential_weighted_charge_17afa93275_src70626a4d14b7.json",
        "gate_3p10": "gf180_differential_weighted_charge_44c7bfed95_src70626a4d14b7.json",
        "mapped_10_percent": "gf180_differential_weighted_charge_f0c40e65f9_src70626a4d14b7.json",
        "mapped_5_percent": "gf180_differential_weighted_charge_58ced1a2ee_src70626a4d14b7.json",
        "mapped_1_percent_linear_interp": "gf180_differential_weighted_charge_e2c397d653_src70626a4d14b7.json",
        "mapped_1_percent_refined": "gf180_differential_weighted_charge_2f8440a9d9_src70626a4d14b7.json",
    }
    runs = {key: read(filename) for key, filename in names.items()}
    full = float(runs["full_scale"]["measurements"]["signal_delta"])
    keys = ["linear_10_percent", "mapped_10_percent", "mapped_5_percent", "mapped_1_percent_linear_interp", "mapped_1_percent_refined"]
    targets = {"linear_10_percent": .10, "linear_1_percent": .01, "mapped_10_percent": .10, "mapped_5_percent": .05,
               "mapped_1_percent_linear_interp": .01, "mapped_1_percent_refined": .01}
    rows = []
    for key in keys:
        run = runs[key]
        actual = float(run["measurements"]["signal_delta"])
        rows.append({
            "normalized_float_magnitude": targets[key],
            "programmed_p_gate_v": float(run["settings"]["p_gate_v"]) if "p_gate_v" in run["settings"] else (3.3 - .55 * targets[key]),
            "measured_signed_differential_output_v": actual,
            "full_scale_output_v": full,
            "measured_fraction_of_full_scale": actual / full,
            "target_fraction": targets[key],
            "relative_error": (actual / full) / targets[key] - 1,
            "report": names[key],
        })
    # Direct linear gate programming results are near zero; report the exact settings.
    for key in ["linear_10_percent", "linear_1_percent"]:
        runs[key]["linear_map_diagnostic"] = {"magnitude": targets[key], "p_gate_v": 3.3 - .55 * targets[key]}
    report = {
        "status": "FIXED_DURATION_CURRENT_CONTROL_LOW_END_NOMINAL_CANDIDATE_ONLY",
        "architecture": "One signed 1us event with continuously stored PMOS gate voltage controlling current amplitude into an extracted differential charge integrator; positive polarity measured. No quantization.",
        "scope": "The integrator, reference, phase switches and phase inverters are qualified extracted layouts. The weight-controlled PMOS current source and inter-macro connection are schematic-only, driven by ideal external analog gate voltages. Nominal TT27, one event, no process mismatch/noise, addressed weight memory, whole-model replay or 5ms service.",
        "full_scale_gate_v": 2.75,
        "full_scale_signal_delta_v": full,
        "measured_weight_points": rows,
        "nominal_inverse_map_candidate": [
            {"normalized_magnitude": 0.0, "gate_v": 3.3, "basis": "zero-current reference"},
            {"normalized_magnitude": 0.01, "gate_v": 2.9136, "measured_fraction": rows[4]["measured_fraction_of_full_scale"]},
            {"normalized_magnitude": 0.05, "gate_v": 2.863, "measured_fraction": rows[2]["measured_fraction_of_full_scale"]},
            {"normalized_magnitude": 0.10, "gate_v": 2.839, "measured_fraction": rows[1]["measured_fraction_of_full_scale"]},
            {"normalized_magnitude": 1.0, "gate_v": 2.75, "measured_fraction": 1.0},
        ],
        "finding": "Linear gate mapping gives essentially no response at10% and1%. Selecting gate voltage from the measured nonlinear transfer yields about89–93% of target charge at1%,5% and10% using a 1us fixed event. The remaining error is roughly7–11% nominal and the inverse points are a characterization, not a circuit encoder.",
        "weight_path_accepted": False,
        "original_float_accuracy_accepted": False,
        "5ms_service_accepted": False,
        "full_chip_layout_complete": False,
        "next": "Physically lay out the analog gate-controlled current source, combine it with the extracted integrator and selected analog weight store, characterize signed transfer and mismatch, then replay the original float model and measure 5ms service. Compare its area and latency with repairing the magnitude-to-duration ramp path.",
        "sources": {k: f"artifacts/analog_asic/results/{v}" for k, v in names.items()},
    }
    sources = [Path(__file__), *[RESULTS / name for name in names.values()]]
    report["sha256"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    assert not OUT.exists(), OUT
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT), "full_scale_signal_delta_v": full,
                      "measured_weight_points": rows, "weight_path_accepted": False}, indent=2))


if __name__ == "__main__":
    main()
