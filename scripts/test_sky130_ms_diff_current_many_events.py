"""Bounded SKY130 differential current-injection accumulation screen.

Opposite MIM nodes receive equal-and-opposite pulse currents so their common
mode stays near VCM while signed differential state grows. TT schematic only.
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
    max_step_ns = float(arg("--max-step-ns", 10))
    timeout_s = int(arg("--timeout-s", 180))
    p_gate_on = float(arg("--p-gate-on", 1.2))
    n_gate_on = float(arg("--n-gate-on", 0.6))
    mixed_start = arg("--mixed-start", "p")
    if min(count, cap_um, pulse_us, period_us, l_um, max_step_ns, timeout_s) <= 0:
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

    def waveform(case: str, gate_kind: str, event_sign: str) -> str:
        off, active = ((1.8, p_gate_on) if gate_kind == "p" else (0.0, n_gate_on))
        guard_us = min(0.01, max(0.0001, (period_us - pulse_us) / 4))
        points = [(0.0, off)]
        for idx, sign in cases[case]:
            if sign != event_sign:
                continue
            start = event_times[idx]
            points += [(start - guard_us, off), (start, active), (start + pulse_us, active), (start + pulse_us + guard_us, off)]
        points.append((5005.0, off))
        return "PWL(" + " ".join(f"{t:g}u {v:g}" for t, v in points) + ")"

    lines = ["SKY130 differential signed current injection into a matched MIM pair", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             f".subckt diff_inject vp vn pp np pn nn vdd vss params: wp=1.5 wn=1 l={l_um:g}",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}",
             "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}",
             "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}",
             ".ends diff_inject"]
    for name in cases:
        vp, vn = f"vp_{name}", f"vn_{name}"
        lines += [f"Xmem_p_{name} {vp} vcm membrane_mim w_um={cap_um:g} l_um={cap_um:g}",
                  f"Xmem_n_{name} {vn} vcm membrane_mim w_um={cap_um:g} l_um={cap_um:g}",
                  f".ic v({vp})=0", f".ic v({vn})=0",
                  f"Vpp_{name} pp_{name} 0 {waveform(name, 'p', 'p')}",
                  f"Vnp_{name} np_{name} 0 {waveform(name, 'n', 'n')}",
                  f"Vpn_{name} pn_{name} 0 {waveform(name, 'p', 'n')}",
                  f"Vnn_{name} nn_{name} 0 {waveform(name, 'n', 'p')}",
                  f"Xinj_{name} {vp} {vn} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject"]
    lines += [".control", "set numdgt=15", f"tran {max_step_ns:g}n 5.005m uic"]
    for phase, time in (("early", "1u"), ("mid", "1m"), ("final", "5m")):
        for name in cases:
            lines += [f"meas tran {phase}_vp_{name} find v(vp_{name}) at={time}",
                      f"meas tran {phase}_vn_{name} find v(vn_{name}) at={time}"]
    lines += ["quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    tag = f"n{count}_w{pulse_us:g}u_cm{cap_um:g}_period{period_us:g}u_l{l_um:g}_bp{p_gate_on:g}_bn{n_gate_on:g}_mix{mixed_start}_s{max_step_ns:g}n"
    deck = BENCH / f"sky130_ms_diff_current_many_events_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", str(timeout_s), "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 15)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_ms_diff_current_many_events_{tag}.log").write_text(log, encoding="utf-8")
    measured = {f"{phase}_{node}_{case}": float(value) for phase, node, case, value in
                re.findall(r"(?im)^\s*(early|mid|final)_(vp|vn)_([a-z_]+)\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and len(measured) == 3 * 2 * len(cases)
    result: dict[str, object] = {
        "test": "sky130_tt_differential_mim_current_injection_many_events",
        "simulation_completed": complete, "return_code": proc.returncode,
        "measurement_count": len(measured), "event_count_per_train": count,
        "membrane_cap_square_width_um": cap_um, "injector_length_um": l_um,
        "positive_gate_bias_v": p_gate_on, "negative_gate_bias_v": n_gate_on,
        "mixed_train_start_polarity": mixed_start,
        "pulse_width_us": pulse_us, "event_period_us": period_us,
        "state_node_early_mid_final_v": {}, "differential_increment_from_ref_mv": {},
        "common_mode_shift_from_ref_mv": {}, "same_sign_linear_error_fraction": {},
        "scope": "Matched MIM pair with complementary pMOS sourcing and nMOS sinking; direct gate-biased MOS injection, TT schematic, no read amplifier, weight DAC, PLIF reset/leak/threshold, PVT, mismatch, noise, extraction, or network feedback.",
    }
    if complete:
        node_traces: dict[str, list[float]] = {}
        for case in cases:
            node_traces[case] = [measured[f"final_vp_{case}"], measured[f"final_vn_{case}"]]
        ref_d = node_traces["ref"][0] - node_traces["ref"][1]
        ref_cm = sum(node_traces["ref"]) / 2
        one_p = (node_traces["p_one"][0] - node_traces["p_one"][1]) - ref_d
        one_n = (node_traces["n_one"][0] - node_traces["n_one"][1]) - ref_d
        response = {
            case: (node_traces[case][0] - node_traces[case][1]) - ref_d
            for case in cases if case != "ref"
        }
        expected = {"p_train": count * one_p, "n_train": count * one_n}
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
            for polarity in ("p", "n")
        }
    output = RES / f"sky130_ms_diff_current_many_events_{tag}.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
