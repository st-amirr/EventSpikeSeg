"""Summarize bounded physical TG storage and conditional 140k scaling."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
LAYOUT = ROOT / "artifacts/analog_asic/layout/sky130_body_tied_transmission_gate/qualification_probe.json"
STATES = 30_976_000


def main() -> None:
    paths = {
        "tt_small": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset1mv.json",
        "tt_wide": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset300mv.json",
        "tt_small_remaining": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset1mv_pwellremaining.json",
        "tt_wide_remaining": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset300mv_pwellremaining.json",
        "tt_small_balanced": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset1mv_dnw1.2v_pwellremaining.json",
        "tt_wide_balanced": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset300mv_dnw1.2v_pwellremaining.json",
        "tt_small_shared_bus": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset1mv_dnw1.2v_pwellremaining_sourcevcm.json",
        "tt_wide_shared_bus": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset300mv_dnw1.2v_pwellremaining_sourcevcm.json",
        "event_time_50ns": RESULTS / "sky130_body_tied_tg_event_time_tt27_dnw1p2_bothdiodes_sourcevcm_step50ns.json",
        "event_time_25ns": RESULTS / "sky130_body_tied_tg_event_time_tt27_dnw1p2_bothdiodes_sourcevcm_step25ns.json",
        "guard_10ff": RESULTS / "sky130_body_tied_tg_event_time_tt27_dnw1p2_bothdiodes_sourcevcm_guard10ff_step50ns.json",
        "guard_100ff": RESULTS / "sky130_body_tied_tg_event_time_tt27_dnw1p2_bothdiodes_sourcevcm_guard100ff_step50ns.json",
        "tt_low_dnw": RESULTS / "sky130_body_tied_tg_pex_hold_tt_temp27_offset1mv_dnw0.902v.json",
        "ss_small": RESULTS / "sky130_body_tied_tg_pex_hold_ss_temp0_offset1mv.json",
        "ff_small": RESULTS / "sky130_body_tied_tg_pex_hold_ff_temp85_offset1mv.json",
        "long_tg": RESULTS / "sky130_min_mim_offswitch_leakage_ss_temp0_offset1mv.json",
        "layout": LAYOUT,
    }
    data = {key: json.loads(path.read_text(encoding="utf-8")) for key, path in paths.items()}
    if not all(data[key]["completed"] for key in ("tt_small", "tt_wide", "tt_low_dnw",
                                                     "tt_small_shared_bus", "tt_wide_shared_bus",
                                                     "event_time_50ns", "event_time_25ns",
                                                     "guard_10ff", "guard_100ff")):
        raise RuntimeError("required diode-proxy hold runs incomplete")

    def case(report: dict, name: str) -> dict:
        return next(item for item in report["cases"] if item["switch"] == name)

    def retained(report: dict, name: str) -> float:
        item = case(report, name)
        return (item["high_end_v"] - item["low_end_v"]) / (item["high_start_v"] - item["low_start_v"])

    bbox = data["layout"]["gds_bbox_um"]
    tg_footprint = bbox[0] * bbox[1]
    small = data["tt_small_remaining"]
    matched = case(small, "physical_with_well_diode")
    mismatch = case(small, "well_diode_area_mismatch_1pct")
    pair_cap_f = (9.52 + 0.38 + 1.07) * 1e-15
    ratio = abs(mismatch["differential_drift_mv"]) / 0.003
    area = {
        "one_isolated_tg_per_rail_mm2": STATES * tg_footprint / 1e6,
        "two_isolated_tgs_per_differential_state_mm2": STATES * 2 * tg_footprint / 1e6,
        "two_2x2um_mim_plates_per_state_mm2": STATES * 2 * 4 / 1e6,
        "unshared_tg_plus_mim_mm2": STATES * (2 * tg_footprint + 8) / 1e6,
    }
    report = {
        "test": "sky130_body_tied_tg_storage_boundary",
        "source_sha256": {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()},
        "resident_states": STATES,
        "layout_drc0_lvs_unique": data["layout"]["magic_drc_count"] == 0 and data["layout"]["netgen_lvs_unique"],
        "single_tg_bbox_um": bbox,
        "single_tg_bbox_area_um2": tg_footprint,
        "nominal_reduced_mim_effective_cap_per_rail_f": pair_cap_f,
        "tt_1mv_remaining_pwell_both_diodes_differential_drift_uv": case(small, "physical_with_both_well_diodes")["differential_drift_mv"] * 1000,
        "tt_1mv_remaining_pwell_both_diodes_1pct_differential_drift_uv": case(small, "both_well_diodes_area_mismatch_1pct")["differential_drift_mv"] * 1000,
        "tt_300mv_remaining_pwell_both_diodes_differential_drift_mv": case(data["tt_wide_remaining"], "physical_with_both_well_diodes")["differential_drift_mv"],
        "tt_1mv_balanced_dnw_both_diodes_common_mode_drift_mv": case(data["tt_small_balanced"], "physical_with_both_well_diodes")["common_mode_drift_mv"],
        "tt_1mv_balanced_dnw_both_diodes_differential_drift_uv": case(data["tt_small_balanced"], "physical_with_both_well_diodes")["differential_drift_mv"] * 1000,
        "tt_300mv_balanced_dnw_both_diodes_differential_drift_mv": case(data["tt_wide_balanced"], "physical_with_both_well_diodes")["differential_drift_mv"],
        "tt_1mv_shared_bus_both_diodes_differential_drift_mv": case(data["tt_small_shared_bus"], "physical_with_both_well_diodes")["differential_drift_mv"],
        "tt_300mv_shared_bus_both_diodes_differential_drift_mv": case(data["tt_wide_shared_bus"], "physical_with_both_well_diodes")["differential_drift_mv"],
        "tt_1mv_shared_bus_5ms_retained_differential_fraction": retained(data["tt_small_shared_bus"], "physical_with_both_well_diodes"),
        "tt_300mv_shared_bus_5ms_retained_differential_fraction": retained(data["tt_wide_shared_bus"], "physical_with_both_well_diodes"),
        "early_to_late_equal_charge_final_ratio_50ns": data["event_time_50ns"]["early_to_late_final_ratio"],
        "early_to_late_equal_charge_final_ratio_25ns": data["event_time_25ns"]["early_to_late_final_ratio"],
        "passive_guard_10ff_early_to_late_final_ratio_50ns": data["guard_10ff"]["early_to_late_final_ratio"],
        "passive_guard_100ff_early_to_late_final_ratio_50ns": data["guard_100ff"]["early_to_late_final_ratio"],
        "passive_guard_two_tg_per_rail_unshared_bbox_area_mm2": STATES * 4 * tg_footprint / 1e6,
        "tt_1mv_remaining_pwell_single_diode_differential_drift_uv": matched["differential_drift_mv"] * 1000,
        "tt_1mv_remaining_pwell_single_diode_1pct_differential_drift_uv": mismatch["differential_drift_mv"] * 1000,
        "tt_1mv_outer_pwell_both_diodes_differential_drift_uv": case(data["tt_small"], "physical_with_both_well_diodes")["differential_drift_mv"] * 1000,
        "tt_300mv_outer_pwell_both_diodes_differential_drift_mv": case(data["tt_wide"], "physical_with_both_well_diodes")["differential_drift_mv"],
        "tt_1mv_low_dnw_differential_drift_uv": case(data["tt_low_dnw"], "physical_with_well_diode")["differential_drift_mv"] * 1000,
        "ss_1mv_matched_diode_differential_drift_uv": case(data["ss_small"], "physical_with_well_diode")["high_drift_mv"] * 1000 - case(data["ss_small"], "physical_with_well_diode")["low_drift_mv"] * 1000,
        "ff_1mv_matched_diode_differential_drift_uv": case(data["ff_small"], "physical_with_well_diode")["high_drift_mv"] * 1000 - case(data["ff_small"], "physical_with_well_diode")["low_drift_mv"] * 1000,
        "ss_1mv_fixed_bulk_0p5um_drift_mv": case(data["long_tg"], "tg_l0p5")["low_drift_mv"],
        "ss_1mv_fixed_bulk_8um_drift_mv": case(data["long_tg"], "tg_l8")["low_drift_mv"],
        "conditional_unshared_footprint": area,
        "illustrative_cap_multiplier_for_3uv_single_diode_1pct_error": ratio,
        "limitations": "A screening summary, not an accepted macro. Parked-source hold is an optimistic control; the shared-VCM-bus hold and event-time runs are the active topology diagnostics. Passive guard screens add a second extracted body-tied TG and ideal 10fF or 100fF guard capacitor per rail, with no guard co-write or layout. Junction diode geometries are drawn-region proxies, not extracted junctions; ngspice warns of unsupported diode card parameters. The single-diode capacitor scaling assumes fixed current and inverse-C drift, and 3uV is illustrative rather than a model acceptance threshold. Footprint multiplication assumes no tiling, sharing, routing or guard-ring optimization. The MIM is a reduced nominal C plus PEX parasitics. Physical body wiring, foundry DRC, leakage extraction, noise/mismatch distribution, programming, readout and 5ms population service remain open.",
    }
    out = RESULTS / "sky130_body_tied_tg_storage_boundary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
