"""Measure SKY130 MOS-gate storage noise/retention geometry trade-offs.

Ten parallel NFET gates form a MOS capacitor per state rail. The cell is
programmed through the existing physical TG, then held for one 5 ms bin.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RESULTS = OUT / "results"
SIZES_UM = (10, 30, 100)
BIAS_V = (0.6, 0.9, 1.2)
FULL_RAIL_BIAS_V = (0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05,
                    1.2, 1.35, 1.5, 1.65, 1.8)


def run_case(size: int, bias: float) -> dict[str, object]:
    length = size / 10
    bias_tag = str(bias).replace(".", "p")
    tag = f"sky130_mos_scaled_hold_w{size}um_v{bias_tag}"
    lines = [
        "SKY130 TT/27C scaled MOS gate state-cap 5ms hold",
        ".option scale=1u",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        "Vdd vdd 0 1.8", f"Vprogram src 0 {bias:g}",
        "Von on 0 PWL(0 1.8 1u 1.8 1.001u 0 5.01m 0)",
        "Voff off 0 PWL(0 0 1u 0 1.001u 1.8 5.01m 1.8)",
        ".subckt tg a b en enb vdd vss",
        "Xn a en b vss sky130_fd_pr__nfet_01v8 w=1 l=0.15",
        "Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15",
        ".ends tg",
        "Xsw src state on off vdd 0 tg",
    ]
    for finger in range(10):
        lines.append(f"Xcap{finger} 0 state 0 0 sky130_fd_pr__nfet_01v8 w={size} l={length:g}")
    lines += [".control", "tran 1u 5.01m 0 1u",
              "meas tran start find v(state) at=1.9u",
              "meas tran half_ms find v(state) at=0.5m",
              "meas tran one_ms find v(state) at=1m",
              "meas tran five_ms find v(state) at=5m",
              "quit", ".endc", ".end", ""]
    deck = BENCH / f"{tag}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro",
               "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
               "--workdir", "/workspace/artifacts/analog_asic/benches",
               "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
               "90", "ngspice", "-b", deck.name]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=120, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
    values = {name.lower(): float(value) for name, value in re.findall(
        r"(?im)^\s*(start|half_ms|one_ms|five_ms)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(values) != {
            "start", "half_ms", "one_ms", "five_ms"}:
        raise RuntimeError(f"MOS hold simulation failed for {tag}:\n{log[-4000:]}")
    return {"mos_gate_bank_area_um2_per_rail": 10 * size * length,
            "device_geometry_um": {"finger_count": 10, "w_each": size, "l_each": length},
            "program_v": bias, "measured_v": values,
            "five_ms_hold_drift_uv": (values["five_ms"] - values["start"]) * 1e6,
            "simulation_completed": True}


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    full_rail = "--full-rail" in sys.argv[1:]
    rows = ([run_case(100, bias) for bias in FULL_RAIL_BIAS_V] if full_rail else
            [run_case(size, bias) for size in SIZES_UM for bias in BIAS_V])
    report = {"test": "sky130_scaled_mos_gate_state_cap_5ms_hold",
              "corner": "tt", "temperature_c": 27,
              "program_aperture_s": 1e-6, "hold_s": 5e-3,
              "switch": "physical 1um/0.15um NFET + 2um/0.15um PFET TG",
              "rows": rows,
              "full_rail_bias_sweep": full_rail,
              "scope": "Ten parallel NFET gate capacitors per state rail, gate programmed through a physical TG then isolated. State/reference are single-ended test rails, not a differential PLIF. No transient noise, mismatch, PVT, extraction, routed layout, refresh control, or event updates."}
    path = RESULTS / ("sky130_mos_scaled_state_cap_fullrail_hold.json" if full_rail else
                      "sky130_mos_scaled_state_cap_hold.json")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
