"""Bounded SKY130 OTA closed-loop gain/linearity sweep on differential inputs."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

HEADER = r"""* SKY130 TT closed-loop OTA differential gain screen
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    deltas = (0.0, 64e-6, -64e-6, 250e-6, -250e-6, 500e-6, -500e-6)
    gains = (10, 30, 100, 300)
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / "sky130_sc_ota_closedloop_gain.cir"
    devices: list[str] = []
    outputs: list[str] = []
    mapping: list[tuple[int, float, int]] = []
    index = 0
    for gain in gains:
        rg = 10_000.0
        rf = rg * (gain - 1)
        for delta in deltas:
            name = f"d{index}"
            devices += [
                f"Vbn_{name} vbnn_{name} 0 0.65",
                f"Vbp_{name} vbpp_{name} 0 0.75",
                f"Vsignal_{name} signal_{name} 0 {0.9 + delta:.9f}",
                f"Rgain_{name} vcm inp_{name} {rg:g}",
                f"Rfeedback_{name} out_{name} inp_{name} {rf:g}",
                f"Rload_{name} out_{name} vcm 1Meg",
                f"Xota_{name} inp_{name} signal_{name} out_{name} vbnn_{name} vbpp_{name} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
            ]
            outputs.append(f"v(out_{name})")
            mapping.append((index, delta, gain))
            index += 1
    deck.write_text(HEADER + "\n".join(devices) + "\n.control\nop\nprint " + " ".join(outputs) + "\nquit\n.endc\n.end\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "30", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=40)
    log = run.stdout + run.stderr
    (RES / "sky130_sc_ota_closedloop_gain.log").write_text(log, encoding="utf-8")
    parsed = {int(i): float(v) for i, v in re.findall(r"v\(out_d(\d+)\)\s*=\s*([+\-0-9.eE]+)", log)}
    grouped: dict[int, list[dict[str, float | None]]] = {gain: [] for gain in gains}
    for index, delta, gain in mapping:
        grouped[gain].append({"input_diff_v": delta, "output_v": parsed.get(index)})
    for gain, points in grouped.items():
        base = points[0]["output_v"]
        for point in points:
            out = point["output_v"]
            delta = point["input_diff_v"]
            point["output_change_from_zero_v"] = None if out is None or base is None else out - base
            point["target_closedloop_change_v"] = gain * delta
            point["gain_error_v"] = None if out is None or base is None else (out - base) - gain * delta
    report = {
        "test": "sky130_tt_ota_closedloop_differential_gain_screen",
        "simulation_completed": run.returncode == 0 and len(parsed) == len(mapping),
        "return_code": run.returncode,
        "scope": "nominal TT schematic only; 0.9V reference; OTA 10/20/4um input and 2/27.8um second stage; ideal resistor feedback; 1Meg output load; no noise, mismatch, PVT or physical resistor geometry",
        "feedback_gain_sweeps": grouped,
    }
    (RES / "sky130_sc_ota_closedloop_gain.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
