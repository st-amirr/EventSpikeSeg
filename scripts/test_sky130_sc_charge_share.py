"""Bounded SKY130 MIM switched-capacitor charge-sharing screen.

This tests the physical state dependence of a precharged MIM packet capacitor
connected through a real transmission gate. It is not a PLIF or weight cell.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VCM, VDD = 0.9, 1.8
STATES = (0.75, 0.9, 1.05)
PACKET_SIZES_UM = (10.0, 30.0, 100.0)
POLARITIES = ("positive", "negative")
STOP_US = 4.0

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


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 TT MIM packet-capacitor charge sharing", COMMON,
             f"Vdd vdd 0 {VDD}", f"Vcm vcm 0 {VCM}"]
    vectors: list[str] = []
    cases: list[dict[str, object]] = []
    for packet_um in PACKET_SIZES_UM:
        for state_index, initial in enumerate(STATES):
            for polarity in POLARITIES:
                name = f"c{int(packet_um)}_s{state_index}_{polarity[0]}"
                pre_v = VCM + 0.3 if polarity == "positive" else VCM - 0.3
                lines += [
                    f"Vpre_{name} pre_{name} 0 {pre_v}",
                    f"Vpen_{name} pen_{name} 0 PWL(0 1.8 0.999u 1.8 1u 0 4u 0)",
                    f"Vpenb_{name} penb_{name} 0 PWL(0 0 0.999u 0 1u 1.8 4u 1.8)",
                    f"Vinit_{name} init_{name} 0 {initial}",
                    f"Vien_{name} ien_{name} 0 PWL(0 1.8 0.999u 1.8 1u 0 4u 0)",
                    f"Vienb_{name} ienb_{name} 0 PWL(0 0 0.999u 0 1u 1.8 4u 1.8)",
                    f"Vten_{name} ten_{name} 0 PWL(0 0 1.999u 0 2u 1.8 2.999u 1.8 3u 0 4u 0)",
                    f"Vtenb_{name} tenb_{name} 0 PWL(0 1.8 1.999u 1.8 2u 0 2.999u 0 3u 1.8 4u 1.8)",
                    f"Xcm_{name} state_{name} vcm membrane_mim w_um=100 l_um=100",
                    f"Xcp_{name} packet_{name} vcm membrane_mim w_um={packet_um:g} l_um={packet_um:g}",
                    f"Xinit_{name} state_{name} init_{name} ien_{name} ienb_{name} vdd 0 transmission_gate",
                    f"Xpre_{name} packet_{name} pre_{name} pen_{name} penb_{name} vdd 0 transmission_gate",
                    f"Xxfer_{name} packet_{name} state_{name} ten_{name} tenb_{name} vdd 0 transmission_gate",
                ]
                vectors.append(f"v(state_{name})")
                cases.append({"name": name, "packet_size_um": packet_um,
                              "initial_membrane_v": initial, "polarity": polarity,
                              "precharge_v": pre_v})
    data_path = RES / "sky130_sc_charge_share.dat"
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 2n 4u uic",
              f"wrdata ../results/{data_path.name} {' '.join(vectors)}", "quit", ".endc", ".end"]
    deck = BENCH / "sky130_sc_charge_share.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = proc.stdout + proc.stderr
    (RES / "sky130_sc_charge_share.log").write_text(log, encoding="utf-8")
    if proc.returncode != 0 or not data_path.exists():
        report = {"test": "sky130_tt_mim_packet_capacitor_charge_share", "simulation_completed": False,
                  "exit_code": proc.returncode, "log": log[-4000:]}
        (RES / "sky130_sc_charge_share.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2
    rows = []
    for line in data_path.read_text(encoding="utf-8").splitlines()[1:]:
        try:
            rows.append([float(item) for item in line.split()])
        except ValueError:
            continue
    if not rows or len(rows[-1]) != len(cases) + 1:
        raise RuntimeError("ngspice output has missing or malformed final vector row")
    last = rows[-1]
    if any(not math.isfinite(value) for row in rows for value in row):
        raise RuntimeError("ngspice emitted a non-finite trace")
    for index, case in enumerate(cases):
        case["final_membrane_v"] = last[index + 1]
        case["signed_delta_v"] = last[index + 1] - float(case["initial_membrane_v"])
        case["abs_delta_v"] = abs(float(case["signed_delta_v"]))
    grouping: dict[str, dict[str, object]] = {}
    for packet_um in PACKET_SIZES_UM:
        group_cases = [x for x in cases if x["packet_size_um"] == packet_um]
        for polarity in POLARITIES:
            selected = [x for x in group_cases if x["polarity"] == polarity]
            deltas = [abs(float(x["signed_delta_v"])) for x in selected]
            ratio = max(deltas) / min(deltas) if min(deltas) > 0 else None
            grouping[f"{packet_um:g}um_{polarity}"] = {
                "absolute_delta_v_by_initial_state": deltas,
                "max_to_min_packet_gain_ratio_across_membrane_states": ratio,
                "state_independence_error_fraction_of_mean": (max(deltas) - min(deltas)) / (sum(deltas) / len(deltas)) if sum(deltas) else None,
                "correct_polarity_for_all_initial_states": all(
                    (float(x["signed_delta_v"]) > 0 if polarity == "positive" else float(x["signed_delta_v"]) < 0)
                    for x in selected
                ),
            }
    report = {
        "test": "sky130_tt_mim_packet_capacitor_charge_share",
        "simulation_completed": True,
        "exit_code": proc.returncode,
        "membrane_capacitor": "PDK MIM, 100um x 100um",
        "packet_capacitors": "PDK MIM at 10um, 30um, and 100um square; switched through SKY130 CMOS transmission gates",
        "precharge_levels_v": {"positive": VCM + 0.3, "negative": VCM - 0.3},
        "initial_membrane_v": list(STATES),
        "cases": cases,
        "state_dependence": grouping,
        "all_cases_finite_and_correct_sign": all(bool(x["correct_polarity_for_all_initial_states"]) for x in grouping.values()),
        "candidate_screen_pass": False,
        "candidate_screen_reason": "Characterization only: direct charge sharing is state dependent and no analog error bound or system-level scale has been selected.",
        "scope": "single precharged packet and direct charge sharing; no weight code, repeated-event schedule, full PLIF, amplifier, corners, mismatch or extraction",
    }
    (RES / "sky130_sc_charge_share.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(RES / "sky130_sc_charge_share.json"), "state_dependence": grouping}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
