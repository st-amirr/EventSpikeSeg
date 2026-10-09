"""Summarize minimum routed MIM/TG hold and conditional refresh bounds."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
LAYOUT = ROOT / "artifacts/analog_asic/layout/sky130_differential_trim_cap_pair/qualification.json"
MOS_LAYOUT = ROOT / "artifacts/analog_asic/layout/sky130_mos_gate_state_pair_100x10_nf10/qualification.json"
N_STATE = 30_976_000
STEMS = (
    "sky130_min_mim_pair_pex_tg_hold_ss_temp0",
    "sky130_min_mim_pair_pex_tg_hold_ss_temp0_reducedmim",
    "sky130_min_mim_pair_pex_tg_hold_ss_temp0_reducedmim_subground",
    "sky130_min_mim_pair_pex_tg_hold_ss_temp0_subground",
    "sky130_min_mim_pair_pex_tg_hold_ss_temp0_reducedmim_subground_stackedtg",
)
OFFSWITCH_STEMS = (
    "sky130_min_mim_offswitch_leakage_ss_temp0",
    "sky130_min_mim_offswitch_leakage_ss_temp0_standardmim",
)
NARROW_OFFSETS_MV = (1, 10)
EVENT_TIME = RESULTS / "sky130_min_mim_routed_tg_event_time_decay_ss0_step50ns.json"
FLOAT_PARAMS = ROOT / "artifacts/analog_asic/model_reference/eventspikeseg140k_float_parameters.npz"


def main() -> None:
    qual = json.loads(LAYOUT.read_text(encoding="utf-8"))
    mos_qual = json.loads(MOS_LAYOUT.read_text(encoding="utf-8"))
    assert mos_qual["magic_drc_zero"] and mos_qual["netgen_lvs_unique_match"]
    cases = []
    for stem in STEMS:
        path = RESULTS / f"{stem}.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        if not source["simulation_completed"] or source["corner"] != "SS":
            raise RuntimeError(f"incomplete SS case: {path}")
        cases.append({
            "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "reduced_mim": source.get("reduced_mim_internal_series_rc", False),
            "pex_substrate_grounded": source.get("extracted_substrate_node_tied_to_ground", False),
            "two_series_tgs": source.get("two_series_routed_tgs_per_state", False),
            "low_v_hold": source["hold"]["low"],
            "high_v_hold": source["hold"]["high"],
        })
    base = next(row for row in cases if row["reduced_mim"] and row["pex_substrate_grounded"]
                and not row["two_series_tgs"])
    worst_mv = max(abs(base[side]["tg_minus_ideal_drift_mv"]) for side in ("low_v_hold", "high_v_hold"))
    pair_bbox_mm2 = math.prod(qual["gds_bbox_um"]) / 1e6
    cap_per_state_f = qual["unit_capacitance_f"] + 0.38e-15 + 1.07e-15
    inferred_current_a = cap_per_state_f * worst_mv * 1e-3 / 5e-3
    mim_density_f_per_um2 = qual["unit_capacitance_f"] / 4
    fixed_current_area = []
    for allowed_drift_v in (1e-3, 100e-6, 6e-6):
        required_cap_f = inferred_current_a * 5e-3 / allowed_drift_v
        fixed_current_area.append({
            "allowed_drift_v": allowed_drift_v,
            "required_cap_f_if_current_fixed": required_cap_f,
            "bare_mim_area_um2_per_state": required_cap_f / mim_density_f_per_um2,
            "bare_mim_area_mm2_for_inventory": required_cap_f / mim_density_f_per_um2 * N_STATE / 1e6,
        })
    offswitch = []
    for stem in OFFSWITCH_STEMS:
        path = RESULTS / f"{stem}.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        if not source["simulation_completed"]:
            raise RuntimeError(f"incomplete off-switch screen: {path}")
        offswitch.append({
            "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "reduced_mim": source.get("reduced_mim_internal_series_rc", not stem.endswith("standardmim")),
            "cases": {case["switch"]: {key: case[key] for key in ("low_drift_mv", "high_drift_mv")}
                      for case in source["cases"]},
        })
    narrow_hold = []
    for offset_mv in NARROW_OFFSETS_MV:
        path = RESULTS / f"sky130_min_mim_offswitch_leakage_ss_temp0_offset{offset_mv}mv.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        if not source["simulation_completed"] or source["commanded_state_offset_from_vcm_mv"] != offset_mv:
            raise RuntimeError(f"incomplete near-VCM hold source: {path}")
        cases_by_kind = {case["switch"]: case for case in source["cases"]}
        bare, tg, stack = (cases_by_kind[key] for key in ("bare", "routed_tg", "routed_stacked_tg"))
        narrow_hold.append({
            "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "offset_mv": offset_mv,
            "bare_low_drift_mv": bare["low_drift_mv"],
            "bare_high_drift_mv": bare["high_drift_mv"],
            "routed_tg_low_drift_mv": tg["low_drift_mv"],
            "routed_tg_high_drift_mv": tg["high_drift_mv"],
            "two_series_routed_tg_low_drift_mv": stack["low_drift_mv"],
            "two_series_routed_tg_high_drift_mv": stack["high_drift_mv"],
            "low_fraction_of_offset_lost": tg["low_drift_mv"] / offset_mv,
            "high_fraction_of_offset_lost": -tg["high_drift_mv"] / offset_mv,
        })
    event_time_source = json.loads(EVENT_TIME.read_text(encoding="utf-8"))
    if not event_time_source["simulation_completed"]:
        raise RuntimeError(f"incomplete event-time hold source: {EVENT_TIME}")
    event_time = {
        "source": str(EVENT_TIME.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(EVENT_TIME.read_bytes()).hexdigest(),
        "ideal_current_pulse_na": event_time_source["ideal_current_pulse_na"],
        "ideal_pulse_width_ns": event_time_source["ideal_pulse_width_ns"],
        "max_transient_step_ns": event_time_source["max_transient_step_ns"],
        "event_times_ms": event_time_source["event_times_ms"],
        "early_immediate_increment_mv": event_time_source["early_immediate_increment_mv"],
        "late_immediate_increment_mv": event_time_source["late_immediate_increment_mv"],
        "early_final_increment_mv": event_time_source["early_final_increment_mv"],
        "late_final_increment_mv": event_time_source["late_final_increment_mv"],
        "immediate_early_to_late_ratio": event_time_source["immediate_early_to_late_ratio"],
        "early_to_late_final_ratio": event_time_source["early_to_late_final_ratio"],
    }
    with np.load(FLOAT_PARAMS) as exported:
        beta = np.concatenate([exported[key].ravel() for key in exported.files if key.startswith("beta__")])
    beta_comparison = {
        "source": str(FLOAT_PARAMS.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(FLOAT_PARAMS.read_bytes()).hexdigest(),
        "exported_channel_values": int(beta.size),
        "min": float(np.min(beta)),
        "q10": float(np.quantile(beta, 0.1)),
        "median": float(np.median(beta)),
        "q90": float(np.quantile(beta, 0.9)),
        "max": float(np.max(beta)),
        "count_below_0p6": int(np.count_nonzero(beta < 0.6)),
        "count_at_least_0p9": int(np.count_nonzero(beta >= 0.9)),
        "scope": "Unweighted exported per-channel learned beta values, not a state-count or activity-weighted distribution. Float PLIF beta acts once at the bin boundary; physical TG leak acts continuously and attenuates early events more than late ones.",
    }
    report = {
        "test": "sky130_minimum_mim_state_5ms_hold_area_boundary",
        "source_pair_qualification": str(LAYOUT.relative_to(ROOT)).replace("\\", "/"),
        "source_pair_qualification_sha256": hashlib.sha256(LAYOUT.read_bytes()).hexdigest(),
        "cases": cases,
        "off_switch_isolation": offswitch,
        "near_vcm_off_switch_hold": narrow_hold,
        "equal_ideal_charge_event_time_screen": event_time,
        "original_float_learned_beta_comparison": beta_comparison,
        "off_switch_finding": "With ideal programming, the bare minimum MIM holds in the reduced model; NMOS-only drifts downward, PMOS-only upward, and a routed TG drifts about +/-156mV over 5ms. Increasing tested schematic single-device channel length from0.5 to8um changes the 5ms drift by less than0.05mV for NMOS and0.03mV for PMOS on their large-drift rails. The grounded-substrate standard PDK MIM model reproduces this qualitative pattern. This points to junction/body/off-device leakage rather than a simple short-channel-only leakage fix, but transistor internal currents were not independently decomposed.",
        "unrefreshed_5ms_acceptance": False,
        "reason": "Substrate-grounded and reduced-MIM diagnostic removes ideal-control drift, while actual routed TG still causes >149mV state movement at SS/0C. Standard PDK MIM with grounded substrate produces similar switch-dominated movement. Two series routed TGs do not repair it.",
        "reduced_mim_grounded_ss_worst_tg_minus_ideal_drift_mv": worst_mv,
        "nominal_state_cap_with_pex_f": cap_per_state_f,
        "approximate_hold_leakage_a_if_linear": inferred_current_a,
        "conditional_fixed_current_mim_area": fixed_current_area,
        "conditional_refresh_interval_us_at_1mv_drift_if_linear": 5000 / worst_mv,
        "conditional_refresh_operations_per_second_for_inventory_at_1mv_if_linear": N_STATE / (5e-3 / worst_mv),
        "routed_two_mim_pair_bbox_um": qual["gds_bbox_um"],
        "routed_pair_bbox_floor_mm2_if_one_pair_per_two_states": pair_bbox_mm2 * N_STATE / 2,
        "bare_2x2um_mim_plate_floor_mm2": 4 * N_STATE / 1e6,
        "routed_pair_bbox_floor_mm2_if_one_differential_pair_per_state": pair_bbox_mm2 * N_STATE,
        "bare_two_2x2um_mim_plates_floor_mm2_if_differential": 8 * N_STATE / 1e6,
        "large_mos_gate_pair_layout": {
            "source": str(MOS_LAYOUT.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(MOS_LAYOUT.read_bytes()).hexdigest(),
            "bbox_um": mos_qual["gds_bbox_um"],
            "pair_bbox_floor_mm2_if_one_differential_pair_per_state": math.prod(mos_qual["gds_bbox_um"]) * N_STATE / 1e6,
            "scope": "Existing physically extracted MOS pair used by prior ideal companding retention replay; direct repeated-layout bounding-box estimate, no optimized tiling, switches, state update or full-chip assembly.",
        },
        "limitations": "Refresh arithmetic assumes approximately linear drift and ideal restoration. The capacitance/area extrapolation holds the wide-range inferred off-switch current fixed as capacitance grows; near VCM the new measurements show current falls with state offset, so these area values must not be applied to compressed-state operation. They are conditional wide-range design-pressure estimates, not rigorous physical lower bounds or a viable circuit. PEX VSUBS was explicitly grounded in diagnostic runs and the reduced MIM model is not signoff. One corner, selected held voltages, no events, beta, readout, noise/mismatch or full-chip layout.",
    }
    out = RESULTS / "sky130_min_mim_hold_boundary_summary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "drift_mv": worst_mv,
                      "pair_bbox_floor_mm2": report["routed_pair_bbox_floor_mm2_if_one_pair_per_two_states"],
                      "approximate_hold_leakage_a": report["approximate_hold_leakage_a_if_linear"]}, indent=2))


if __name__ == "__main__":
    main()
