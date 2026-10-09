"""Tile 32 extracted one-bit trim selectors into a reusable placed bank."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_trim_plate_selector_bank32"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "sky130_trim_plate_selector_bank32"
SRC_DIR = ROOT / "artifacts/analog_asic/layout/sky130_trim_plate_selector"
SRC_CELL = "sky130_trim_plate_selector"
COLS, ROWS = 32, 1
XPITCH, YPITCH = 2400, 3000


def docker(entrypoint: str, args: list[str], stdin: str | None = None, timeout: int = 300) -> str:
    p = subprocess.run(["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
        "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
        "-w", f"/workspace/{OUT.relative_to(ROOT).as_posix()}", "--entrypoint", entrypoint,
        IMAGE, *args], input=stdin, text=True, capture_output=True, timeout=timeout, cwd=ROOT)
    log = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f"{entrypoint} failed ({p.returncode}):\n{log[-6000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    src = SRC_DIR / f"{SRC_CELL}.mag"
    sections: dict[str, list[tuple[int, int, int, int]]] = {}
    labels: list[tuple[str, tuple[int, ...], str]] = []
    sec = None
    src_port = 0
    for line in src.read_text(encoding="ascii").splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            sec = line[3:-3]
            if sec in {"end", "properties", "checkpaint"}:
                sec = None
        elif sec == "labels" and line.startswith("rlabel "):
            m = re.match(r"rlabel (\S+) (\S+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (\d+) (\S+)$", line)
            if not m:
                raise RuntimeError(f"Cannot parse selector label: {line}")
            layer, just, x1, y1, x2, y2, _port, name = m.groups()
            labels.append((layer, (int(x1), int(y1), int(x2), int(y2)), name))
        elif sec == "labels" and line.startswith("port "):
            src_port += 1
        elif sec and line.startswith("rect "):
            sections.setdefault(sec, []).append(tuple(map(int, line.split()[1:])))
    if len(labels) != 16 or src_port != 16:
        raise RuntimeError(f"Expected16 one-bit layout labels/ports; found{len(labels)}/{src_port}")

    mag = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    all_layers = {layer: [] for layer in sections}
    label_lines: list[tuple[str, str, tuple[int,int,int,int]]] = []
    port = 1
    for bit in range(COLS * ROWS):
        col, row = bit % COLS, bit // COLS
        dx, dy = col * XPITCH, row * YPITCH
        for layer, rects in sections.items():
            all_layers.setdefault(layer, []).extend((x1+dx,y1+dy,x2+dx,y2+dy) for x1,y1,x2,y2 in rects)
        for layer, (x1,y1,x2,y2), name in labels:
            translated = (x1+dx,y1+dy,x2+dx,y2+dy)
            label_lines.append((layer, f"{name}_B{bit}", translated))
    for layer, rects in all_layers.items():
        mag.append(f"<< {layer} >>")
        mag.extend("rect " + " ".join(map(str,r)) for r in rects)
    mag.append("<< labels >>")
    for layer, name, (x1,y1,x2,y2) in label_lines:
        mag += [f"rlabel {layer} s {x1} {y1} {x2} {y2} 4 {name}", f"port {port} nsew"]
        port += 1
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
        raise RuntimeError("Selector-bank DRC failed:\n" + log[-5000:])

    extracted = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    top = re.search(rf"(?im)^\.subckt\s+{CELL}([^\n]*(?:\n\+[^\n]*)*)", extracted)
    pins = top.group(1).replace("+", " ").split() if top else []
    required = {f"{name}_B{bit}" for bit in range(32) for name in ("PRE","EN_PRE","ENB_PRE","HI","EN_HI","ENB_HI","LO","EN_LO","ENB_LO","PLATE")}
    if not required.issubset(pins):
        missing = sorted(required - set(pins))
        raise RuntimeError(f"Missing bank signal ports ({len(missing)}): {missing[:20]}")

    onebit = (SRC_DIR / f"{SRC_CELL}.spice").read_text(encoding="ascii")
    inst_pins = ["PRE", "EN_PRE", "ENB_PRE", "HI", "EN_HI", "ENB_HI", "LO", "EN_LO", "ENB_LO",
                 "BULKN_LO", "PLATE", "BULKP_LO", "BULKP_HI", "BULKP_PRE"]
    bulk_n_net = next((p for p in pins if p.startswith("BULKN_")), None)
    if not bulk_n_net:
        raise RuntimeError("No extracted substrate body port found")
    ref = [f".subckt {CELL} {' '.join(pins)}"]
    for bit in range(32):
        mapped = [f"{name}_B{bit}" for name in inst_pins]
        mapped[9] = bulk_n_net  # Common p-substrate is a single physical net.
        ref.append(f"XSEL{bit} {' '.join(mapped)} {SRC_CELL}")
    ref.append(f".ends {CELL}")
    (OUT / "reference.spice").write_text(onebit + "\n" + "\n".join(ref) + "\n", encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs = docker("netgen-lvs", ["-batch", "lvs", f"{CELL}.spice {CELL}", f"reference.spice {CELL}", setup, "lvs.out"])
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely." not in lvs:
        raise RuntimeError("Selector-bank LVS failed:\n" + lvs[-5000:])

    ruby = OUT / "inspect_gds.rb"
    ruby.write_text("include RBA\nl=Layout.new\n" +
        f"l.read('/workspace/{(OUT / (CELL+'.gds')).relative_to(ROOT).as_posix()}')\n" +
        f"c=l.cell('{CELL}')\nb=c.bbox\n" +
        'puts "bbox_um=#{(b.width*l.dbu).round(4)}x#{(b.height*l.dbu).round(4)}"\n', encoding="ascii")
    geom = docker("klayout", ["-b", "-r", f"/workspace/{ruby.relative_to(ROOT).as_posix()}"], timeout=120)
    (OUT / "klayout_geometry.log").write_text(geom, encoding="utf-8")
    bbox = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", geom)
    if not bbox:
        raise RuntimeError("KLayout bbox measurement failed:\n" + geom[-2000:])
    report = {"cell": CELL, "selector_bits": 32, "transmission_gates": 96,
        "magic_drc_zero": True, "netgen_unique_match": True, "gds_written": (OUT / f"{CELL}.gds").is_file(),
        "gds_bbox_um": [float(bbox.group(1)), float(bbox.group(2))],
        "pex_coupling_capacitors": len(re.findall(r"(?im)^C\S+\s", (OUT/f"{CELL}_pex.spice").read_text(encoding="ascii"))),
        "scope": "Placed 32-selector bank with each bit's precharge/HI/LO rails, controls, and plate separately pinned; decoder and weighted-MIM integration are not included."}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
