"""Summarize the bounded physical final-fusion float fan-in simulation."""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
BASE = "sky130_ms_first_touch_float_fanin_ss0"


def main() -> int:
    corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                   if arg.startswith("--corner=")), "ss")
    temperature_c = {"ss": 0, "tt": 27, "ff": 85}.get(corner)
    if temperature_c is None:
        raise ValueError("unknown corner")
    map_corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                       if arg.startswith("--map-corner=")), corner)
    if map_corner not in ("ss", "tt", "ff"):
        raise ValueError("unknown map corner")
    order_set = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                      if arg.startswith("--orders=")), "all")
    if order_set not in ("all", "forward", "reverse", "shuffle"):
        raise ValueError("unknown orders")
    site = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                 if arg.startswith("--site=")), "max_fanin")
    if site not in ("max_fanin", "high_cancellation", "near_threshold_scale"):
        raise ValueError("unknown site")
    mapping = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                    if arg.startswith("--mapping=")), "short_linear")
    if mapping not in ("short_linear", "stage_linear", "stage_log"):
        raise ValueError("unknown mapping")
    stem = BASE.replace("ss0", f"{corner}{temperature_c}")
    if map_corner != corner:
        stem += f"_map{map_corner}"
    if site != "max_fanin":
        stem += f"_{site}"
    if mapping != "short_linear":
        stem += f"_{mapping}"
    if order_set != "all":
        stem += f"_{order_set}only"
    deck = json.loads((RES / f"{stem}_deck.json").read_text(encoding="utf-8"))
    log = (RES / f"{stem}.log").read_text(encoding="utf-8", errors="replace")
    if "ngspice-36 done" not in log or "Error:" in log or "Timestep too small" in log:
        raise RuntimeError("physical float fan-in transient did not complete cleanly")
    measures = {}
    for name in ("ref", *deck.get("event_orders", ("forward", "reverse", "shuffle"))):
        match = re.search(rf"^final_{name}\s*=\s*([+-]?[\d.]+[eE][+-]?\d+)", log, re.M)
        if match is None:
            raise RuntimeError(f"missing physical final_{name} measure")
        measures[name] = float(match.group(1))
    ideal = deck["ideal_event_sum_v"]
    corrected = {name: value - measures["ref"] for name, value in measures.items() if name != "ref"}
    report = {**deck, "test": "sky130_first_touch_full_float_fanin_physical_sum",
              "simulation_completed": True, "corner": corner, "temperature_c": temperature_c,
              "ngspice_version": 36, "zero_event_reference_v": measures["ref"],
              "physical_final_differential_v": measures,
              "physical_final_minus_reference_v": corrected,
              "error_v_by_order": {name: value - ideal for name, value in corrected.items()},
              "relative_error_by_order": {name: value / ideal - 1 for name, value in corrected.items()} if ideal else None,
              "max_order_spread_v": max(corrected.values()) - min(corrected.values()),
              "max_order_spread_fraction_of_ideal_magnitude":
                  (max(corrected.values()) - min(corrected.values())) / abs(ideal),
              "pwl_aggregate_mapping_qualified": False,
              "full_float_neuron_function_qualified": False,
              "interpretation": "Actual float signed weights and activation multiplicities at one saved final-fusion site produce a physical signed sum. Reordering the identical events changes the final state. Gate voltages are inferred from a sparse single-event charge curve; interpolation error and accumulation state dependence remain separable only by further calibration. Ideal gate controls, no physical DAC/calibration, noise, mismatch, adaptation, reset, readout or extraction."}
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("event_count", "ideal_event_sum_v", "physical_final_minus_reference_v", "relative_error_by_order", "max_order_spread_v")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
