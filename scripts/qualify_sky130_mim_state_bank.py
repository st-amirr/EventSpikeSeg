"""Recheck the extracted 12-plate M3_2 state-bank layout and 5 ms switch hold.

This qualifies the capacitor bank primitive only. The switch remains schematic,
and no PLIF/readout/noise/PVT or model-level acceptance is implied.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches/mim_large_probe"
CELL = "membrane_state_mim_m3_2_w30_l30_m12"
IMAGE = "eventspikeseg:analog-layout"
SIM = "eventspikeseg:analog-ngspice36"
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"


def docker(image: str, entrypoint: str, args: list[str], *, input_text: str | None = None,
           timeout: int = 180) -> str:
    command = ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
               "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
               "-w", "/workspace/artifacts/analog_asic/benches/mim_large_probe",
               "--entrypoint", entrypoint, image, *args]
    proc = subprocess.run(command, input=input_text, text=True, capture_output=True,
                          timeout=timeout, cwd=ROOT)
    log = proc.stdout + proc.stderr
    if proc.returncode:
        raise RuntimeError(f"{entrypoint} failed ({proc.returncode}):\n{log}")
    return log


def main() -> int:
    mag = BENCH / f"{CELL}.mag"
    spice = BENCH / f"{CELL}.spice"
    gds = BENCH / f"{CELL}.gds"
    if not all(path.is_file() for path in (mag, spice, gds)):
        raise FileNotFoundError("Expected flattened Magic, extracted SPICE and GDS are required")
    drc_log = docker("eventspikeseg:analog-layout", "magic",
                     ["-dnull", "-noconsole", "-rcfile", MAGIC_RC],
                     input_text=f"load {CELL}\ndrc check\ndrc count\nquit -noprompt\n")
    if "Total DRC errors found: 0" not in drc_log:
        raise RuntimeError(f"MIM bank DRC did not pass:\n{drc_log}")

    ref = BENCH / "mim_state_reference.spice"
    ref.write_text(".subckt mim_state_reference MEM_P MEM_N\n"
                   "X0 MEM_P MEM_N sky130_fd_pr__cap_mim_m3_2 w=30 l=30 m=12\n"
                   ".ends\n", encoding="ascii")
    lvs = docker(IMAGE, "netgen-lvs", ["-batch", "lvs", f"{CELL}.spice {CELL}",
                 "mim_state_reference.spice mim_state_reference",
                 "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl",
                 "mim_state_lvs_recheck.out"])
    if "Circuits match uniquely." not in lvs:
        raise RuntimeError(f"Netgen did not report a unique match:\n{lvs}")

    cvdeck = BENCH / "mim_bank_cv.cir"
    cvlog = docker(SIM, "ngspice", ["-b", f"/workspace/{cvdeck.relative_to(ROOT).as_posix()}"],
                   timeout=180)
    cv = re.search(r"\bceff\s*=\s*([-+0-9.eE]+)", cvlog, re.I)
    if not cv or "ngspice-36 done" not in cvlog:
        raise RuntimeError(f"Extracted-bank CV did not complete:\n{cvlog[-4000:]}")
    holddeck = BENCH / "mim_bank_hold_5ms.cir"
    holdlog = docker(SIM, "ngspice", ["-b", f"/workspace/{holddeck.relative_to(ROOT).as_posix()}"],
                     timeout=240)
    if "ngspice-36 done" not in holdlog:
        raise RuntimeError(f"5ms hold simulation did not complete:\n{holdlog[-4000:]}")
    measurements = {k: float(v) for k, v in re.findall(
        r"^(\w+_\w+)\s*=\s*([-+0-9.eE]+)", holdlog, re.I | re.M)}
    spice_text = spice.read_text(encoding="ascii")
    dimensions = re.search(r"\bl=3e\+07u\s+w=3e\+07u\b", spice_text)
    if len(re.findall(r"^X\d+ MEM_P MEM_N sky130_fd_pr__cap_mim_m3_2", spice_text, re.M)) != 12 or not dimensions:
        raise RuntimeError("Extracted netlist does not contain twelve 30x30um M3_2 units")
    cases = {}
    for bias, label in (("06", "0.6V"), ("12", "1.2V")):
        for switch in ("n_only", "p_only", "tg"):
            start = measurements[f"{switch}_{bias}_start"]
            end = measurements[f"{switch}_{bias}_end"]
            cases[f"{switch}_{label}"] = {"start_v": start, "end_v": end,
                                             "drift_mv": (end - start) * 1e3}
    report = {"cell": CELL, "unit_capacitor": "sky130_fd_pr__cap_mim_m3_2",
              "unit_geometry_um": [30, 30], "unit_count": 12,
              "drc_zero_errors": True, "netgen_unique_match": True,
              "extracted_bank_ceff_f": float(cv.group(1)),
              "hold_5ms_completed": True, "hold_drift": cases,
              "switch_layout_extracted": False,
              "scope": "Capacitor array layout/extraction qualified; transistor switches are schematic-only; no sampled-noise, PLIF or full-model acceptance."}
    (BENCH / "mim_state_bank_qualification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
