"""Run the bounded SAR/writeback and phase-sequencer RTL smoke in Docker."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/results/sky130_ms_slot_controller_rtl.json"
IMAGE = "eventspikeseg:torch2.2.2-cpu-verification"


def main() -> int:
    cmd = [
        "docker", "run", "--rm", "--memory", "1g", "--cpus", "1",
        "--volume", f"{ROOT}:/workspace:ro", "--workdir", "/workspace",
        "--entrypoint", "sh", IMAGE, "-lc",
        "iverilog -g2012 -s tb_sky130_ms_slot_controller -o /tmp/ms_slot.vvp "
        "asic/analog/sky130_ms_slot_controller.sv "
        "scripts/tb_sky130_ms_slot_controller.sv && vvp /tmp/ms_slot.vvp",
    ]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    output = run.stdout + run.stderr
    passed = run.returncode == 0 and "PASS slot_seq=3 sar_decisions=72" in output
    report = {
        "test": "sky130_ms_slot_controller_ideal_code_comparator_rtl_smoke",
        "simulation_completed": run.returncode == 0,
        "exit_code": run.returncode,
        "pass": passed,
        "stdout_stderr": output,
        "limitations": [
            "Comparator is an ideal code-level testbench model.",
            "No analog DAC settling, comparator offset/noise, sample acquisition, or PDK extraction is tested.",
            "The +12,544-code inverse is a fixed TT schematic correction, not a calibrated physical map.",
            "No physical 5ms population schedule is claimed.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
