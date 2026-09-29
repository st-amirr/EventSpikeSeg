"""Bounded TT physical-TG first-event clamp timing screen, without noise/mismatch."""
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


def main() -> int:
    corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                   if arg.startswith("--mos-corner=")), "tt")
    temperature_c = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                if arg.startswith("--temperature-c=")), "27"))
    gate_fraction = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                if arg.startswith("--gate-fraction=")), "0.6"))
    tight_solver = "--tight-solver" in sys.argv[1:]
    step_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                         if arg.startswith("--step-ns=")), "0.5"))
    event_width_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                if arg.startswith("--event-width-ns=")), "10.5"))
    initial_diff_v = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                 if arg.startswith("--initial-diff-v=")), "0"))
    polarity = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                     if arg.startswith("--polarity=")), "positive")
    if corner not in ("tt", "ss", "ff"):
        raise ValueError("MOS corner must be tt, ss or ff")
    if not 0 < gate_fraction < 1:
        raise ValueError("gate fraction must be within (0, 1)")
    if step_ns <= 0:
        raise ValueError("step must be positive")
    if not 0 < event_width_ns <= 500:
        raise ValueError("event width must fit bounded 500ns screen")
    if abs(initial_diff_v) > 1.6:
        raise ValueError("initial differential exceeds 1.8V rails")
    if polarity not in ("positive", "negative"):
        raise ValueError("polarity must be positive or negative")
    tag = ("tt" if corner == "tt" and temperature_c == 27 else
           f"{corner}_temp{temperature_c:g}".replace("-", "m").replace(".", "p"))
    if gate_fraction != 0.6:
        tag += f"_g{gate_fraction:g}".replace(".", "p")
    if tight_solver:
        tag += "_tight"
    if step_ns != 0.5:
        tag += f"_s{step_ns:g}n".replace(".", "p")
    if event_width_ns != 10.5:
        tag += f"_w{event_width_ns:g}n".replace(".", "p")
    if initial_diff_v:
        tag += f"_d{initial_diff_v:g}v".replace("-", "m").replace(".", "p")
    if polarity == "negative":
        tag += "_neg"
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    # Relative to a 3 us event beginning; reference has 500 ns to float.
    cases = {"reference": 2.5, "before_10ns": 2.99, "before_2ns": 2.998,
             "before_1ns": 2.999, "before_0p5ns": 2.9995, "before_0p2ns": 2.9998,
             "at_event": 3.0,
             "after_1ns": 3.001, "held": 3.2}
    case_arg = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                     if arg.startswith("--cases=")), None)
    if case_arg:
        selected = case_arg.split(",")
        if len(selected) != len(set(selected)) or any(name not in cases for name in selected):
            raise ValueError("cases must name unique known timing cases")
        cases = {name: cases[name] for name in selected}
        tag += "_only" + "-".join(selected)
    if event_width_ns > 150 and "held" in cases:
        raise ValueError("held-clamp control releases during long event; select early cases")
    lines = [f"SKY130 {corner.upper()} first-touch physical clamp release and MOS event",
             ".option scale=1u", *([".option reltol=1e-5 abstol=1e-15 vntol=1e-9"] if tight_solver else []),
             f".temp {temperature_c:g}",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
             f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
             '.include "../../../asic/analog/modules.spice"',
             '.include "../../../asic/analog/sky130_ms_plif.spice"',
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             ".subckt diff_inject vp vn pp nn vdd vss",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w=1 l=10",
             ".ends diff_inject"]
    init_p, init_n = ("vcm", "vcm")
    if initial_diff_v:
        lines += [f"Vstate_init_p state_init_p 0 {0.9 + initial_diff_v/2:.12g}",
                  f"Vstate_init_n state_init_n 0 {0.9 - initial_diff_v/2:.12g}"]
        init_p, init_n = "state_init_p", "state_init_n"
    for case, release_us in cases.items():
        for event in (False, True):
            name = f'{case}_{"event" if event else "zero"}'
            end = max(3.2, 3.0 + event_width_ns / 1000 + 0.2)
            # 0.1 ns voltage transition; controls are ideal but switches are PDK MOS.
            lines += [f"Vcl_{name} cl_{name} 0 PWL(0 1.8 {release_us:.6f}u 1.8 {release_us+0.0001:.6f}u 0 {end}u 0)",
                      f"Vclb_{name} clb_{name} 0 PWL(0 0 {release_us:.6f}u 0 {release_us+0.0001:.6f}u 1.8 {end}u 1.8)",
                      f"Xmem_p_{name} vp_{name} vcm membrane_mim w_um=10 l_um=10",
                      f"Xmem_n_{name} vn_{name} vcm membrane_mim w_um=10 l_um=10",
                      f"Xcl_p_{name} {init_p} vp_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                      f"Xcl_n_{name} {init_n} vn_{name} cl_{name} clb_{name} vdd 0 transmission_gate"]
            if event:
                pg = 1.8 - gate_fraction * 1.08
                ng = gate_fraction * 0.6
                finish = 3.0 + event_width_ns / 1000
                lines += [f"Vpp_{name} pp_{name} 0 PWL(0 1.8 2.9999u 1.8 3u {pg:.9g} {finish:.9g}u {pg:.9g} {finish+0.0001:.9g}u 1.8 {end}u 1.8)",
                          f"Vnn_{name} nn_{name} 0 PWL(0 0 2.9999u 0 3u {ng:.9g} {finish:.9g}u {ng:.9g} {finish+0.0001:.9g}u 0 {end}u 0)"]
            else:
                lines += [f"Vpp_{name} pp_{name} 0 1.8", f"Vnn_{name} nn_{name} 0 0"]
            first, second = ((f"vp_{name}", f"vn_{name}") if polarity == "positive" else
                             (f"vn_{name}", f"vp_{name}"))
            lines.append(f"Xinj_{name} {first} {second} pp_{name} nn_{name} vdd 0 diff_inject")
    stop_us = max(3.2, 3.0 + event_width_ns / 1000 + 0.2)
    lines += [".control", "set numdgt=15", f"tran {step_ns:g}n {stop_us:.9g}u uic"]
    for case in cases:
        for suffix in ("zero", "event"):
            name = f"{case}_{suffix}"
            lines.append(f"let diff_{name}=v(vp_{name})-v(vn_{name})")
            post_at = max(3.02, 3.0 + event_width_ns / 1000 + 0.01)
            for phase, at in (("pre", "2.998u"), ("post", f"{post_at:.9g}u"), ("end", f"{stop_us-0.01:.9g}u")):
                lines.append(f"meas tran {phase}_{name} find diff_{name} at={at}")
    lines += ["quit", ".endc", ".end"]
    deck = BENCH / f"sky130_ms_first_event_clamp_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (RES / f"sky130_ms_first_event_clamp_{tag}.log").write_text(log, encoding="utf-8")
    found = {f"{phase}_{name}": float(value) for phase, name, value in re.findall(
        r"(?im)^\s*(pre|post|end)_(\w+_(?:zero|event))\s*=\s*([-+0-9.eE]+)", log)}
    rows = []
    complete = run.returncode == 0 and len(found) == 6 * len(cases)
    if complete:
        for case, release_us in cases.items():
            rows.append({"case": case, "release_us": release_us,
                         **{f"{phase}_no_event_diff_uv": found[f"{phase}_{case}_zero"] * 1e6
                            for phase in ("pre", "post", "end")},
                         **{f"{phase}_event_minus_no_event_uv":
                            (found[f"{phase}_{case}_event"] - found[f"{phase}_{case}_zero"]) * 1e6
                            for phase in ("pre", "post", "end")}})
    report = {"test": "sky130_first_touch_clamp_physical_tg_timing", "simulation_completed": complete,
              "return_code": run.returncode, "mim_width_um": 10, "mos_corner": corner,
              "temperature_c": temperature_c,
              "tight_solver": tight_solver,
              "transient_step_ns": step_ns,
              "initial_differential_v": initial_diff_v,
              "event_polarity": polarity,
              "event_start_us": 3.0, "event_width_ns": event_width_ns, "gate_fraction": gate_fraction,
              "selected_timing_cases": list(cases),
              "cases": rows, "scope": "Deterministic schematic PDK MOS/TG/MIM; ideal common-mode supply and control ramps. No kT/C, charge-injection variation, mismatch, extracted parasitics, arbiter, comparator, threshold/reset, or full population."}
    (RES / f"sky130_ms_first_event_clamp_{tag}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
