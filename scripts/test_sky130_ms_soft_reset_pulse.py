"""Check a pulse-duration implementation of the float PLIF subtractive reset."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VCM = 0.9
INITIAL_STATES_V = (0.75, 0.9, 1.05)
THRESHOLD_STEPS_V = (0.06, 0.10, 0.15)
PULSE_START_US = 100.0
PULSE_LOGICAL_WIDTH_US = 100.0
PULSE_PHYSICAL_WIDTH_US = 700.0
RESET_START_US = 1000.0
NOMINAL_NEGATIVE_GAIN_V_PER_US = 0.00130
STOP_US = 1200.0

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


def pwl(polarity: str, start: float, width: float, off: float, active: float) -> str:
    end = start + width
    return (f"PWL(0 {off:g} {start-0.001:g}u {off:g} {start:g}u {active:g} "
            f"{end:g}u {active:g} {end+0.001:g}u {off:g} {STOP_US:g}u {off:g})")


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 TT subtractive reset pulse screen", COMMON,
             "Vdd vdd 0 1.8", f"Vcm vcm 0 {VCM}", "Vcap capture 0 0", "Vcapb capture_b 0 1.8",
             "Vinit initialize 0 0", "Vinitb initialize_b 0 1.8", "Vleak leak_en 0 0",
             "Vleakb leak_enb 0 1.8", "Vbias vbias 0 0.65"]
    vectors: list[str] = []
    cases = []
    for vi, initial_v in enumerate(INITIAL_STATES_V):
        base_name = f"base{vi}"
        lines += [f"V{base_name}p pg_{base_name} 0 {pwl('positive', PULSE_START_US, PULSE_PHYSICAL_WIDTH_US, 1.8, 1.0)}",
                  f"V{base_name}n ng_{base_name} 0 0",
                  f"V{base_name}rp rgp_{base_name} 0 1.8",
                  f"V{base_name}rn rgn_{base_name} 0 0",
                  f"X{base_name} {base_name}_mem {base_name}_snap {base_name}_spike capture capture_b "
                  f"initialize initialize_b leak_en leak_enb pg_{base_name} ng_{base_name} "
                  f"rgp_{base_name} rgn_{base_name} vbias vdd 0 vcm analog_plif_channel_pulse_duration_soft_reset "
                  "theta=0.4 scale=0.2 w_um=100 l_um=100",
                  f".ic v({base_name}_mem)={initial_v-VCM:g}"]
        vectors.append(f"v({base_name}_mem)")
        for threshold_step in THRESHOLD_STEPS_V:
            name = f"v{vi}_t{int(threshold_step*1000)}"
            reset_width = threshold_step / NOMINAL_NEGATIVE_GAIN_V_PER_US
            reset_end = RESET_START_US + reset_width
            lines += [
                f"V{name}p pg_{name} 0 {pwl('positive', PULSE_START_US, PULSE_PHYSICAL_WIDTH_US, 1.8, 1.0)}",
                f"V{name}n ng_{name} 0 0",
                f"V{name}rp rgp_{name} 0 1.8",
                f"V{name}rn rgn_{name} 0 {pwl('negative', RESET_START_US, reset_width, 0.0, 0.525)}",
                f"X{name} {name}_mem {name}_snap {name}_spike capture capture_b "
                f"initialize initialize_b leak_en leak_enb pg_{name} ng_{name} "
                f"rgp_{name} rgn_{name} vbias vdd 0 vcm analog_plif_channel_pulse_duration_soft_reset "
                "theta=0.4 scale=0.2 w_um=100 l_um=100",
                f".ic v({name}_mem)={initial_v-VCM:g}",
            ]
            vectors.append(f"v({name}_mem)")
            cases.append({"name": name, "base": base_name, "initial_membrane_v": initial_v,
                          "threshold_step_v": threshold_step, "reset_logical_width_us": reset_width,
                          "reset_end_us": reset_end})
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 0.1u 1.2m uic",
              f"wrdata ../results/sky130_ms_soft_reset_pulse.dat {' '.join(vectors)}", "quit", ".endc", ".end"]
    deck = BENCH / "sky130_ms_soft_reset_pulse.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=140)
    (RES / "sky130_ms_soft_reset_pulse.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    data = RES / "sky130_ms_soft_reset_pulse.dat"
    rows = []
    header: list[str] = []
    if data.exists():
        data_lines = data.read_text().splitlines()
        if data_lines:
            header = data_lines[0].split()
        for line in data_lines[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                pass
    col = {name.lower(): i for i, name in enumerate(header)}
    time_col = col.get("time", 0)
    measurements = []
    for case in cases:
        target_time = float(case["reset_end_us"]) + 0.1
        row = min(rows, key=lambda r: abs(r[time_col] * 1e6 - target_time)) if rows else []
        base_col = col.get(f"v({case['base']}_mem)".lower())
        reset_col = col.get(f"v({case['name']}_mem)".lower())
        if row and base_col is not None and reset_col is not None:
            base_v = row[base_col]
            reset_v = row[reset_col]
            delivered = base_v - reset_v
            target = float(case["threshold_step_v"])
            measurements.append({**case, "sample_time_us": row[time_col] * 1e6,
                                 "baseline_state_v": base_v, "soft_reset_state_v": reset_v,
                                 "reset_delta_v": delivered,
                                 "relative_threshold_step_error": (delivered / target) - 1.0})
    completed = proc.returncode == 0 and len(rows) > 1 and len(measurements) == len(cases)
    max_error = max((abs(float(m["relative_threshold_step_error"])) for m in measurements), default=float("inf"))
    report = {
        "test": "sky130_tt_pulse_duration_subtractive_soft_reset",
        "simulation_completed": completed,
        "exit_code": proc.returncode,
        "membrane": "SKY130 PDK MIM 100um x 100um",
        "initial_membrane_v": list(INITIAL_STATES_V),
        "threshold_steps_v": list(THRESHOLD_STEPS_V),
        "positive_excitation_logical_width_us": PULSE_LOGICAL_WIDTH_US,
        "positive_excitation_physical_width_us": PULSE_PHYSICAL_WIDTH_US,
        "reset_width_mapping": "threshold voltage / nominal 1.30mV per logical microsecond negative transfer",
        "cases": measurements,
        "max_relative_step_error": max_error,
        "provisional_error_screen_limit": 0.15,
        "candidate_screen_pass": bool(completed and max_error <= 0.15),
        "scope": "TT schematic single-event reset only; no comparator-trigger integration, adaptation threshold coding, PVT/mismatch/extraction, event serialization, or full-model spike-equivalence claim.",
    }
    (RES / "sky130_ms_soft_reset_pulse.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"simulation_completed": completed, "candidate_screen_pass": report["candidate_screen_pass"],
                      "cases": len(measurements), "max_relative_step_error": max_error}, indent=2))
    return 0 if report["candidate_screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
