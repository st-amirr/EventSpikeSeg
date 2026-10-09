"""Compare ideal, unit-device, and routed-bank high-range destructive reads."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
QUAL = ROOT / "artifacts/analog_asic/layout/sky130_shared_read_mim_bank_5x10x10/qualification.json"
UNIT_QUAL = ROOT / "artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2/qualification.json"
DIRECT = RESULTS / "sky130_destructive_read_boundary.json"
N_STATES = 30_976_000
PREFIX = "sky130_min_mim_offswitch_leakage_tt_temp27_"
SUFFIX = "sourcevcm_physicalmoscap_sharedread_inputw0.42um"


def file_info(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def result(offset_mv: int, variant: str, *, reversed_state: bool = False) -> dict:
    offset = "" if offset_mv == 300 else f"offset{offset_mv}mv_"
    reverse = "reversed_" if reversed_state else ""
    path = RESULTS / f"{PREFIX}{offset}{reverse}{SUFFIX}_{variant}.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    if not source["simulation_completed"] or not source["shared_read_attached"]:
        raise RuntimeError(f"incomplete read source: {path}")
    read = source["shared_read_values_v"]
    return {
        "source": file_info(path),
        "commanded_rail_offset_mv": -offset_mv if reversed_state else offset_mv,
        "output_differential_mv": (read["read_outn_end"] - read["read_outp_end"]) * 1e3,
        "state_differential_preconnect_mv": (read["read_high_before"] - read["read_low_before"]) * 1e3,
        "state_differential_end_mv": (read["read_high_end"] - read["read_low_end"]) * 1e3,
        "state_common_mode_step_mv": ((read["read_high_end"] + read["read_low_end"])
                                      - (read["read_high_before"] + read["read_low_before"])) * 500,
    }


def corner_result(corner: str, temp_c: int, offset_mv: int) -> dict:
    path = RESULTS / (f"sky130_min_mim_offswitch_leakage_{corner}_temp{temp_c}_offset{offset_mv}mv_"
                      f"{SUFFIX}_physicalreadbank_rangeselecthigh.json")
    source = json.loads(path.read_text(encoding="utf-8"))
    read = source["shared_read_values_v"]
    if source["return_code"] != 0 or len(read) != 8:
        raise RuntimeError(f"incomplete corner run: {path}")
    commanded_diff_mv = 2 * offset_mv
    initial = next((case for case in source["cases"] if case["switch"] == "routed_tg_moscap_read"), None)
    return {
        "source": file_info(path),
        "commanded_rail_offset_mv": offset_mv,
        "simulation_completed_and_initialization_guard_passed": source["simulation_completed"],
        "initial_differential_mv": ((initial["high_start_v"] - initial["low_start_v"]) * 1e3
                                    if initial else None),
        "commanded_differential_mv": commanded_diff_mv,
        "state_differential_preconnect_mv": (read["read_high_before"] - read["read_low_before"]) * 1e3,
        "output_differential_mv": (read["read_outn_end"] - read["read_outp_end"]) * 1e3,
    }


def main() -> None:
    qualification = json.loads(QUAL.read_text(encoding="utf-8"))
    unit = json.loads(UNIT_QUAL.read_text(encoding="utf-8"))
    direct = json.loads(DIRECT.read_text(encoding="utf-8"))
    if not (qualification["magic_drc_zero"] and qualification["netgen_lvs_unique_match"]
            and qualification["total_physical_mim_units"] == 10):
        raise RuntimeError("shared MIM bank is not physically qualified")
    variants = {
        "ideal_1000ff_each_rail": [result(v, "inputcap1000ff") for v in (450, 750, 900)],
        "five_extracted_unrouted_units_each_rail": [result(v, "readmim5u") for v in (750, 900)],
        "routed_extracted_bank": [result(v, "physicalreadbank") for v in (750, 900)],
        "unrouted_extracted_units_reversed_900mv": result(900, "readmim5u", reversed_state=True),
        "routed_bank_selected_low_signed_1mv": [result(1, "physicalreadbank_rangeselectlow", reversed_state=True),
                                                 result(1, "physicalreadbank_rangeselectlow")],
        "routed_bank_selected_high_750_900mv": [result(v, "physicalreadbank_rangeselecthigh")
                                                 for v in (750, 900)],
        "routed_bank_selected_high_reversed_900mv": result(900, "physicalreadbank_rangeselecthigh",
                                                            reversed_state=True),
    }
    pvt = {corner: [corner_result(corner, temp_c, offset) for offset in (750, 900)]
           for corner, temp_c in (("ss", 0), ("ff", 85))}
    pvt_slopes = {}
    for corner, rows in pvt.items():
        delta_output = rows[1]["output_differential_mv"] - rows[0]["output_differential_mv"]
        delta_preconnect = (rows[1]["state_differential_preconnect_mv"]
                            - rows[0]["state_differential_preconnect_mv"])
        pvt_slopes[corner] = {
            "output_mv_per_commanded_rail_offset_mv": delta_output / 150,
            "output_mv_per_actual_preconnect_differential_mv": delta_output / delta_preconnect,
            "preconnect_differential_gain_mv_per_commanded_rail_offset_mv": delta_preconnect / 150,
            "qualified_as_transfer_slope": all(row["simulation_completed_and_initialization_guard_passed"]
                                               for row in rows),
        }
    short_hold_path = RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_end0.1ms_offset750mv_"
                                 f"{SUFFIX}_physicalreadbank_rangeselecthigh.json")
    short_hold = json.loads(short_hold_path.read_text(encoding="utf-8"))
    if not short_hold["simulation_completed"]:
        raise RuntimeError("short-hold FF screen did not complete")
    short_case = next(case for case in short_hold["cases"] if case["switch"] == "routed_tg_moscap_read")
    short_initial_diff = (short_case["high_start_v"] - short_case["low_start_v"]) * 1e3
    short_pre_diff = (short_hold["shared_read_values_v"]["read_high_before"]
                      - short_hold["shared_read_values_v"]["read_low_before"]) * 1e3
    series_path = RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_offset750mv_"
                             "sourcevcm_physicalmoscap_prechargedseries.json")
    series = json.loads(series_path.read_text(encoding="utf-8"))
    if not series["simulation_completed"]:
        raise RuntimeError("precharged series screen did not complete")
    series_rows = {case["switch"]: {
        "initial_differential_mv": (case["high_start_v"] - case["low_start_v"]) * 1e3,
        "end_differential_mv": (case["high_end_v"] - case["low_end_v"]) * 1e3,
    } for case in series["cases"] if case["switch"] in
        ("routed_tg_moscap", "routed_stacked_precharged_moscap")}
    hv_rows = {}
    for overdrive_v, suffix in ((0.5, "_hvoverdrive"), (1.0, "_hvoverdrive1v")):
        hv_path = RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_offset750mv_"
                             f"sourcevcm_physicalmoscap{suffix}.json")
        hv = json.loads(hv_path.read_text(encoding="utf-8"))
        if not hv["simulation_completed"]:
            raise RuntimeError(f"HV isolation screen did not complete: {hv_path}")
        cases = {case["switch"]: {
            "initial_differential_mv": (case["high_start_v"] - case["low_start_v"]) * 1e3,
            "end_differential_mv": (case["high_end_v"] - case["low_end_v"]) * 1e3,
            "high_rail_drift_mv": case["high_drift_mv"],
            "low_rail_drift_mv": case["low_drift_mv"],
        } for case in hv["cases"] if case["switch"] in
            ("hv_tg_moscap", "hv_tg_overdrive_moscap", "hv_asym_overdrive_moscap",
             "routed_tg_moscap")}
        hv_rows[f"off_gate_overdrive_{overdrive_v:g}v"] = {"source": file_info(hv_path), "cases": cases}
    near_zero_path = RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_offset1mv_"
                                "sourcevcm_physicalmoscap_hvoverdrive1v.json")
    near_zero = json.loads(near_zero_path.read_text(encoding="utf-8"))
    if not near_zero["simulation_completed"]:
        raise RuntimeError("asymmetric near-zero screen did not complete")
    near_zero_cases = {case["switch"]: {
        "initial_differential_mv": (case["high_start_v"] - case["low_start_v"]) * 1e3,
        "end_differential_mv": (case["high_end_v"] - case["low_end_v"]) * 1e3,
    } for case in near_zero["cases"] if case["switch"] in
        ("hv_tg_overdrive_moscap", "hv_n_overdrive_moscap", "hv_p_overdrive_moscap",
         "hv_asym_overdrive_moscap")}
    reverse_path = RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_offset750mv_reversed_"
                              "sourcevcm_physicalmoscap_hvoverdrive1v.json")
    reverse = json.loads(reverse_path.read_text(encoding="utf-8"))
    if not reverse["simulation_completed"]:
        raise RuntimeError("asymmetric reversed-state screen did not complete")
    reverse_case = next(case for case in reverse["cases"] if case["switch"] == "hv_asym_overdrive_moscap")
    parked_path = RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_offset750mv_"
                             "physicalmoscap_hvoverdrive1v.json")
    parked = json.loads(parked_path.read_text(encoding="utf-8"))
    if not parked["simulation_completed"]:
        raise RuntimeError("parked-source HV leakage screen did not complete")
    vcm_hv = json.loads((RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_offset750mv_"
                                    "sourcevcm_physicalmoscap_hvoverdrive1v.json")).read_text(encoding="utf-8"))
    vcm_cases = {case["switch"]: case for case in vcm_hv["cases"]}
    parked_cases = {case["switch"]: case for case in parked["cases"]}
    hv_source_comparison = {kind: {
        mode: {"low_drift_mv": cases[kind]["low_drift_mv"],
               "high_drift_mv": cases[kind]["high_drift_mv"]}
        for mode, cases in (("fixed_vcm_bus", vcm_cases), ("parked_initial_state_bus", parked_cases))}
        for kind in ("hv_tg_moscap", "hv_tg_overdrive_moscap",
                     "hv_n_overdrive_moscap", "hv_p_overdrive_moscap")}
    body_path = RESULTS / ("sky130_min_mim_offswitch_leakage_ff_temp85_offset750mv_"
                           "sourcevcm_physicalmoscap_hvoverdrive1v_bodycurrents.json")
    body = json.loads(body_path.read_text(encoding="utf-8"))
    if not body["simulation_completed"]:
        raise RuntimeError("HV terminal-current screen did not complete")
    hv_current_rows = {}
    for side in ("low", "high"):
        for device in ("n", "p"):
            key = f"hv_tg_overdrive_moscap_{side}_{device}"
            body_a = body["hv_body_current_end_a"][f"body_{key}_current_end"]
            source_a = body["hv_terminal_current_end_a"][f"term_{key}_source_current_end"]
            state_a = body["hv_terminal_current_end_a"][f"term_{key}_state_current_end"]
            hv_current_rows[key] = {
                "body_probe_a": body_a, "source_terminal_probe_a": source_a,
                "state_terminal_probe_a": state_a,
                "body_minus_source_plus_state_a": body_a - (source_a + state_a),
            }
    slopes = {name: ((rows[-1]["output_differential_mv"] - rows[-2]["output_differential_mv"]) / 150)
              for name, rows in variants.items() if isinstance(rows, list)
              and rows[-2]["commanded_rail_offset_mv"] == 750}
    bbox = qualification["gds_bbox_um"]
    bank_area_mm2 = math.prod(bbox) / 1e6
    read_window_us = 10
    precharge_window_us = 10
    channels_if_serial_20us = math.ceil(N_STATES * (read_window_us + precharge_window_us) / 5000)
    report = {
        "test": "sky130_shared_mim_bank_high_range_read_boundary",
        "bank_qualification": {**file_info(QUAL), "gds_bbox_um": bbox,
                               "unit_count": qualification["total_physical_mim_units"],
                               "pex_explicit_capacitors": qualification["pex_explicit_capacitors"]},
        "unit_qualification": {**file_info(UNIT_QUAL),
                               "tt_extracted_cv_f_per_unit": unit["extracted_cv_f"]},
        "variants": variants,
        "selected_high_range_ss_ff_750_900mv": pvt,
        "selected_high_range_ss_ff_slopes": pvt_slopes,
        "short_hold_ff_100us_750mv": {
            "source": file_info(short_hold_path),
            "initial_differential_mv": short_initial_diff,
            "preconnect_differential_mv": short_pre_diff,
            "fraction_retained_before_read": short_pre_diff / short_initial_diff,
        },
        "precharged_two_tg_ff_5ms_750mv": {"source": file_info(series_path), "cases": series_rows},
        "schematic_hv_off_bias_ff_5ms_750mv": hv_rows,
        "schematic_hv_asymmetric_near_zero_ff_5ms_1mv": {
            "source": file_info(near_zero_path), "cases": near_zero_cases},
        "schematic_hv_asymmetric_reversed_ff_5ms_750mv": {
            "source": file_info(reverse_path),
            "initial_differential_mv": (reverse_case["high_start_v"] - reverse_case["low_start_v"]) * 1e3,
            "end_differential_mv": (reverse_case["high_end_v"] - reverse_case["low_end_v"]) * 1e3,
        },
        "schematic_hv_fixed_vs_parked_source_ff_5ms_750mv": {
            "parked_source": file_info(parked_path), "cases": hv_source_comparison},
        "schematic_hv_terminal_currents_ff_5ms_750mv": {
            "source": file_info(body_path), "overdriven_tg_5ms": hv_current_rows},
        "tt_output_slope_mv_per_mv_commanded_rail_offset_750_to_900": slopes,
        "direct_no_extra_cap_boundary": file_info(DIRECT),
        "direct_no_extra_cap_slope_mv_per_mv": direct["tt_output_mv_per_rail_offset_mv_750_to_900"],
        "conditional_service": {
            "resident_state_count": N_STATES, "semantic_bin_us": 5000,
            "diagnostic_precharge_window_us": precharge_window_us,
            "diagnostic_read_window_us": read_window_us,
            "zero_overhead_parallel_channels_if_serial_windows": channels_if_serial_20us,
            "read_bank_bbox_mm2_per_channel": bank_area_mm2,
            "read_bank_bbox_mm2_at_that_channel_count": bank_area_mm2 * channels_if_serial_20us,
            "parallel_channels_if_100us_refresh_with_same_20us_visit": math.ceil(N_STATES * 20 / 100),
            "read_bank_bbox_mm2_if_100us_refresh": bank_area_mm2 * math.ceil(N_STATES * 20 / 100),
            "excludes": "State storage, access TGs, sensor, routing, calibration, writeback, clock, DAG contention and margins; windows are bench timing, not proven minimum settling times."
        },
        "decision": "The routed five-MIM-per-rail shared bank is a qualified physical capacitor module. A selectable extracted-TG connection retains low-range signed response and high-range slope in bounded TT deterministic screens. SS/FF high-range measurements show substantial hold compression; the FF 900mV command fails the initialization guard and is a diagnostic only. At FF/85C and 750mV, even a 100us visit loses material stored differential before read; a correctly precharged two-TG intermediate node does not restore 5ms retention. Schematic 5V-device off-gate overdrive from 0.5 to 1.0V has negligible further benefit. Holding the overdriven TG source at the initial state voltage instead of VCM leaves its drift unchanged. Zero-volt terminal probes show pA-scale body currents accounting for the switch terminal currents at 5ms, making the held-node body/junction path the next topology target. An asymmetric NMOS-low/PMOS-high cell reduces positive750mV hold error but produces a false 100.48mV differential from a 2.02mV near-zero state at FF and attenuates reversed750mV to -1250.65mV. Reject that fixed asymmetric cell. State is heavily disturbed, so the shared bank remains a candidate readout component, not an accepted state architecture. Stop high-range readout promotion until retention and initialization are fixed or scheduled refresh is proved.",
        "limitations": "Standard PDK MIM model and extracted bank coupling; diagnostic SUB parasitic node tied to ground in the SPICE include, not an explicit substrate GDS port. Other state MIM uses reduced-order model. Sensor, precharge, selection and clock are schematic/ideal; physical modules are separate. HV TGs are schematic PDK devices with ideal off-gate sources and no DRC/LVS/PEX or complete PVT; do not treat them as a laid-out reliable switch. Sparse transfer/PVT endpoints, no switched noise/mismatch, writeback or complete event sequence. FF 900mV completed ngspice but failed the source bench's initial-value guard; its output is diagnostic only. Service/area multiplication is conditional only.",
    }
    out = RESULTS / "sky130_shared_range_read_boundary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "slopes_mv_per_mv": slopes,
                      "conditional_channels": channels_if_serial_20us,
                      "conditional_bank_bbox_mm2": report["conditional_service"]["read_bank_bbox_mm2_at_that_channel_count"]}, indent=2))


if __name__ == "__main__":
    main()
