#!/usr/bin/env python3
"""Measure the static trip point of the PDK piecewise-range comparator."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import BENCH, COMMON, RES, ROOT

IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    corner = sys.argv[1].lower() if len(sys.argv) > 1 else "tt"
    temperature = float(sys.argv[2]) if len(sys.argv) > 2 else {"tt": 27, "ss": 0, "ff": 85}.get(corner, 27)
    trim_uv = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    size = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    vbias = float(sys.argv[5]) if len(sys.argv) > 5 else 0.7
    if corner not in {"tt", "ss", "ff"}:
        raise ValueError("corner must be tt, ss or ff")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    common = COMMON.replace("__tt.corner.spice", f"__{corner}.corner.spice")
    threshold = 1.05
    ref = threshold + trim_uv * 1e-6
    lines = [f"SKY130 {corner.upper()} piecewise comparator DC transfer",
             common, f".temp {temperature:g}", "Vdd vdd 0 1.8", f"Vbias vbias 0 {vbias:g}",
             f"Vstate state 0 {threshold:g}", f"Vref ref 0 {ref:.12g}",
             ".subckt range_compare inp inn output vbias vdd vss",
             f"Xip d1 inp tail vss sky130_fd_pr__nfet_01v8 w={10*size:g} l=0.5",
             f"Xin d2 inn tail vss sky130_fd_pr__nfet_01v8 w={10*size:g} l=0.5",
             f"Xtail tail vbias vss vss sky130_fd_pr__nfet_01v8 w={5*size:g} l=1",
             f"Xload1 d1 d1 vdd vdd sky130_fd_pr__pfet_01v8 w={20*size:g} l=0.5",
             f"Xload2 d2 d1 vdd vdd sky130_fd_pr__pfet_01v8 w={20*size:g} l=0.5",
             "Xb1p invnode d2 vdd vdd sky130_fd_pr__pfet_01v8 w=10 l=0.5",
             "Xb1n invnode d2 vss vss sky130_fd_pr__nfet_01v8 w=5 l=0.5",
             "Xb2p output invnode vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
             "Xb2n output invnode vss vss sky130_fd_pr__nfet_01v8 w=10 l=0.5",
             ".ends range_compare", "Xrange state ref range_out vbias vdd 0 range_compare",
             ".control", "set numdgt=15", "dc Vstate 1.045 1.055 1u",
             "meas dc trip_state when v(range_out)=0.9 rise=1",
             "meas dc output_low find v(range_out) at=1.045",
             "meas dc output_high find v(range_out) at=1.054", "quit", ".endc", ".end", ""]
    stem = f"sky130_piecewise_comparator_dc_{corner}_temp{temperature:g}_trim{trim_uv:g}uv_size{size:g}x_vbias{vbias:g}"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume",
           f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           IMAGE, "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {k: float(v) for k, v in re.findall(
        r"(?im)^\s*(trip_state|output_low|output_high)\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and "ngspice-36 done" in log and set(values) == {
        "trip_state", "output_low", "output_high"}
    report = {"test": "sky130_piecewise_range_comparator_static_trip",
              "simulation_completed": complete, "corner": corner.upper(),
              "temperature_c": temperature, "target_boundary_v": threshold,
              "comparator_reference_v": ref, "reference_trim_uv": trim_uv,
              "transistor_width_scale": size,
              "tail_bias_v": vbias,
              "state_sweep_v": [1.045, 1.055], "state_step_v": 1e-6,
              "measurements": values,
              "scope": "Static DC transfer of the schematic PDK comparator used by the two-range event bench. No startup, MIM/TG input load, PEX, mismatch/noise, event injector or physical trim implementation."}
    if complete:
        report["static_trip_error_vs_target_uv"] = (values["trip_state"] - threshold) * 1e6
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
