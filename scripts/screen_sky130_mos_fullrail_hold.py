"""Bounded SKY130 MOS-gate/TG 5ms hold map over the candidate 0-1.8V rail."""
from __future__ import annotations

import json
import re
import subprocess

from screen_sky130_mos_decay_prediction import deck
from screen_sky130_mos_state_cap import BENCH, OUT, RESULTS, ROOT

BIASES = (0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9,
          1.05, 1.2, 1.35, 1.5, 1.65, 1.8)


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for bias in BIASES:
        tag = f"sky130_mos_fullrail_hold_{str(bias).replace('.', 'p')}v"
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
        rows.append({"program_v": bias,
                     "simulation_completed": proc.returncode == 0 and len(values) == 5,
                     "exit_code": proc.returncode,
                     "measured_v": values,
                     "program_error_v": values["start"] - bias if "start" in values else None,
                     "hold_drift_v": values["five_ms"] - values["start"]
                     if "start" in values and "five_ms" in values else None,
                     "failure_hint": next((line for line in log.splitlines()
                                           if "error" in line.lower() or "undefined" in line.lower()), None)})
    completed = all(row["simulation_completed"] for row in rows)
    starts = [row["measured_v"].get("start") for row in rows]
    monotonic = completed and all(left < right for left, right in zip(starts, starts[1:]))
    report = {
        "scope": "SKY130 TT nominal 100um2 drawn MOS gate bank programmed through physical 1.8V TG for 1us, isolated for 5ms, ideal voltage observation at five times. Thirteen 0-1.8V programmed levels. No injected events, noise, mismatch, PVT, extraction or layout. Endpoint programming errors must be kept distinct from hold drift.",
        "all_simulations_completed": completed,
        "measured_start_voltages_strictly_increasing": monotonic,
        "rows": rows,
    }
    (RESULTS / "sky130_mos_fullrail_hold_boundary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_simulations_completed": completed,
                      "measured_start_voltages_strictly_increasing": monotonic,
                      "rows": [{"program_v": row["program_v"], "program_error_v": row["program_error_v"],
                                "hold_drift_v": row["hold_drift_v"],
                                "simulation_completed": row["simulation_completed"]} for row in rows]}, indent=2))
    return 0 if completed and monotonic else 2


if __name__ == "__main__":
    raise SystemExit(main())
