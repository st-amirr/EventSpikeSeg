"""Bounded physical MOS state TG hold at selected SKY130 process/temperature points."""
from __future__ import annotations

import json
import re
import subprocess

from screen_sky130_mos_decay_prediction import deck
from screen_sky130_mos_state_cap import BENCH, OUT, RESULTS, ROOT

CORNERS = (("ss", 0), ("tt", 27), ("ff", 85))
BIASES = (0.15, 0.9, 1.65)


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for corner, temperature_c in CORNERS:
        for bias in BIASES:
            tag = f"sky130_mos_pvt_hold_{corner}_temp{temperature_c}_{str(bias).replace('.', 'p')}v"
            text = deck(bias).replace("__tt.corner.spice", f"__{corner}.corner.spice")
            text = text.replace("Vdd vdd 0 1.8", f".temp {temperature_c}\nVdd vdd 0 1.8")
            (BENCH / f"{tag}.cir").write_text(text, encoding="utf-8")
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
            rows.append({"mos_corner": corner, "temperature_c": temperature_c,
                         "program_v": bias,
                         "simulation_completed": proc.returncode == 0 and len(values) == 5,
                         "exit_code": proc.returncode,
                         "program_error_v": values["start"] - bias if "start" in values else None,
                         "hold_drift_v": values["five_ms"] - values["start"]
                         if "start" in values and "five_ms" in values else None,
                         "measurements_v": values,
                         "failure_hint": next((line for line in log.splitlines()
                                               if "error" in line.lower() or "undefined" in line.lower()), None)})
    report = {
        "scope": "SKY130 nominal process corners SS/0C, TT/27C, FF/85C, physical 1.8V TG programming a 100um2 drawn MOS-gate bank for 1us then holding to 5ms at 0.15/0.9/1.65V. These are three process/temperature combinations, not all nine crossed points or mismatch/noise/extraction/layout.",
        "all_simulations_completed": all(row["simulation_completed"] for row in rows),
        "results": rows,
    }
    (RESULTS / "sky130_mos_pvt_hold_boundary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"all_simulations_completed": report["all_simulations_completed"],
                      "rows": [{"mos_corner": row["mos_corner"],
                                "temperature_c": row["temperature_c"],
                                "program_v": row["program_v"],
                                "program_error_v": row["program_error_v"],
                                "hold_drift_v": row["hold_drift_v"],
                                "simulation_completed": row["simulation_completed"]}
                               for row in rows]}, indent=2))
    return 0 if report["all_simulations_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
