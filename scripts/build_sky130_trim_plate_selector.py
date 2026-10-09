"""Build a routed, three-way SKY130 MIM plate selector (precharge/HI/LO)."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_trim_plate_selector"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "sky130_trim_plate_selector"
TG = ROOT / "artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_raw.mag"
TG_SPICE = ROOT / "artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate.spice"


def docker(entrypoint: str, args: list[str], stdin: str | None = None, timeout: int = 240) -> str:
    p = subprocess.run(["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
        "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
        "-w", f"/workspace/{OUT.relative_to(ROOT).as_posix()}", "--entrypoint", entrypoint,
        IMAGE, *args], input=stdin, text=True, capture_output=True, timeout=timeout, cwd=ROOT)
    log = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f"{entrypoint} failed ({p.returncode}):\n{log[-5000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sections: dict[str, list[tuple[int, int, int, int]]] = {}
    sec = None
    for line in TG.read_text(encoding="ascii").splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            sec = line[3:-3]
            if sec in {"labels", "end", "properties", "checkpaint"}:
                sec = None
        elif sec and line.startswith("rect "):
            sections.setdefault(sec, []).append(tuple(map(int, line.split()[1:])))

    # 0=VCM precharge, 1=upper trim rail, 2=lower trim rail.
    stride = 800
    dxs = [0, stride, 2 * stride]
    shapes = {layer: [] for layer in sections}
    for dx in dxs:
        for layer, rects in sections.items():
            shapes[layer].extend((x1+dx, y1, x2+dx, y2) for x1,y1,x2,y2 in rects)
    shapes.setdefault("metal2", [])
    shapes.setdefault("via1", [])
    # The three B terminals share a metal2 plate bus. Each B contact is
    # reached by a via1 and an M2 riser; A, gate, and body pins remain explicit.
    bxs = [dx+44 for dx in dxs]
    bus_y = 2000
    for x in bxs:
        shapes["via1"].append((x-20, 335, x+20, 375))
        shapes["metal2"].append((x-20, 355, x+20, bus_y))
    shapes["metal2"].append((bxs[0]-20, bus_y-20, bxs[-1]+20, bus_y+20))

    mag = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in shapes.items():
        mag.append(f"<< {layer} >>")
        mag.extend("rect " + " ".join(map(str, r)) for r in rects)
    mag.append("<< labels >>")
    ports: list[tuple[str, str, int, int]] = []
    for i, (name, dx) in enumerate(zip(("PRE", "HI", "LO"), dxs)):
        ports.extend([(f"{name}", "metal1", dx-44, 355),
                      (f"EN_{name}", "metal1", dx, 295),
                      (f"ENB_{name}", "metal1", dx, 1195),
                      (f"BULKP_{name}", "nsubdiff", dx-110, 1163),
                      (f"BULKN_{name}", "psubdiff", dx-110, 258)])
    ports.append(("PLATE", "metal2", bxs[1], bus_y))
    for port, (name, layer, x, y) in enumerate(ports, 1):
        half = 10 if layer in {"psubdiff", "nsubdiff"} else 20
        mag += [f"rlabel {layer} s {x-half} {y-half} {x+half} {y+half} 4 {name}",
                f"port {port} nsew"]
    mag += ["<< end >>", ""]
    (OUT / f"{CELL}.mag").write_text("\n".join(mag), encoding="ascii")

    tcl = "\n".join([f"load {CELL}", "drc check", "drc count", "extract all",
        "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
        "ext2spice cthresh 0", "ext2spice rthresh infinite",
        f"ext2spice -o {CELL}_pex.spice", f"gds write {CELL}.gds", "save", "quit -noprompt", ""])
    log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC], tcl)
    (OUT / "magic_extract.log").write_text(log, encoding="utf-8")
    drc = re.search(r"Total DRC errors found: (\d+)", log)
    if not drc or drc.group(1) != "0":
        raise RuntimeError("Selector DRC failed:\n" + log[-4000:])

    ext = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    hdr = re.search(rf"(?im)^\.subckt\s+{CELL}([^\n]*(?:\n\+[^\n]*)*)", ext)
    pins = hdr.group(1).replace("+", " ").split() if hdr else []
    required = {x[0] for x in ports if x[0] not in {"BULKN_PRE", "BULKN_HI"}}
    if not required.issubset(pins) or not {"PRE", "HI", "LO", "PLATE"}.issubset(pins):
        raise RuntimeError(f"Missing selector signal pins: {pins!r}; expected at least {sorted(required)!r}")

    # SKY130 extraction collapses the three p-substrate contacts to one net;
    # use the extracted terminal order and net name for the reference too.
    ref = [f".subckt {CELL} {' '.join(pins)}"]
    tg_ref = TG_SPICE.read_text(encoding="ascii")
    (OUT / "tg_raw_reference.spice").write_text(tg_ref, encoding="ascii")
    for name in ("PRE", "HI", "LO"):
        ref.append(f"X{name} {name} PLATE EN_{name} ENB_{name} BULKP_{name} BULKN_LO sky130_transmission_gate_raw")
    ref.append(f".ends {CELL}")
    (OUT / "reference.spice").write_text(tg_ref + "\n" + "\n".join(ref)+"\n", encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs = docker("netgen-lvs", ["-batch", "lvs", f"{CELL}.spice {CELL}", f"reference.spice {CELL}", setup, "lvs.out"])
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely." not in lvs:
        raise RuntimeError("Selector LVS failed:\n" + lvs[-4000:])

    pex = (OUT / f"{CELL}_pex.spice").read_text(encoding="ascii")
    report = {"cell": CELL, "switches": 3, "function": ["precharge to VCM", "select HI", "select LO"],
        "magic_drc_zero": True, "netgen_unique_match": True,
        "gds_written": (OUT / f"{CELL}.gds").is_file(), "extracted_pins": pins,
        "pex_coupling_capacitors": len(re.findall(r"(?im)^C\S+\s", pex)),
        "scope": "Reusable one-bit physical selector prototype; controls and supplies external, no decoder or full 32-bit selector-bank integration yet."}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
