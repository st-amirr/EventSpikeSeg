#!/usr/bin/env python3
"""Bounded physical-MOS signed event-order screen on one fixed PDK MIM state."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import BENCH, COMMON, RES, ROOT


SEQUENCES = ("zz", "pz", "nz", "pp", "pn", "np", "nn")
PULSE_START = (1.0, 3.0)
PULSE_END = (2.5, 4.5)


def gate_pwl(sequence: str, sign: str, active: float, off: float) -> str:
    points = [(0.0, off)]
    for index, event in enumerate(sequence):
        if event != sign:
            continue
        start, end = PULSE_START[index], PULSE_END[index]
        points.extend(((start - 0.0001, off), (start, active),
                       (end - 0.0001, active), (end, off)))
    points.append((5.0, off))
    return "PWL(" + " ".join(f"{time:g}u {voltage:g}" for time, voltage in points) + ")"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    negative_gate_v = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4
    corner = sys.argv[2].lower() if len(sys.argv) > 2 else "tt"
    temperature = float(sys.argv[3]) if len(sys.argv) > 3 else {"tt": 27, "ss": 0, "ff": 85}[corner]
    positive_gate_v = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    if not (0.0 <= negative_gate_v <= 1.8 and 0.0 <= positive_gate_v <= 1.8):
        raise ValueError("event gates must be within the 1.8V supply")
    if corner not in {"tt", "ss", "ff"}:
        raise ValueError("corner must be tt, ss or ff")
    name = f"sky130_piecewise_signed_direct_sequence_{corner}{temperature:g}_ng{negative_gate_v:g}_pg{positive_gate_v:g}"
    common = COMMON.replace("__tt.corner.spice", f"__{corner}.corner.spice")
    lines = [f"SKY130 {corner.upper()} fixed-cap signed sequence with physical direct current devices",
             common, f".temp {temperature:g}", "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             "Vinitial initial 0 0.9",
             "Vinit init 0 PWL(0 1.8 0.1999u 1.8 0.2u 0 5u 0)",
             "Vinitb initb 0 PWL(0 0 0.1999u 0 0.2u 1.8 5u 1.8)"]
    for sequence in SEQUENCES:
        lines.extend((
            f"Xmem_{sequence} state_{sequence} vcm membrane_mim w_um=20 l_um=20",
            f"Xinit_{sequence} state_{sequence} initial init initb vdd 0 transmission_gate",
            f"Vp_{sequence} pg_{sequence} 0 {gate_pwl(sequence, 'p', positive_gate_v, 1.8)}",
            f"Vn_{sequence} ng_{sequence} 0 {gate_pwl(sequence, 'n', negative_gate_v, 0.0)}",
            f"Xp_{sequence} state_{sequence} pg_{sequence} vdd vdd sky130_fd_pr__pfet_01v8 w=4.24 l=2",
            f"Xn_{sequence} state_{sequence} ng_{sequence} 0 0 sky130_fd_pr__nfet_01v8 w=4.24 l=2",
        ))
    lines.extend((".control", "set numdgt=15", "tran 100p 5u uic"))
    for sequence in SEQUENCES:
        for label, time in (("before", 0.9), ("first", 2.7), ("second", 4.7)):
            lines.append(f"meas tran {sequence}_{label} find v(state_{sequence}) at={time:g}u")
    lines.extend(("quit", ".endc", ".end", ""))
    deck = BENCH / f"{name}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume",
           f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"{name}.log").write_text(log, encoding="utf-8")
    values = {key: float(value) for key, value in re.findall(
        r"(?im)^\s*((?:zz|pz|nz|pp|pn|np|nn)_(?:before|first|second))\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and "ngspice-36 done" in log and len(values) == 3 * len(SEQUENCES)
    report = {"test": "sky130_fixed_mim_signed_direct_event_order_screen",
              "simulation_completed": complete, "corner": corner.upper(), "temperature_c": temperature,
              "state_cap": "one PDK MIM 20x20um per sequence",
              "pulse_width_us": 1.5, "positive_gate_v": positive_gate_v, "negative_gate_v": negative_gate_v,
              "sequences": {},
              "scope": "Physical SKY130 PFET source and NFET sink, schematic MIM and initialization TG. Ideal fixed gate sources; no live range comparator, learned float weight, PEX, mismatch/noise, 5ms hold, PLIF update, or network service."}
    if complete:
        baseline = values["zz_second"] - values["zz_before"]
        for sequence in SEQUENCES:
            before, first, second = (values[f"{sequence}_{key}"] for key in ("before", "first", "second"))
            report["sequences"][sequence] = {
                "initial_v": before, "after_first_v": first, "after_second_v": second,
                "net_update_vs_no_event_mv": ((second - before) - baseline) * 1e3,
            }
        rows = report["sequences"]
        report["ideal_linear_pn_mv"] = rows["pz"]["net_update_vs_no_event_mv"] + rows["nz"]["net_update_vs_no_event_mv"]
        report["pn_order_difference_mv"] = rows["pn"]["net_update_vs_no_event_mv"] - rows["np"]["net_update_vs_no_event_mv"]
        report["pn_nonadditivity_mv"] = rows["pn"]["net_update_vs_no_event_mv"] - report["ideal_linear_pn_mv"]
        report["np_nonadditivity_mv"] = rows["np"]["net_update_vs_no_event_mv"] - report["ideal_linear_pn_mv"]
    (RES / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
