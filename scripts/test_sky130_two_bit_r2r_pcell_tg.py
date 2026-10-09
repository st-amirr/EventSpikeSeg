"""Screen a 2-bit resistor ladder using extracted SKY130 resistor PCells.

Resistors come from the wrapper-mapped extracted three-tap layout cell. Bit
selection uses SKY130 MOS transmission gates; this is a schematic integration
screen, not a full physical DAC layout.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / "artifacts/analog_asic/layout/sky130_tapped_resistor_string3"
OUT_SCHEMATIC = ROOT / "artifacts/analog_asic/results/sky130_two_bit_r2r_pcell_tg"
OUT_PHYSICAL = ROOT / "artifacts/analog_asic/results/sky130_two_bit_r2r_physical_tg"
PHYSICAL_TG = "--physical-tg" in sys.argv
SIM = "eventspikeseg:analog-ngspice36"
TOP = "sky130_tapped_resistor_string3_raw"
CORNER = next((arg.split("=",1)[1].lower() for arg in sys.argv if arg.startswith("--corner=")),"tt")
TEMP_C = int(next((arg.split("=",1)[1] for arg in sys.argv if arg.startswith("--temp=")),"27"))
OUT = (ROOT / f"artifacts/analog_asic/results/sky130_two_bit_r2r_physical_tg_{CORNER}_{TEMP_C}c"
       if PHYSICAL_TG and (CORNER != "tt" or TEMP_C != 27) else
       OUT_PHYSICAL if PHYSICAL_TG else OUT_SCHEMATIC)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    netlist = LAYOUT / "sky130_tapped_resistor_string3.spice"
    if not netlist.is_file():
        raise FileNotFoundError("Build the extracted tapped resistor cell first")
    spice = netlist.read_text(encoding="ascii")
    body_nodes = sorted(set(re.findall(
        r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41\s",
        spice, re.M)) - {"IN", "TAP1", "TAP2", "OUT"})
    if not body_nodes:
        raise RuntimeError("No extracted resistor substrate connection found")
    body = body_nodes[0]

    lines = [
        "* Two-bit SKY130 R-2R proof using wrapper-mapped extracted resistor PCells",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
        f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{CORNER}.corner.spice"',
        f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{CORNER}.corner.spice"',
        f'.include "/workspace/artifacts/analog_asic/layout/sky130_tapped_resistor_string3/{netlist.name}"',
        *([f'.include "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"',
           ".subckt transmission_gate a b en enb vdd vss",
           "Xphysical a b en enb vdd vss sky130_transmission_gate_raw",
           ".ends transmission_gate"] if PHYSICAL_TG else
          ['.include "/workspace/asic/analog/modules.spice"']),
        f".global {body}",
        ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
        ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
        f"Vbody {body} 0 0",
        "Vdd vdd 0 1.8", "Vss vss 0 0", "Vcm cm 0 0.9",
        "Vhi rail_hi 0 0.95", "Vlo rail_lo 0 0.85",
    ]
    for code in range(4):
        b1, b0 = (code >> 1) & 1, code & 1
        for bit, value in ((1, b1), (0, b0)):
            node = f"b{bit}_{code}"
            comp = f"bb{bit}_{code}"
            lines += [f"V{node} {node} 0 {1.8 if value else 0}",
                      f"V{comp} {comp} 0 {0 if value else 1.8}"]
        lines += [
            f"Xcore{code} out{code} n1_{code} n0_{code} n0_{code} {TOP}",
            f"Xterm{code} n0_{code} termmid_{code} cm termopen_{code} {TOP}",
            f"Xbranch1_{code} n1_{code} b1mid_{code} b1sel_{code} b1open_{code} {TOP}",
            f"Xbranch0_{code} n0_{code} b0mid_{code} b0sel_{code} b0open_{code} {TOP}",
            f"Xb1hi_{code} rail_hi b1sel_{code} b1_{code} bb1_{code} vdd vss transmission_gate",
            f"Xb1lo_{code} rail_lo b1sel_{code} bb1_{code} b1_{code} vdd vss transmission_gate",
            f"Xb0hi_{code} rail_hi b0sel_{code} b0_{code} bb0_{code} vdd vss transmission_gate",
            f"Xb0lo_{code} rail_lo b0sel_{code} bb0_{code} b0_{code} vdd vss transmission_gate",
            f"Rload{code} out{code} cm 100Meg",
        ]
    lines += [f".temp {TEMP_C}", ".control", "op"]
    for code in range(4):
        lines += [f"let v_code{code}=v(out{code})", f"print v_code{code}"]
    lines += ["quit", ".endc", ".end", ""]
    deck = OUT / "two_bit_r2r_pcell_tg.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    proc = subprocess.run([
        "docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
        "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models",
        "--entrypoint", "ngspice", SIM, "-b",
        f"/workspace/{deck.relative_to(ROOT).as_posix()}"],
        capture_output=True, text=True, timeout=120, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUT / "two_bit_r2r_pcell_tg.log").write_text(log, encoding="utf-8")
    values = {int(index): float(value) for index, value in re.findall(
        r"(?im)^v_code([0-3])\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or len(values) != 4 or "ngspice-36 done" not in log:
        raise RuntimeError(f"Two-bit R-2R/TG transient failed:\n{log[-4000:]}")
    outputs = [values[i] for i in range(4)]
    steps = [outputs[i+1]-outputs[i] for i in range(3)]
    report = {
        "test": ("sky130_two_bit_r2r_extracted_resistor_physical_tg_screen" if PHYSICAL_TG else
                 "sky130_two_bit_r2r_extracted_resistor_schematic_tg_screen"),
        "simulation_completed": True,
        "process_corner": CORNER.upper(),
        "temperature_c": TEMP_C,
        "codes": list(range(4)),
        "output_v": outputs,
        "code_steps_v": steps,
        "strictly_monotonic": all(step > 0 for step in steps),
        "resistors": "Magic flat extracted layout, remapped to the exact 1.41um xhigh-poly PCell wrapper",
        "switches": ("DRC/LVS-clean extracted SKY130 1um NFET + 2um PFET TG layout" if PHYSICAL_TG else
                     "SKY130 NFET/PFET transmission-gate schematic from modules.spice"),
        "scope": "Four 2-bit code points at DC with 100Meg output load using layout-derived resistor and TG cells. TT/27C, SS/0C, or FF/85C point per report; resistor ratio mismatch, noise, full-float replay, full DAC layout, and 5ms service are not tested.",
    }
    (OUT / "two_bit_r2r_pcell_tg.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
