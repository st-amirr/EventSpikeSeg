#!/usr/bin/env python3
"""Bounded PDK transient for one continuous range-boundary comparator."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from test_sky130_sc_physical_accumulation import BENCH, RES, ROOT

IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    threshold = 1.05  # VCM + 150mV, first positive six-range boundary.
    ramp_start, ramp_end = 1.0e-6, 1.02e-6
    lines = ["SKY130 TT continuous range comparator dynamic response",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9", ".temp 27",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
             '.include "../../../asic/analog/modules.spice"',
             "Vdd vdd 0 1.8", "Vbias vbias 0 0.7", f"Vref ref 0 {threshold:g}",
             f"Vstate state 0 PWL(0 1.0 {ramp_start*1e6-0.1:g}u 1.0 {ramp_start*1e6:g}u 1.0 {ramp_end*1e6:g}u 1.1 1.5u 1.1)",
             "Xrange state ref range_out vbias vdd 0 comparator", "Cload range_out 0 30f",
             ".control", "set numdgt=15", "tran 20p 1.5u uic",
             "meas tran output_low find v(range_out) at=0.9u",
             "meas tran output_high find v(range_out) at=1.1u",
             "meas tran crossing_time when v(range_out)=0.9 rise=2",
             "quit", ".endc", ".end", ""]
    stem = "sky130_piecewise_range_comparator_tt"
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
    values = {key: float(value) for key, value in re.findall(
        r"(?im)^\s*(output_low|output_high|crossing_time)\s*=\s*([-+0-9.eE]+)", log)}
    complete = (run.returncode == 0 and "ngspice-36 done" in log and
                all(key in values for key in ("output_low", "output_high", "crossing_time")))
    report = {"test": "sky130_single_six_range_boundary_comparator_tt_transient",
              "simulation_completed": complete, "corner": "TT", "temperature_c": 27,
              "threshold_v": threshold, "state_input_ramp_v": [1.0, 1.1],
              "state_input_ramp_duration_ns": (ramp_end-ramp_start)*1e9,
              "output_load_ff": 30, "measurements": values,
              "scope": "One schematic transistor-level SKY130 comparator loaded by30fF, ideal state ramp across the first positive six-range threshold at0.9V common mode. No comparator layout/PEX, mismatch/noise/PVT, complete one-hot range decoder, injector switching, or coupled membrane test."}
    if complete:
        report["comparator_delay_from_ideal_threshold_ns"] = (
            values["crossing_time"] - (ramp_start + (threshold-1.0)/0.1*(ramp_end-ramp_start)))*1e9
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
