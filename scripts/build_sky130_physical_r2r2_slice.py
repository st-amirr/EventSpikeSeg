#!/usr/bin/env python3
"""Build a routed 2-bit SKY130 R-2R resistor slice from resistor PCells.

This is the physical passive ladder only. Bit selection is driven by ideal
sources in the follow-on transient bench; no accuracy claim is implied for a
larger DAC or for the SNN weight path.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_physical_r2r2_slice"
IMAGE = "eventspikeseg:analog-layout"
SIM = "eventspikeseg:analog-ngspice36"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
PCELL = "sky130_fd_pr__res_xhigh_po_1p41_DFRRR3"
CELL = "sky130_physical_r2r2_slice"
TOP = f"{CELL}_raw"


def docker(entrypoint: str, args: list[str], text: str | None = None, timeout: int = 180) -> str:
    cmd = ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
           "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
           "-w", f"/workspace/{OUT.relative_to(ROOT).as_posix()}",
           "--entrypoint", entrypoint, IMAGE, *args]
    p = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=timeout, cwd=ROOT)
    log = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f"{entrypoint} returned {p.returncode}:\n{log[-4000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    src = ROOT / "artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe" / f"{PCELL}.mag"
    if not src.exists():
        raise FileNotFoundError(src)
    shutil.copy2(src, OUT / src.name)

    # R0 anchors and 980-DBU terminal spacing follow the extracted PCell pin
    # centers (-490,+490). Two units in series make each 2R branch/termination.
    cells = [("spine_r", 0, 3000), ("term_r0", 10000, 6000), ("term_r1", 10000, 9000),
             ("b1_r0", 5000, 3980), ("b1_r1", 5000, 6000),
             ("b0_r0", -5000, 3000), ("b0_r1", -5000, 6000)]
    labels = [(1, "OUT", 0, 3980), (2, "VLO", 10000, 9980),
              (3, "B1", 5000, 6980), (4, "B0", -5000, 6980)]
    raw = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0",
           "<< checkpaint >>", "<< labels >>"]
    for port, name, x, y in labels:
        raw += [f"rlabel metal1 s {x-131} {y-6} {x+131} {y+6} 4 {name}", f"port {port} nsew"]
    raw += ["<< end >>"]
    (OUT / f"{TOP}.mag").write_text("\n".join(raw) + "\n", encoding="ascii")

    build = [f"load {TOP}"]
    for _, x, y in cells:
        # Magic's command coordinates are in half-database units for this
        # magscale; the root labels below are already in database units.
        build.append(f"dump {PCELL} child R0 parent {x // 2} {y // 2}")
    # Backbone and both 2R bit branches; each wire joins neighboring terminal
    # pads. Branches leave on opposite sides to avoid crossing each other.
    for x, ya, yb in [(10000, 6980, 9000),
                       (5000, 4960, 6000), (-5000, 3980, 6000)]:
        build.append(f"wire segment metal1 75 {x // 2} {ya // 2} {x // 2} {yb // 2}")
    build += ["wire segment metal1 75 0 1990 2500 1990",
              "wire segment metal1 75 2500 2480 2500 3000",
              "wire segment metal1 75 0 1500 -2500 1500",
              "wire segment metal1 75 0 1500 5000 1500",
              "wire segment metal1 75 5000 1500 5000 3000",
              "save", "quit -noprompt", ""]
    magic_args = ["magic", "-dnull", "-noconsole", "-rcfile", RC]
    log = docker("magic", magic_args[1:], "\n".join(build))
    (OUT / "magic_build.log").write_text(log, encoding="utf-8")
    if "Unrecognized parent/child keyword" in log or "Couldn't find label" in log or "No cell" in log:
        raise RuntimeError(f"Magic did not place the resistor cells:\n{log[-3000:]}")
    if not re.search(r"<< xpolyres >>", (OUT / f"{TOP}.mag").read_text(encoding="ascii")):
        raise RuntimeError("Magic top cell contains no extracted resistor geometry")

    mag = OUT / f"{TOP}.mag"
    cleaned = []
    skip_port = False
    for line in mag.read_text(encoding="ascii").splitlines():
        if skip_port and line.startswith("port "):
            skip_port = False
            continue
        skip_port = False
        if line.startswith("rlabel ") and line.rsplit(" ", 1)[-1] in {"R0", "R1"}:
            skip_port = True
            continue
        cleaned.append(line)
    mag.write_text("\n".join(cleaned) + "\n", encoding="ascii")
    extract = [f"load {TOP}", "drc check", "drc count", "extract all", "ext2spice lvs",
               "ext2spice scale off", f"ext2spice -o {CELL}.spice",
               f"gds write {CELL}.gds", "save", "quit -noprompt", ""]
    xlog = docker("magic", magic_args[1:], "\n".join(extract))
    (OUT / "magic_extract.log").write_text(xlog, encoding="utf-8")
    if "Total DRC errors found: 0" not in xlog:
        raise RuntimeError(f"Magic DRC failed:\n{xlog[-3000:]}")

    net = OUT / f"{CELL}.spice"
    spice = net.read_text(encoding="ascii")
    if f".subckt {TOP} OUT VLO B1 B0" not in spice:
        raise RuntimeError(f"Unexpected extracted ports:\n{spice[:1200]}")
    if "\nX" not in spice:
        raise RuntimeError("Magic extracted no electrical devices")
    spice, mapped = re.subn(r"sky130_fd_pr__res_xhigh_po\s+w=1\.41e\+06u\s+l=700000u",
                             "sky130_fd_pr__res_xhigh_po_1p41 l=700000u", spice)
    if mapped != len(cells):
        raise RuntimeError(f"Expected {len(cells)} extracted resistors, mapped {mapped}")
    net.write_text(spice, encoding="ascii")

    reference = [f".subckt {TOP} OUT VLO B1 B0",
                 "Xspine OUT NODE0 BODY sky130_fd_pr__res_xhigh_po_1p41 l=700000u",
                 "Xt0 NODE0 T0 BODY sky130_fd_pr__res_xhigh_po_1p41 l=700000u",
                 "Xt1 T0 VLO BODY sky130_fd_pr__res_xhigh_po_1p41 l=700000u",
                 "Xb10 OUT B1T BODY sky130_fd_pr__res_xhigh_po_1p41 l=700000u",
                 "Xb11 B1T B1 BODY sky130_fd_pr__res_xhigh_po_1p41 l=700000u",
                 "Xb00 NODE0 B0T BODY sky130_fd_pr__res_xhigh_po_1p41 l=700000u",
                 "Xb01 B0T B0 BODY sky130_fd_pr__res_xhigh_po_1p41 l=700000u",
                 ".ends", ""]
    (OUT / "reference.spice").write_text("\n".join(reference), encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs = docker("netgen-lvs", ["-batch", "lvs", f"{net.name} {TOP}", f"reference.spice {TOP}", setup, "lvs.out"])
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely" not in lvs:
        raise RuntimeError(f"Netgen LVS failed:\n{lvs[-3000:]}")

    report = {"test": "sky130_r2r2_passive_resistor_slice_layout",
              "resistor_count": len(cells), "resistor_pcell": "xhigh-poly 1.41um x 0.7um",
              "magic_drc_zero": True, "netgen_lvs_unique": True,
              "gds_written": (OUT / f"{CELL}.gds").exists(),
              "physical_scope": "R-2R passive resistor/interconnect slice, two bits, extracted resistor PCells; ideal voltage sources drive B0/B1 for DC code characterization. No TG switches, output buffer, mismatch, noise, PVT or SNN replay.",
              "simulation_completed": False}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
