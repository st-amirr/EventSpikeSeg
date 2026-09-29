"""Screen pulse-width transfer versus membrane common mode and long duration."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VDD, VCM = 1.8, 0.9
INITIAL_STATES_V = (0.75, 0.9, 1.05)
LOGICAL_WIDTHS_US = (0.05, 4.0, 100.0, 500.0)
PULSE_START_US = 10.0
STOP_US = 5000.0

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


def source(name: str, polarity: str, physical_width_us: float) -> str:
    stop = PULSE_START_US + physical_width_us
    if polarity == "positive":
        return (f"V{name} pg_{name} 0 PWL(0 1.8 {PULSE_START_US-0.001:g}u 1.8 "
                f"{PULSE_START_US:g}u 1.0 {stop:g}u 1.0 {stop+0.001:g}u 1.8 {STOP_US:g}u 1.8)")
    return (f"V{name} ng_{name} 0 PWL(0 0 {PULSE_START_US-0.001:g}u 0 "
            f"{PULSE_START_US:g}u 0.525 {stop:g}u 0.525 {stop+0.001:g}u 0 {STOP_US:g}u 0)")


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 TT pulse-width operating-range screen", COMMON,
             f"Vdd vdd 0 {VDD}", f"Vcm vcm 0 {VCM}", "Vcap capture 0 0",
             "Vcapb capture_b 0 1.8", "Vreset reset 0 0", "Vresetb reset_b 0 1.8",
             "Vleak leak_en 0 0", "Vleakb leak_enb 0 1.8", "Vbias vbias 0 0.65"]
    vectors: list[str] = []
    refs: dict[float, str] = {}
    cases: list[dict[str, object]] = []
    for state_index, initial_v in enumerate(INITIAL_STATES_V):
        ref = f"ref{state_index}"
        refs[initial_v] = ref
        lines += [f"V{ref}p pg_{ref} 0 1.8", f"V{ref}n ng_{ref} 0 0",
                  f"X{ref} {ref}_mem {ref}_snap {ref}_spike capture capture_b reset reset_b "
                  f"leak_en leak_enb pg_{ref} ng_{ref} vbias vdd 0 vcm "
                  "analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100",
                  f".ic v({ref}_mem)={initial_v-VCM:g}"]
        vectors.append(f"v({ref}_mem)")
        for polarity in ("positive", "negative"):
            duration_scale = 7.0 if polarity == "positive" else 1.0
            for width in LOGICAL_WIDTHS_US:
                name = f"s{state_index}_{polarity[0]}_{str(width).replace('.', 'p')}"
                physical = width * duration_scale
                if polarity == "positive":
                    lines += [source(name, polarity, physical), f"V{name}n ng_{name} 0 0"]
                else:
                    lines += [f"V{name}p pg_{name} 0 1.8", source(name, polarity, physical)]
                lines += [
                    f"X{name} {name}_mem {name}_snap {name}_spike capture capture_b reset reset_b "
                    f"leak_en leak_enb pg_{name} ng_{name} vbias vdd 0 vcm "
                    "analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100",
                    f".ic v({name}_mem)={initial_v-VCM:g}",
                ]
                vectors.append(f"v({name}_mem)")
                cases.append({"name": name, "initial_v": initial_v,
                              "polarity": polarity, "logical_width_us": width,
                              "physical_width_us": physical})
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 1u 5m uic",
              f"wrdata ../results/sky130_ms_pulse_width_operating_range.dat {' '.join(vectors)}",
              "quit", ".endc", ".end"]
    deck = BENCH / "sky130_ms_pulse_width_operating_range.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=140)
    (RES / "sky130_ms_pulse_width_operating_range.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    data = RES / "sky130_ms_pulse_width_operating_range.dat"
    rows = []
    header: list[str] = []
    if data.exists():
        raw_rows = data.read_text().splitlines()
        if raw_rows:
            header = raw_rows[0].split()
        for row in raw_rows[1:]:
            try:
                rows.append([float(v) for v in row.split()])
            except ValueError:
                continue
    final = rows[-1] if rows else []
    column = {name.lower(): i for i, name in enumerate(header)}
    measurements = []
    for case in cases:
        mem_name = f"v({case['name']}_mem)".lower()
        ref_name = f"v({refs[case['initial_v']]}_mem)".lower()
        if len(final) <= max(column.get(mem_name, 10**9), column.get(ref_name, 10**9)):
            continue
        delta = final[column[mem_name]] - final[column[ref_name]]
        measurements.append({**case, "signed_delta_v": delta})
    summary = {}
    for initial_v in INITIAL_STATES_V:
        summary[str(initial_v)] = {}
        for polarity in ("positive", "negative"):
            points = sorted((x for x in measurements if x["initial_v"] == initial_v and x["polarity"] == polarity),
                            key=lambda x: float(x["logical_width_us"]))
            deltas = [float(x["signed_delta_v"]) for x in points]
            correct = all(v > 0 for v in deltas) if polarity == "positive" else all(v < 0 for v in deltas)
            monotonic = all(a < b for a, b in zip(deltas, deltas[1:])) if polarity == "positive" else all(a > b for a, b in zip(deltas, deltas[1:]))
            per_us = [abs(v) / float(x["logical_width_us"]) for x, v in zip(points, deltas)]
            summary[str(initial_v)][polarity] = {
                "points": points,
                "correct_sign": correct,
                "monotonic_magnitude": monotonic,
                "gain_v_per_logical_us": per_us,
                "longest_case_fraction_of_vcm_to_rail": (
                    abs(deltas[-1]) / min(initial_v, VDD - initial_v) if deltas else None
                ),
            }
    completed = proc.returncode == 0 and len(rows) > 1 and len(measurements) == len(cases)
    monotonic_all = all(summary[str(v)][p]["correct_sign"] and summary[str(v)][p]["monotonic_magnitude"]
                        for v in INITIAL_STATES_V for p in ("positive", "negative"))
    report = {
        "test": "sky130_tt_pulse_duration_initial_state_and_long_width_screen",
        "simulation_completed": completed,
        "exit_code": proc.returncode,
        "membrane": "SKY130 PDK MIM 100um x 100um",
        "initial_membrane_v": list(INITIAL_STATES_V),
        "logical_width_us": list(LOGICAL_WIDTHS_US),
        "positive_duration_scale": 7.0,
        "negative_duration_scale": 1.0,
        "physical_pulse_max_us": max(float(x["physical_width_us"]) for x in cases),
        "update_bin_budget_us": STOP_US,
        "transfer_by_initial_state": summary,
        "all_states_both_signs_correct_and_monotonic": monotonic_all,
        "candidate_screen_pass": bool(completed and monotonic_all),
        "scope": "TT schematic MIM screen only; long widths can approach rails; one isolated event, no leak/reset, no PVT/mismatch/extraction, and no float-model weight mapping or 5ms population-service claim.",
    }
    (RES / "sky130_ms_pulse_width_operating_range.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"simulation_completed": completed, "candidate_screen_pass": report["candidate_screen_pass"],
                      "all_states_both_signs_correct_and_monotonic": monotonic_all,
                      "measurements": len(measurements), "rows": len(rows), "header": header[:8]}, indent=2))
    return 0 if report["candidate_screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
