"""Place and qualify a routed differential pair of SKY130 MIM state banks."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_differential_mim_state_pair"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "sky130_differential_mim_state_pair"
TOP = CELL + "_raw"
CHILD = "mim_state_square_3x4_w30_l30"


def docker(entrypoint: str, args: list[str], *, stdin: str | None = None,
           timeout: int = 180, workdir: str | None = None) -> str:
    cmd = ["docker", "run", "--rm"]
    if stdin is not None:
        cmd.append("-i")
    cmd += ["-v", f"{ROOT}:/workspace", "-e",
            "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root"]
    if workdir:
        cmd += ["-w", workdir]
    cmd += ["--entrypoint", entrypoint, IMAGE, *args]
    p = subprocess.run(cmd, input=stdin, text=True, capture_output=True,
                       timeout=timeout, cwd=ROOT)
    log = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f"{entrypoint} failed ({p.returncode}):\n{log[-5000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "artifacts/analog_asic/layout/sky130_mim_state_bank_square" / f"{CHILD}.mag"
    if not source.is_file():
        raise FileNotFoundError(source)
    (OUT / f"{CHILD}.mag").write_bytes(source.read_bytes())

    # Flatten the two already-qualified cap banks into one .mag. This avoids
    # depending on hierarchy pin promotion for the common-plate connection.
    sections: dict[str, list[tuple[int, int, int, int]]] = {}
    section: str | None = None
    for line in source.read_text(encoding="ascii").splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            section = line[3:-3]
            continue
        if section and section not in {"labels", "end", "checkpaint", "properties"} and line.startswith("rect "):
            x1, y1, x2, y2 = map(int, line.split()[1:])
            sections.setdefault(section, []).append((x1, y1, x2, y2))
    left_dx, right_dx = -15000, 15000
    raw = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in sections.items():
        raw.append(f"<< {layer} >>")
        for x1, y1, x2, y2 in rects:
            raw.append(f"rect {x1 + left_dx} {y1} {x2 + left_dx} {y2}")
            raw.append(f"rect {x1 + right_dx} {y1} {x2 + right_dx} {y2}")
    raw += ["<< metal3 >>", "rect -26200 -17100 4000 -16900", "<< labels >>",
            "rlabel metal5 s -15100 6310 -14900 6390 4 MEM_P", "port 1 nsew",
            "rlabel metal5 s 14900 6310 15100 6390 4 MEM_N", "port 2 nsew",
            "rlabel metal3 s -100 -17040 100 -16960 4 VCM", "port 3 nsew",
            "<< end >>", ""]
    (OUT / f"{CELL}_raw.mag").write_text("\n".join(raw), encoding="ascii")
    build = "\n".join([f"load {CELL}_raw", "save", "quit -noprompt", ""])
    build_log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC],
                       stdin=build, workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    if "No cell" in build_log or "Couldn't find label" in build_log:
        raise RuntimeError(f"Magic failed to place/connect state banks:\n{build_log[-3000:]}")
    (OUT / "magic_build.log").write_text(build_log, encoding="utf-8")

    verify = "\n".join([f"load {CELL}_raw", "drc check", "drc count", "extract all",
                        "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
                        f"gds write {CELL}.gds", "save", "quit -noprompt", ""])
    verify_log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC],
                        stdin=verify, workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "magic_extract.log").write_text(verify_log, encoding="utf-8")
    drc = re.search(r"Total DRC errors found: (\d+)", verify_log)
    if not drc or drc.group(1) != "0":
        raise RuntimeError(f"Composite state-pair DRC did not pass:\n{verify_log[-5000:]}")

    netlist = OUT / f"{CELL}.spice"
    spice = netlist.read_text(encoding="ascii")
    header = re.search(rf"(?im)^\.subckt\s+{TOP}(.*)$", spice)
    if not header:
        raise RuntimeError(f"Could not find extracted top subcircuit:\n{spice[:2000]}")
    ports = header.group(1).split()
    if ports != ["MEM_P", "MEM_N", "VCM"]:
        raise RuntimeError(f"Unexpected extracted ports {ports}; expected MEM_P MEM_N VCM")
    (OUT / "reference.spice").write_text(
        f".subckt {TOP} MEM_P MEM_N VCM\n" +
        "\n".join([f"XLP{i} MEM_P VCM sky130_fd_pr__cap_mim_m3_2 w=30 l=30" for i in range(12)] +
                   [f"XLN{i} MEM_N VCM sky130_fd_pr__cap_mim_m3_2 w=30 l=30" for i in range(12)]) +
        f"\n.ends {TOP}\n",
        encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs = docker("netgen-lvs", ["-batch", "lvs",
                                f"{CELL}.spice {TOP}", f"reference.spice {TOP}",
                                setup, "lvs.out"],
                 workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely." not in lvs:
        raise RuntimeError(f"Netgen LVS did not uniquely match:\n{lvs[-5000:]}")

    pex_cmd = "\n".join([f"load {CELL}_raw", "extract all", "ext2spice lvs",
                          "ext2spice scale off", "ext2spice cthresh 0",
                          "ext2spice rthresh infinite", f"ext2spice -o {CELL}_pex.spice",
                          "quit -noprompt", ""])
    pex_log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC],
                     stdin=pex_cmd, workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "magic_pex.log").write_text(pex_log, encoding="utf-8")
    pex = (OUT / f"{CELL}_pex.spice").read_text(encoding="ascii")
    caps = len(re.findall(r"(?im)^C\S+\s", pex))

    ruby = OUT / "inspect_gds.rb"
    ruby.write_text(
        "include RBA\nl=Layout.new\n"
        f"l.read('/workspace/{(OUT / (CELL + '.gds')).relative_to(ROOT).as_posix()}')\n"
        f"c=l.cell('{CELL}_raw')\nb=c.bbox\n"
        'puts "bbox_um=#{(b.width*l.dbu).round(4)}x#{(b.height*l.dbu).round(4)}"\n',
        encoding="ascii")
    inspect_log = docker("klayout", ["-b", "-r",
                                     f"/workspace/{ruby.relative_to(ROOT).as_posix()}"],
                         workdir="/workspace")
    (OUT / "klayout_geometry.log").write_text(inspect_log, encoding="utf-8")
    bbox = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", inspect_log)
    if not bbox:
        raise RuntimeError(f"Could not read GDS geometry:\n{inspect_log[-2000:]}")
    report = {
        "cell": CELL, "ports": ports, "state_capacitor_banks": 2,
        "state_cap_bank_cell": CHILD, "state_cap_bank_copies_per_rail": 1,
        "shared_plate_net": "VCM", "magic_drc_zero": True,
        "netgen_lvs_unique": True, "gds_written": (OUT / f"{CELL}.gds").is_file(),
        "gds_bbox_um": [float(bbox.group(1)), float(bbox.group(2))],
        "pex_coupling_capacitors": caps,
        "wire_resistance_extraction": False,
        "scope": "Routed paired MIM state-capacitor layout; state reset, packet injection switches, readout, mismatch/noise and PLIF behavior are outside this macro.",
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
