#!/usr/bin/env python3
"""Measure range-comparator delay at analog event-scale state slews."""
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
    temp = float(sys.argv[2]) if len(sys.argv) > 2 else {"tt": 27, "ss": 0, "ff": 85}.get(corner, 27)
    trim_uv = float(sys.argv[3]) if len(sys.argv) > 3 else 1970.0
    step_uv = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
    size = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    vbias = float(sys.argv[6]) if len(sys.argv) > 6 else 0.7
    if corner not in {"tt", "ss", "ff"} or step_uv <= 0:
        raise ValueError("corner must be tt, ss or ff; step_uv must be positive")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    threshold = 1.05
    # The measured large-event ramp is about 6 uV/ns; scale duration to the
    # selected analog step, then hold to test whether the comparator resolves.
    ramp_ns = step_uv / 6.0
    t0_us = 1.0
    t1_us = t0_us + ramp_ns * 1e-3
    stop_us = 1.5
    start_v, end_v = threshold - step_uv * 0.5e-6, threshold + step_uv * 0.5e-6
    common = COMMON.replace("__tt.corner.spice", f"__{corner}.corner.spice")
    reference = threshold + trim_uv * 1e-6
    lines = [f"SKY130 {corner.upper()} range comparator {step_uv:g}uV event slew",
             common, f".temp {temp:g}", "Vdd vdd 0 1.8", f"Vbias vbias 0 {vbias:g}",
             f"Vref ref 0 {reference:.12g}",
             f"Vstate state 0 PWL(0 {start_v:.12g} {t0_us-0.0001:g}u {start_v:.12g} {t0_us:g}u {start_v:.12g} {t1_us:.12g}u {end_v:.12g} {stop_us:g}u {end_v:.12g})",
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
             "Cload range_out 0 30f", ".control", "set numdgt=15",
             ".ic v(range_out)=0", "tran 20p 1.5u uic",
             "meas tran target_cross when v(state)=1.05 rise=1",
             "meas tran comparator_cross when v(range_out)=0.9 rise=2",
             "meas tran state_at_comparator find v(state) when v(range_out)=0.9 rise=2",
             f"meas tran output_at_42ns find v(range_out) at={t1_us+0.042:g}u",
             f"meas tran output_at_100ns find v(range_out) at={t1_us+0.1:g}u",
             "quit", ".endc", ".end", ""]
    stem = f"sky130_piecewise_comparator_slew_{corner}_temp{temp:g}_trim{trim_uv:g}uv_step{step_uv:g}uv_size{size:g}x_vbias{vbias:g}"
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
        r"(?im)^\s*(target_cross|comparator_cross|state_at_comparator|output_at_42ns|output_at_100ns)\s*=\s*([-+0-9.eE]+)", log)}
    required = {"target_cross", "output_at_42ns", "output_at_100ns"}
    complete = run.returncode == 0 and "ngspice-36 done" in log and required <= values.keys()
    report = {"test": "sky130_piecewise_comparator_analog_event_slew",
              "simulation_completed": complete, "corner": corner.upper(), "temperature_c": temp,
              "target_boundary_v": threshold, "comparator_reference_v": reference,
              "reference_trim_uv": trim_uv, "event_step_uv": step_uv,
              "transistor_width_scale": size,
              "tail_bias_v": vbias,
              "assumed_state_slew_uv_per_ns": 6.0, "ramp_duration_ns": ramp_ns,
              "output_load_ff": 30, "measurements": values,
              "scope": "Ideal state-voltage ramp into the schematic PDK comparator; no state-cap/injector, physical trim, PEX or noise. Output is held for at least100ns after the ramp."}
    if complete:
        if "comparator_cross" in values:
            report["comparator_latency_after_target_ns"] = (values["comparator_cross"]-values["target_cross"])*1e9
            report["comparator_state_error_uv"] = (values["state_at_comparator"]-threshold)*1e6
        else:
            report["comparator_output_crossed"] = False
        report["resolved_within_42ns"] = values["output_at_42ns"] >= 0.9
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
