"""Place and qualify a differential SKY130 trim MIM cap pair."""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_differential_trim_cap_pair"
CELL = "sky130_differential_trim_cap_pair"
UNIT = "packet_cap_mim_2x2um"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"

def docker(entrypoint: str, args: list[str], *, stdin: str | None = None,
           timeout: int = 180, workdir: str | None = None) -> str:
    command = ["docker", "run", "--rm"]
    if stdin is not None: command.append("-i")
    command += ["-v", f"{ROOT}:/workspace", "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root"]
    if workdir: command += ["-w", workdir]
    command += ["--entrypoint", entrypoint, IMAGE, *args]
    result = subprocess.run(command, input=stdin, text=True, capture_output=True, timeout=timeout, cwd=ROOT)
    log = result.stdout + result.stderr
    if result.returncode: raise RuntimeError(f"{entrypoint} failed ({result.returncode}):\n{log[-5000:]}")
    return log

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "artifacts/analog_asic/layout/sky130_mim_packet_2x2" / f"{UNIT}.mag"
    sections: dict[str, list[tuple[int, int, int, int]]] = {}
    section = None
    for line in source.read_text(encoding="ascii").splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            section = line[3:-3]; continue
        if section and section not in {"labels", "end", "checkpaint", "properties"} and line.startswith("rect "):
            x1, y1, x2, y2 = map(int, line.split()[1:])
            sections.setdefault(section, []).append((x1, y1, x2, y2))
    offsets = {"p": -1800, "n": 1800}
    lines = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in sections.items():
        lines.append(f"<< {layer} >>")
        for x1, y1, x2, y2 in rects:
            for dx in offsets.values(): lines.append(f"rect {x1+dx} {y1} {x2+dx} {y2}")
    lines += ["<< labels >>", "rlabel mimcap2 s -1650 470 -1350 490 4 TRIM_P", "port 1 nsew",
              "rlabel metal4 s -1600 565 -1400 585 4 STATE_P", "port 2 nsew",
              "rlabel mimcap2 s 1950 470 2250 490 4 TRIM_N", "port 3 nsew",
              "rlabel metal4 s 2000 565 2200 585 4 STATE_N", "port 4 nsew", "<< end >>", ""]
    (OUT / f"{CELL}.mag").write_text("\n".join(lines), encoding="ascii")
    verify = "\n".join([f"load {CELL}", "drc check", "drc count", "extract all", "ext2spice lvs",
                        "ext2spice scale off", f"ext2spice -o {CELL}.spice",
                        f"gds write {CELL}.gds", "save", "quit -noprompt", ""])
    log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC], stdin=verify,
                 workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "magic_extract.log").write_text(log, encoding="utf-8")
    drc = re.search(r"Total DRC errors found: (\d+)", log)
    if not drc or drc.group(1) != "0": raise RuntimeError(f"DRC failed:\n{log[-5000:]}")
    extracted = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    match = re.search(rf"(?im)^\.subckt\s+{CELL}(.*)$", extracted)
    ports = match.group(1).split() if match else []
    expected_ports = ["TRIM_P", "STATE_P", "TRIM_N", "STATE_N"]
    if ports != expected_ports: raise RuntimeError(f"Unexpected extracted pins {ports}")
    (OUT / "reference.spice").write_text(
        f".subckt {CELL} TRIM_P STATE_P TRIM_N STATE_N\n"
        "XCP TRIM_P STATE_P sky130_fd_pr__cap_mim_m3_2 w=2 l=2\n"
        "XCN TRIM_N STATE_N sky130_fd_pr__cap_mim_m3_2 w=2 l=2\n"
        f".ends {CELL}\n", encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs = docker("netgen-lvs", ["-batch", "lvs", f"{CELL}.spice {CELL}", f"reference.spice {CELL}", setup, "lvs.out"],
                 workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely." not in lvs: raise RuntimeError(f"LVS failed:\n{lvs[-4000:]}")
    pex_cmd = "\n".join([f"load {CELL}", "extract all", "ext2spice lvs", "ext2spice scale off",
                          "ext2spice cthresh 0", "ext2spice rthresh infinite",
                          f"ext2spice -o {CELL}_pex.spice", "quit -noprompt", ""])
    pex_log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC], stdin=pex_cmd,
                     workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "magic_pex.log").write_text(pex_log, encoding="utf-8")
    ruby = OUT / "inspect_gds.rb"
    ruby.write_text("include RBA\nl=Layout.new\n" +
                    f"l.read('/workspace/{(OUT / (CELL + '.gds')).relative_to(ROOT).as_posix()}')\n" +
                    f"c=l.cell('{CELL}')\nb=c.bbox\n" +
                    'puts "bbox_um=#{(b.width*l.dbu).round(4)}x#{(b.height*l.dbu).round(4)}"\n', encoding="ascii")
    geometry = docker("klayout", ["-b", "-r", f"/workspace/{ruby.relative_to(ROOT).as_posix()}"], timeout=90, workdir="/workspace")
    (OUT / "klayout_geometry.log").write_text(geometry, encoding="utf-8")
    bbox = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", geometry)
    if not bbox: raise RuntimeError(f"GDS inspection failed:\n{geometry[-2000:]}")
    report = {"cell": CELL, "ports": ports, "unit_capacitance_f": 9.52e-15,
              "unit_geometry_um": [2, 2], "unit_count": 2, "magic_drc_zero": True,
              "netgen_unique_match": True, "gds_written": (OUT / f"{CELL}.gds").is_file(),
              "gds_bbox_um": [float(bbox.group(1)), float(bbox.group(2))],
              "scope": "Two extracted differential trim MIM cells only; no switch, decoder, weighted array or latch."}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
