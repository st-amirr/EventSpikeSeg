"""Fit a local reset-pulse map, then validate held-out threshold steps in SPICE."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
CAL = RES / "sky130_ms_soft_reset_pulse.json"
VCM = 0.9
INITIAL_STATES_V = (0.75, 0.9, 1.05)
HOLDOUT_STEPS_V = (0.08, 0.12, 0.14)
PULSE_START_US, PULSE_WIDTH_US, RESET_START_US, STOP_US = 100.0, 700.0, 1000.0, 1200.0
MAX_ERROR = 0.15

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


def pwl(start: float, width: float, inactive: float, active: float) -> str:
    end = start + width
    return (f"PWL(0 {inactive:g} {start-0.001:g}u {inactive:g} {start:g}u {active:g} "
            f"{end:g}u {active:g} {end+0.001:g}u {inactive:g} {STOP_US:g}u {inactive:g})")


def main() -> int:
    calibration = json.loads(CAL.read_text(encoding="utf-8"))
    coefficients: dict[float, tuple[float, float]] = {}
    for initial_v in INITIAL_STATES_V:
        points = [x for x in calibration["cases"] if float(x["initial_membrane_v"]) == initial_v]
        widths = [float(x["reset_logical_width_us"]) for x in points]
        deltas = [float(x["reset_delta_v"]) for x in points]
        s11 = sum(x ** 2 for x in widths)
        s12 = sum(x ** 3 for x in widths)
        s22 = sum(x ** 4 for x in widths)
        r1 = sum(x * y for x, y in zip(widths, deltas))
        r2 = sum(x * x * y for x, y in zip(widths, deltas))
        determinant = s11 * s22 - s12 * s12
        a = (r1 * s22 - r2 * s12) / determinant
        b = (s11 * r2 - s12 * r1) / determinant
        coefficients[initial_v] = (a, b)

    cases = []
    widths_for = {}
    for initial_v in INITIAL_STATES_V:
        a, b = coefficients[initial_v]
        for target in HOLDOUT_STEPS_V:
            if abs(b) <= 1e-15:
                width = target / a
            else:
                discriminant = a * a + 4.0 * b * target
                root = math.sqrt(discriminant)
                candidates = ((-a + root) / (2.0 * b), (-a - root) / (2.0 * b))
                width = next(value for value in candidates if value > 0)
            name = f"v{int(initial_v*100)}_t{int(target*1000)}"
            widths_for[name] = width
            cases.append({"name": name, "base": f"base{int(initial_v*100)}",
                          "initial_membrane_v": initial_v, "target_threshold_step_v": target,
                          "predicted_reset_width_us": width, "predicted_by": "quadratic local fit to prior three calibration points"})

    lines = ["SKY130 TT held-out soft reset calibration", COMMON,
             "Vdd vdd 0 1.8", f"Vcm vcm 0 {VCM}", "Vcap capture 0 0", "Vcapb capture_b 0 1.8",
             "Vinit initialize 0 0", "Vinitb initialize_b 0 1.8", "Vleak leak_en 0 0",
             "Vleakb leak_enb 0 1.8", "Vbias vbias 0 0.65"]
    vectors = []
    for initial_v in INITIAL_STATES_V:
        base = f"base{int(initial_v*100)}"
        lines += [f"V{base}p pg_{base} 0 {pwl(PULSE_START_US, PULSE_WIDTH_US, 1.8, 1.0)}",
                  f"V{base}n ng_{base} 0 0", f"V{base}rp rgp_{base} 0 1.8",
                  f"V{base}rn rgn_{base} 0 0",
                  f"X{base} {base}_mem {base}_snap {base}_spike capture capture_b initialize initialize_b "
                  f"leak_en leak_enb pg_{base} ng_{base} rgp_{base} rgn_{base} vbias vdd 0 vcm "
                  "analog_plif_channel_pulse_duration_soft_reset theta=0.4 scale=0.2 w_um=100 l_um=100",
                  f".ic v({base}_mem)={initial_v-VCM:g}"]
        vectors.append(f"v({base}_mem)")
    for case in cases:
        name = str(case["name"])
        width = widths_for[name]
        lines += [f"V{name}p pg_{name} 0 {pwl(PULSE_START_US, PULSE_WIDTH_US, 1.8, 1.0)}",
                  f"V{name}n ng_{name} 0 0", f"V{name}rp rgp_{name} 0 1.8",
                  f"V{name}rn rgn_{name} 0 {pwl(RESET_START_US, width, 0.0, 0.525)}",
                  f"X{name} {name}_mem {name}_snap {name}_spike capture capture_b initialize initialize_b "
                  f"leak_en leak_enb pg_{name} ng_{name} rgp_{name} rgn_{name} vbias vdd 0 vcm "
                  "analog_plif_channel_pulse_duration_soft_reset theta=0.4 scale=0.2 w_um=100 l_um=100",
                  f".ic v({name}_mem)={float(case['initial_membrane_v'])-VCM:g}"]
        vectors.append(f"v({name}_mem)")
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 0.1u 1.2m uic",
              f"wrdata ../results/sky130_ms_soft_reset_calibration.dat {' '.join(vectors)}", "quit", ".endc", ".end"]
    deck = BENCH / "sky130_ms_soft_reset_calibration.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=140)
    (RES / "sky130_ms_soft_reset_calibration.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    data = RES / "sky130_ms_soft_reset_calibration.dat"
    rows = []
    header = []
    if data.exists():
        raw = data.read_text(encoding="utf-8").splitlines()
        if raw:
            header = raw[0].split()
        for line in raw[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                pass
    col = {value.lower(): i for i, value in enumerate(header)}
    for case in cases:
        name, base = str(case["name"]), str(case["base"])
        width = widths_for[name]
        t_us = RESET_START_US + width + 0.1
        row = min(rows, key=lambda r: abs(r[0] * 1e6 - t_us)) if rows else []
        bi, ri = col.get(f"v({base}_mem)".lower()), col.get(f"v({name}_mem)".lower())
        if row and bi is not None and ri is not None:
            delivered = row[bi] - row[ri]
            case.update({"sample_time_us": row[0] * 1e6, "measured_reset_delta_v": delivered,
                         "relative_threshold_step_error": delivered / float(case["target_threshold_step_v"]) - 1.0})
    complete = proc.returncode == 0 and len(rows) > 1 and all("measured_reset_delta_v" in c for c in cases)
    max_error = max((abs(float(c["relative_threshold_step_error"])) for c in cases if "relative_threshold_step_error" in c), default=float("inf"))
    report = {
        "test": "sky130_tt_soft_reset_state_calibration_heldout_thresholds",
        "simulation_completed": complete,
        "exit_code": proc.returncode,
        "calibration_source": CAL.name,
        "per_start_state_response_fit": {
            str(v): {"linear_gain_v_per_us": coefficients[v][0], "quadratic_gain_v_per_us2": coefficients[v][1]}
            for v in INITIAL_STATES_V
        },
        "heldout_threshold_steps_v": list(HOLDOUT_STEPS_V),
        "cases": cases,
        "max_relative_step_error": max_error,
        "provisional_error_limit": MAX_ERROR,
        "candidate_screen_pass": bool(complete and max_error <= MAX_ERROR),
        "scope": "Calibration-conditioned TT schematic test only. Assumes the starting membrane voltage is known to choose a per-state pulse width; no on-chip state sensor/controller, comparator-trigger coupling, PVT/mismatch/extraction or full model equivalence.",
    }
    (RES / "sky130_ms_soft_reset_calibration.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"simulation_completed": complete, "candidate_screen_pass": report["candidate_screen_pass"],
                      "cases": len(cases), "max_relative_step_error": max_error}, indent=2))
    return 0 if report["candidate_screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
