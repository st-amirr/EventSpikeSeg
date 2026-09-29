"""Check signed two-packet accumulation/order on the MOS charge integrator."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VCM, STOP_US = 0.9, 7.0
STATES = (0.75, 0.9, 1.05)
SEQUENCES = ("pp", "nn", "pn", "np")

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
    lines = ["SKY130 TT charge-integrator two-packet signed accumulation", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbp vbiasp 0 0.75"]
    vectors: list[str] = []
    cases: list[dict[str, object]] = []
    for state_index, state in enumerate(STATES):
        for sequence in SEQUENCES:
            name = f"s{state_index}_{sequence}"
            lines += [
                f"Vbn_{name} vbiasn_{name} 0 0.65",
                f"Vinitlvl_{name} initlvl_{name} 0 {state}",
                f"Vinit_{name} init_{name} 0 0", f"Vinitb_{name} initb_{name} 0 1.8",
                f".ic v(out_{name})={state - VCM} v(sum_{name})={VCM}",
                f"Vreset_{name} reset_{name} 0 0", f"Vresetb_{name} resetb_{name} 0 1.8",
                f"VpacketReset_{name} packet_reset_{name} 0 PWL(0 1.8 0.499u 1.8 0.5u 0 2.549u 0 2.55u 1.8 2.849u 1.8 2.85u 0 4.949u 0 4.95u 1.8 5.249u 1.8 5.25u 0 {STOP_US}u 0)",
                f"VpacketResetb_{name} packet_resetb_{name} 0 PWL(0 0 0.499u 0 0.5u 1.8 2.549u 1.8 2.55u 0 2.849u 0 2.85u 1.8 4.949u 1.8 4.95u 0 5.249u 0 5.25u 1.8 {STOP_US}u 1.8)",
                f"Vconn_{name} conn_{name} 0 PWL(0 0 0.499u 0 0.5u 1.8 2.399u 1.8 2.4u 0 2.999u 0 3u 1.8 4.899u 1.8 4.9u 0 {STOP_US}u 0)",
                f"Vconnb_{name} connb_{name} 0 PWL(0 1.8 0.499u 1.8 0.5u 0 2.399u 0 2.4u 1.8 2.999u 1.8 3u 0 4.899u 0 4.9u 1.8 {STOP_US}u 1.8)",
                f"Vpkt_{name} ptop_{name} 0 PWL(0 0.9 0.999u 0.9 1u {1.2 if sequence[0] == 'p' else 0.6} 2.499u {1.2 if sequence[0] == 'p' else 0.6} 2.5u 0.9 3.499u 0.9 3.5u {1.2 if sequence[1] == 'p' else 0.6} 4.999u {1.2 if sequence[1] == 'p' else 0.6} 5u 0.9 {STOP_US}u 0.9)",
                f"Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} initlvl_{name} init_{name} initb_{name} conn_{name} connb_{name} vbiasn_{name} vbiasp vdd 0 vcm sky130_sc_charge_integrator cpacket_um=10",
            ]
            vectors += [f"v(out_{name})", f"v(sum_{name})"]
            cases.append({"name": name, "initial_state_v": state, "sequence": sequence})
    data_path = RES / "sky130_sc_charge_integrator_accumulation.dat"
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 5n 7u uic",
              f"wrdata ../results/{data_path.name} {' '.join(vectors)}", "quit", ".endc", ".end"]
    deck = BENCH / "sky130_sc_charge_integrator_accumulation.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = proc.stdout + proc.stderr
    (RES / "sky130_sc_charge_integrator_accumulation.log").write_text(log, encoding="utf-8")
    rows = []
    if data_path.exists():
        for line in data_path.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                continue
    report: dict[str, object] = {
        "test": "sky130_tt_mos_virtual_summing_node_signed_two_packet_accumulation",
        "simulation_completed": proc.returncode == 0 and bool(rows),
        "exit_code": proc.returncode,
        "sequence_order": "positive-positive, negative-negative, positive-negative, negative-positive",
        "packet_cell": "10um-square PDK MIM packet, 0.3V top-plate excursion, two-stage MOS OTA, MIM feedback cap",
        "cases": cases,
    }
    if not report["simulation_completed"] or len(rows[-1]) != 1 + 2 * len(cases):
        report["log_tail"] = log[-4000:]
        (RES / "sky130_sc_charge_integrator_accumulation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2
    times = [row[0] for row in rows]
    sample_i = min(range(len(times)), key=lambda i: abs(times[i] - 6.5e-6))
    baseline_i = min(range(len(times)), key=lambda i: abs(times[i] - 0.9e-6))
    trace_sample_times_us = (0.9, 2.4, 2.8, 3.4, 4.9, 5.3, 6.5)
    for i, case in enumerate(cases):
        case["final_state_v"] = rows[sample_i][1 + 2 * i]
        case["pre_packet_state_v"] = rows[baseline_i][1 + 2 * i]
        case["final_sum_v"] = rows[sample_i][2 + 2 * i]
        case["state_change_v"] = float(case["final_state_v"]) - float(case["pre_packet_state_v"])
        case["transient_state_samples"] = [
            {"time_us": sample_us,
             "state_v": rows[min(range(len(times)), key=lambda j: abs(times[j] - sample_us * 1e-6))][1 + 2 * i],
             "sum_v": rows[min(range(len(times)), key=lambda j: abs(times[j] - sample_us * 1e-6))][2 + 2 * i]}
            for sample_us in trace_sample_times_us
        ]
    single = json.loads((RES / "sky130_sc_charge_integrator.json").read_text(encoding="utf-8"))
    one_event_delta = {}
    for state in STATES:
        for polarity, first in (("p", "positive"), ("n", "negative")):
            sample = next(x for x in single["cases"] if float(x["packet_size_um"]) == 10.0 and
                          float(x["initial_membrane_v"]) == state and x["polarity"] == first)
            one_event_delta[(state, polarity)] = float(sample["signed_state_change_v"])
    for case in cases:
        state, sequence = float(case["initial_state_v"]), str(case["sequence"])
        expected = sum(one_event_delta[(state, polarity)] for polarity in sequence)
        case["independent_single_packet_expected_change_v"] = expected
        case["accumulation_error_v"] = float(case["state_change_v"]) - expected
    order_errors = []
    for state in STATES:
        pn = next(x for x in cases if x["initial_state_v"] == state and x["sequence"] == "pn")
        np_ = next(x for x in cases if x["initial_state_v"] == state and x["sequence"] == "np")
        order_errors.append(abs(float(pn["state_change_v"]) - float(np_["state_change_v"])))
    values = [value for row in rows for value in row]
    report.update({
        "transient_end_time_s": times[-1],
        "trace_finite": all(math.isfinite(value) for value in values),
        "max_absolute_error_from_independent_packet_sum_v": max(abs(float(x["accumulation_error_v"])) for x in cases),
        "max_pn_np_order_residual_v": max(order_errors),
        "candidate_screen_pass": False,
        "candidate_screen_reason": "Characterization only; no model-derived error budget, repeated-event timing, corners, mismatch or extraction.",
        "scope": "two events in a 7us TT schematic transient at three state voltages; ideal fixed ±0.3V packet sources, one capacitor, break-before-make packet disconnect/reset/reconnect phases; no model-weight selection or physical bias generation",
    })
    (RES / "sky130_sc_charge_integrator_accumulation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(RES / "sky130_sc_charge_integrator_accumulation.json"),
                      "max_sum_error_v": report["max_absolute_error_from_independent_packet_sum_v"],
                      "max_order_residual_v": report["max_pn_np_order_residual_v"]}, indent=2))
    return 0 if report["simulation_completed"] and report["trace_finite"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
