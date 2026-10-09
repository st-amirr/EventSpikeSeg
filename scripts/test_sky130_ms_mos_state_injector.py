"""Replay selected original-float fan-in through the SKY130 MOS state cell.

Supports the matched-load transfer map, ideal state correction, measured-map
open-loop correction, and an explicit behavioral gate-bias source that reads
the simulated membrane differential. None of these behavioral controls is a
transistor-level sensor or calibrated physical bias generator.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
RES = OUT / "results"
EXPORTER = ROOT / "scripts/export_sky130_ms_first_touch_float_fanin.py"
EXPECTED_SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def main() -> int:
    site = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                 if arg.startswith("--site=")), "high_cancellation")
    if site not in ("max_fanin", "high_cancellation", "near_threshold_scale"):
        raise ValueError(f"unsupported trace site: {site}")
    orders = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                   if arg.startswith("--orders=")), "all")
    if orders not in ("all", "forward", "reverse", "shuffle"):
        raise ValueError(f"unsupported event order set: {orders}")
    extracted_layout_bank = "--extracted-layout-bank" in sys.argv[1:]
    full_range_linear = "--full-range-linear" in sys.argv[1:]
    export_args = [
        sys.executable, str(EXPORTER), "--corner=ss", "--map-corner=ss",
        f"--site={site}", f"--orders={orders}",
        "--mapping=stage_continuous_geometry", "--banked-transfer-map",
        *( [] if full_range_linear else ["--piecewise-first-range"] ),
        "--transfer-map-width-ns=4400" if extracted_layout_bank else "--transfer-map-width-ns=42.2657",
        "--event-period-ns=5000" if extracted_layout_bank else "--event-period-ns=55",
        "--prefix-measure-step=40",
        "--mos-layout-state-cap" if extracted_layout_bank else "--mos-state-cap",
    ] + [arg for arg in sys.argv[1:] if not arg.startswith("--site=")
         and not arg.startswith("--orders=") and arg != "--full-range-linear"]
    exported = subprocess.run(export_args, cwd=ROOT, capture_output=True, text=True, timeout=60)
    if exported.returncode:
        raise RuntimeError(f"SPICE export failed: {exported.stdout}\n{exported.stderr}")
    meta = json.loads(exported.stdout)
    expected_period = 5000.0 if extracted_layout_bank else 55.0
    if (meta["checkpoint_sha256"] != EXPECTED_SHA or meta["qat_or_quantized_reference_used"]
            or meta["event_count"] <= 0 or meta["period_ns"] != expected_period
            or (not extracted_layout_bank and meta["state_cap_architecture"].startswith("two 10um"))):
        raise RuntimeError("unexpected float trace or state-cap configuration")
    deck = meta["deck"]
    command = [
        "docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
        "--volume", f"{ROOT}:/workspace:ro",
        "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
        "--workdir", "/workspace/artifacts/analog_asic/benches",
        "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
        "600", "ngspice", "-b", deck,
    ]
    simulated = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=630)
    log = simulated.stdout + simulated.stderr
    log_path = RES / (Path(deck).stem + ".log")
    log_path.write_text(log, encoding="utf-8")
    measured = {name.lower(): float(value) for name, value in re.findall(
        r"^(prefix_(?:ref|forward|reverse|shuffle)_\d+|final_(?:ref|forward|reverse|shuffle))\s*=\s*([-+0-9.eE]+)",
        log, re.I | re.M)}
    counts = [int(value) for value in meta["prefix_measure_counts"]]
    prefixes = []
    by_order = {}
    for order, expected_map in meta["ideal_prefix_sums_v_by_order"].items():
        order_prefixes = []
        for count in counts:
            keys = (f"prefix_ref_{count}", f"prefix_{order}_{count}")
            if any(key not in measured for key in keys) or str(count) not in expected_map:
                continue
            actual = measured[keys[1]] - measured[keys[0]]
            target = float(expected_map[str(count)])
            order_prefixes.append({"event_count": count, "ideal_target_v": target,
                                   "physical_delta_minus_reference_v": actual,
                                   "error_v": actual - target,
                                   "sign_matches": (actual == 0 and target == 0) or actual * target > 0})
        final_key = f"final_{order}"
        final_delta = measured.get(final_key, float("nan")) - measured.get("final_ref", float("nan"))
        by_order[order] = {"physical_final_minus_reference_v": final_delta,
                           "ideal_target_final_v": meta["ideal_event_sum_v"],
                           "final_error_v": final_delta - meta["ideal_event_sum_v"],
                           "max_abs_sampled_prefix_error_v": max(
                               (abs(row["error_v"]) for row in order_prefixes), default=None),
                           "prefix_sign_mismatch_count": sum(not row["sign_matches"] for row in order_prefixes),
                           "prefixes": order_prefixes}
        prefixes.extend(order_prefixes)
    completed = (simulated.returncode == 0 and "ngspice-36 done" in log
                 and "Timestep too small" not in log and all(len(row["prefixes"]) == len(counts)
                                                              for row in by_order.values())
                 and all(f"final_{order}" in measured for order in by_order)
                 and "final_ref" in measured)
    report = {
        "test": "sky130_physical_MOS_state_cap_with_physical_signed_injector",
        "checkpoint_sha256": EXPECTED_SHA,
        "qat_or_quantized_reference_used": False,
        "export_metadata": meta,
        "simulation_completed": completed,
        "simulator_exit_code": simulated.returncode,
        "spice_log": log_path.name,
        "ideal_target_final_v": meta["ideal_event_sum_v"],
        "results_by_order": by_order,
        "behavioral_state_feedback": bool(meta.get("physical_state_feedback")),
        "behavioral_state_feedback_slope_per_v": (meta.get("state_correction_slope_per_volt")
                                                    if meta.get("physical_state_feedback") else None),
        "full_range_transition_supported": False,
        "physical_bias_ladder_instantiated": False,
        "physical_state_sensor_or_feedback_instantiated": False,
        "noise_mismatch_retention_threshold_beta_and_reset_qualified": False,
        "layout_or_population_service_qualified": False,
        "full_analog_architecture_ready": False,
        "scope": (f"SS/0C physical SKY130 shared 13-geometry signed MOS injector drives two {'extracted-layout replicated' if extracted_layout_bank else '100um2 drawn'} MOS gate-cap banks through a {meta['transfer_map_pulse_width_ns'] if 'transfer_map_pulse_width_ns' in meta else ('4400ns' if extracted_layout_bank else '42.2657ns')} transfer map. The original full-float {meta['event_count']}-event {site} fan-in is replayed in {orders} order at {meta['period_ns']:g}ns slots within the ideal first range. "
                 + ("A behavioral gate-bias source reads the instantaneous simulated membrane differential with ideal bandwidth and the recorded slope; no physical sensor or calibrated bias generator is present. "
                    if meta.get("physical_state_feedback") else "Per-event geometry and bias commands are ideal controls. ")
                 + "Measured output subtracts a matched no-event reference. Noise/mismatch, 5ms retention during the train, PLIF threshold/beta/reset, extraction, layout, and 30.976M-state service remain unqualified.")
    }
    slope_arg = next((arg for arg in sys.argv[1:] if arg.startswith("--state-correction-slope=")), None)
    suffix = f"_{site}_{orders}"
    if slope_arg and "--physical-state-feedback" not in sys.argv[1:]:
        suffix += "_statecorr_" + slope_arg.split("=", 1)[1].replace(".", "p")
    if "--measured-state-transfer-correction" in sys.argv[1:]:
        suffix += "_statecal"
    if "--physical-state-feedback" in sys.argv[1:]:
        suffix += "_statefb"
        if slope_arg:
            suffix += "_k" + slope_arg.split("=", 1)[1].replace(".", "p")
    if extracted_layout_bank:
        suffix += "_layoutbank"
    if full_range_linear:
        suffix += "_fullrange"
    if "--layout-bank-duration-map" in sys.argv[1:]:
        suffix += "_durationmap"
    if "--bidirectional-state-feedback" in sys.argv[1:]:
        suffix += "_bidirectional"
    event_limit_arg = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                            if arg.startswith("--event-limit=")), None)
    if event_limit_arg:
        suffix += f"_n{event_limit_arg}"
    timestep_arg = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                         if arg.startswith("--tran-max-step-ns=")), None)
    if timestep_arg:
        suffix += "_dt" + timestep_arg.replace(".", "p")
    (RES / f"sky130_ms_mos_state_injector_boundary{suffix}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"simulation_completed": completed, "ideal_target_final_v": meta["ideal_event_sum_v"],
                      "results_by_order": {order: {key: value for key, value in row.items()
                                                    if key != "prefixes"}
                                           for order, row in by_order.items()}}, indent=2))
    return 0 if completed else 2


if __name__ == "__main__":
    raise SystemExit(main())
