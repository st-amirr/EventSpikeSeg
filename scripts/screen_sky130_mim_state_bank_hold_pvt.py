"""Screen schematic off-switch retention on the extracted compact MIM bank."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_mim_state_bank_square"
BENCH = ROOT / "artifacts/analog_asic/benches/mim_large_probe"
CELL = "mim_state_square_3x4_w30_l30"
CORNER = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--corner=")), "ss")
TEMP = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--temp=")), "0"))
if (CORNER, TEMP) not in (("ss", 0), ("ff", 85), ("tt", 27)):
    raise ValueError("supported pairs: ss/0, tt/27, ff/85")
TAG = f"square_bank_hold_{CORNER}_temp{TEMP}"


def main() -> int:
    source_path = OUT / "square_bank_hold_5ms.cir"
    deck = source_path.read_text(encoding="ascii")
    deck = deck.replace('sky130.lib.spice" tt', f'sky130.lib.spice" {CORNER}')
    deck = deck.replace('.lib "', f".temp {TEMP}\n.lib ", 1)
    run_deck = OUT / f"{TAG}.cir"
    run_deck.write_text(deck, encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
               "-v", f"{ROOT}:/workspace", "-w",
               "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
               "--entrypoint", "ngspice", "eventspikeseg:analog-ngspice36", "-b",
               f"/workspace/{run_deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=300, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUT / f"{TAG}.log").write_text(log, encoding="utf-8")
    if proc.returncode or "ngspice-36 done" not in log:
        raise RuntimeError(f"PVT retention screen failed:\n{log[-4000:]}")
    values = {k.lower(): float(v) for k, v in re.findall(
        r"^(\w+_\w+)\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}
    cases = {}
    for bias, label in (("06", "0.6V"), ("12", "1.2V")):
        for sw in ("n_only", "p_only", "tg"):
            start, end = values[f"{sw}_{bias}_start"], values[f"{sw}_{bias}_end"]
            cases[f"{sw}_{label}"] = {"start_v": start, "end_v": end,
                                        "drift_mv": (end-start)*1e3}
    report = {"test": "sky130_extracted_square_mim_bank_schematic_switch_hold",
              "corner": CORNER, "temperature_c": TEMP,
              "state_bank": CELL, "extracted_bank_cap_f": 21.83739e-12,
              "simulation_duration_s": 5e-3, "simulation_completed": True,
              "drift": cases,
              "limitations": ["off-switches are schematic, not extracted layout",
                              "no sampled noise/mismatch or state-update event sequence"]}
    (OUT / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
