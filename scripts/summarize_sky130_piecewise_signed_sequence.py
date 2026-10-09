"""Summarize fixed-gate physical signed sequence corner sensitivity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
CASES = (
    "sky130_piecewise_signed_direct_sequence_tt27_ng0.3678.json",
    "sky130_piecewise_signed_direct_sequence_ss0_ng0.3678.json",
    "sky130_piecewise_signed_direct_sequence_ff85_ng0.3678.json",
)
CALIBRATED_CASES = (
    "sky130_piecewise_signed_direct_sequence_tt27_ng0.3678.json",
    "sky130_piecewise_signed_direct_sequence_ss0_ng0.4271_pg0.9.json",
    "sky130_piecewise_signed_direct_sequence_ff85_ng0.2732_pg1.16.json",
)


def row_for(name: str) -> dict:
    path = RESULTS / name
    source = json.loads(path.read_text(encoding="utf-8"))
    if not source["simulation_completed"]:
        raise RuntimeError(f"incomplete sequence source: {path}")
    sequences = source["sequences"]
    return {
        "source": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "corner": source["corner"], "temperature_c": source["temperature_c"],
        "ideal_positive_gate_v": source["positive_gate_v"],
        "ideal_negative_gate_v": source["negative_gate_v"],
        "positive_single_mv": sequences["pz"]["net_update_vs_no_event_mv"],
        "negative_single_mv": sequences["nz"]["net_update_vs_no_event_mv"],
        "pn_residual_mv": sequences["pn"]["net_update_vs_no_event_mv"],
        "np_residual_mv": sequences["np"]["net_update_vs_no_event_mv"],
        "pn_minus_np_mv": source["pn_order_difference_mv"],
        "pn_nonadditivity_mv": source["pn_nonadditivity_mv"],
        "np_nonadditivity_mv": source["np_nonadditivity_mv"],
    }


def main() -> None:
    rows = [row_for(name) for name in CASES]
    calibrated = [row_for(name) for name in CALIBRATED_CASES]
    report = {
        "test": "sky130_fixed_cap_signed_direct_sequence_corner_summary",
        "cases": rows,
        "individually_fitted_cases": calibrated,
        "interpretation": "A manually balanced TT direct PFET/NFET gate pair is not portable to SS/FF. Individually fitted gate pairs recover about 10mV single-event magnitude and tens of microvolts pair residual in all three corners, but this requires ideal per-corner commands and still has roughly 17-21uV pn/np order spread. A physical state-aware driver and much better accuracy would be needed for original-float margins.",
        "scope": "TT/27C, SS/0C, FF/85C physical MOS/schematic-MIM deterministic two-event screens on one state each, with ideal gate pulses and matched no-event drift. No live range comparator, physical bias calibration, PEX, mismatch/noise, 5ms hold, PLIF semantics, actual float fan-in, or network throughput.",
    }
    output = RESULTS / "sky130_piecewise_signed_sequence_corner_summary.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
