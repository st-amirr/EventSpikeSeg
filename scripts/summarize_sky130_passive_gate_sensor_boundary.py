"""Screen passive input-gate storage and power-up cost from bounded PEX holds."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
PREFIX = "sky130_min_mim_offswitch_leakage_"
N_STATES = 30_976_000
MOSCAP_QUAL = ROOT / "artifacts/analog_asic/layout/sky130_moscap_pcell_probe_10x1_nf1/moscap_layout_qualification.json"


def source(stem: str) -> tuple[dict, dict]:
    path = RESULTS / f"{PREFIX}{stem}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data["simulation_completed"] or data["off_switch_source_mode"] != "vcm":
        raise RuntimeError(f"incomplete fixed-bus source: {path}")
    return data, {"path": path.relative_to(ROOT).as_posix(),
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def state(row: dict, kind: str = "routed_tg_sensor") -> dict:
    case = next(case for case in row["cases"] if case["switch"] == kind)
    start = case["high_start_v"] - case["low_start_v"]
    end = case["high_end_v"] - case["low_end_v"]
    return {"start_differential_mv": start * 1000,
            "end_differential_mv": end * 1000,
            "retention_fraction": end / start,
            "end_common_mode_v": (case["low_end_v"] + case["high_end_v"]) / 2}


def main() -> None:
    cases = []
    for corner, temp in (("tt", 27), ("ss", 0), ("ff", 85)):
        stem = f"{corner}_temp{temp}_offset1mv_sourcevcm_sensor"
        on, on_source = source(stem)
        off, off_source = source(stem + "_tail0v_supply0v")
        physical, physical_source = source(stem.removesuffix("_sensor") + "_physicalmoscap")
        no_sensor, no_source = source(stem.removesuffix("_sensor"))
        plain = next(case for case in no_sensor["cases"] if case["switch"] == "routed_tg")
        plain_start = plain["high_start_v"] - plain["low_start_v"]
        plain_end = plain["high_end_v"] - plain["low_end_v"]
        cases.append({
            "corner": corner.upper(), "temperature_c": temp,
            "sources": {"always_on": on_source, "fully_off": off_source,
                        "physical_moscap": physical_source, "no_sensor": no_source},
            "no_sensor_retention_fraction": plain_end / plain_start,
            "sensor_always_on": state(on),
            "sensor_fully_off": state(off),
            "physical_moscap": state(physical, "routed_tg_moscap"),
            "sensor_always_on_supply_current_ua": (
                -on["sensor_supply_current_end_a"] * 1e6
                if on.get("sensor_supply_current_end_a") is not None else None),
            "sensor_fully_off_supply_current_a": off["sensor_supply_current_end_a"],
        })
    dynamic, dynamic_source = source("tt_temp27_offset1mv_sourcevcm_sensor_enable4.99ms_ramp1us")
    dynamic_state = state(dynamic)
    dynamic_state["source"] = dynamic_source
    dynamic_state["pre_enable_common_mode_v"] = sum(dynamic["sensor_pre_enable_state_v"].values()) / 2
    dynamic_state["enable_common_mode_step_mv_at_5ms"] = (
        dynamic_state["end_common_mode_v"] - dynamic_state["pre_enable_common_mode_v"]) * 1000
    shared_read = []
    for width, suffix in ((10.0, ""), (0.42, "_inputw0.42um"),
                          (0.42, "_inputw0.42um_idealswitch")):
        read, read_source = source("tt_temp27_offset1mv_sourcevcm_physicalmoscap_sharedread" + suffix)
        rv = read["shared_read_values_v"]
        read_before_diff = rv["read_high_before"] - rv["read_low_before"]
        read_end_diff = rv["read_high_end"] - rv["read_low_end"]
        shared_read.append({
            "source": read_source,
            "schematic_sensor_input_width_um": width,
            "ideal_read_switch": bool(read.get("ideal_read_switch", False)),
            "preconnect_differential_mv": read_before_diff * 1000,
            "end_differential_mv": read_end_diff * 1000,
            "end_to_preconnect_differential_fraction": read_end_diff / read_before_diff,
            "end_to_no_read_end_differential_fraction": (read_end_diff * 1000) /
                cases[0]["physical_moscap"]["end_differential_mv"],
            "preconnect_common_mode_v": (rv["read_low_before"] + rv["read_high_before"]) / 2,
            "end_common_mode_v": (rv["read_low_end"] + rv["read_high_end"]) / 2,
            "common_mode_step_mv": ((rv["read_low_end"] + rv["read_high_end"])
                                    - (rv["read_low_before"] + rv["read_high_before"])) * 500,
            "sensor_output_differential_end_mv": (rv["read_outn_end"] - rv["read_outp_end"]) * 1000,
        })
    tt_current_a = cases[0]["sensor_always_on_supply_current_ua"] * 1e-6
    moscap_qual = json.loads(MOSCAP_QUAL.read_text(encoding="utf-8"))
    if not (moscap_qual["magic_drc_zero"] and moscap_qual["netgen_lvs_unique_match"]):
        raise RuntimeError("physical MOSCAP probe not DRC/LVS qualified")
    report = {
        "test": "sky130_minimum_mim_sensor_gate_retention_and_power_boundary",
        "physical_moscap_qualification": {"path": MOSCAP_QUAL.relative_to(ROOT).as_posix(),
                                          "sha256": hashlib.sha256(MOSCAP_QUAL.read_bytes()).hexdigest(),
                                          "tt_ac_capacitance_f": moscap_qual["extracted_cgate_f"]},
        "cases": cases,
        "late_enable_tt_1us_ramp": dynamic_state,
        "tt_prebiased_shared_read_width_screen": shared_read,
        "always_on_tt_power_w_per_state": tt_current_a * 1.8,
        "conditional_all_states_always_on_tt_power_w": tt_current_a * 1.8 * N_STATES,
        "unshared_two_10x1um_nfet_gate_active_area_mm2": 20 * N_STATES / 1e6,
        "decision": "An attached unpowered input pair and extracted passive MOSCAP substantially improve deterministic 5ms hold, but the read path remains unsolved. A continuously biased per-state sensor is power-prohibitive by direct population multiplication. Powering the same circuit at the bin boundary injects a large common-mode step. A prebiased shared sensor through extracted read TGs consumes about half the stored differential with 10um inputs at TT; minimum 0.42um inputs reduce but do not remove read disturbance. An ideal-switch control shows the physical read TG causes most of the remaining common-mode kick and differential loss, while ideal charge sharing still perturbs the state. Redesign the read connection and quantify kickback/noise/area before layout promotion.",
        "limitations": "2x2um routed MIM/TG PEX plus schematic sensor with ideal programming and fixed VCM source; reduced MIM model, ideal sensor supplies, no sensor layout, power switch, real writeback, transient noise/mismatch, arbitrary state range, event sequence, calibration or system timing. Unshared gate active area is transistor W*L only, not a GDS bounding box. Population power assumes every sensor biased continuously and is not a measured chip-power estimate. Late enable step compares 4.989ms with 5ms, so it also includes 11us of leakage.",
    }
    out = RESULTS / "sky130_passive_gate_sensor_boundary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "tt_off_retention": cases[0]["sensor_fully_off"]["retention_fraction"],
                      "conditional_always_on_power_w": report["conditional_all_states_always_on_tt_power_w"],
                      "late_enable_common_mode_step_mv": dynamic_state["enable_common_mode_step_mv_at_5ms"],
                      "shared_read_retention_fractions": [x["end_to_preconnect_differential_fraction"] for x in shared_read]}, indent=2))


if __name__ == "__main__":
    main()
