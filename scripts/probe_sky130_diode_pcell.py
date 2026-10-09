"""Build and qualify a SKY130 P+ to N-well update diode primitive."""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_diode_pd2nw_05v5_probe_1x1"
IMAGE = "eventspikeseg:analog-layout"
RCFILE = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "diode_pd2nw_05v5_probe"


def run_magic(script: str) -> str:
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
         "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
         "-w", f"/workspace/{OUT.relative_to(ROOT).as_posix()}",
         "--entrypoint", "magic", IMAGE, "-dnull", "-noconsole", "-rcfile", RCFILE],
        input=script, capture_output=True, text=True, timeout=240, cwd=ROOT)
    log = proc.stdout + proc.stderr
    if proc.returncode:
        raise RuntimeError(f"Magic failed: {log[-3000:]}")
    return log


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diode_raw.mag").write_text(
        "magic\ntech sky130A\nmagscale 1 2\ntimestamp 0\n<< checkpaint >>\n<< end >>\n",
        encoding="ascii")
    generated = run_magic("\n".join([
        "load diode_raw",
        "magic::gencell sky130::sky130_fd_pr__diode_pd2nw_05v5 diode -spice w 1 l 1",
        "save", "writeall force", "quit -noprompt", "",
    ]))
    (OUT / "magic_generate.log").write_text(generated, encoding="utf-8")
    cells = sorted(OUT.glob("sky130_fd_pr__diode_pd2nw_05v5_*.mag"),
                   key=lambda path: path.stat().st_mtime)
    if not cells:
        raise RuntimeError("diode PCell did not produce a saved MAG cell")
    mag_text = cells[-1].read_text(encoding="ascii")
    labels = ("<< labels >>\n"
              "rlabel metal1 s 44 -10 50 10 4 ANODE\nport 1 nsew\n"
              "rlabel locali s 60 84 90 100 4 CATHODE\nport 2 nsew\n"
              "rlabel psubdiff s 153 -10 170 10 4 SUB\nport 3 nsew\n")
    mag_text = mag_text.replace("<< end >>", labels + "<< end >>")
    (OUT / f"{CELL}.mag").write_text(mag_text, encoding="ascii")
    extracted = run_magic("\n".join([
        f"load {CELL}", "drc check", "drc count", "extract all",
        "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
        f"gds write {CELL}.gds", "save", "quit -noprompt", "",
    ]))
    (OUT / "magic_extract.log").write_text(extracted, encoding="utf-8")
    spice = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    ref = OUT / "diode_reference.spice"
    ref.write_text(".subckt diode_reference ANODE CATHODE SUB\n"
                   "D0 ANODE CATHODE sky130_fd_pr__diode_pd2nw_05v5 area=1 pj=4\n"
                   ".ends\n", encoding="ascii")
    cmd = ["docker", "run", "--rm", "-v", f"{ROOT}:/workspace",
           "-w", f"/workspace/{OUT.relative_to(ROOT).as_posix()}",
           "--entrypoint", "netgen-lvs", IMAGE, "-batch", "lvs",
           f"{CELL}.spice {CELL}", "diode_reference.spice diode_reference",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl",
           "diode_lvs.out"]
    lvs = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=ROOT)
    lvs_log = lvs.stdout + lvs.stderr
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    drc_zero = "Total DRC errors found: 0" in extracted
    lvs_unique = lvs.returncode == 0 and "Result: Circuits match uniquely." in lvs_log
    if not drc_zero or not lvs_unique:
        raise RuntimeError(f"diode DRC/LVS failed: drc_zero={drc_zero} lvs_tail={lvs_log[-1200:]}")
    if not re.search(r"(?im)^D\S+\s+ANODE\s+CATHODE\s+sky130_fd_pr__diode_pd2nw_05v5\b", spice):
        raise RuntimeError("extracted diode does not match labeled terminal order")
    pex_log = run_magic("\n".join([
        f"load {CELL}", "extract all", "ext2spice lvs", "ext2spice scale off",
        "ext2spice cthresh 0", f"ext2spice -o {CELL}_pex.spice",
        "quit -noprompt", "",
    ]))
    (OUT / "magic_pex.log").write_text(pex_log, encoding="utf-8")
    pex_path = OUT / f"{CELL}_pex.spice"
    pex = pex_path.read_text(encoding="ascii")
    top = re.search(r"(?im)^\.subckt\s+\S+\s+(.+)$", pex)
    if not top or set(top.group(1).split()) != {"ANODE", "CATHODE", "SUB"}:
        raise RuntimeError(f"unexpected extracted diode interface: {top.group(1) if top else 'none'}")
    inspect = OUT / "inspect_bbox.rb"
    inspect.write_text("\n".join([
        "include RBA", "layout=Layout.new",
        f"layout.read('/workspace/{(OUT / (CELL + '.gds')).relative_to(ROOT).as_posix()}')",
        f"box=layout.cell('{CELL}').bbox",
        'puts "bbox_um=#{box.width*layout.dbu}x#{box.height*layout.dbu}"', "",
    ]), encoding="ascii")
    bbox_proc = subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "--entrypoint", "klayout",
         IMAGE, "-b", "-r", f"/workspace/{inspect.relative_to(ROOT).as_posix()}"],
        capture_output=True, text=True, timeout=120, cwd=ROOT)
    bbox_log = bbox_proc.stdout + bbox_proc.stderr
    match = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", bbox_log)
    if bbox_proc.returncode or not match:
        raise RuntimeError(f"missing diode GDS bounding box: {bbox_log[-1500:]}")
    gds = OUT / f"{CELL}.gds"
    report = {
        "cell": CELL, "device": "sky130_fd_pr__diode_pd2nw_05v5",
        "magic_drc_zero": drc_zero, "netgen_lvs_unique_match": lvs_unique,
        "ports_in_extracted_order": top.group(1).split(), "drawn_pplus_area_um2": 1.0,
        "drawn_pplus_perimeter_um": 4.0,
        "nwell_bbox_um": [2.38, 2.38],
        "estimated_nwell_area_um2_from_mag_rectangle": 2.38 * 2.38,
        "estimated_nwell_perimeter_um_from_mag_rectangle": 4 * 2.38,
        "gds_bbox_um": [float(match.group(1)), float(match.group(2))],
        "pex_explicit_capacitors": len(re.findall(r"(?im)^C\S+\s", pex)),
        "pex_has_explicit_substrate_port": bool(re.search(r"(?im)^\.subckt\s+\S+\s+.*\bSUB\b", pex)),
        "sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in (gds, OUT / f"{CELL}.spice", pex_path)},
        "limitations": "Standalone diode PCell only. Nwell-to-substrate area is inferred from MAG rectangle, not an extracted junction. No programming, addressing, array routing, local noise/mismatch or full PLIF qualification.",
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
