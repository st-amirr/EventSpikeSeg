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
    per_synapse_devices = "--per-synapse-devices" in sys.argv[1:]
    isolate_inactive_synapses = "--isolate-inactive-synapses" in sys.argv[1:]
    isolation_precharge = "--isolation-precharge" in sys.argv[1:]
    isolation_switch_scale = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                         if arg.startswith("--isolation-switch-scale=")), "1"))
    event_width_scale = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                    if arg.startswith("--event-width-scale=")), "1"))
    map_width_override = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                               if arg.startswith("--transfer-map-width-ns=")), None)
    event_period_override = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                  if arg.startswith("--event-period-ns=")), None)
    banked_transfer_map = "--banked-transfer-map" in sys.argv[1:]
    variable_pulse_floor = "--variable-pulse-floor" in sys.argv[1:]
    piecewise_first_range = "--piecewise-first-range" in sys.argv[1:]
    ideal_state_polarity_correction = "--ideal-state-polarity-correction" in sys.argv[1:]
    event_limit = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                            if arg.startswith("--event-limit=")), "0"))
    if mapping not in ("short_linear", "stage_linear", "stage_log", "stage_discrete_geometry",
                       "stage_continuous_geometry"):
        raise ValueError("unknown mapping")
    stem = BASE.replace("ss0", f"{corner}{temperature_c}")
    if map_corner != corner:
        stem += f"_map{map_corner}"
    if site != "max_fanin":
        stem += f"_{site}"
    if mapping != "short_linear":
        stem += f"_{mapping}"
    if map_width_override:
        stem += f"_mapw{float(map_width_override):g}n".replace(".", "p")
    if banked_transfer_map:
        stem += "_bankedmap"
    if variable_pulse_floor:
        stem += "_durationfloor"
    if piecewise_first_range:
        stem += "_piecewise1"
    if ideal_state_polarity_correction:
        stem += "_statebiasideal"
    if per_synapse_devices:
        stem += "_per_synapse"
    if isolate_inactive_synapses:
        stem += "_isolated"
        if isolation_precharge:
            stem += "_precharge"
        if isolation_switch_scale != 1:
            stem += f"_sw{isolation_switch_scale:g}".replace(".", "p")
    if event_width_scale != 1:
        stem += f"_wscale{event_width_scale:g}".replace(".", "p")
    map_width = float(map_width_override) if map_width_override else 40.2530474317
    event_period = float(event_period_override) if event_period_override else map_width + 10.0
    if abs(event_period - (map_width + 10.0)) > 0.001:
        stem += f"_slot{event_period:g}n".replace(".", "p")
    if event_limit:
        stem += f"_n{event_limit}events"
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
              "interpretation": (f"Actual float signed weights and activation multiplicities are mapped to the nearest of104 measured SS/0C event-charge levels (13 geometries by eight shared biases) at the fixed40.253ns stage pulse. The measured TT/27C R-2R event gain ratios are applied as effective gate-fraction shifts, assuming independence from MOS geometry and process corner; the full fan-in deck does not contain the R-2R ladder itself. Device topology: {deck.get('device_architecture')}. Physical MOS/TG/MIM devices accumulate the signed sequence. This is one event ordering at one site; no mismatch/noise, adaptation, reset, readout or extraction."
                              if mapping == "stage_discrete_geometry" else
                              "Actual float signed weights and activation multiplicities at one saved final-fusion site produce a physical signed sum. Reordering the identical events changes the final state. Gate voltages are inferred from a sparse single-event charge curve; interpolation error and accumulation state dependence remain separable only by further calibration. Ideal gate controls, no physical DAC/calibration, noise, mismatch, adaptation, reset, readout or extraction.")}
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("event_count", "ideal_event_sum_v", "physical_final_minus_reference_v", "relative_error_by_order", "max_order_spread_v")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
