"""Measure the SS first-touch injector at the actual final-fusion pulse width."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
FRACTIONS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95)


def main() -> int:
    corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                   if arg.startswith("--corner=")), "ss")
    temperature_c = {"ss": 0, "tt": 27, "ff": 85}.get(corner)
    if temperature_c is None:
        raise ValueError("corner must be ss, tt or ff")
    fanin = json.loads((RES / "sky130_ms_first_touch_float_fanin_ss0_deck.json").read_text(encoding="utf-8"))
    width = fanin["width_ns"]
    commanded_width = float(f"{width:g}")
    rows = []
    for fraction in FRACTIONS:
        gate_tag = "" if fraction == 0.6 else f"_g{fraction:g}".replace(".", "p")
        width_tag = f"{commanded_width:g}".replace(".", "p")
        corner_tag = "tt" if corner == "tt" else f"{corner}_temp{temperature_c}"
        filename = f"sky130_ms_first_event_clamp_{corner_tag}{gate_tag}_tight_s0p1n_w{width_tag}n_onlyreference-before_0p2ns.json"
        path = RES / filename
        if path.exists():
            source = json.loads(path.read_text(encoding="utf-8"))
        else:
            cmd = [sys.executable, "scripts/test_sky130_ms_first_event_clamp.py",
                   f"--mos-corner={corner}", f"--temperature-c={temperature_c}", f"--gate-fraction={fraction:g}",
                   f"--event-width-ns={commanded_width:g}", "--tight-solver", "--step-ns=0.1",
                   "--cases=reference,before_0p2ns"]
            run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=150)
            if run.returncode:
                raise RuntimeError(f"stage-width SPICE failed at {fraction}: {run.stderr[-1000:]}")
            source = json.loads(run.stdout)
        if not source["simulation_completed"] or source["event_width_ns"] != commanded_width:
            raise RuntimeError(f"invalid stage-width SPICE result: {path}")
        early = next(row for row in source["cases"] if row["case"] == "before_0p2ns")
        rows.append({"gate_fraction": fraction,
                     "event_step_uv": early["post_event_minus_no_event_uv"],
                     "source_result": filename})
        print(f"{corner}/{temperature_c}C fraction {fraction:g}: {rows[-1]['event_step_uv']:.6f} uV", flush=True)
    short = json.loads((RES / "sky130_ms_first_event_pvt_transfer_curve_tight.json").read_text(encoding="utf-8"))
    short_condition = next(row for row in short["conditions"] if row["mos_corner"] == corner)
    for row, old in zip(rows, short_condition["points"]):
        if row["gate_fraction"] != old["gate_fraction"]:
            raise RuntimeError("gate fraction mismatch")
        row["error_from_linear_width_scaling_fraction"] = (
            row["event_step_uv"] / (old["event_step_uv"] * commanded_width / 10.5) - 1)
    result = {"test": "sky130_first_touch_ss_stage_width_transfer", "simulation_completed": True,
              "corner": corner, "temperature_c": temperature_c, "pulse_width_ns": commanded_width,
              "target_stage_width_ns": width,
              "points": rows,
              "scope": "One positive event per gate fraction, physical 10um MIM/TG/MOS, ideal gate driver, tight solver. No negative polarity, accumulation, mismatch, noise, calibration DAC, or extraction."}
    path = RES / f"sky130_ms_first_event_{corner}_stage_width_transfer.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
