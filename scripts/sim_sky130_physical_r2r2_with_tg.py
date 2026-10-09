#!/usr/bin/env python3
"""Sweep the extracted resistor ladder with extracted SKY130 TG bit switches."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / "artifacts/analog_asic/layout"
OUT = ROOT / "artifacts/analog_asic/results/sky130_physical_r2r2_with_tg"
TOP = "sky130_physical_r2r2_slice_raw"
TG_TOP = "sky130_transmission_gate_raw"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ladder = LAYOUT / "sky130_physical_r2r2_slice" / f"sky130_physical_r2r2_slice.spice"
    tg = LAYOUT / "sky130_transmission_gate" / "sky130_transmission_gate_pex.spice"
    src = ladder.read_text(encoding="ascii")
    bodyset = set(re.findall(r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41", src, re.M))
    if len(bodyset) != 1 or not tg.exists():
        raise RuntimeError("Missing physical resistor body node or extracted TG netlist")
    body = next(iter(bodyset))
    reports = {}
    for corner, temp in (("tt", 27), ("ss", 0), ("ff", 85)):
        lines = [
            f"* Extracted passive R-2R ladder + physical TG, {corner.upper()} {temp}C",
            ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
            f".temp {temp}",
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
            f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
            f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
            f'.include "/workspace/{ladder.relative_to(ROOT).as_posix()}"',
            f'.include "/workspace/{tg.relative_to(ROOT).as_posix()}"',
            f".global {body}",
            ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
            ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
            f"Vbody {body} 0 0", "Vdd vdd 0 1.8", "Vss vss 0 0",
            "Vhi rail_hi 0 0.95", "Vlo_switch rail_lo 0 0.85", "Vlo_ref vlo 0 0.85", "Vcm cm 0 0.9",
        ]
        lines += [".subckt transmission_gate a b en enb vdd vss params: mscale=1",
                  "Xn b en a vss sky130_fd_pr__nfet_01v8 w=1 l=0.15 m={mscale}",
                  "Xp b enb a vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15 m={mscale}",
                  ".ends transmission_gate"]
        for mult in (1, 10, 32, 64, 100, 128, 256, 1000):
            for code in range(4):
                tag = f"m{mult}_c{code}"
                b1, b0 = code >> 1, code & 1
                for name, value in (("b1", b1), ("b0", b0)):
                    lines += [f"V{name}_{tag} sel_{name}_{tag} 0 {1.8 if value else 0}",
                              f"V{name}b_{tag} selb_{name}_{tag} 0 {0 if value else 1.8}"]
                lines += [f"Xdac_{tag} out_{tag} vlo b1_{tag} b0_{tag} {TOP}"]
                for name in ("b1", "b0"):
                    lines += [f"X{name}hi_{tag} rail_hi {name}_{tag} sel_{name}_{tag} selb_{name}_{tag} vdd vss transmission_gate params: mscale={mult}",
                              f"X{name}lo_{tag} rail_lo {name}_{tag} selb_{name}_{tag} sel_{name}_{tag} vdd vss transmission_gate params: mscale={mult}"]
                lines.append(f"Rload_{tag} out_{tag} cm 100Meg")
        lines += [".control", "set numdgt=15", "op"]
        for mult in (1, 10, 32, 64, 100, 128, 256, 1000):
            for code in range(4):
                tag = f"m{mult}_c{code}"
                lines += [f"let {tag}=v(out_{tag})", f"print {tag}"]
        lines += ["quit", ".endc", ".end", ""]
        deck = OUT / f"physical_r2r2_with_tg_{corner}_{temp}c.cir"
        deck.write_text("\n".join(lines), encoding="ascii")
        cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
               "-w", "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models", "--entrypoint", "ngspice",
               IMAGE, "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=90, cwd=ROOT)
        log = p.stdout + p.stderr
        (OUT / f"physical_r2r2_with_tg_{corner}_{temp}c.log").write_text(log, encoding="utf-8")
        values = {name: float(v) for name, v in re.findall(
            r"(?im)^\s*(m[0-9]+_c[0-3])\s*=\s*([-+0-9.eE]+)", log)}
        if p.returncode or "ngspice-36 done" not in log or len(values) != 32:
            raise RuntimeError(f"Extracted R-2R + TG simulation failed at {corner}/{temp}:\n{log[-3000:]}")
        reports[f"{corner.upper()}_{temp}C"] = {}
        for mult in (1, 10, 32, 64, 100, 128, 256, 1000):
            outputs = [values[f"m{mult}_c{code}"] for code in range(4)]
            steps = [outputs[i+1] - outputs[i] for i in range(3)]
            reports[f"{corner.upper()}_{temp}C"][str(mult)] = {
                "code_v": outputs, "steps_v": steps,
                "strictly_monotonic": all(s > 0 for s in steps),
                "max_step_deviation_from_mean_pct": max(abs(s/(sum(steps)/3)-1) for s in steps)*100}
    report = {"test": "sky130_extracted_r2r2_resistors_and_transmission_gate_dc",
              "simulation_completed": True, "resistors": "seven Magic-extracted PCells and metal1 routes",
              "switches": "base 1um/2um TG device sizes match the extracted cell; m=1/10/32/64/100/128/256/1000 are PDK model multiplicity screens and omit scaled physical interconnect parasitics",
              "temperature_and_corner": reports, "load": "100Meg to 0.9V",
              "scope": "Cell-level 2-bit transfer using extracted resistor and switch layouts, ideal select waveforms, PDK device corners. No combined GDS/LVS top, resistor mismatch, noise, transient settling, high-resolution ladder or full-float SNN replay."}
    (OUT / "physical_r2r2_with_tg.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
