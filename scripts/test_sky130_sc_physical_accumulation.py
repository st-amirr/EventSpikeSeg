"""Test physically initialized, held SC state under repeated signed packets."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
STATES = (0.75, 0.90, 1.05)
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


def cell(name: str, state: float, sequence: str | None, long_bin: bool = False, precharge: bool = False, sleep: bool = False, softstart: bool = False, membrane_cap_um: float = 100.0, packet_cap_um: float = 1.0) -> list[str]:
    def polarity(which: int) -> float:
        if sequence is None:
            return 0.9
        if sequence[which] == "z":
            return 0.9
        return 1.2 if sequence[which] == "p" else 0.6

    if long_bin:
        packet = (f"PWL(0 0.9 499.9u 0.9 500u {polarity(0):g} 501.9u {polarity(0):g} 502u 0.9 "
                  f"4.4999m 0.9 4.5m {polarity(1):g} 4.5019m {polarity(1):g} 4.502m 0.9 5.005m 0.9)")
        conn = "PWL(0 0 499u 0 499.1u 1.8 501.9u 1.8 502u 0 4.499m 0 4.4991m 1.8 4.5019m 1.8 4.502m 0 5.005m 0)"
        connb = "PWL(0 1.8 499u 1.8 499.1u 0 501.9u 0 502u 1.8 4.499m 1.8 4.4991m 0 4.5019m 0 4.502m 1.8 5.005m 1.8)"
        reset = "PWL(0 0 399u 0 400u 1.8 449u 1.8 450u 0 4.099m 0 4.1m 1.8 4.349m 1.8 4.35m 0 5.005m 0)"
        resetb = "PWL(0 1.8 399u 1.8 400u 0 449u 0 450u 1.8 4.099m 1.8 4.1m 0 4.349m 0 4.35m 1.8 5.005m 1.8)"
        amp = "PWL(0 0 499u 0 499.1u 1.8 502.4u 1.8 502.5u 0 4.499m 0 4.4991m 1.8 4.5024m 1.8 4.5025m 0 5.005m 0)"
        ampb = "PWL(0 1.8 499u 1.8 499.1u 0 502.4u 0 502.5u 1.8 4.499m 1.8 4.4991m 0 4.5024m 0 4.5025m 1.8 5.005m 1.8)"
    else:
        packet = (f"PWL(0 0.9 3.499u 0.9 3.5u {polarity(0):g} 4.9u {polarity(0):g} 4.91u 0.9 "
                  f"5.999u 0.9 6u {polarity(1):g} 7.4u {polarity(1):g} 7.41u 0.9 8u 0.9)")
        conn = "PWL(0 0 2.999u 0 3u 1.8 4.899u 1.8 4.9u 0 5.499u 0 5.5u 1.8 7.399u 1.8 7.4u 0 8u 0)"
        connb = "PWL(0 1.8 2.999u 1.8 3u 0 4.899u 0 4.9u 1.8 5.499u 1.8 5.5u 0 7.399u 0 7.4u 1.8 8u 1.8)"
        reset = "PWL(0 0 2.699u 0 2.7u 1.8 2.949u 1.8 2.95u 0 5.099u 0 5.1u 1.8 5.349u 1.8 5.35u 0 8u 0)"
        resetb = "PWL(0 1.8 2.699u 1.8 2.7u 0 2.949u 0 2.95u 1.8 5.099u 1.8 5.1u 0 5.349u 0 5.35u 1.8 8u 1.8)"
        amp = "PWL(0 0 2.999u 0 3u 1.8 4.899u 1.8 4.9u 0 5.499u 0 5.5u 1.8 7.399u 1.8 7.4u 0 8u 0)"
        ampb = "PWL(0 1.8 2.999u 1.8 3u 0 4.899u 0 4.9u 1.8 5.499u 1.8 5.5u 0 7.399u 0 7.4u 1.8 8u 1.8)"
    if precharge:
        precharge_signal = "PWL(0 0 498.49u 0 498.5u 1.8 498.9u 1.8 498.91u 0 4.49849m 0 4.4985m 1.8 4.4989m 1.8 4.49891m 0 5.005m 0)"
        precharge_bar_signal = "PWL(0 1.8 498.49u 1.8 498.5u 0 498.9u 0 498.91u 1.8 4.49849m 1.8 4.4985m 0 4.4989m 0 4.49891m 1.8 5.005m 1.8)"
        precharge_nodes = [f"Vprecharge_{name} precharge_{name} 0 {precharge_signal}",
                           f"Vprechargeb_{name} prechargeb_{name} 0 {precharge_bar_signal}"]
        precharge_pins = f"precharge_{name} prechargeb_{name} "
        cell_type = "sky130_sc_charge_integrator_sleep_precharged" if sleep else "sky130_sc_charge_integrator_precharged"
    else:
        precharge_nodes = []
        precharge_pins = ""
        cell_type = "sky130_sc_charge_integrator_sleep" if sleep else "sky130_sc_charge_integrator_held"
    if softstart:
        bias_sources = [
            f"Vbn_{name} vbiasn_{name} 0 PWL(0 0.65 499u 0.65 499.1u 0 499.6u 0.65 4.499m 0.65 4.4991m 0 4.4996m 0.65 5.005m 0.65)",
            f"Vbp_{name} vbiasp_{name} 0 PWL(0 0.75 499u 0.75 499.1u 1.8 499.6u 0.75 4.499m 0.75 4.4991m 1.8 4.4996m 0.75 5.005m 0.75)",
        ]
    else:
        bias_sources = [f"Vbn_{name} vbiasn_{name} 0 0.65", f"Vbp_{name} vbiasp_{name} 0 0.75"]
    return [
        *bias_sources,
        f"Vinitlvl_{name} initlvl_{name} 0 {state:g}",
        f"Vinit_{name} init_{name} 0 PWL(0 1.8 2.499u 1.8 2.5u 0 8u 0)",
        f"Vinitb_{name} initb_{name} 0 PWL(0 0 2.499u 0 2.5u 1.8 8u 1.8)",
        f".ic v(out_{name})={state:g} v(sum_{name})=0.9",
        f"Vreset_{name} reset_{name} 0 0",
        f"Vresetb_{name} resetb_{name} 0 1.8",
        f"VpacketReset_{name} packet_reset_{name} 0 {reset}",
        f"VpacketResetb_{name} packet_resetb_{name} 0 {resetb}",
        f"Vconn_{name} conn_{name} 0 {conn}",
        f"Vconnb_{name} connb_{name} 0 {connb}",
        f"Vamp_{name} amp_{name} 0 {amp}",
        f"Vampb_{name} ampb_{name} 0 {ampb}",
        *precharge_nodes,
        f"Vpkt_{name} ptop_{name} 0 {packet}",
        f"Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} initlvl_{name} init_{name} initb_{name} conn_{name} connb_{name} amp_{name} ampb_{name} {precharge_pins}vbiasn_{name} vbiasp_{name} vdd 0 vcm {cell_type} cmem_um={membrane_cap_um:g} cpacket_um={packet_cap_um:g}",
    ]


def main() -> int:
    use_combo = "--long-bin-sleep-precharge" in sys.argv
    use_softstart = "--long-bin-sleep-ramp" in sys.argv
    use_precharge = "--long-bin-precharge" in sys.argv or use_combo
    use_sleep = "--long-bin-sleep" in sys.argv or use_combo or use_softstart
    long_bin = "--long-bin" in sys.argv or use_precharge or use_sleep
    active_states = (0.90,) if long_bin else STATES
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 TT physical init, held state and repeated signed packet accumulation", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    names: list[str] = []
    cases: list[dict[str, object]] = []
    for state in active_states:
        state_i = STATES.index(state)
        for sequence in SEQUENCES:
            name = f"s{state_i}_{sequence}"
            names.append(name)
            lines += cell(name, state, sequence, long_bin, use_precharge, use_sleep, use_softstart)
            cases.append({"name": name, "initial_state_v": state, "sequence": sequence})
        name = f"s{state_i}_baseline"
        names.append(name)
        lines += cell(name, state, None, long_bin, use_precharge, use_sleep, use_softstart)
    vectors = " ".join(f"v(out_{name}) v(sum_{name})" for name in names)
    suffix = "long_bin_sleep_ramp" if use_softstart else ("long_bin_sleep_precharge" if use_combo else ("long_bin_precharge" if use_precharge else ("long_bin_sleep" if use_sleep else ("long_bin" if long_bin else "short"))))
    data = RES / f"sky130_sc_physical_accumulation_{suffix}.dat"
    stop, step = ("5.005m", "100n") if long_bin else ("8u", "5n")
    lines += [".control", "set wr_singlescale", "set wr_vecnames", f"tran {step} {stop} uic",
              f"wrdata ../results/{data.name} {vectors}", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_physical_accumulation_{suffix}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_sc_physical_accumulation_{suffix}.log").write_text(log, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                pass
    completed = proc.returncode == 0 and bool(rows) and len(rows[-1]) == 1 + 2 * len(names)
    report_path = RES / (f"sky130_sc_physical_{suffix}_accumulation.json" if long_bin else "sky130_sc_physical_accumulation.json")
    report: dict[str, object] = {"test": "sky130_tt_physical_init_two_signed_packets_over_5ms_bin_with_slow_ota_bias_wakeup" if use_softstart else ("sky130_tt_physical_init_two_signed_packets_over_5ms_bin_with_ota_sleep_and_output_precharge" if use_combo else ("sky130_tt_physical_init_two_signed_packets_over_5ms_bin_with_ota_sleep" if use_sleep else ("sky130_tt_physical_init_two_signed_packets_over_5ms_bin_with_output_precharge" if use_precharge else ("sky130_tt_physical_init_two_signed_packets_over_5ms_bin" if long_bin else "sky130_tt_physical_init_two_signed_packets")))), "simulation_completed": completed,
        "mapping_qualified": False, "sequence_order": "connect packet; top-plate step; disconnect packet and OTA; return top plate; repeat",
        "packet_cell": "1um-square PDK MIM packet; 100um-square MIM membrane; held-output two-stage MOS OTA; physical TG initialization",
        "cases": cases, "scope": "nominal TT schematic; initialized from transistor TG, 2.5us init plus 0.5us guard; two packets with phase-safe disconnect; no PVT, mismatch, extraction, noise or model accuracy"}
    if not completed:
        report["exit_code"] = proc.returncode
        report["log_tail"] = log[-4000:]
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"simulation_completed": False, "exit_code": proc.returncode}, indent=2))
        return 2
    times = [r[0] for r in rows]
    before_i = min(range(len(times)), key=lambda i: abs(times[i] - 2.9e-6))
    after_time = 5.0e-3 if long_bin else 7.8e-6
    after_i = min(range(len(times)), key=lambda i: abs(times[i] - after_time))
    first_post_i = min(range(len(times)), key=lambda i: abs(times[i] - (0.5025e-3 if long_bin else 4.95e-6)))
    before_second_i = min(range(len(times)), key=lambda i: abs(times[i] - (4.499e-3 if long_bin else 5.95e-6)))
    for case in cases:
        n = names.index(str(case["name"]))
        baseline_n = names.index(f"s{STATES.index(float(case['initial_state_v']))}_baseline")
        initial = rows[before_i][1 + 2*n]
        final = rows[after_i][1 + 2*n]
        baseline_change = rows[after_i][1 + 2*baseline_n] - rows[before_i][1 + 2*baseline_n]
        case["physical_init_error_v"] = initial - float(case["initial_state_v"])
        case["raw_two_packet_change_v"] = final - initial
        case["no_event_two_window_drift_v"] = baseline_change
        case["corrected_two_packet_change_v"] = final - initial - baseline_change
        expected = sum((-1 if pol == "p" else 1) * 41.15e-6 for pol in str(case["sequence"]))
        case["reference_sum_from_single_packet_screen_v"] = expected
        case["accumulation_error_v"] = float(case["corrected_two_packet_change_v"]) - expected
        if long_bin:
            first_increment = rows[first_post_i][1 + 2*n] - rows[first_post_i][1 + 2*baseline_n]
            held_increment = rows[before_second_i][1 + 2*n] - rows[before_second_i][1 + 2*baseline_n]
            first_sign = -1 if str(case["sequence"])[0] == "p" else 1
            second_sign = -1 if str(case["sequence"])[1] == "p" else 1
            case["first_packet_increment_after_first_window_v"] = first_increment
            case["first_packet_increment_before_second_window_v"] = held_increment
            case["first_packet_increment_hold_change_over_4ms_v"] = held_increment - first_increment
            case["first_packet_increment_error_v"] = first_increment - first_sign * 41.15e-6
            case["second_packet_increment_v"] = float(case["corrected_two_packet_change_v"]) - held_increment
            case["second_packet_increment_error_v"] = float(case["second_packet_increment_v"]) - second_sign * 41.15e-6
    order_errors = []
    for state in active_states:
        pn = next(c for c in cases if c["initial_state_v"] == state and c["sequence"] == "pn")
        np_ = next(c for c in cases if c["initial_state_v"] == state and c["sequence"] == "np")
        order_errors.append(abs(float(pn["corrected_two_packet_change_v"]) - float(np_["corrected_two_packet_change_v"])))
    report["max_abs_physical_init_error_v"] = max(abs(float(c["physical_init_error_v"])) for c in cases)
    report["max_abs_accumulation_error_v"] = max(abs(float(c["accumulation_error_v"])) for c in cases)
    report["max_pn_np_order_difference_v"] = max(order_errors)
    if long_bin:
        report["max_abs_first_packet_hold_change_over_4ms_v"] = max(abs(float(c["first_packet_increment_hold_change_over_4ms_v"])) for c in cases)
        report["max_abs_first_packet_increment_error_v"] = max(abs(float(c["first_packet_increment_error_v"])) for c in cases)
        report["max_abs_second_packet_increment_error_v"] = max(abs(float(c["second_packet_increment_error_v"])) for c in cases)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("simulation_completed", "max_abs_physical_init_error_v", "max_abs_accumulation_error_v", "max_pn_np_order_difference_v")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
