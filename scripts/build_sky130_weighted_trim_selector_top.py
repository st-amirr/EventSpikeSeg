"""Route the 32-bit plate-selector strip onto the weighted MIM trim array."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_weighted_trim_selector_top"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "sky130_weighted_trim_selector_top"
ARRAY = "sky130_cap_trim_weighted_array"
BANK = "sky130_trim_plate_selector_bank32"
ARRAY_DIR = ROOT / "artifacts/analog_asic/layout" / ARRAY
BANK_DIR = ROOT / "artifacts/analog_asic/layout" / "sky130_trim_plate_selector_bank32"


def docker(entrypoint: str, args: list[str], stdin: str | None = None, timeout: int = 360) -> str:
    p = subprocess.run(["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
        "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
        "-w", f"/workspace/{OUT.relative_to(ROOT).as_posix()}", "--entrypoint", entrypoint,
        IMAGE, *args], input=stdin, text=True, capture_output=True, timeout=timeout, cwd=ROOT)
    log = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f"{entrypoint} failed ({p.returncode}):\n{log[-6000:]}")
    return log


def read_mag(path: Path):
    shapes: dict[str, list[tuple[int,int,int,int]]] = {}
    labels: list[tuple[str, tuple[int,int,int,int], str]] = []
    section = None
    for line in path.read_text(encoding="ascii").splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            section = line[3:-3]
            if section in {"end", "properties", "checkpaint"}:
                section = None
        elif section == "labels" and line.startswith("rlabel "):
            m = re.match(r"rlabel (\S+) \S+ (-?\d+) (-?\d+) (-?\d+) (-?\d+) \d+ (\S+)$", line)
            if m:
                layer, x1,y1,x2,y2,name=m.groups()
                labels.append((layer, tuple(map(int,(x1,y1,x2,y2))), name))
        elif section and line.startswith("rect "):
            shapes.setdefault(section, []).append(tuple(map(int,line.split()[1:])))
    return shapes, labels


def parse_pins(path: Path, cell: str) -> list[str]:
    t = path.read_text(encoding="ascii")
    m = re.search(rf"(?im)^\.subckt\s+{cell}([^\n]*(?:\n\+[^\n]*)*)", t)
    if not m:
        raise RuntimeError(f"Missing .subckt {cell} in {path}")
    return m.group(1).replace("+", " ").split()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    array_shapes, array_labels = read_mag(ARRAY_DIR / f"{ARRAY}.mag")
    bank_shapes, bank_labels = read_mag(BANK_DIR / f"{BANK}.mag")
    array_w = max(x2 for rects in array_shapes.values() for _x1,_y1,x2,_y2 in rects)
    bank_x = array_w + 5000  # 25um clear channel outside the largest weighted row.
    merged: dict[str, list[tuple[int,int,int,int]]] = {}
    for layer, rects in array_shapes.items():
        merged.setdefault(layer, []).extend(rects)
    for layer, rects in bank_shapes.items():
        merged.setdefault(layer, []).extend((x1+bank_x,y1,x2+bank_x,y2) for x1,y1,x2,y2 in rects)
    for layer in ("metal3", "metal4", "metal5", "via2", "via3", "via4"):
        merged.setdefault(layer, [])

    # The weighted-array macro lists banks in COARSE_P, COARSE_N, FINE_P,
    # FINE_N order. The 32 selectors are laid out as a one-row strip in that
    # same bit order. MIM plate buses are M3; connect each selector M2 plate
    # through an isolated M4 riser and an M5 row strap.
    array_plate_points: dict[str, tuple[int,int]] = {}
    for layer, (x1,y1,x2,y2), name in array_labels:
        if name.startswith("PLATE_") and layer == "metal3":
            array_plate_points[name] = (1000, (y1+y2)//2)
    bank_plate_points: dict[int, tuple[int,int]] = {}
    for layer, (x1,y1,x2,y2), name in bank_labels:
        m = re.fullmatch(r"PLATE_B(\d+)", name)
        if m and layer == "metal2":
            bank_plate_points[int(m.group(1))] = (bank_x+(x1+x2)//2, (y1+y2)//2)
    ordered_caps = [f"PLATE_{bank}_B{bit}" for bank in ("COARSE_P","COARSE_N","FINE_P","FINE_N") for bit in range(8)]
    if set(bank_plate_points) != set(range(32)) or not set(ordered_caps).issubset(array_plate_points):
        raise RuntimeError("Plate-pin maps do not contain all32 weighted MIM/selector nodes")
    for bit, capname in enumerate(ordered_caps):
        sx, sy = bank_plate_points[bit]
        tx, ty = array_plate_points[capname]
        via = 20
        merged["via2"].append((sx-via,sy-via,sx+via,sy+via))
        merged["metal3"].append((sx-40,sy-40,sx+40,sy+40))
        merged["via3"].append((sx-via,sy-via,sx+via,sy+via))
        merged["metal4"].append((sx-40,min(sy,ty),sx+40,max(sy,ty)))
        merged["via4"].append((sx-via,ty-via,sx+via,ty+via))
        merged["metal4"].append((sx-40,ty-40,sx+40,ty+40))
        merged["metal5"].append((min(sx,tx),ty-40,max(sx,tx),ty+40))
        merged["via4"].append((tx-via,ty-via,tx+via,ty+via))
        merged["metal4"].append((tx-40,ty-40,tx+40,ty+40))
        merged["via3"].append((tx-via,ty-via,tx+via,ty+via))
        merged["metal3"].append((tx-40,ty-40,tx+40,ty+40))

    mag = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in merged.items():
        mag.append(f"<< {layer} >>")
        mag.extend("rect " + " ".join(map(str,r)) for r in rects)
    mag.append("<< labels >>")
    port=1
    # Keep all capacitor-array ports as debug/module pins. The matched
    # PLATE_ names on both macros form one physical net after routing.
    for layer, box, name in array_labels:
        x1,y1,x2,y2=box
        mag += [f"rlabel {layer} s {x1} {y1} {x2} {y2} 4 {name}", f"port {port} nsew"]
        port += 1
    for layer, box, name in bank_labels:
        if name.startswith("PLATE_B"):
            continue
        x1,y1,x2,y2=box
        mag += [f"rlabel {layer} s {x1+bank_x} {y1} {x2+bank_x} {y2} 4 {name}", f"port {port} nsew"]
        port += 1
    mag += ["<< end >>", ""]
    (OUT / f"{CELL}.mag").write_text("\n".join(mag), encoding="ascii")

    tcl = "\n".join([f"load {CELL}", "drc check", "drc count", "extract all",
        "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
        "ext2spice cthresh 0", "ext2spice rthresh infinite", f"ext2spice -o {CELL}_pex.spice",
        f"gds write {CELL}.gds", "save", "quit -noprompt", ""])
    log=docker("magic",["-dnull","-noconsole","-rcfile",RC],tcl)
    (OUT/"magic_extract.log").write_text(log,encoding="utf-8")
    drc=re.search(r"Total DRC errors found: (\d+)",log)
    if not drc or drc.group(1)!="0":
        raise RuntimeError("Integrated trim-top DRC failed:\n"+log[-5000:])

    ext=(OUT/f"{CELL}.spice").read_text(encoding="ascii")
    top_pins=parse_pins(OUT/f"{CELL}.spice",CELL)
    array_pins=parse_pins(ARRAY_DIR/f"{ARRAY}.spice",ARRAY)
    bank_pins=parse_pins(BANK_DIR/f"{BANK}.spice",BANK)
    # Hierarchical LVS reference: cap-array plates and selector outputs are
    # connected by identical net names, with extracted top pin order retained.
    ref=[(ARRAY_DIR/f"{ARRAY}.spice").read_text(encoding="ascii"),
         (BANK_DIR/f"{BANK}.spice").read_text(encoding="ascii"),
         f".subckt {CELL} {' '.join(top_pins)}"]
    ref.append("XARRAY " + " ".join(array_pins) + f" {ARRAY}")
    bank_nodes=[]
    for pin in bank_pins:
        m=re.fullmatch(r"PLATE_B(\d+)",pin)
        bank_nodes.append(ordered_caps[int(m.group(1))] if m else pin)
    ref.append("XBANK " + " ".join(bank_nodes) + f" {BANK}")
    ref.append(f".ends {CELL}")
    (OUT/"reference.spice").write_text("\n".join(ref)+"\n",encoding="ascii")
    setup="/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs=docker("netgen-lvs",["-batch","lvs",f"{CELL}.spice {CELL}",f"reference.spice {CELL}",setup,"lvs.out"])
    (OUT/"netgen_lvs.log").write_text(lvs,encoding="utf-8")
    if "Circuits match uniquely." not in lvs:
        raise RuntimeError("Integrated trim-top LVS failed:\n"+lvs[-6000:])

    ruby=OUT/"inspect_gds.rb"
    ruby.write_text("include RBA\nl=Layout.new\n"+f"l.read('/workspace/{(OUT/(CELL+'.gds')).relative_to(ROOT).as_posix()}')\n"+
        f"c=l.cell('{CELL}')\nb=c.bbox\n"+'puts "bbox_um=#{(b.width*l.dbu).round(4)}x#{(b.height*l.dbu).round(4)}"\n',encoding="ascii")
    geom=docker("klayout",["-b","-r",f"/workspace/{ruby.relative_to(ROOT).as_posix()}"],timeout=120)
    (OUT/"klayout_geometry.log").write_text(geom,encoding="utf-8")
    bbox=re.search(r"bbox_um=([0-9.]+)x([0-9.]+)",geom)
    if not bbox: raise RuntimeError("Integrated GDS bbox unavailable:\n"+geom[-1500:])
    report={"cell":CELL,"weighted_mim_cells":1020,"selector_bits":32,"selector_transmission_gates":96,
        "physical_plate_routes":32,"plate_route_layers":"M2-to-M4 riser, M5 row strap, M3 MIM bus",
        "magic_drc_zero":True,"netgen_unique_match":True,"gds_written":(OUT/f"{CELL}.gds").is_file(),
        "gds_bbox_um":[float(bbox.group(1)),float(bbox.group(2))],
        "pex_coupling_capacitors":len(re.findall(r"(?im)^C\S+\s",(OUT/f"{CELL}_pex.spice").read_text(encoding="ascii"))),
        "scope":"Integrated weighted MIM trim array and physically routed plate selectors, with external rails and independent controls. No decoder, calibration sequencer, mismatch/noise or readout integration yet."}
    (OUT/"qualification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
