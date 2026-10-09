#!/usr/bin/env python3
"""Screen resistor-length versus TG size for the extracted 2-bit R-2R ladder."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / "artifacts/analog_asic/layout/sky130_physical_r2r2_slice/sky130_physical_r2r2_slice.spice"
OUT = ROOT / "artifacts/analog_asic/results/sky130_r2r2_resistor_length_tradeoff"
IMAGE = "eventspikeseg:analog-ngspice36"
TOP = "sky130_physical_r2r2_slice_raw"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    src = LAYOUT.read_text(encoding="ascii")
    bodyset = set(re.findall(r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41", src, re.M))
    if len(bodyset) != 1:
        raise RuntimeError(f"Expected one extracted resistor body node, got {bodyset}")
    body = next(iter(bodyset))
    scales = (1, 5, 10, 25, 50)
    corners = (("tt", 27), ("ss", 0), ("ff", 85))
    report = {"test": "sky130_extracted_r2r2_resistor_length_vs_switch_resistance",
              "simulation_completed": True, "ladder_topology": "Magic-extracted 7-resistor 2-bit slice",
              "tg": "PDK MOS model at extracted TG device sizes (1um NFET, 2um PFET), m=1",
              "resistor_variants": {}, "scope": "PDK model length-scaling sensitivity only; original physical resistor geometry/interconnect extracted, but longer resistor geometries not yet generated or extracted. No mismatch, noise, dynamic settling or SNN replay."}
    for corner, temp in corners:
        lines = [
            f"* R-2R resistance length tradeoff: {corner}/{temp}C",
            ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9", f".temp {temp}",
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',
            '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
            f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
            f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
            ".subckt tg a b en enb vdd vss",
            "Xn b en a vss sky130_fd_pr__nfet_01v8 w=1 l=0.15",
            "Xp b enb a vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15",
            ".ends tg", f".global {body}",
            ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
            ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
            f"Vbody {body} 0 0", "Vdd vdd 0 1.8", "Vss vss 0 0",
            "Vhi rail_hi 0 0.95", "Vlo rail_lo 0 0.85", "Vcm cm 0 0.9",
        ]
        for scale in scales:
            scaled = re.sub(r"(?<=l=)700000u", f"{700000*scale}u", src)
            if scaled == src and scale != 1:
                raise RuntimeError("Could not scale extracted resistor model length")
            subname = f"r2r2_l{scale}"
            scaled = scaled.replace(f".subckt {TOP}", f".subckt {subname}", 1)
            (OUT / f"{subname}.spice").write_text(scaled, encoding="ascii")
            lines.append(f'.include "/workspace/{(OUT / f"{subname}.spice").relative_to(ROOT).as_posix()}"')
            for code in range(4):
                tag = f"l{scale}_c{code}"
                b1, b0 = code >> 1, code & 1
                for bit, value in (("b1", b1), ("b0", b0)):
                    lines += [f"V{bit}_{tag} sel_{bit}_{tag} 0 {1.8 if value else 0}",
                              f"V{bit}b_{tag} selb_{bit}_{tag} 0 {0 if value else 1.8}"]
                lines += [f"Xdac_{tag} out_{tag} vlo b1_{tag} b0_{tag} {subname}"]
                for bit in ("b1", "b0"):
                    lines += [f"X{bit}hi_{tag} rail_hi {bit}_{tag} sel_{bit}_{tag} selb_{bit}_{tag} vdd vss tg",
                              f"X{bit}lo_{tag} rail_lo {bit}_{tag} selb_{bit}_{tag} sel_{bit}_{tag} vdd vss tg"]
                lines.append(f"Rload_{tag} out_{tag} cm 100Meg")
        lines += [".control", "set numdgt=15", "op"]
        for scale in scales:
            for code in range(4):
                tag = f"l{scale}_c{code}"
                lines += [f"let {tag}=v(out_{tag})", f"print {tag}"]
        lines += ["quit", ".endc", ".end", ""]
        deck = OUT / f"r2r2_len_sweep_{corner}_{temp}c.cir"
        deck.write_text("\n".join(lines), encoding="ascii")
        cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
               "-w", "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models", "--entrypoint", "ngspice",
               IMAGE, "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=90, cwd=ROOT)
        log = p.stdout + p.stderr
        (OUT / f"r2r2_len_sweep_{corner}_{temp}c.log").write_text(log, encoding="utf-8")
        values = {tag: float(value) for tag, value in re.findall(
            r"(?im)^\s*(l[0-9]+_c[0-3])\s*=\s*([-+0-9.eE]+)", log)}
        if p.returncode or "ngspice-36 done" not in log or len(values) != len(scales)*4:
            raise RuntimeError(f"Length sweep failed {corner}/{temp}:\n{log[-2500:]}")
        report["resistor_variants"][f"{corner.upper()}_{temp}C"] = {}
        for scale in scales:
            outputs = [values[f"l{scale}_c{c}"] for c in range(4)]
            steps = [outputs[i+1] - outputs[i] for i in range(3)]
            report["resistor_variants"][f"{corner.upper()}_{temp}C"][str(scale)] = {
                "model_length_multiplier": scale, "output_v": outputs, "steps_v": steps,
                "strictly_monotonic": all(step > 0 for step in steps),
                "max_step_deviation_from_mean_pct": max(abs(s/(sum(steps)/3)-1) for s in steps)*100}
    path = OUT / "r2r2_resistor_length_tradeoff.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
