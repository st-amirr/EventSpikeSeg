"""Bound one physical sampled analog weight gate and event mux over a 5 ms hold."""

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


def argument(name: str, default: str) -> str:
    return next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                 if arg.startswith(name + "=")), default)


def main() -> int:
    corner = argument("--corner", "ss")
    temperature_c = {"ss": 0, "tt": 27, "ff": 85}.get(corner)
    if temperature_c is None:
        raise ValueError("unknown corner")
    cap_width_um = float(argument("--weight-cap-um", "10"))
    hold_us = float(argument("--hold-us", "5000"))
    program_us = float(argument("--program-us", "1"))
    fraction = float(argument("--gate-fraction", "0.8"))
    width_ns = float(argument("--event-width-ns", "40.253"))
    if not 1 <= cap_width_um <= 100 or not 0 <= hold_us <= 5000 or not 1 <= program_us <= 100 or not 0.1 <= fraction <= 0.95:
        raise ValueError("bounded gate hold limits exceeded")
    pg, ng = 1.8 - fraction * 1.08, fraction * 0.6
    start = hold_us + program_us + 2.0
    finish = start + width_ns / 1000
    post = finish + 0.010
    stop = post + 0.050
    tag = f"{corner}{temperature_c}_c{cap_width_um:g}_h{hold_us:g}_f{fraction:g}_w{width_ns:g}"
    if program_us != 1:
        tag += f"_prog{program_us:g}"
    tag = tag.replace(".", "p")
    stem = f"sky130_ms_weight_gate_hold_{tag}"
    lines = [f"SKY130 physical analog weight hold {tag}",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
             f".temp {temperature_c}",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
             f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
             '.include "../../../asic/analog/modules.spice"',
             '.include "../../../asic/analog/sky130_ms_plif.spice"',
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             f"Vpgsrc pgsrc 0 {pg:.12g}", f"Vngsrc ngsrc 0 {ng:.12g}",
             f"Vsample sample 0 PWL(0 1.8 {program_us:.12g}u 1.8 {program_us+.0001:.12g}u 0 {stop:.12g}u 0)",
             f"Vsampleb sampleb 0 PWL(0 0 {program_us:.12g}u 0 {program_us+.0001:.12g}u 1.8 {stop:.12g}u 1.8)",
             f"Vevent event 0 PWL(0 0 {start-.0001:.12g}u 0 {start:.12g}u 1.8 {finish:.12g}u 1.8 {finish+.0001:.12g}u 0 {stop:.12g}u 0)",
             f"Veventb eventb 0 PWL(0 1.8 {start-.0001:.12g}u 1.8 {start:.12g}u 0 {finish:.12g}u 0 {finish+.0001:.12g}u 1.8 {stop:.12g}u 1.8)",
             f"Voff off 0 PWL(0 1.8 {start-.0004:.12g}u 1.8 {start-.0003:.12g}u 0 {finish+.0003:.12g}u 0 {finish+.0004:.12g}u 1.8 {stop:.12g}u 1.8)",
             f"Voffb offb 0 PWL(0 0 {start-.0004:.12g}u 0 {start-.0003:.12g}u 1.8 {finish+.0003:.12g}u 1.8 {finish+.0004:.12g}u 0 {stop:.12g}u 0)",
             ".subckt diff_inject vp vn pp nn vdd vss",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w=1 l=10",
             ".ends diff_inject"]
    for name in ("direct", "held", "zero"):
        lines += [f"Xmem_p_{name} vp_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Xmem_n_{name} vn_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Vcl_{name} cl_{name} 0 PWL(0 1.8 {start-.0003:.12g}u 1.8 {start-.0002:.12g}u 0 {stop:.12g}u 0)",
                  f"Vclb_{name} clb_{name} 0 PWL(0 0 {start-.0003:.12g}u 0 {start-.0002:.12g}u 1.8 {stop:.12g}u 1.8)",
                  f"Xcl_p_{name} vcm vp_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Xcl_n_{name} vcm vn_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Xinj_{name} vp_{name} vn_{name} pp_{name} nn_{name} vdd 0 diff_inject"]
    lines += [f"Vpp_direct pp_direct 0 PWL(0 1.8 {start-.0001:.12g}u 1.8 {start:.12g}u {pg:.12g} {finish:.12g}u {pg:.12g} {finish+.0001:.12g}u 1.8 {stop:.12g}u 1.8)",
              f"Vnn_direct nn_direct 0 PWL(0 0 {start-.0001:.12g}u 0 {start:.12g}u {ng:.12g} {finish:.12g}u {ng:.12g} {finish+.0001:.12g}u 0 {stop:.12g}u 0)",
              "Vpp_zero pp_zero 0 1.8", "Vnn_zero nn_zero 0 0",
              f"Xwcap_p storep vcm membrane_mim w_um={cap_width_um:g} l_um={cap_width_um:g}",
              f"Xwcap_n storen vcm membrane_mim w_um={cap_width_um:g} l_um={cap_width_um:g}",
              "Xprog_p pgsrc storep sample sampleb vdd 0 transmission_gate",
              "Xprog_n ngsrc storen sample sampleb vdd 0 transmission_gate",
              "Xon_p storep pp_held event eventb vdd 0 transmission_gate",
              "Xon_n storen nn_held event eventb vdd 0 transmission_gate",
              "Xoff_p vdd pp_held off offb vdd 0 transmission_gate",
              "Xoff_n 0 nn_held off offb vdd 0 transmission_gate",
              ".control", "set numdgt=15", f"tran 100n {stop:.12g}u uic",
              "let diff_direct=v(vp_direct)-v(vn_direct)",
              "let diff_held=v(vp_held)-v(vn_held)",
              "let diff_zero=v(vp_zero)-v(vn_zero)"]
    for phase, at in (("after_program", program_us + .1), ("pre_event", start - .001),
                      ("during_event", start + width_ns / 2000), ("post_event", post)):
        for node in ("storep", "storen"):
            lines.append(f"meas tran {phase}_{node} find v({node}) at={at:.12g}u")
    for name in ("direct", "held", "zero"):
        lines.append(f"meas tran final_{name} find diff_{name} at={post:.12g}u")
    lines += ["quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    found = {name: float(value) for name, value in re.findall(
        r"(?m)^\s*((?:after_program|pre_event|during_event|post_event)_(?:storep|storen)|final_(?:direct|held|zero))\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and len(found) == 11 and "Timestep too small" not in log
    report = {"test": "sky130_physical_sampled_analog_weight_gate_hold", "simulation_completed": complete,
              "return_code": run.returncode, "corner": corner, "temperature_c": temperature_c,
              "weight_cap_square_um": cap_width_um, "hold_us": hold_us,
              "program_us": program_us,
              "gate_fraction": fraction, "programmed_p_gate_v": pg, "programmed_n_gate_v": ng,
              "event_width_ns": width_ns, "event_start_us": start, "measurements_v": found,
              "scope": "Physical PDK TG and MIM analog gate storage, physical event mux and MOS injector, 10um first-touch membrane pair. Ideal programming source, clock control and supplies. Deterministic transient only; no switched thermal noise, mismatch, routing parasitics, level generator, repeated events or beta/reset/readout."}
    if complete:
        report["stored_p_gate_drift_v"] = found["pre_event_storep"] - found["after_program_storep"]
        report["stored_n_gate_drift_v"] = found["pre_event_storen"] - found["after_program_storen"]
        report["direct_event_step_v"] = found["final_direct"] - found["final_zero"]
        report["held_event_step_v"] = found["final_held"] - found["final_zero"]
        report["held_minus_direct_event_step_v"] = report["held_event_step_v"] - report["direct_event_step_v"]
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
