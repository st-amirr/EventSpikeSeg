"""Aggregate bounded tight-solver first-touch MOS charge transfer across corners."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
DRIVER = ROOT / "scripts/test_sky130_ms_first_event_clamp.py"
FRACTIONS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
CONDITIONS = (("tt", 27), ("ss", 0), ("ff", 85))


def main() -> int:
    curves = []
    for corner, temperature_c in CONDITIONS:
        rows = []
        for fraction in FRACTIONS:
            tag = ("tt" if corner == "tt" and temperature_c == 27 else
                   f"{corner}_temp{temperature_c:g}")
            if fraction != 0.6:
                tag += f"_g{fraction:g}".replace(".", "p")
            tag += "_tight_s0p1n_onlyreference-before_0p2ns"
            path = RES / f"sky130_ms_first_event_clamp_{tag}.json"
            if not path.exists():
                cmd = [sys.executable, str(DRIVER), f"--mos-corner={corner}",
                       f"--temperature-c={temperature_c}", f"--gate-fraction={fraction:g}",
                       "--tight-solver", "--step-ns=0.1", "--cases=reference,before_0p2ns"]
                run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=150)
                if run.returncode:
                    raise RuntimeError(f"bounded SPICE failed for {corner}/{temperature_c}/{fraction}: {run.stderr[-1000:]}")
            source = json.loads(path.read_text(encoding="utf-8"))
            if not source["simulation_completed"] or source["gate_fraction"] != fraction:
                raise RuntimeError(f"invalid first-touch transfer source: {path}")
            by_case = {row["case"]: row for row in source["cases"]}
            early = by_case["before_0p2ns"]["post_event_minus_no_event_uv"]
            reference = by_case["reference"]["post_event_minus_no_event_uv"]
            rows.append({"gate_fraction": fraction, "event_step_uv": early,
                         "free_reference_event_step_uv": reference,
                         "early_minus_reference_uv": early - reference,
                         "source_result": path.name})
            print(f"{corner}/{temperature_c:g}C fraction {fraction:g}: {early:.6f} uV", flush=True)
        curves.append({"mos_corner": corner, "temperature_c": temperature_c,
                       "points": rows})
    report = {"test": "sky130_first_touch_mos_pvt_charge_curve_tight",
              "simulation_completed": True, "mim_width_um": 10,
              "pulse_width_ns": 10.5, "solver": "reltol=1e-5 abstol=1e-15 vntol=1e-9; tran step=0.1ns",
              "conditions": curves,
              "scope": "Deterministic positive signed event, physical TT/SS/FF MOS/TG and typical MIM/R/C with ideal 0.9V common-mode and gate waveforms. Single event per circuit. No negative polarity curve, weight DAC, temperature sensor, trim loop, mismatch, switched noise, supply sweep, extraction or network feedback."}
    dest = RES / "sky130_ms_first_event_pvt_transfer_curve_tight.json"
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
