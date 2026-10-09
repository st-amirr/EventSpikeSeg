"""Route a differential five-unit/rail SKY130 MIM read-capacitor bank."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/analog_asic"
SOURCE = ART / "layout/sky130_mim_membrane_10x10_m3_2/membrane_cap_mim_10x10um.mag"
OUT = ART / "layout/sky130_shared_read_mim_bank_5x10x10"
CELL = "shared_read_mim_bank_5x10x10"
PDK = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A"
RC = f"{PDK}/libs.tech/magic/sky130A.magicrc"
IMAGE = "eventspikeseg:analog-layout"
COUNT = 5
Y_PITCH = 2600
X_PITCH = 4000


def docker(entrypoint: str, args: list[str], *, stdin: str | None = None) -> str:
    command = ["docker", "run", "--rm"]
    if stdin is not None:
        command.append("-i")
    command += ["-v", f"{ROOT}:/workspace", "-e", f"PDK_ROOT={PDK}",
                "-w", f"/workspace/{OUT.relative_to(ROOT).as_posix()}",
                "--entrypoint", entrypoint, IMAGE, *args]
    done = subprocess.run(command, input=stdin, capture_output=True, text=True,
                          timeout=240, cwd=ROOT)
    log = done.stdout + done.stderr
    if done.returncode:
        raise RuntimeError(f"{entrypoint} failed ({done.returncode}): {log[-4000:]}")
    return log


def source_shapes() -> dict[str, list[tuple[int, int, int, int]]]:
    shapes: dict[str, list[tuple[int, int, int, int]]] = {}
    layer: str | None = None
    for row in SOURCE.read_text(encoding="ascii").splitlines():
        if row.startswith("<< ") and row.endswith(" >>"):
            layer = row[3:-3]
            if layer in ("labels", "end"):
                layer = None
            elif layer not in shapes:
                shapes[layer] = []
        elif layer is not None and row.startswith("rect "):
            shapes[layer].append(tuple(map(int, row.split()[1:])))
    if "mimcap2contact" not in shapes or "metal5" not in shapes:
        raise RuntimeError("unexpected source MIM geometry")
    return shapes


def create_layout() -> None:
    shapes: dict[str, list[tuple[int, int, int, int]]] = {}
    for layer, rects in source_shapes().items():
        dest = shapes.setdefault(layer, [])
        for xoff in (0, X_PITCH):
            for index in range(COUNT):
                yoff = index * Y_PITCH
                dest.extend((x1 + xoff, y1 + yoff, x2 + xoff, y2 + yoff)
                            for x1, y1, x2, y2 in rects)
    m5 = shapes["metal5"]
    for xoff in (0, X_PITCH):
        # The inner M5 rim contacts the top MIM plate; the outer M5/via4
        # ring contacts the bottom. Keep these two vertical buses separate.
        m5.append((100 + xoff, 140, 160 + xoff, (COUNT - 1) * Y_PITCH + 2084))
        m5.append((2480 + xoff, -100, 2560 + xoff, (COUNT - 1) * Y_PITCH + 2201))
    m5.append((2480, -100, X_PITCH + 2560, -20))
    rows = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in shapes.items():
        rows.append(f"<< {layer} >>")
        rows.extend("rect " + " ".join(map(str, rect)) for rect in rects)
    rows += ["<< labels >>",
             "rlabel metal5 s 100 500 160 580 4 READP", "port 1 nsew",
             f"rlabel metal5 s {X_PITCH+100} 500 {X_PITCH+160} 580 4 READN", "port 2 nsew",
             "rlabel metal5 s 2480 500 2560 580 4 VCM", "port 3 nsew",
             "<< end >>", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{CELL}.mag").write_text("\n".join(rows), encoding="ascii")


def main() -> None:
    create_layout()
    tcl = "\n".join([f"load {CELL}", "drc check", "drc count", "extract all",
                     "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
                     f"gds write {CELL}.gds", "save", "quit -noprompt", ""])
    log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC], stdin=tcl)
    (OUT / "magic_build.log").write_text(log, encoding="utf-8")
    if "Total DRC errors found: 0" not in log:
        raise RuntimeError(f"bank DRC failed: {log[-3000:]}")
    reference = OUT / "reference.spice"
    devices = [f"X{side}{index} {side} VCM sky130_fd_pr__cap_mim_m3_2 w=10 l=10"
               for side in ("READP", "READN") for index in range(COUNT)]
    reference.write_text(".subckt reference READP READN VCM\n" + "\n".join(devices)
                         + "\n.ends reference\n", encoding="ascii")
    lvs = docker("netgen-lvs", ["-batch", "lvs", f"{CELL}.spice {CELL}",
                                "reference.spice reference",
                                f"{PDK}/libs.tech/netgen/sky130A_setup.tcl", "lvs.out"])
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely." not in lvs:
        raise RuntimeError(f"bank LVS failed: {lvs[-4000:]}")
    pex_tcl = "\n".join([f"load {CELL}", "extract all", "ext2spice lvs",
                         "ext2spice scale off", "ext2spice cthresh 0",
                         f"ext2spice -o {CELL}_pex.spice", "quit -noprompt", ""])
    pex_log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC], stdin=pex_tcl)
    (OUT / "magic_pex.log").write_text(pex_log, encoding="utf-8")
    pex = (OUT / f"{CELL}_pex.spice").read_text(encoding="ascii")
    spice = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    top = re.search(r"(?im)^\.subckt\s+\S+\s+(.+)$", spice)
    if not top or top.group(1).split() != ["READP", "READN", "VCM"]:
        raise RuntimeError(f"unexpected bank ports: {top.group(1) if top else 'none'}")
    if len(re.findall(r"(?im)^X\S+\s+.*sky130_fd_pr__cap_mim_m3_2", spice)) != 10:
        raise RuntimeError("extracted MIM device count is not 10")
    inspect = OUT / "inspect_bbox.rb"
    inspect.write_text("\n".join(["include RBA", "layout=Layout.new",
                                   f"layout.read('/workspace/{(OUT / (CELL + '.gds')).relative_to(ROOT).as_posix()}')",
                                   f"box=layout.cell('{CELL}').bbox",
                                   'puts "bbox_um=#{box.width*layout.dbu}x#{box.height*layout.dbu}"', ""]),
                       encoding="ascii")
    bbox_log = docker("klayout", ["-b", "-r", f"/workspace/{inspect.relative_to(ROOT).as_posix()}"])
    bbox = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", bbox_log)
    if not bbox:
        raise RuntimeError(f"missing bank bbox: {bbox_log[-2000:]}")
    report = {
        "cell": CELL, "magic_drc_zero": True, "netgen_lvs_unique_match": True,
        "physical_mim_units_per_rail": COUNT, "total_physical_mim_units": 2 * COUNT,
        "unit_geometry_um": [10, 10], "ports": ["READP", "READN", "VCM"],
        "gds_bbox_um": [float(bbox.group(1)), float(bbox.group(2))],
        "pex_explicit_capacitors": len(re.findall(r"(?im)^C\S+\s", pex)),
        "scope": "Routed shared read MIM capacitor bank; no selectors, sensor, calibration, noise, or full 5ms service qualification.",
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
