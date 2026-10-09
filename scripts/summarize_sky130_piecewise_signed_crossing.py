"""Summarize signed fixed-cap live-range crossing PDK diagnostics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
CASES = (
    "sky130_piecewise_fixedcap_crossing_tt_temp27_trim1203uv_gate1_width1.5us_init-6000uv_branchprobes.json",
    "sky130_piecewise_fixedcap_crossing_tt_temp27_trim-100uv_gate0.4_width1.5us_init+6000uv_branchprobes_negative.json",
    "sky130_piecewise_fixedcap_crossing_ss_temp0_trim723uv_gate0.45_width1.5us_init+6000uv_branchprobes_negative.json",
    "sky130_piecewise_fixedcap_crossing_ff_temp85_trim-1643.5uv_gate0.305_width1.5us_init+6000uv_branchprobes_negative.json",
)


def main() -> None:
    rows = []
    for name in CASES:
        path = RESULTS / name
        source = json.loads(path.read_text(encoding="utf-8"))
        if not source["simulation_completed"] or not source["branch_current_probes_enabled"]:
            raise RuntimeError(f"incomplete branch-crossing source: {path}")
        v = source["measurements"]
        sign = source.get("event_sign", "positive")
        update_mv = source["net_event_change_vs_no_event_v"] * 1e3
        if (update_mv > 0) != (sign == "positive"):
            raise RuntimeError(f"wrong signed event response: {path}")
        rows.append({
            "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "corner": source["corner"],
            "temperature_c": source["temperature_c"],
            "event_sign": sign,
            "ideal_gate_v": source["pulse_gate_level_v"],
            "ideal_comparator_reference_trim_uv": source["analog_reference_trim_uv"],
            "pulse_width_us": source["pulse_width_us"],
            "net_event_update_mv": update_mv,
            "fast_branch_charge_fc": v["fast_charge_c"] * 1e15,
            "slow_branch_charge_fc": v["slow_charge_c"] * 1e15,
            "selector_delay_from_state_cross_ns": source["selector_latency_after_state_cross_ns"],
            "state_at_selector_error_from_boundary_uv": source["comparator_trip_state_offset_vs_target_uv"],
            "event_within_static_fast_slow_controls": source["dynamic_within_static_control_bracket"],
        })
    negative_magnitudes = [abs(row["net_event_update_mv"]) for row in rows[1:]]
    report = {
        "test": "sky130_fixed_mim_signed_live_range_crossing_screen",
        "cases": rows,
        "tt_positive_negative_update_magnitude_ratio": abs(rows[1]["net_event_update_mv"] / rows[0]["net_event_update_mv"]),
        "negative_corner_update_range_mv": [min(negative_magnitudes), max(negative_magnitudes)],
        "interpretation": "A signed positive and negative live boundary crossing is possible in one fixed PDK MIM/TG/comparator topology under external gate and comparator-reference commands. SS/FF negative cases were manually fitted to the selected single event; the required gate/reference values differ substantially by corner. This does not encode an original-float weight, prove pulse-completion scheduling, or preserve a 5ms resident state.",
        "scope": "One positive TT and three negative TT/SS/FF deterministic schematic events, each 1.5us. Ideal gate waveforms and comparator reference; PDK MOS switches/current branches/comparator and schematic 20x20um MIM. No PEX, noise/mismatch, negative and positive same-corner sequence, repeat-event order, beta/threshold/reset/adaptation, full-float replay, state hold or layout acceptance.",
    }
    out = RESULTS / "sky130_piecewise_signed_crossing_summary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "cases": rows}, indent=2))


if __name__ == "__main__":
    main()
