"""Sweep source-degenerated SKY130 OTA gain for high-impedance differential sensing."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

HEADER = r"""* SKY130 TT source-degenerated OTA sensitivity sweep
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""

OTA = r""".subckt sky130_sc_ota_degen inp inn out vbiasn vbiasp vdd vss vcm
+ params: win=10 wload=20 wtail=4 wn3=2 wp3=27.8 cc=100f rsdeg=0
Xn1 n1 inp nsrc1 vss sky130_fd_pr__nfet_01v8 w={win} l=1
Xn2 n2 inn nsrc2 vss sky130_fd_pr__nfet_01v8 w={win} l=1
Rsrc1 nsrc1 ntail {rsdeg}
Rsrc2 nsrc2 ntail {rsdeg}
Xntail ntail vbiasn vss vss sky130_fd_pr__nfet_01v8 w={wtail} l=2
Xp1 n1 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={wload} l=1
Xp2 n2 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={wload} l=1
Xn3 out n2 vss vss sky130_fd_pr__nfet_01v8 w={wn3} l=0.5
Xp3 out vbiasp vdd vdd sky130_fd_pr__pfet_01v8 w={wp3} l=0.5
Ccomp n2 out {cc}
.ends sky130_sc_ota_degen
"""


def main() -> int:
    deltas = (0.0, 64e-6, -64e-6, 250e-6, -250e-6, 500e-6, -500e-6)
    degenerations = (0.001, 2_000, 10_000, 50_000)
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / "sky130_sc_ota_degenerated_gain.cir"
    devices: list[str] = []
    outputs: list[str] = []
    mapping: list[tuple[int, float, float]] = []
    index = 0
    for rdeg in degenerations:
        for delta in deltas:
            name = f"d{index}"
            devices += [
                f"Vbn_{name} vbnn_{name} 0 0.65",
                f"Vbp_{name} vbpp_{name} 0 0.75",
                f"Vinp_{name} inp_{name} 0 {0.9 + delta:.9f}",
                f"Vinn_{name} inn_{name} 0 0.900000000",
                f"Rload_{name} out_{name} vcm 1Meg",
                f"Xota_{name} inp_{name} inn_{name} out_{name} vbnn_{name} vbpp_{name} vdd 0 vcm sky130_sc_ota_degen rsdeg={rdeg:g}",
            ]
            outputs.append(f"v(out_{name})")
            mapping.append((index, delta, rdeg))
            index += 1
    deck.write_text(HEADER + OTA + "\n".join(devices) + "\n.control\nop\nprint " + " ".join(outputs) + "\nquit\n.endc\n.end\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "30", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=40)
    log = run.stdout + run.stderr
    (RES / "sky130_sc_ota_degenerated_gain.log").write_text(log, encoding="utf-8")
    parsed = {int(i): float(v) for i, v in re.findall(r"v\(out_d(\d+)\)\s*=\s*([+\-0-9.eE]+)", log)}
    groups: dict[str, list[dict[str, float | None]]] = {str(x): [] for x in degenerations}
    for index, delta, rdeg in mapping:
        groups[str(rdeg)].append({"input_diff_v": delta, "output_v": parsed.get(index)})
    for rdeg, points in groups.items():
        baseline = points[0]["output_v"]
        for point in points:
            output = point["output_v"]
            delta = point["input_diff_v"]
            change = None if output is None or baseline is None else output - baseline
            point["output_change_from_zero_v"] = change
            point["incremental_gain_v_per_v"] = None if change is None or not delta else change / delta
    report = {
        "test": "sky130_tt_ota_source_degenerated_differential_sensitivity",
        "simulation_completed": run.returncode == 0 and len(parsed) == len(mapping),
        "return_code": run.returncode,
        "scope": "nominal TT transistor schematic; source-degeneration resistors ideal, no input loading or feedback; fixed OTA biases and 1Meg output load; no noise, mismatch, PVT or layout",
        "source_degeneration_ohm": groups,
    }
    (RES / "sky130_sc_ota_degenerated_gain.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
