"""Combine bounded extracted low-end signed-weight transfer cases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
RESULTS = BASE / "results"
OUT = RESULTS / "gf180_weight_low_end_characterization_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> tuple[dict, dict]:
    path = RESULTS / name
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["module_simulation_completed"], path
    rows = report["cases"]
    assert len(rows) == 1, (path, len(rows))
    return report, rows[0]


def main() -> None:
    sources = {
        "5_percent": "gf180_weight_low_end_5pct_v10_src6f3c8edbf795.json",
        "10_percent": "gf180_weight_low_end_10pct_v10_src4bad89be4cd3.json",
        "15_percent": "gf180_weight_low_end_15pct_v20_src6f8bf00afa74.json",
        "20_percent": "gf180_weight_low_end_20pct_v10_srcc11afd19434a.json",
    }
    loaded = {k: load(v) for k, v in sources.items()}
    full = json.loads((RESULTS / "gf180_weight_delivery_float_mapping_v1.json").read_text(encoding="utf-8"))
    full_row = full["measured_transfer"]["full_scale_positive"]
    qfull = float(full_row["net_charge_into_state_c"])
    points = []
    expected = {"5_percent": .05, "10_percent": .10, "15_percent": .15, "20_percent": .20}
    for key in sources:
        run, row = loaded[key]
        q = expected[key]
        measured = float(row["net_charge_into_state_c"])
        points.append({
            "normalized_float_magnitude": q,
            "programmed_magnitude_v": row["programmed_magnitude_v"],
            "pulse_width_us": row["pulse_width_us"],
            "measured_charge_c": measured,
            "measured_fraction_of_full_scale_charge": measured / qfull,
            "ideal_fraction_of_full_scale_charge": q,
            "relative_error_vs_linear_weight": (measured / qfull) / q - 1,
            "state_step_v": row["state_step_v"],
            "one_sample_each_native_phase": all(v == 1 for v in row["sequencer_strobe_counts"].values()),
            "report": sources[key],
            "run_sha256": run.get("sha256", {}),
        })
    points.extend([
        {
            "normalized_float_magnitude": .25,
            "programmed_magnitude_v": full["measured_transfer"]["quarter_scale_v1p1"]["programmed_magnitude_v"],
            "pulse_width_us": full["measured_transfer"]["quarter_scale_v1p1"]["pulse_width_us"],
            "measured_charge_c": full["measured_transfer"]["quarter_scale_v1p1"]["net_charge_into_state_c"],
            "measured_fraction_of_full_scale_charge": full["measured_transfer"]["quarter_scale_charge_fraction_of_full"],
            "ideal_fraction_of_full_scale_charge": .25,
            "relative_error_vs_linear_weight": full["measured_transfer"]["quarter_scale_relative_charge_error"],
            "state_step_v": full["measured_transfer"]["quarter_scale_v1p1"]["state_step_v"],
            "one_sample_each_native_phase": True,
            "report": "gf180_weight_delivery_float_mapping_v1.json",
        },
        {
            "normalized_float_magnitude": 1.0,
            "programmed_magnitude_v": full_row["programmed_magnitude_v"],
            "pulse_width_us": full_row["pulse_width_us"],
            "measured_charge_c": qfull,
            "measured_fraction_of_full_scale_charge": 1.0,
            "ideal_fraction_of_full_scale_charge": 1.0,
            "relative_error_vs_linear_weight": 0.0,
            "state_step_v": full_row["state_step_v"],
            "one_sample_each_native_phase": True,
            "report": "gf180_weight_delivery_float_mapping_v1.json",
        },
    ])
    inventory = full["float_inventory"]
    report = {
        "status": "LOW_END_WEIGHT_MAPPING_FAILS_LINEAR_TRANSFER_AT_NOMINAL_TT27",
        "mapping": full["diagnostic_conditions"]["weight_voltage_map_candidate"],
        "physical_test": "Extracted GF180 230-MOS/4-MIM sequencer and injector with 1,225 routed-capacitance branches, native phase generation, two physical MIM state loads, fixed nominal biases, one positive event, TT27C. MAG_DATA driven by an ideal test source; no addressed weight memory/readout, process mismatch/noise or model replay.",
        "full_scale_reference_charge_c": qfull,
        "measured_points": points,
        "response_assessment": {
            "no_pulse_at_5_percent": points[0]["pulse_width_us"] is None,
            "no_pulse_at_10_percent": points[1]["pulse_width_us"] is None,
            "pulse_at_15_percent": points[2]["pulse_width_us"] is not None,
            "onset_bracket_normalized_magnitude": [0.10, 0.15],
            "charge_at_15_percent_is_only_fraction_of_full": points[2]["measured_fraction_of_full_scale_charge"],
            "interpretation": "The nominal linear 1.0–1.4V map produces no observed event at 5% or 10% weight, under-delivers at 15% and 20%, then is near-linear at 25%. Threshold onset is bracketed, not precisely located. The candidate mapping does not preserve low-end weights.",
        },
        "float_inventory": {
            "source": inventory["source"],
            "sha256": inventory["sha256"],
            "fraction_below_1_percent": inventory["fraction_below_normalized_magnitude"]["0.01"],
            "fraction_below_5_percent": inventory["fraction_below_normalized_magnitude"]["0.05"],
            "fraction_below_10_percent": inventory["fraction_below_normalized_magnitude"]["0.1"],
            "weight_values": inventory["weight_values"],
        },
        "accuracy_acceptance": False,
        "full_float_accuracy_accepted": False,
        "5ms_service_accepted": False,
        "full_chip_layout_complete": False,
        "next": "Replace or recalibrate the low-magnitude weight-to-charge transfer, connect it to addressed weight storage/readout, then replay the original epoch58 float model before accepting this weight path. Preserve the signed one-event-per-presynaptic-spike semantics.",
        "sources": {
            "summary_script": str(Path(__file__).relative_to(ROOT)).replace("\\", "/"),
            "float_mapping_report": "artifacts/analog_asic/results/gf180_weight_delivery_float_mapping_v1.json",
            **{k: f"artifacts/analog_asic/results/{v}" for k, v in sources.items()},
        },
    }
    consumed = [Path(__file__), RESULTS / "gf180_weight_delivery_float_mapping_v1.json"] + [RESULTS / name for name in sources.values()]
    report["sha256"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in consumed}
    assert not OUT.exists(), OUT
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT), "response_assessment": report["response_assessment"], "float_inventory": report["float_inventory"], "full_float_accuracy_accepted": False}, indent=2))


if __name__ == "__main__":
    main()
