"""Screen a MOS virtual-summing-node switched-cap charge integrator."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VCM = 0.9
STATES = (0.75, 0.9, 1.05)
POLARITIES = ("positive", "negative")
PACKET_SIZES_UM = (1.0, 3.0, 10.0)
STOP_US = 5.0

COMMON = """.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
"""


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 TT MOS charge integrator schematic screen", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbp vbiasp 0 0.75"]
    vectors: list[str] = []
    cases: list[dict[str, object]] = []
    for packet_um in PACKET_SIZES_UM:
      for state_index, state in enumerate(STATES):
        for polarity in POLARITIES:
            name = f"s{state_index}_c{int(packet_um)}_{polarity[0]}"
            packet_v = 1.2 if polarity == "positive" else 0.6
            lines += [
                f"Vinitlvl_{name} initlvl_{name} 0 {state}",
                f"Vbn_{name} vbiasn_{name} 0 0.65",
                f"Vinit_{name} init_{name} 0 0", f"Vinitb_{name} initb_{name} 0 1.8",
                f".ic v(out_{name})={state - VCM} v(sum_{name})={VCM}",
                f"Vreset_{name} reset_{name} 0 0", f"Vresetb_{name} resetb_{name} 0 1.8",
                f"Vpacket_reset_{name} packet_reset_{name} 0 0", f"Vpacket_resetb_{name} packet_resetb_{name} 0 1.8",
                f"Vconn_{name} conn_{name} 0 PWL(0 0 0.499u 0 0.5u 1.8 2.499u 1.8 2.5u 0 {STOP_US}u 0)",
                f"Vconnb_{name} connb_{name} 0 PWL(0 1.8 0.499u 1.8 0.5u 0 2.499u 0 2.5u 1.8 {STOP_US}u 1.8)",
                f"Vpkt_{name} ptop_{name} 0 PWL(0 0.9 0.999u 0.9 1u {packet_v} 2.499u {packet_v} 2.5u 0.9 {STOP_US}u 0.9)",
                f"Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} initlvl_{name} init_{name} initb_{name} conn_{name} connb_{name} vbiasn_{name} vbiasp vdd 0 vcm sky130_sc_charge_integrator cpacket_um={packet_um:g}",
            ]
            vectors += [f"v(out_{name})", f"v(sum_{name})"]
            cases.append({"name": name, "initial_membrane_v": state, "packet_size_um": packet_um, "polarity": polarity,
                          "packet_step_v": packet_v - VCM})
    data_path = RES / "sky130_sc_charge_integrator.dat"
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 5n 5u uic",
              f"wrdata ../results/{data_path.name} {' '.join(vectors)}", "quit", ".endc", ".end"]
    deck = BENCH / "sky130_sc_charge_integrator.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = proc.stdout + proc.stderr
    (RES / "sky130_sc_charge_integrator.log").write_text(log, encoding="utf-8")
    rows = []
    if data_path.exists():
        for line in data_path.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                continue
    report: dict[str, object] = {"test": "sky130_tt_mos_virtual_summing_node_charge_integrator",
                                 "simulation_completed": proc.returncode == 0 and bool(rows),
                                 "exit_code": proc.returncode,
                                 "cell": "two-stage MOS OTA, PDK MIM feedback and 1/3/10um packet capacitors, PDK TG packet isolation, 1e15-ohm DC feedback path",
                                 "cases": cases}
    if not report["simulation_completed"] or len(rows[-1]) != 1 + 2 * len(cases):
        report["log_tail"] = log[-4000:]
        (RES / "sky130_sc_charge_integrator.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2
    times = [row[0] for row in rows]
    sampled_times_us = (1.05, 1.1, 1.2, 1.5, 2.1, 2.4, 3.5)
    for i, case in enumerate(cases):
        state_i = 1 + 2 * i
        state_pre = min(range(len(times)), key=lambda j: abs(times[j] - 0.9e-6))
        state_post = min(range(len(times)), key=lambda j: abs(times[j] - 3.5e-6))
        initial_v = rows[state_pre][state_i]
        final_v = rows[state_post][state_i]
        sum_node = rows[state_post][state_i + 1]
        case["pre_packet_state_v_at_0p9us"] = initial_v
        case["requested_state_initialization_error_v"] = initial_v - float(case["initial_membrane_v"])
        case["final_state_v_at_3p5us"] = final_v
        case["signed_state_change_v"] = final_v - initial_v
        case["final_virtual_sum_node_v"] = sum_node
        case["virtual_ground_error_v"] = sum_node - VCM
        # The chosen charge-amplifier input is inverting: positive packet swing
        # should move the stored output down; negative packet swing moves it up.
        case["correct_sign"] = (final_v < initial_v if case["polarity"] == "positive" else final_v > initial_v)
        final_delta = final_v - initial_v
        crossed = [j for j, row in enumerate(rows) if times[j] >= 1.0e-6 and
                   ((row[state_i] - initial_v <= 0.9 * final_delta) if final_delta < 0 else
                    (row[state_i] - initial_v >= 0.9 * final_delta))]
        case["response_time_us_to_90pct_of_final_packet_delta"] = (times[crossed[0]] - 1.0e-6) * 1e6 if crossed else None
        case["transient_samples_us"] = [
            {"time_us": sample_us,
             "state_v": rows[min(range(len(times)), key=lambda j: abs(times[j] - sample_us * 1e-6))][state_i],
             "virtual_sum_v": rows[min(range(len(times)), key=lambda j: abs(times[j] - sample_us * 1e-6))][state_i + 1]}
            for sample_us in sampled_times_us
        ]
    deltas_by_polarity = {}
    for packet_um in PACKET_SIZES_UM:
      for polarity in POLARITIES:
        selected = [x for x in cases if x["polarity"] == polarity and x["packet_size_um"] == packet_um]
        deltas = [abs(float(x["signed_state_change_v"])) for x in selected]
        deltas_by_polarity[f"{packet_um:g}um_{polarity}"] = {
            "abs_delta_v_by_initial_state": deltas,
            "max_to_min_gain_ratio_across_membrane_states": max(deltas) / min(deltas) if min(deltas) else None,
        }
    values = [v for row in rows for v in row]
    report.update({
        "transient_end_time_s": times[-1],
        "trace_finite": all(math.isfinite(x) for x in values),
        "polarity_sensitivity": deltas_by_polarity,
        "all_cases_correct_sign": all(bool(case["correct_sign"]) for case in cases),
        "max_abs_virtual_ground_error_v": max(abs(float(case["virtual_ground_error_v"])) for case in cases),
        "max_requested_state_initialization_error_v": max(abs(float(case["requested_state_initialization_error_v"])) for case in cases),
        "network_sign_mapping_requires_inversion": True,
        "state_initialization_fixture": "ngspice .ic preloads the capacitor differential state correctly; physical initialization through the cell reset path is not tested",
        "state_initialization_qualified": False,
        "candidate_screen_pass": False,
        "candidate_screen_reason": "Nominal transistor-level packet transfer is state independent under correct ideal initial conditions, but no gain/settling/linearity budget is selected, physical state initialization is untested, corners/mismatch/extraction are absent, and tail/second-stage bias rails are ideal.",
        "scope": "three membrane initial states, 1/3/10um-square MIM packet capacitors, one fixed 0.3V packet step per sign, transistor-level TT transient; initial states use differential .ic and are not generated by a qualified physical reset circuit; no full model mapping or timing schedule",
    })
    (RES / "sky130_sc_charge_integrator.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(RES / "sky130_sc_charge_integrator.json"),
                      "simulation_completed": report["simulation_completed"],
                      "polarity_sensitivity": deltas_by_polarity,
                      "max_abs_virtual_ground_error_v": report["max_abs_virtual_ground_error_v"],
                      "correct_sign": report["all_cases_correct_sign"]}, indent=2))
    return 0 if report["simulation_completed"] and report["trace_finite"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
