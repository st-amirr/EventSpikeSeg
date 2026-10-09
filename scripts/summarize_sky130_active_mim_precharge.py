#!/usr/bin/env python3
"""Aggregate bounded SKY130 active MIM precharge sweeps without qualifying them."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
OUT = RESULTS / "sky130_active_mim_precharge_sweep_summary.json"


def main() -> int:
    rows = []
    for path in sorted(RESULTS.glob("sky130_active_mim_range_precharge_tt_edge*ns_diff*mv*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        if not report.get("simulation_completed"):
            continue
        rows.append({
            "source_report": path.name,
            "state_diff_mv": report["initial_state_differential_mv"],
            "edge_ns": report["control_edge_ns"],
            "win_um": report.get("ota_input_pair_width_um", 10.0),
            "vbiasp_v": report.get("ota_vbiasp_v", 0.75),
            "switch_on_v": report.get("switch_on_levels_v", [1.8, 0.0])[0],
            "extension_error_uv": report["extension_precharge_error_vs_live_state_uv"],
            "state_error_vs_reference_uv": report["state_error_vs_reference_after_settle_uv"],
        })
    rows.sort(key=lambda item: (item["state_diff_mv"], item["switch_on_v"], item["vbiasp_v"], item["win_um"]))
    summary = {
        "test": "sky130_active_mim_extension_precharge_parameter_sweep",
        "simulation_reports_included": len(rows),
        "qualified_transition": False,
        "ranking_metric": "absolute final differential state error versus the initialized no-extension reference; this is a diagnostic, not an acceptance threshold",
        "scope": "Nominal TT/27C schematic OTA+PDK TG+MIM only. No layout/PEX, PVT, mismatch/noise, actual boundary crossings, weighted events or full-float replay.",
        "cases": rows,
        "best_by_state_span": {},
    }
    for diff in sorted({row["state_diff_mv"] for row in rows}):
        candidates = [row for row in rows if row["state_diff_mv"] == diff]
        summary["best_by_state_span"][str(diff)] = min(
            candidates, key=lambda row: abs(row["state_error_vs_reference_uv"]))
    OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": str(OUT.relative_to(ROOT)),
                      "cases": len(rows), "best_by_state_span": summary["best_by_state_span"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
