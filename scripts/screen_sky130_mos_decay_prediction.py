"""Check whether two-point MOS state-leak calibration predicts held voltages."""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

from screen_sky130_mos_state_cap import BENCH, HEADER, OUT, RESULTS, ROOT

VCM = 0.9
BIASES = (0.6, 0.75, 0.9, 1.05, 1.2)
TIMES = {"start": 2e-6, "half_ms": 0.5e-3, "one_ms": 1e-3,
         "two_half_ms": 2.5e-3, "five_ms": 5e-3}


def deck(bias: float) -> str:
    lines = [HEADER, f"Vprogram src 0 {bias}",
             "Von on 0 PWL(0 1.8 1u 1.8 1.001u 0 5.01m 0)",
             "Voff off 0 PWL(0 0 1u 0 1.001u 1.8 5.01m 1.8)",
             "Xsw src state on off vdd 0 transmission_gate"]
    for finger in range(10):
        lines.append(f"Xcap{finger} 0 state 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1")
    lines.extend([".control", "tran 1u 5.01m 0 1u"])
    for name, time_s in TIMES.items():
        lines.append(f"meas tran {name} find v(state) at={time_s}")
    lines.extend(["quit", ".endc", ".end"])
    return "\n".join(lines) + "\n"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for bias in BIASES:
        tag = f"sky130_mos_decay_{str(bias).replace('.', 'p')}v"
        (BENCH / f"{tag}.cir").write_text(deck(bias), encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro",
               "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
               "--workdir", "/workspace/artifacts/analog_asic/benches",
               "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
               "120", "ngspice", "-b", f"{tag}.cir"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        log = proc.stdout + proc.stderr
        (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
        values = {name.lower(): float(value) for name, value in re.findall(
            r"^(start|half_ms|one_ms|two_half_ms|five_ms)\s*=\s*([-+0-9.eE]+)",
            log, re.I | re.M)}
        rows.append({"program_v": bias, "simulation_completed": proc.returncode == 0 and
                     set(values) == set(TIMES), "exit_code": proc.returncode,
                     "measured_v": values})
    if not all(row["simulation_completed"] for row in rows):
        raise RuntimeError("incomplete MOS state hold screen")
    by_bias = {row["program_v"]: row for row in rows}
    tau_by_sign = {}
    for bias in (0.6, 1.2):
        values = by_bias[bias]["measured_v"]
        fraction = ((values["five_ms"] - VCM) / (values["start"] - VCM))
        tau_by_sign["below" if bias < VCM else "above"] = (
            -(TIMES["five_ms"] - TIMES["start"]) / math.log(fraction))
    for row in rows:
        bias = row["program_v"]
        if bias == VCM:
            continue
        tau = tau_by_sign["below" if bias < VCM else "above"]
        start = row["measured_v"]["start"]
        row["two_endpoint_single_pole_prediction_errors_uv"] = {
            name: (row["measured_v"][name] -
                   (VCM + (start - VCM) * math.exp(-(time_s - TIMES["start"]) / tau))) * 1e6
            for name, time_s in TIMES.items() if name != "start"
        }
    report = {
        "scope": "SKY130 TT physical TG plus 100um2 drawn MOS gate bank, ideal voltage observations only. Single-pole tau fit at 0.6/1.2V using 2us and 5ms, then reused at 0.75/1.05V. Not a physical sense/compensation circuit; no noise/PVT/mismatch or injected events.",
        "all_simulations_completed": True,
        "time_points_s": TIMES,
        "endpoint_fitted_tau_s": tau_by_sign,
        "rows": rows,
    }
    (RESULTS / "sky130_mos_decay_prediction_boundary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
