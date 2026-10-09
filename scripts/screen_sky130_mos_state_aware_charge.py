"""Isolate MOS state-store C(V) error under ideal float-aware charge commands.

The voltage/charge controller and current source in this screen are ideal. This
does not implement a physical state sensor, injector, PLIF or full chip.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import math
import random
import re
import subprocess
from pathlib import Path

import numpy as np

from screen_sky130_mos_state_cap import BENCH, OUT, RESULTS, ROOT

REF = OUT / "model_reference"
CHECKPOINT = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
EXPECTED_SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
LEVELS = (0.15, 0.30, 0.45, 0.60, 0.75, 0.90, 1.05, 1.20, 1.35, 1.50, 1.65)
PROBE_Q = 0.5e-15
PREFIXES = (1, 10, 40, 100, 200, 300)

HEADER = """Physical MOS gate state, ideal event-charge command
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 rm4=0.047 rcvia4=0.38 tc1rvia4=0 tc2rvia4=0
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/modules.spice"
Vdd vdd 0 1.8
Vprogram src 0 0.9
Von on 0 PWL(0 1.8 1u 1.8 1.001u 0 5.01m 0)
Voff off 0 PWL(0 0 1u 0 1.001u 1.8 5.01m 1.8)
Xsw src state on off vdd 0 transmission_gate
Xswref src ref on off vdd 0 transmission_gate
"""


def run(tag: str, deck: str, limit_s: int = 120) -> tuple[str, int]:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (BENCH / f"{tag}.cir").write_text(deck, encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
           str(limit_s), "ngspice", "-b", f"{tag}.cir"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=limit_s + 30)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
    return log, proc.returncode


def mos_pair() -> str:
    return "\n".join(f"Xcap_{node}_{i} 0 {node} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1"
                     for node in ("state", "ref") for i in range(10))


def values(log: str) -> dict[str, float]:
    return {key.lower(): float(number) for key, number in re.findall(
        r"^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}


def calibrate() -> list[dict]:
    rows = []
    for index, level in enumerate(LEVELS):
        tag = f"sky130_mos_charge_cv_{index:02d}"
        current = PROBE_Q / 0.2e-6
        deck = (HEADER.replace("Vprogram src 0 0.9", f"Vprogram src 0 {level}") +
                mos_pair() + "\n" +
                f"Ievent 0 state PWL(0 0 2u 0 2.001u {current:.12g} 2.201u {current:.12g} 2.202u 0 3u 0)\n" +
                ".control\ntran 2n 3u 0 2n\n" +
                "meas tran before find v(state) at=1.9u\n" +
                "meas tran after find v(state) at=2.3u\n" +
                "meas tran ref_before find v(ref) at=1.9u\n" +
                "meas tran ref_after find v(ref) at=2.3u\nquit\n.endc\n.end\n")
        log, code = run(tag, deck)
        v = values(log)
        good = code == 0 and all(key in v for key in ("before", "after", "ref_before", "ref_after"))
        delta = (v["after"] - v["before"] - v["ref_after"] + v["ref_before"]) if good else None
        rows.append({"program_v": level, "measured_start_v": v.get("ref_before"),
                     "event_delta_v": delta, "effective_capacitance_f": PROBE_Q / delta if delta and delta > 0 else None,
                     "completed": bool(good and delta and delta > 0), "deck": f"{tag}.cir"})
    if not all(row["completed"] for row in rows):
        raise RuntimeError("MOS C(V) probe failed; inspect saved logs")
    return rows


def float_events(site: str) -> tuple[list[float], dict]:
    demand = json.loads((RESULTS / "sky130_piecewise_actual_event_range_three_sites.json").read_text(encoding="utf-8"))
    source_name = demand["sites"][site]["source_deck"].replace(".cir", "_deck.json")
    source = json.loads((RESULTS / source_name).read_text(encoding="utf-8"))
    trace = json.loads((REF / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    if (source["checkpoint_sha256"] != EXPECTED_SHA or trace["checkpoint_sha256"] != EXPECTED_SHA
            or source["qat_or_quantized_reference_used"] or trace["qat_or_quantized_reference_used"]):
        raise RuntimeError("float source/checkpoint mismatch")
    arrays = np.load(REF / "float_patch_trace_all.npz")
    weights = np.load(REF / "eventspikeseg140k_float_parameters.npz")["weight__final_fuse__standard"]
    presyn = arrays["presynaptic_input__final_fuse__standard"]
    batch, output = source["selected_flat_batch"], source["selected_output_channel"]
    y, x = source["selected_yx"]
    event_weights = []
    for ic in range(weights.shape[1]):
        for ky in range(weights.shape[2]):
            for kx in range(weights.shape[3]):
                iy, ix = y + ky - 1, x + kx - 1
                if 0 <= iy < presyn.shape[-2] and 0 <= ix < presyn.shape[-1]:
                    event_weights.extend([float(weights[output, ic, ky, kx])] * int(presyn[batch, ic, iy, ix]))
    if len(event_weights) != source["event_count"] or abs(sum(event_weights) - source["sum_folded_float_event_weights"]) > 1e-4:
        raise RuntimeError("float event reconstruction mismatch")
    ordered = sorted(event_weights, key=lambda value: (value > 0, abs(value)))
    random.Random(140).shuffle(ordered)
    return ordered, source


def main() -> int:
    if hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest() != EXPECTED_SHA:
        raise RuntimeError("original full-float checkpoint hash differs")
    calibration = calibrate()
    xs = [row["measured_start_v"] for row in calibration]
    cs = [row["effective_capacitance_f"] for row in calibration]
    if any(left >= right for left, right in zip(xs, xs[1:])):
        raise RuntimeError("MOS program map is not monotone")
    def cap(v: float) -> float:
        return float(np.interp(v, xs, cs))
    def charge_between(a: float, b: float) -> float:
        if b < a:
            return -charge_between(b, a)
        points = [a] + [x for x in xs if a < x < b] + [b]
        return sum((cap(left) + cap(right)) * (right - left) / 2
                   for left, right in zip(points, points[1:]))
    state_ref = json.loads((RESULTS / "sky130_float_state_saturation_validation_0_all_neurons_full_none_g5000-10000_asinh_ideal.json").read_text(encoding="utf-8"))
    maximum = state_ref["actor_max_absolute_candidate_model_units"]["final_fuse.standard"]
    knots_m = [maximum / 10000 * math.sinh(math.asinh(10000) * i / 8) for i in range(9)]
    def encode(m: float) -> float:
        magnitude = min(abs(m), maximum)
        i = min(bisect.bisect_right(knots_m, magnitude) - 1, 7)
        return 0.9 + math.copysign(0.1125 * (i + (magnitude - knots_m[i]) /
                                              (knots_m[i + 1] - knots_m[i])), m)
    cases = []
    for site in ("high_cancellation", "max_fanin"):
        events, source = float_events(site)
        slot = 55e-9
        width = 10e-9
        first = 2e-6
        model_state = 0.0
        targets = []
        pulses = [(0, 0), (first - 1e-9, 0)]
        for i, weight in enumerate(events):
            before = encode(model_state)
            model_state += weight
            after = encode(model_state)
            q = charge_between(before, after)
            current = q / width
            t = first + i * slot
            pulses.extend(((t, 0), (t + 0.1e-9, current),
                           (t + width + 0.1e-9, current), (t + width + 0.2e-9, 0)))
            targets.append({"event": i + 1, "target_v": after, "ideal_charge_c": q})
        final_t = first + len(events) * slot + 0.5e-6
        pulses.append((final_t, 0))
        tag = f"sky130_mos_state_aware_ideal_charge_{site}"
        deck = HEADER + mos_pair() + "\n" + "Ievent 0 state PWL(" + " ".join(
            f"{t:.12g} {current:.12g}" for t, current in pulses) + ")\n"
        checkpoints = sorted(set(p for p in PREFIXES if p <= len(events)) | {len(events)})
        deck += ".control\n" + f"tran 2n {final_t:.12g} 0 2n\n"
        for p in checkpoints:
            t = first + (p - 1) * slot + width + 5e-9
            deck += f"meas tran state_{p} find v(state) at={t:.12g}\n"
            deck += f"meas tran ref_{p} find v(ref) at={t:.12g}\n"
        deck += "quit\n.endc\n.end\n"
        log, code = run(tag, deck, 180)
        found = values(log)
        prefixes = []
        for p in checkpoints:
            measured = (found.get(f"state_{p}", float("nan")) - found.get(f"ref_{p}", float("nan")))
            target = targets[p - 1]["target_v"] - 0.9
            prefixes.append({"events": p, "ideal_delta_v": target, "physical_minus_reference_v": measured,
                             "error_v": measured - target})
        cases.append({"site": site, "event_count": len(events), "float_sum_model_units": model_state,
                      "total_event_window_us": len(events) * slot * 1e6,
                      "maximum_ideal_current_a": max(abs(q["ideal_charge_c"]) / width for q in targets),
                      "maximum_ideal_charge_c": max(abs(q["ideal_charge_c"]) for q in targets),
                      "simulation_completed": code == 0 and all(math.isfinite(row["error_v"]) for row in prefixes),
                      "prefixes": prefixes, "deck": f"{tag}.cir"})
    report = {"test": "sky130_mos_state_store_ideal_state_aware_charge_screen",
              "checkpoint_sha256": EXPECTED_SHA, "qat_or_quantized_reference_used": False,
              "calibration": calibration, "cases": cases,
              "all_simulations_completed": all(row["simulation_completed"] for row in cases),
              "physical_state_sensor_implemented": False, "physical_charge_source_implemented": False,
              "full_analog_architecture_ready": False,
              "scope": "TT/27C 100um2 MOS gate state bank plus physical 1.8V sampling TG. An ideal externally calculated signed charge pulse uses original full-float shuffled fan-in and an 8-range nonlinear state map, with Q(V) integrated from a separately simulated eleven-point MOS C(V) probe. 55ns slots and 10ns ideal pulses. Reference branch subtracts shared programming/hold drift, which is not a physical correction circuit. No physical state sensor, charge driver, threshold, beta, reset, noise, mismatch, extracted layout, or population-service qualification."}
    path = RESULTS / "sky130_mos_state_aware_ideal_charge_boundary.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_simulations_completed": report["all_simulations_completed"],
                      "cases": cases, "calibration": calibration}, indent=2))
    return 0 if report["all_simulations_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
