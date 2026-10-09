#!/usr/bin/env python3
"""Probe Magic DRC/extraction of an isolated SKY130 low-voltage NFET."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from build_sky130_transmission_gate_flat import parse


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_isolated_nfet_probe"
SOURCE = ROOT / "artifacts/analog_asic/layout/sky130_tg_pcell/sky130_fd_pr__nfet_01v8_648S5X.mag"
TOP = "sky130_isolated_nfet_probe"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    layers = parse(SOURCE, 0)
    # Magic unit is 5nm. The isolated p-well remains the PCell's own well;
    # deep n-well surrounds it. A surrounding n-well/tap is added only after
    # inspecting the initial DRC and extracted topology.
    layers.setdefault("dnwell", []).append((-550, -650, 550, 650))
    mag = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in layers.items():
        mag.append(f"<< {layer} >>")
        mag.extend("rect " + " ".join(map(str, rect)) for rect in rects)
    mag.extend(("<< end >>", ""))
    (OUT / f"{TOP}.mag").write_text("\n".join(mag), encoding="ascii")
    tcl = "\n".join((f"load {TOP}", "drc check", "drc count", "extract all",
                     "ext2spice lvs", "ext2spice scale off",
                     f"ext2spice -o {TOP}.spice", "save", "quit -noprompt", ""))
    cmd = ["docker", "run", "--rm", "-i", "--volume", f"{ROOT}:/workspace",
           "--env", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
           "--workdir", f"/workspace/{OUT.relative_to(ROOT).as_posix()}",
           "--entrypoint", "magic", IMAGE, "-dnull", "-noconsole", "-rcfile", RC]
    run = subprocess.run(cmd, input=tcl, text=True, capture_output=True, cwd=ROOT, timeout=180)
    log = run.stdout + run.stderr
    (OUT / "magic_probe.log").write_text(log, encoding="utf-8")
    match = re.search(r"Total DRC errors found: (\d+)", log)
    report = {
        "test": "sky130_low_voltage_nfet_deep_nwell_layout_probe",
        "magic_exit_code": run.returncode,
        "magic_drc_count": int(match.group(1)) if match else None,
        "extracted_netlist_exists": (OUT / f"{TOP}.spice").exists(),
        "deep_nwell_rect_magic_units": [-550, -650, 550, 650],
        "scope": "One reused physical NFET PCell plus deep n-well paint. No complete n-well guard/tap, TG, MIM, LVS or validated body connection; diagnostic only.",
        "log_tail": log[-2500:],
    }
    (OUT / "qualification_probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if run.returncode == 0 and match else 2


if __name__ == "__main__":
    raise SystemExit(main())
