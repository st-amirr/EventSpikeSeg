"""Check signed Q7.16 DAC-to-MOS injection monotonicity at SKY130 TT."""
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
WEIGHTS = (0, 1 << 16, 8 << 16, 68 << 16)
WEIGHT_ABSMAX = 68.37539672851562
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


def dac_code_for_weight(weight_value: float, polarity: str, curves: dict) -> tuple[int, float]:
    curve = curves[polarity]
    fraction = min(1.0, weight_value / WEIGHT_ABSMAX)
    target = curve["max_abs_current_a"] * fraction
    points = curve["points"]
    ordered = sorted(points, key=lambda p: abs(p["current_into_state_source_a"]))
    code = ordered[-1]["dac_code_u23"]
    for a, b in zip(ordered, ordered[1:]):
        ia, ib = abs(a["current_into_state_source_a"]), abs(b["current_into_state_source_a"])
        if min(ia, ib) <= target <= max(ia, ib) and ia != ib:
            code = round(a["dac_code_u23"] + (target - ia) * (b["dac_code_u23"] - a["dac_code_u23"]) / (ib - ia))
            break
    return max(0, min((1 << 23) - 1, code)), target


def run_case(weight: int, negative: bool, curves: dict) -> dict:
    sign = int(negative)
    polarity = "negative" if negative else "positive"
    weight_value = weight / 65536
    dac_code, target_current = dac_code_for_weight(weight_value, polarity, curves)
    name = f"sky130_weight_inject_{'neg' if negative else 'pos'}_{weight}"
    bit_sources = "\n".join(
        f"Vw{i} w{i} 0 {VDD if (dac_code >> i) & 1 else 0}"
        for i in range(23)
    )
    weight_pins = " ".join(f"w{i}" for i in range(22, -1, -1))
    pulse_p = VDD if negative else 0.0
    pulse_n = VDD if negative else 0.0
    deck = f"""SKY130 signed Q7.16 MOS injection weight={weight/65536:g} negative={negative}
{COMMON}
Vdd vdd 0 {VDD}
Vstate state 0 0.9
Vweight_hi weight_hi 0 {VDD}
Vweight_lo weight_lo 0 0
Voff ibias_n_off 0 {VDD}
Vsign sign_n 0 {sign*VDD}
Vpp pulse_pos 0 {pulse_p}
Vpn pulse_neg 0 {pulse_n}
{bit_sources}
Xinject state pulse_pos pulse_neg sign_n {weight_pins} weight_hi weight_lo ibias_n_off vdd 0 weight_inject_q716
.control
op
print i(Vstate)
quit
.endc
.end
"""
    (BENCH / f"{name}.cir").write_text(deck, encoding="utf-8")
    cmd = [
        "docker", "run", "--rm", "--memory", "2g", "--cpus", "1",
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
    done = proc.returncode == 0 and current is not None and math.isfinite(current)
    return {
        "weight_q716": weight,
        "weight_value": weight_value,
        "calibration_source": "integrated TT R-2R plus pulsed MOS path",
        "calibrated_gate_dac_code_u23": dac_code,
        "target_abs_current_a_from_mos_curve_and_p_sizing": target_current,
        "polarity": "negative" if negative else "positive",
        "state_v": 0.9,
        "current_into_state_source_a": current,
        "simulation_completed": done,
        "exit_code": proc.returncode,
    }


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    characterization_path = RES / "sky130_weight_dac_current_characterization.json"
    if not characterization_path.is_file():
        raise FileNotFoundError("Run scripts/characterize_sky130_weight_dac_current.py first")
    curves = json.loads(characterization_path.read_text(encoding="utf-8"))["curves"]
    rows = [run_case(w, n, curves) for n in (False, True) for w in WEIGHTS]
    polarity_checks = {}
    for negative in (False, True):
        pol = "negative" if negative else "positive"
        subset = [r for r in rows if r["polarity"] == pol]
        valid = len(subset) == len(WEIGHTS) and all(r["simulation_completed"] for r in subset)
        currents = [r["current_into_state_source_a"] for r in subset] if valid else []
        zero_ok = bool(currents) and abs(currents[0]) < 1e-9
        polarity_checks[pol] = {
            "simulations_complete": valid,
            "zero_weight_current_abs_a": abs(currents[0]) if currents else None,
            "zero_weight_off_pass": zero_ok,
            "strict_magnitude_monotonic": (
                all(a < b for a, b in zip(map(abs, currents), map(abs, currents[1:])))
                if currents else False
            ),
            "expected_current_sign": (all(i > 0 for i in currents[1:]) if not negative else all(i < 0 for i in currents[1:])) if currents else False,
        }
    for row in rows:
        target = row.get("target_abs_current_a_from_mos_curve_and_p_sizing", 0.0)
        current = row.get("current_into_state_source_a")
        row["relative_abs_current_error"] = (
            abs(current) / target - 1.0 if current is not None and target > 0 else None
        )
    proportional = all(
        row["relative_abs_current_error"] is not None
        and abs(row["relative_abs_current_error"]) <= 0.20
        for row in rows if row["weight_q716"] != 0
    )
    report = {
        "architecture": "sky130_q716_signed_weight_dac_mos_injector_tt_op",
        "weight_codes_tested": list(WEIGHTS),
        "weight_rails_v": [0.0, VDD],
        "weight_calibration": "offline TT MOS I-V LUT maps Q7.16 magnitude to target current then sign-specific 23-bit gate DAC code",
        "current_screen": "DC operating point with membrane clamped at 0.9V; not pulse charge or PLIF accuracy",
        "weight_dac_q716_precision_qualified": False,
        "current_linearity_qualified": False,
        "target_current_within_20pct_pass": proportional,
        "corner": "TT",
        "rows": rows,
        "polarity_checks": polarity_checks,
        "coarse_monotonic_screen_pass": all(
            p["simulations_complete"] and p["zero_weight_off_pass"]
            and p["strict_magnitude_monotonic"] and p["expected_current_sign"]
            for p in polarity_checks.values()
        ),
    }
    report["screen_pass"] = report["coarse_monotonic_screen_pass"] and proportional
    path = RES / "sky130_weight_q716_injector_screen.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
