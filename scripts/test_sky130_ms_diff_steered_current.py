"""Bounded SKY130 differential, pulse-steered constant-current screen.

Separate rail-biased MOS current sources feed the two MIM state nodes through
TG switches; idle TGs clamp the unused current-source outputs to the rails.
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
RES = OUT / "results"

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
    arg = lambda name, default: next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith(name + "=")), str(default))
    count = int(arg("--events", 100))
    cap_um = float(arg("--membrane-cap-um", 20))
    pulse_us = float(arg("--pulse-us", 0.14))
    period_us = float(arg("--period-us", 49))
    l_um = float(arg("--injector-length-um", 10))
    tg_length_um = float(arg("--tg-length-um", 10))
    tg_width_um = float(arg("--tg-width-um", 10))
    max_step_ns = float(arg("--max-step-ns", 10))
    timeout_s = int(arg("--timeout-s", 180))
    p_gate_bias = float(arg("--p-gate-bias", 0.72))
    n_gate_bias = float(arg("--n-gate-bias", 0.6))
    mixed_start = arg("--mixed-start", "p")
    selected_cases = [x for x in arg("--cases", "ref,p_one,n_one,p_train,n_train,mixed_train").split(",") if x]
    if min(count, cap_um, pulse_us, period_us, l_um, tg_length_um, tg_width_um, max_step_ns, timeout_s) <= 0:
        raise ValueError("count, geometry, timing, and timeout must be positive")
    if pulse_us <= 2 * max_step_ns * 1e-3:
        raise ValueError("pulse must exceed two transient time steps")
    if mixed_start not in {"p", "n"}:
        raise ValueError("mixed start polarity must be p or n")
    event_times = [100.0 + i * period_us for i in range(count)]
    if event_times[-1] + pulse_us + 0.01 >= 5000:
        raise ValueError("event train must finish before 5ms")

    cases: dict[str, list[tuple[int, str]]] = {
        "ref": [], "p_one": [(0, "p")], "n_one": [(0, "n")],
        "p_train": [(i, "p") for i in range(count)],
        "n_train": [(i, "n") for i in range(count)],
        "mixed_train": [(i, mixed_start if i % 2 == 0 else ("n" if mixed_start == "p" else "p")) for i in range(count)],
    }
    unknown_cases = set(selected_cases) - set(cases)
    if unknown_cases:
        raise ValueError(f"unknown cases: {sorted(unknown_cases)}")
    cases = {name: cases[name] for name in selected_cases}

    def waveform(case: str, event_sign: str) -> str:
        off, active = 0.0, 1.8
        points = [(0.0, off)]
        for idx, sign in cases[case]:
            if sign != event_sign:
                continue
            start = event_times[idx]
            points += [(start - 0.01, off), (start, active), (start + pulse_us, active), (start + pulse_us + 0.01, off)]
        points.append((5005.0, off))
        return "PWL(" + " ".join(f"{t:g}u {v:g}" for t, v in points) + ")"

    lines = ["SKY130 differential pulse-steered current-source injection into a matched MIM pair", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             f"Vbp vbp 0 {p_gate_bias:g}", f"Vbn vbn 0 {n_gate_bias:g}",
             ".subckt diff_tg_long a b en enb vdd vss",
             f"Xn1 a en mid vss sky130_fd_pr__nfet_01v8 w={tg_width_um:g} l={tg_length_um:g}",
             f"Xp1 a enb mid vdd sky130_fd_pr__pfet_01v8 w={2*tg_width_um:g} l={tg_length_um:g}",
             f"Xn2 mid en b vss sky130_fd_pr__nfet_01v8 w={tg_width_um:g} l={tg_length_um:g}",
             f"Xp2 mid enb b vdd sky130_fd_pr__pfet_01v8 w={2*tg_width_um:g} l={tg_length_um:g}",
             ".ends diff_tg_long",
             f".subckt diff_steered vp vn ep epb en enb cp cpb cn cnb vbp vbn vdd vss params: wp=1.5 wn=1 l={l_um:g}",
             "Xp_src vp_src vbp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}",
             "Xn_sink vp_sink vbn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}",
             "Xp_src_n vn_src vbp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}",
             "Xn_sink_n vn_sink vbn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}",
             "Xsw_pp vp_src vp ep epb vdd vss diff_tg_long",
             "Xsw_np vp_sink vp en enb vdd vss diff_tg_long",
             "Xsw_pn vn_src vn en enb vdd vss diff_tg_long",
             "Xsw_nn vn_sink vn ep epb vdd vss diff_tg_long",
             "Xclamp_pp vp_src vdd cp cpb vdd vss diff_tg_long",
             "Xclamp_np vp_sink vss cn cnb vdd vss diff_tg_long",
             "Xclamp_pn vn_src vdd cn cnb vdd vss diff_tg_long",
             "Xclamp_nn vn_sink vss cp cpb vdd vss diff_tg_long",
             ".ends diff_steered"]
    for name in cases:
        vp, vn = f"vp_{name}", f"vn_{name}"
        event_p = waveform(name, "p")
        event_n = waveform(name, "n")
        event_pb = "PWL(" + " ".join(f"{float(t):g}u {1.8-float(v):g}" for t, v in re.findall(r"([0-9.eE+-]+)u ([0-9.eE+-]+)", event_p)) + ")"
        event_nb = "PWL(" + " ".join(f"{float(t):g}u {1.8-float(v):g}" for t, v in re.findall(r"([0-9.eE+-]+)u ([0-9.eE+-]+)", event_n)) + ")"
        lines += [f"Xmem_p_{name} {vp} vcm membrane_mim w_um={cap_um:g} l_um={cap_um:g}",
                  f"Xmem_n_{name} {vn} vcm membrane_mim w_um={cap_um:g} l_um={cap_um:g}",
                  f".ic v({vp})=0", f".ic v({vn})=0",
                  f"Vep_{name} ep_{name} 0 {event_p}", f"Vepb_{name} epb_{name} 0 {event_pb}",
                  f"Ven_{name} en_{name} 0 {event_n}", f"Venb_{name} enb_{name} 0 {event_nb}",
                  f"Xinj_{name} {vp} {vn} ep_{name} epb_{name} en_{name} enb_{name} epb_{name} ep_{name} enb_{name} en_{name} vbp vbn vdd 0 diff_steered"]
    lines += [".control", "set numdgt=15", f"tran {max_step_ns:g}n 5.005m uic"]
    for phase, time in (("early", "1u"), ("mid", "1m"), ("final", "5m")):
        for name in cases:
            lines += [f"meas tran {phase}_vp_{name} find v(vp_{name}) at={time}",
                      f"meas tran {phase}_vn_{name} find v(vn_{name}) at={time}"]
    lines += ["quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    tag = f"n{count}_w{pulse_us:g}u_cm{cap_um:g}_period{period_us:g}u_il{l_um:g}_tg{tg_width_um:g}x{tg_length_um:g}_bp{p_gate_bias:g}_bn{n_gate_bias:g}_mix{mixed_start}_cases{'-'.join(selected_cases)}_s{max_step_ns:g}n"
    deck = BENCH / f"sky130_ms_diff_steered_current_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", str(timeout_s), "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 15)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_ms_diff_steered_current_{tag}.log").write_text(log, encoding="utf-8")
    measured = {f"{phase}_{node}_{case}": float(value) for phase, node, case, value in
                re.findall(r"(?im)^\s*(early|mid|final)_(vp|vn)_([a-z_]+)\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and len(measured) == 3 * 2 * len(cases)
    result: dict[str, object] = {
        "test": "sky130_tt_differential_pulse_steered_current_source_many_events",
        "simulation_completed": complete, "return_code": proc.returncode,
        "measurement_count": len(measured), "event_count_per_train": count,
        "cases_tested": selected_cases,
        "membrane_cap_square_width_um": cap_um, "injector_length_um": l_um,
        "tg_width_um_nmos": tg_width_um, "tg_width_um_pmos": 2*tg_width_um, "tg_length_um": tg_length_um,
        "positive_current_source_gate_bias_v": p_gate_bias, "negative_current_source_gate_bias_v": n_gate_bias,
        "mixed_train_start_polarity": mixed_start,
        "pulse_width_us": pulse_us, "event_period_us": period_us,
        "state_node_early_mid_final_v": {}, "differential_increment_from_ref_mv": {},
        "common_mode_shift_from_ref_mv": {}, "same_sign_linear_error_fraction": {},
        "scope": "Matched MIM pair with fixed-gate pMOS sourcing and nMOS sinking through event-steered TGs; unused source nodes are clamped to rails; TT schematic, no read amplifier, weight DAC, PLIF reset/leak/threshold, PVT, mismatch, noise, extraction, or network feedback.",
    }
    if complete:
        node_traces: dict[str, list[float]] = {}
        for case in cases:
            node_traces[case] = [measured[f"final_vp_{case}"], measured[f"final_vn_{case}"]]
        ref_d = node_traces["ref"][0] - node_traces["ref"][1]
        ref_cm = sum(node_traces["ref"]) / 2
        one_p = ((node_traces["p_one"][0] - node_traces["p_one"][1]) - ref_d) if "p_one" in node_traces else None
        one_n = ((node_traces["n_one"][0] - node_traces["n_one"][1]) - ref_d) if "n_one" in node_traces else None
        response = {
            case: (node_traces[case][0] - node_traces[case][1]) - ref_d
            for case in cases if case != "ref"
        }
        expected = {
            key: count * one for key, one in (("p_train", one_p), ("n_train", one_n))
            if key in response and one is not None
        }
        result["state_node_early_mid_final_v"] = {
            case: {phase: [measured[f"{phase}_vp_{case}"], measured[f"{phase}_vn_{case}"]]
                   for phase in ("early", "mid", "final")} for case in cases
        }
        result["differential_increment_from_ref_mv"] = {case: value * 1e3 for case, value in response.items()}
        result["common_mode_shift_from_ref_mv"] = {
            case: ((sum(node_traces[case]) / 2) - ref_cm) * 1e3 for case in cases if case != "ref"
        }
        result["same_sign_linear_error_fraction"] = {
            polarity: abs(response[f"{polarity}_train"] - expected[f"{polarity}_train"]) / max(abs(expected[f"{polarity}_train"]), 1e-15)
            for polarity in ("p", "n") if f"{polarity}_train" in expected
        }
    output = RES / f"sky130_ms_diff_steered_current_{tag}.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
