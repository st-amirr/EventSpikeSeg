"""Characterize integrated SKY130 R-2R plus signed MOS current transfer."""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VDD = 1.8
U23_MAX = (1 << 23) - 1
CODE_FRACTIONS = (0.0, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0)
COMMON = """.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
"""


def measure(code: int, polarity: str) -> dict:
    negative = polarity == "negative"
    name = f"sky130_weight_dac_current_{polarity}_{code}"
    bits = "\n".join(f"Vw{i} w{i} 0 {VDD if (code >> i) & 1 else 0}" for i in range(23))
    pins = " ".join(f"w{i}" for i in range(22, -1, -1))
    pulse_p, pulse_n, sign = ((VDD, VDD, VDD) if negative else (0.0, 0.0, 0.0))
    deck = f"""SKY130 integrated weight DAC current code={code} polarity={polarity}
{COMMON}
Vdd vdd 0 {VDD}
Vstate state 0 0.9
Vweight_hi weight_hi 0 {VDD}
Vweight_lo weight_lo 0 0
Voff ibias_n_off 0 {VDD}
Vsign sign_n 0 {sign}
Vpp pulse_pos 0 {pulse_p}
Vpn pulse_neg 0 {pulse_n}
{bits}
Xinject state pulse_pos pulse_neg sign_n {pins} weight_hi weight_lo ibias_n_off vdd 0 weight_inject_q716
.control
op
print i(Vstate)
print v(xinject.vw)
quit
.endc
.end
"""
    (BENCH / f"{name}.cir").write_text(deck, encoding="utf-8")
    cmd = [
        "docker", "run", "--rm", "--memory", "8g", "--cpus", "1",
        "--volume", f"{ROOT}:/workspace:ro",
        "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
        "--workdir", "/workspace/artifacts/analog_asic/benches",
        "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
        "30", "ngspice", "-b", f"{name}.cir",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    log = proc.stdout + proc.stderr
    (RES / f"{name}.log").write_text(log, encoding="utf-8")
    match = re.search(r"i\(vstate\)\s*=\s*([-+0-9.eE]+)", log, re.I)
    current = float(match.group(1)) if match else None
    gate_match = re.search(r"v\(xinject\.vw\)\s*=\s*([-+0-9.eE]+)", log, re.I)
    gate_voltage = float(gate_match.group(1)) if gate_match else None
    return {
        "polarity": polarity,
        "dac_code_u23": code,
        "dac_code_fraction": code / U23_MAX,
        "current_into_state_source_a": current,
        "weight_gate_voltage_v": gate_voltage,
        "simulation_completed": proc.returncode == 0 and current is not None and math.isfinite(current),
        "exit_code": proc.returncode,
    }


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    rows = {
        pol: [measure(round(f*U23_MAX), pol) for f in CODE_FRACTIONS]
        for pol in ("positive", "negative")
    }
    summaries = {}
    for pol, points in rows.items():
        currents = [abs(p["current_into_state_source_a"]) for p in points]
        summaries[pol] = {
            "complete": all(p["simulation_completed"] for p in points),
            "strict_monotonic": all(a < b for a, b in zip(currents, currents[1:])),
            "zero_weight_current_a": currents[0],
            "max_abs_current_a": currents[-1],
            "points": points,
        }
    ratio = summaries["positive"]["max_abs_current_a"] / summaries["negative"]["max_abs_current_a"]
    report = {
        "test": "sky130_tt_integrated_r2r_mos_current_curve",
        "state_v": 0.9,
        "pmos_width_um": 11.3,
        "nmos_width_um": 2.0,
        "code_fractions": list(CODE_FRACTIONS),
        "curves": summaries,
        "positive_to_negative_full_scale_current_ratio": ratio,
        "scope": "TT DC operating points through actual 24-bit R-2R and pulse gate; no transient charge, mismatch, corners, or extraction.",
        "calibration_candidate_pass": all(s["complete"] and s["strict_monotonic"] for s in summaries.values()) and ratio > 0.8 and ratio < 1.25,
    }
    path = RES / "sky130_weight_dac_current_characterization.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["calibration_candidate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
