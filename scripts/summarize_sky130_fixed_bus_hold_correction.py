"""Bound correction conditioning for the routed small-MIM state on a shared VCM bus."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
SOURCES = (
    "sky130_min_mim_offswitch_leakage_tt_temp27_offset1mv_sourcevcm",
    "sky130_min_mim_offswitch_leakage_tt_temp27_sourcevcm",
    "sky130_min_mim_offswitch_leakage_ss_temp0_offset1mv_sourcevcm",
    "sky130_min_mim_offswitch_leakage_ss_temp0_sourcevcm",
    "sky130_min_mim_offswitch_leakage_ff_temp85_offset1mv_sourcevcm",
    "sky130_min_mim_offswitch_leakage_ff_temp85_sourcevcm",
)


def main() -> None:
    cases = []
    for stem in SOURCES:
        path = RESULTS / f"{stem}.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        if not source["simulation_completed"] or source["off_switch_source_mode"] != "vcm":
            raise RuntimeError(f"incomplete fixed-bus source: {path}")
        routed = next(case for case in source["cases"] if case["switch"] == "routed_tg")
        start = routed["high_start_v"] - routed["low_start_v"]
        end = routed["high_end_v"] - routed["low_end_v"]
        fraction = end / start
        cases.append({
            "source": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "corner": source["corner"],
            "temperature_c": source["temperature_c"],
            "commanded_offset_mv": source["commanded_state_offset_from_vcm_mv"],
            "initial_differential_mv": start * 1e3,
            "end_differential_mv": end * 1e3,
            "differential_retention_fraction": fraction,
            "ideal_inverse_read_error_gain": 1 / fraction,
            "initial_common_mode_v": (routed["low_start_v"] + routed["high_start_v"]) / 2,
            "end_common_mode_v": (routed["low_end_v"] + routed["high_end_v"]) / 2,
            "common_mode_shift_mv": ((routed["low_end_v"] + routed["high_end_v"])
                                     - (routed["low_start_v"] + routed["high_start_v"])) * 500,
        })
    report = {
        "test": "sky130_small_mim_fixed_shared_bus_hold_inverse_conditioning",
        "cases": cases,
        "retention_fraction_range": [min(x["differential_retention_fraction"] for x in cases),
                                     max(x["differential_retention_fraction"] for x in cases)],
        "ideal_inverse_read_error_gain_range": [min(x["ideal_inverse_read_error_gain"] for x in cases),
                                                max(x["ideal_inverse_read_error_gain"] for x in cases)],
        "decision": "A calibrated differential inverse is algebraically possible in these two symmetric input-offset screens, but it multiplies state read error by about two. The FF/85C common-mode shift is large. This is not an accepted restoration circuit or 5ms service architecture; do not promote this minimum-MIM/TG cell to resident state layout.",
        "next_gate": "Demonstrate physically compact differential sensing and writeback with switched noise/mismatch, source-state-dependent transfer, event bucket integration, and one visit per resident state per 5ms including DAG timing. The existing 30us large sampled readout fails direct population area/service scaling.",
        "limitations": "Only symmetric +/-1mV and +/-300mV initial states at TT27, SS0 and FF85; fixed ideal 0.9V access bus, ideal programming and reduced-order PDK MIM, extracted MIM/TG parasitics. No transfer interpolation, read/write circuitry, injected events, stochastic noise, calibration variation, yield or full-chip evidence. Inverse gain is a local deterministic error multiplier, not measured noise or accuracy.",
    }
    out = RESULTS / "sky130_fixed_bus_hold_correction_boundary.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "retention_fraction_range": report["retention_fraction_range"],
                      "inverse_error_gain_range": report["ideal_inverse_read_error_gain_range"]}, indent=2))


if __name__ == "__main__":
    main()
