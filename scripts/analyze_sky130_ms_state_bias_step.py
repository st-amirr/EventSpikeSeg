"""Summarize bounded physical MOS event steps from precharged membrane states."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
PREFIX = ("sky130_ms_first_event_clamp_ss_temp0_g0p95_geom4_tight_s0p1n_"
          "w42p2657n_post20n_rise2n")
SMALL_PREFIX = ("sky130_ms_first_event_clamp_ss_temp0_g0p9_geom0p5_tight_s0p1n_"
                "w42p2657n_post20n_rise2n")


def main() -> int:
    rows = []
    for polarity, values in (("positive", (-1.2, 0, 0.6, 1.2)),
                             ("negative", (-1.2, 0, 0.6, 1.2))):
        for initial in values:
            state_tag = ("" if initial == 0 else
                         "_d" + f"{initial:g}".replace("-", "m").replace(".", "p") + "v")
            polarity_tag = "" if polarity == "positive" else "_neg"
            stem = f"{PREFIX}{state_tag}{polarity_tag}_banked_onlybefore_10ns"
            source = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
            if (not source["simulation_completed"] or source["mos_corner"] != "ss" or
                    source["temperature_c"] != 0 or source["event_polarity"] != polarity or
                    source["initial_differential_v"] != initial or
                    source["selected_timing_cases"] != ["before_10ns"]):
                raise RuntimeError(f"invalid state-bias physical result: {stem}")
            case = source["cases"][0]
            rows.append({
                "source_result": f"{stem}.json",
                "event_polarity": polarity,
                "initial_differential_v": initial,
                "actual_pre_event_differential_v": case["pre_no_event_diff_uv"] * 1e-6,
                "post_event_minus_no_event_step_mv": case["post_event_minus_no_event_uv"] * 1e-3,
            })
    absolute_steps = [abs(row["post_event_minus_no_event_step_mv"]) for row in rows]
    small_rows = []
    for polarity in ("positive", "negative"):
        for initial in (-0.6, 0.6):
            state_tag = "_d" + f"{initial:g}".replace("-", "m").replace(".", "p") + "v"
            polarity_tag = "" if polarity == "positive" else "_neg"
            stem = f"{SMALL_PREFIX}{state_tag}{polarity_tag}_banked_onlybefore_10ns"
            source = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
            if (not source["simulation_completed"] or source["event_polarity"] != polarity or
                    source["initial_differential_v"] != initial or
                    source["gate_fraction"] != 0.9 or source["injector_geometry_scale"] != 0.5):
                raise RuntimeError(f"invalid smaller-drive state-bias result: {stem}")
            small_rows.append({"source_result": f"{stem}.json", "event_polarity": polarity,
                               "initial_differential_v": initial,
                               "post_event_minus_no_event_step_mv":
                                   source["cases"][0]["post_event_minus_no_event_uv"] * 1e-3})
    small_steps = [abs(row["post_event_minus_no_event_step_mv"]) for row in small_rows]
    repeated_rows = []
    sequence_prefix = ("sky130_ms_first_touch_long_event_sequence_ss0_n10_w42p2657n_"
                       "p50p253n_g0p9_geom0p5")
    for initial in (0, -0.6, -0.3, 0.3, 0.6):
        state_tag = ("" if initial == 0 else
                     "_d" + f"{initial:g}".replace("-", "m").replace(".", "p") + "v")
        stem = sequence_prefix + "_lead10n" + state_tag + "_rise2n_banked"
        source = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
        if (not source["simulation_completed"] or not source["shared_bank_load"] or
                source["initial_differential_v"] != initial or source["event_count"] != 10 or
                source["event_spacing_ns"] != 50.253 or source["gate_slew_ns"] != 2):
            raise RuntimeError(f"invalid bank-loaded repeated small-drive result: {stem}")
        steps = source["final_differential_change_from_no_event_mv"]
        repeated_rows.append({
            "source_result": f"{stem}.json", "initial_differential_v": initial,
            "positive_one_step_mv": steps["p_one"],
            "negative_one_step_mv": steps["n_one"],
            "positive_ten_step_mv": steps["p_train"],
            "negative_ten_step_mv": steps["n_train"],
            "positive_negative_alternating_residual_mv": steps["pn_alt"],
            "negative_positive_alternating_residual_mv": steps["np_alt"],
            "positive_negative_single_step_magnitude_difference_mv":
                steps["p_one"] + steps["n_one"],
        })
    correction_rows = []
    for initial, sign_tag, bias_tag, fractions in (
        (-0.6, "ng", "dm0p6v", (0.901, 0.90116)),
        (-0.3, "ng", "dm0p3v", (0.90058,)),
        (0.3, "pg", "d0p3v", (0.90058,)),
        (0.6, "pg", "d0p6v", (0.901, 0.90116)),
    ):
        baseline = next(row for row in repeated_rows
                        if row["initial_differential_v"] == initial)
        for corrected_fraction in fractions:
            fraction_tag = f"{corrected_fraction:g}".replace(".", "p")
            stem = ("sky130_ms_first_touch_long_event_sequence_ss0_n10_w42p2657n_"
                    f"p50p253n_g0p9_{sign_tag}{fraction_tag}_geom0p5_lead10n_"
                    f"{bias_tag}_rise2n_banked")
            source = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
            if (not source["simulation_completed"] or not source["shared_bank_load"] or
                    source["initial_differential_v"] != initial or
                    source["positive_gate_fraction" if initial > 0 else "negative_gate_fraction"] !=
                    corrected_fraction):
                raise RuntimeError(f"invalid polarity-corrected sequence: {stem}")
            steps = source["final_differential_change_from_no_event_mv"]
            before = max(abs(baseline["positive_negative_alternating_residual_mv"]),
                         abs(baseline["negative_positive_alternating_residual_mv"]))
            after = max(abs(steps["pn_alt"]), abs(steps["np_alt"]))
            correction_rows.append({
                "source_result": f"{stem}.json", "initial_differential_v": initial,
                "strengthened_polarity": "positive" if initial > 0 else "negative",
                "strengthened_gate_fraction": corrected_fraction,
                "maximum_absolute_alternating_residual_before_mv": before,
                "maximum_absolute_alternating_residual_after_mv": after,
                "maximum_residual_reduction_factor": before / after,
                "positive_negative_single_step_magnitude_difference_mv":
                    steps["p_one"] + steps["n_one"],
            })
    report = {
        "test": "sky130_shared_MOS_bank_first_event_state_bias_sweep",
        "simulation_completed": True,
        "mos_corner": "ss",
        "temperature_c": 0,
        "geometry_scale": 4,
        "gate_fraction": 0.95,
        "event_width_ns": 42.2657,
        "physical_case_count": len(rows),
        "cases": rows,
        "minimum_absolute_step_mv": min(absolute_steps),
        "maximum_absolute_step_mv": max(absolute_steps),
        "max_to_min_absolute_step_ratio": max(absolute_steps) / min(absolute_steps),
        "smaller_drive": {"geometry_scale": 0.5, "gate_fraction": 0.9,
                          "physical_case_count": len(small_rows), "cases": small_rows,
                          "minimum_absolute_step_mv": min(small_steps),
                          "maximum_absolute_step_mv": max(small_steps),
                          "max_to_min_absolute_step_ratio": max(small_steps) / min(small_steps)},
        "repeated_smaller_drive": {"geometry_scale": 0.5, "gate_fraction": 0.9,
                                    "physical_case_count": len(repeated_rows),
                                    "event_count_per_sequence": 10, "cases": repeated_rows},
        "manual_polarity_gate_correction": {"physical_case_count": len(correction_rows),
                                            "cases": correction_rows,
                                            "physical_state_sensor_or_programmer_implemented": False},
        "scope": "Twelve bounded SKY130 SS/0C physical first-event MIM/TG/MOS state-bias sweeps plus five ten-event bank-loaded repeated-sequence decks and six manually polarity-corrected sequence decks. One geometry-4 maximum-drive or geometry-0.5 smaller-drive branch of the shared 13-geometry bank is pulsed with ideal fixed gate levels after TG-prepared differential states. Matched no-event controls remove baseline drift. The repeated sequence uses 10ns TG release lead and 2ns gate slew; a manually chosen approximately state-proportional polarity gate correction suppresses the biased-state cancellation residual at four prepared states. No physical state sensor, programmed adaptive bias, actual mixed float weights, dynamic threshold, beta/reset, noise, mismatch, 5ms hold or layout is included. These steps are not universal current-state bounds or proof of state-dependent encoded updates."
    }
    path = RES / "sky130_ms_state_bias_step_ss0_geom4.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"physical_case_count": len(rows),
                      "minimum_absolute_step_mv": report["minimum_absolute_step_mv"],
                      "maximum_absolute_step_mv": report["maximum_absolute_step_mv"],
                      "max_to_min_absolute_step_ratio": report["max_to_min_absolute_step_ratio"],
                      "smaller_drive": {key: value for key, value in report["smaller_drive"].items()
                                        if key != "cases"},
                      "repeated_smaller_drive": repeated_rows,
                      "manual_polarity_gate_correction": correction_rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
