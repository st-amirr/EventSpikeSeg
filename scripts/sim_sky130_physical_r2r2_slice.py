#!/usr/bin/env python3
"""Characterize DC code transfer of the extracted SKY130 2-bit R-2R slice."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / "artifacts/analog_asic/layout/sky130_physical_r2r2_slice"
OUT = ROOT / "artifacts/analog_asic/results/sky130_physical_r2r2_slice"
TOP = "sky130_physical_r2r2_slice_raw"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    extracted = LAYOUT / "sky130_physical_r2r2_slice.spice"
    spice = extracted.read_text(encoding="ascii")
    bodies = set(re.findall(r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41", spice, re.M))
    if len(bodies) != 1:
        raise RuntimeError(f"Expected one common resistor body net; found {bodies}")
    body = next(iter(bodies))
    lines = [
        "* DC transfer of Magic-extracted 2-bit resistor ladder layout",
        ".option scale=1u reltol=1e-6 abstol=1e-15 vntol=1e-10",
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
        f'.include "/workspace/{extracted.relative_to(ROOT).as_posix()}"',
        f".global {body}",
        ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
        ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
        f"Vbody {body} 0 0", "Vhi vhi 0 0.95", "Vlo vlo 0 0.85", "Vcm cm 0 0.9",
    ]
    for code in range(4):
        b1, b0 = code >> 1, code & 1
        lines += [f"Vb1_{code} b1_{code} 0 {0.85 + 0.10*b1:.9g}",
                  f"Vb0_{code} b0_{code} 0 {0.85 + 0.10*b0:.9g}",
                  f"Xdac_{code} out_{code} vlo b1_{code} b0_{code} {TOP}",
                  f"Rload_{code} out_{code} cm 100Meg"]
    logs = []
    values = {}
    for temp in (0, 27, 85):
        deck = OUT / f"physical_r2r2_slice_dc_t{temp}.cir"
        deck_lines = list(lines)
        # A separate top-level .temp is required; ngspice does not accept it
        # as an interactive command within .control.
        deck_lines += [f".temp {temp}", ".control", "set numdgt=15", "op"]
        for code in range(4):
            deck_lines += [f"let c{code}=v(out_{code})", f"print c{code}"]
        deck_lines += ["quit", ".endc", ".end", ""]
        deck.write_text("\n".join(deck_lines), encoding="ascii")
        cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
               "-w", "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models", "--entrypoint", "ngspice", IMAGE,
               "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=90, cwd=ROOT)
        log = p.stdout + p.stderr
        logs.append(f"===== {temp} C =====\n{log}")
        got = {f"c{c}_t{temp}": float(v) for c, v in re.findall(
            r"(?im)^\s*c([0-3])\s*=\s*([-+0-9.eE]+)", log)}
        if p.returncode or "ngspice-36 done" not in log or len(got) != 4 or f"TEMP = {temp:.6f}" not in log:
            (OUT / "physical_r2r2_slice_dc.log").write_text("\n".join(logs), encoding="utf-8")
            raise RuntimeError(f"Extracted R-2R DC simulation incomplete at {temp}C:\n{log[-3000:]}")
        values.update(got)
    log = "\n".join(logs)
    (OUT / "physical_r2r2_slice_dc.log").write_text(log, encoding="utf-8")
    by_temp = {}
    for temp in (0, 27, 85):
        outputs = [values[f"c{c}_t{temp}"] for c in range(4)]
        steps = [outputs[i+1] - outputs[i] for i in range(3)]
        by_temp[str(temp)] = {"code_v": outputs, "steps_v": steps,
                              "strictly_monotonic": all(s > 0 for s in steps),
                              "max_step_deviation_from_mean_pct":
                                  max(abs(s / (sum(steps)/3) - 1) for s in steps) * 100}
    report = {"test": "sky130_physical_r2r2_resistor_slice_dc_transfer",
              "simulation_completed": True, "resistor_layout": str(extracted.relative_to(ROOT)),
              "resistors": "seven extracted 1.41um xhigh-poly PCells with Magic-extracted metal1 routing, wrapper-mapped resistor model",
              "bit_switches": "ideal voltage sources at B0/B1; no TGs",
              "output_load": "100Meg to VCM=0.9V", "temperature_c": [0, 27, 85],
              "transfer": by_temp,
              "scope": "Standalone passive 2-bit ladder DC test. Resistor geometry/interconnect extracted; ideal bit rails and no resistor mismatch, noise, PVT process corners, output buffer, weight-map conversion, dynamic settling or SNN replay."}
    (OUT / "physical_r2r2_slice_dc.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    qpath = LAYOUT / "qualification.json"
    q = json.loads(qpath.read_text(encoding="utf-8"))
    q["simulation_completed"] = True
    q["dc_transfer_report"] = str((OUT / "physical_r2r2_slice_dc.json").relative_to(ROOT))
    q["simulation_scope"] = "Extracted resistor/interconnect, ideal bit rails, TT resistor model at 0/27/85C."
    qpath.write_text(json.dumps(q, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
