#!/usr/bin/env python3
"""Build a deep-n-well SKY130 TG body-access layout probe."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from build_sky130_transmission_gate_flat import parse


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_body_tied_transmission_gate"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
SETUP = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
CELL = "sky130_body_tied_transmission_gate"
TOP = CELL + "_raw"
NF = ROOT / "artifacts/analog_asic/layout/sky130_tg_pcell/sky130_fd_pr__nfet_01v8_648S5X.mag"
PF = ROOT / "artifacts/analog_asic/layout/sky130_tg_pcell/sky130_fd_pr__pfet_01v8_XGAKDL.mag"


def run(entrypoint: str, args: list[str], stdin: str | None = None) -> str:
    cmd = ["docker", "run", "--rm"]
    if stdin is not None:
        cmd.append("-i")
    cmd += ["--volume", f"{ROOT}:/workspace", "--env",
            "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
            "--workdir", f"/workspace/{OUT.relative_to(ROOT).as_posix()}",
            "--entrypoint", entrypoint, IMAGE, *args]
    proc = subprocess.run(cmd, input=stdin, text=True, capture_output=True, timeout=180, cwd=ROOT)
    log = proc.stdout + proc.stderr
    if proc.returncode:
        raise RuntimeError(f"{entrypoint} failed: {log[-4000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    layers = parse(NF, 0)
    for layer, rects in parse(PF, 2200).items():
        layers.setdefault(layer, []).extend(rects)
    # Low-voltage NFET p-well in a deep n-well. PFET is shifted beyond it so
    # the two independent wells do not merge. The DNW contact is a port, not
    # a complete external bias route or guard ring; no signoff is claimed.
    layers.setdefault("dnwell", []).append((-550, -650, 550, 650))
    # A separated n-well strip overlaps the deep n-well and carries its bias
    # contact. The p-well body tap inside the NFET PCell remains independent.
    layers.setdefault("nwell", []).append((-700, -650, -300, 650))
    layers.setdefault("nsubdiff", []).append((-550, -100, -400, 100))
    layers.setdefault("nsubdiffcont", []).append((-520, -50, -430, 50))
    layers.setdefault("locali", []).append((-550, -100, -400, 100))
    layers.setdefault("metal1", []).extend((
        (-54, 88, -34, 2112),
        (34, -100, 54, 2412),
        (-15, 172, 15, 300),
        (-15, 2481, 15, 2600),
    ))
    mag = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in layers.items():
        mag.append(f"<< {layer} >>")
        mag.extend("rect " + " ".join(map(str, rect)) for rect in rects)
    mag += ["<< labels >>",
            "rlabel metal1 s -54 1300 -34 1330 4 A", "port 1 nsew",
            "rlabel metal1 s 34 1300 54 1330 4 B", "port 2 nsew",
            "rlabel metal1 s -15 280 15 310 4 EN", "port 3 nsew",
            "rlabel metal1 s -15 2580 15 2610 4 ENB", "port 4 nsew",
            "rlabel psubdiff s -120 250 -100 265 4 BULKN", "port 5 nsew",
            "rlabel nsubdiff s -120 2555 -100 2570 4 BULKP", "port 6 nsew",
            "rlabel nsubdiff s -500 -20 -450 20 4 DNW", "port 7 nsew",
            "<< end >>", ""]
    (OUT / f"{TOP}.mag").write_text("\n".join(mag), encoding="ascii")
    magic_args = ["-dnull", "-noconsole", "-rcfile", RC]
    tcl = "\n".join((f"load {TOP}", "drc check", "drc count", "extract all",
                     "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
                     f"gds write {CELL}.gds", "save", "quit -noprompt", ""))
    log = run("magic", magic_args, tcl)
    (OUT / "magic_extract.log").write_text(log, encoding="utf-8")
    match = re.search(r"Total DRC errors found: (\d+)", log)
    if not match:
        raise RuntimeError(f"Magic did not report DRC: {log[-4000:]}")
    report = {"cell": TOP, "magic_drc_count": int(match.group(1)),
              "gds_exists": (OUT / f"{CELL}.gds").is_file(),
              "source_nf": str(NF.relative_to(ROOT)).replace("\\", "/"),
              "source_pf": str(PF.relative_to(ROOT)).replace("\\", "/"),
              "deep_nwell_rect_magic_units": [-550, -650, 550, 650],
              "deep_nwell_tap": "separate n-well strip and N+ contact labeled DNW",
              "scope": "Deep-n-well-painted low-voltage NFET plus separated PFET TG physical probe. DNW tap exists; external bias routing and full DRC/guard-ring qualification remain open."}
    spice_path = OUT / f"{CELL}.spice"
    if spice_path.is_file():
        spice = spice_path.read_text(encoding="ascii")
        sub = re.search(r"(?im)^\.subckt\s+(\S+)\s+([^\n]+)", spice)
        report["extracted_subckt_ports"] = sub.group(2).split() if sub else None
        report["extracted_device_count"] = len(re.findall(r"(?im)^X\S+\s", spice))
    (OUT / "qualification_probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["magic_drc_count"] != 0 or not spice_path.is_file():
        print(json.dumps(report, indent=2))
        return 2
    reference = OUT / "reference.spice"
    reference.write_text(
        f".subckt {TOP} A B EN ENB BULKP BULKN DNW\n"
        "Xn B EN A BULKN sky130_fd_pr__nfet_01v8 w=1 l=0.15\n"
        "Xp B ENB A BULKP sky130_fd_pr__pfet_01v8 w=2 l=0.15\n"
        f".ends {TOP}\n", encoding="ascii")
    lvs_log = run("netgen-lvs", ["-batch", "lvs", f"{CELL}.spice {TOP}",
                                 f"{reference.name} {TOP}", SETUP, "lvs.out"])
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    report["netgen_lvs_unique"] = "Circuits match uniquely" in lvs_log
    pex_tcl = "\n".join((f"load {TOP}", "extract all", "ext2spice lvs",
                         "ext2spice scale off", "ext2spice cthresh 0",
                         "ext2spice rthresh infinite", f"ext2spice -o {CELL}_pex.spice",
                         "quit -noprompt", ""))
    pex_log = run("magic", magic_args, pex_tcl)
    (OUT / "magic_pex.log").write_text(pex_log, encoding="utf-8")
    pex = (OUT / f"{CELL}_pex.spice").read_text(encoding="ascii")
    report["pex_capacitor_count"] = len(re.findall(r"(?im)^C\S+\s", pex))
    report["pex_body_coupling_lines"] = [line for line in pex.splitlines()
                                          if line.startswith("C") and ("BULKN" in line or "BULKP" in line)]
    ruby = OUT / "inspect_bbox.rb"
    ruby.write_text("include RBA\nl=Layout.new\n"
                    f"l.read('/workspace/{(OUT / (CELL + '.gds')).relative_to(ROOT).as_posix()}')\n"
                    f"c=l.cell('{TOP}')\nb=c.bbox\n"
                    'puts "bbox_um=#{(b.width*l.dbu).round(4)}x#{(b.height*l.dbu).round(4)}"\n',
                    encoding="ascii")
    bbox_log = run("klayout", ["-b", "-r", f"/workspace/{ruby.relative_to(ROOT).as_posix()}"])
    bbox = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", bbox_log)
    report["gds_bbox_um"] = [float(bbox.group(1)), float(bbox.group(2))] if bbox else None
    report["scope"] = ("Magic DRC0 and Netgen LVS for a deep-n-well-painted NFET plus separate PFET. "
                       "DNW tap is a separate port; external DNW bias and body-to-state metal routing, "
                       "guard-ring/full-foundry DRC, junction leakage extraction and integrated MIM hold remain open.")
    (OUT / "qualification_probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["netgen_lvs_unique"] or not report["gds_bbox_um"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
