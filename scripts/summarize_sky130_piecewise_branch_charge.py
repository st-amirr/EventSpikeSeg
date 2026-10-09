"""Summarize bounded physical branch-charge probes for live range crossing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
CASES = (
    "sky130_piecewise_fixedcap_crossing_tt_temp27_trim1203uv_gate1_width1.5us_init-6000uv_branchprobes.json",
    "sky130_piecewise_fixedcap_crossing_ss_temp0_trim212uv_gate0.9_width2us_init-6000uv_branchprobes.json",
    "sky130_piecewise_fixedcap_crossing_ff_temp85_trim582uv_gate1_width1.5us_init-6000uv_branchprobes.json",
    "sky130_piecewise_fixedcap_crossing_ff_temp85_trim582uv_gate1.1_width1.5us_init-6000uv_branchprobes.json",
)


def main() -> None:
    rows = []
    for name in CASES:
        path = RESULTS / name
        source = json.loads(path.read_text(encoding="utf-8"))
        assert source["simulation_completed"] and source["branch_current_probes_enabled"]
        measurement = source["measurements"]
        fast_fc = measurement["fast_charge_c"] * 1e15
        slow_fc = measurement["slow_charge_c"] * 1e15
        rows.append({
            "source": name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "corner": source["corner"],
            "temperature_c": source["temperature_c"],
            "ideal_pulse_gate_level_v": source["pulse_gate_level_v"],
            "ideal_boundary_trim_uv": source["analog_reference_trim_uv"],
            "fast_branch_charge_fc": fast_fc,
            "slow_branch_charge_fc": slow_fc,
            "total_branch_charge_fc": fast_fc + slow_fc,
            "slow_fraction_of_total": slow_fc / (fast_fc + slow_fc),
            "event_minus_no_event_mv": source["net_event_change_vs_no_event_v"] * 1e3,
            "selector_delay_from_nominal_state_cross_ns": source["selector_latency_after_state_cross_ns"],
            "state_at_selector_error_uv": source["comparator_trip_state_offset_vs_target_uv"],
            "dynamic_inside_static_control_bracket": source["dynamic_within_static_control_bracket"],
        })
    tt = rows[0]
    ff_a, ff_b = rows[2:]
    report = {
        "test": "sky130_fixed_cap_live_crossing_branch_charge_diagnostic",
        "cases": rows,
        "ff_gate_step_v": ff_b["ideal_pulse_gate_level_v"] - ff_a["ideal_pulse_gate_level_v"],
        "ff_event_change_ratio_before_to_after_gate_step": ff_a["event_minus_no_event_mv"] / ff_b["event_minus_no_event_mv"],
        "ff_event_change_ratio_to_tt_at_gate_1v": ff_a["event_minus_no_event_mv"] / tt["event_minus_no_event_mv"],
        "finding": "The live two-range branch charge is measurable across TT/SS/FF, but the ideal pulse-gate voltage strongly changes charge and comparator timing. FF at 1.1V changes range before the state reaches the nominal boundary, so event charge and comparator trip must be calibrated together. This is no evidence of a physically encoded original-float weight or a PVT-robust full PLIF update.",
        "scope": "One positive 20um MIM state crossing per case, with ideal gate and comparator reference sources, PDK schematic PFET/TG/comparator and branch-current probes. No signed negative event, physical bias generator, full-float weight sequence, mismatch/noise, extracted layout, 5ms hold or full-chip service.",
    }
    out = RESULTS / "sky130_piecewise_branch_charge_summary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
