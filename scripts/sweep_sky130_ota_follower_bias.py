#!/usr/bin/env python3
"""Bounded PVT bias screen for the SKY130 OTA used as an analog bit buffer."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/results/sky130_ota_follower_bias"
IMAGE = "eventspikeseg:analog-ngspice36"
PDK = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
BIAS_PAIRS = ((0.55, 0.65), (0.55, 0.75), (0.65, 0.65),
              (0.65, 0.75), (0.75, 0.65), (0.75, 0.75))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    for corner, temp in (("tt", 27), ("ss", 0), ("ff", 85)):
        lines = [
            f"* SKY130 {corner.upper()} OTA follower bias grid, two reference levels",
            ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
            f".temp {temp}",
            f'.include "{PDK}/models/parameters/invariant.spice"',
            f'.include "{PDK}/models/r+c/res_typical__cap_typical__lin.spice"',
            f'.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
            f'.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
            '.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"',
            "Vdd vdd 0 1.8", "Vcm cm 0 0.9", "Vlow low 0 0.85", "Vhigh high 0 0.95",
        ]
        names = []
        for idx, (vbn, vbp) in enumerate(BIAS_PAIRS):
            for rail, source in (("low", "low"), ("high", "high")):
                name = f"c{idx}_{rail}"
                names.append((name, idx, rail, vbn, vbp, 0.85 if rail == "low" else 0.95))
                lines += [f"Vbn_{name} vbnn_{name} 0 {vbn}",
                          f"Vbp_{name} vbpp_{name} 0 {vbp}",
                          f"Xota_{name} out_{name} {source} out_{name} vbnn_{name} vbpp_{name} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=500f",
                          f"Rload_{name} out_{name} cm 100k"]
        lines += [".control", "set numdgt=15", "op"]
        lines += [f"print v(out_{name})" for name, *_ in names]
        lines += ["quit", ".endc", ".end", ""]
        deck = OUT / f"follower_bias_{corner}.cir"
        deck.write_text("\n".join(lines), encoding="ascii")
        cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v",
               f"{ROOT}:/workspace", "-w", "/workspace/artifacts/analog_asic/results",
               "--entrypoint", "ngspice", IMAGE, "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
        log = run.stdout + run.stderr
        (OUT / f"follower_bias_{corner}.log").write_text(log, encoding="utf-8")
        values = {name: float(v) for name, v in re.findall(
            r"(?im)^\s*v\(out_(c\d+_(?:low|high))\)\s*=\s*([-+0-9.eE]+)", log)}
        if run.returncode or "ngspice-36 done" not in log:
            raise RuntimeError(f"{corner} bias screen did not complete: {log[-2500:]}")
        rows = []
        for name, idx, rail, vbn, vbp, target in names:
            actual = values.get(name)
            rows.append({"candidate": idx, "vbiasn_v": vbn, "vbiasp_v": vbp,
                         "input_v": target, "output_v": actual,
                         "error_mv": None if actual is None else (actual-target)*1000,
                         "within_0_to_1p8_v": actual is not None and 0 <= actual <= 1.8})
        pairs = []
        for idx, (vbn, vbp) in enumerate(BIAS_PAIRS):
            r = [x for x in rows if x["candidate"] == idx]
            errors = [abs(x["error_mv"]) for x in r if x["error_mv"] is not None]
            pairs.append({"candidate": idx, "vbiasn_v": vbn, "vbiasp_v": vbp,
                          "max_abs_error_mv": max(errors) if len(errors) == 2 else None,
                          "both_outputs_rail_bounded": all(x["within_0_to_1p8_v"] for x in r)})
        reports[f"{corner.upper()}_{temp}C"] = {"simulation_completed": len(values) == len(names),
            "rows": rows, "bias_pair_summary": pairs,
            "scope": "schematic OTA PDK devices, 100k load to VCM, DC-only; no loop stability transient, mismatch or physical layout."}
    result = {"test": "sky130_ota_follower_bias_pvt_screen", "simulation_completed": True,
              "temperature_and_corner": reports,
              "interpretation": "DC bias candidates only; best row is not a qualified follower until loaded ladder transfer and transient stability pass."}
    (OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {"bias_pair_summary": v["bias_pair_summary"]} for k, v in reports.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
