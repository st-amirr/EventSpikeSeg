"""Bounded direct differential injector pulse-width sweep.

Measures one signed event into matched SKY130 MIM membrane capacitors at TT.
This supplies a physical width-to-differential-voltage curve for the
full-float pulse-duration sensitivity replay; it is not a qualified cell.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RESULTS = OUT / "results"
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
    caps = [float(x) for x in _arg("--caps-um", "20,40,60").split(",")]
    widths_ns = [float(x) for x in _arg("--widths-ns", "0.25,0.5,1,2,4,8,16,32,64").split(",")]
    max_step_ns = float(_arg("--max-step-ns", "0.05"))
    timeout_s = int(_arg("--timeout-s", "240"))
    p_gate_on = float(_arg("--p-gate-on", "0.72"))
    n_gate_on = float(_arg("--n-gate-on", "0.6"))
    initial_cm = float(_arg("--initial-common-mode-v", "0.9"))
    if min(caps + widths_ns + [max_step_ns, timeout_s]) <= 0:
        raise ValueError("cap sizes, widths, timestep, and timeout must be positive")
    if min(widths_ns) <= 2 * max_step_ns:
        raise ValueError("each pulse must exceed two transient timesteps")
    end_ns = 100.0 + max(widths_ns) + 100.0
    measure_ns = end_ns - 10.0
    lines = ["SKY130 TT direct differential pulse-width transfer", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             ".subckt diff_inject vp vn pp np pn nn vdd vss params: wp=1.5 wn=1 l=10",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}",
             "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}",
             "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}",
             ".ends diff_inject"]
    cases: list[tuple[str, float, str]] = []
    for cap in caps:
        cases.append((f"c{cap:g}_ref", cap, "ref"))
        for width in widths_ns:
            for sign in ("p", "n"):
                cases.append((f"c{cap:g}_w{width:g}_{sign}", cap, f"{width:g}_{sign}"))
    for name, cap, event in cases:
        vp, vn = f"vp_{name}", f"vn_{name}"
        lines += [f"Xmem_p_{name} {vp} vcm membrane_mim w_um={cap:g} l_um={cap:g}",
                  f"Xmem_n_{name} {vn} vcm membrane_mim w_um={cap:g} l_um={cap:g}",
                  f".ic v({vp})={initial_cm:.12g}", f".ic v({vn})={initial_cm:.12g}",
                  f".ic v(xmem_p_{name}.xmim.a)={initial_cm:.12g}", f".ic v(xmem_n_{name}.xmim.a)={initial_cm:.12g}"]
        if event == "ref":
            pp = pn = "1.8"; np = nn = "0"
        else:
            width_s, sign = event.split("_")
            width = float(width_s)
            ton, toff = 100.0, 100.0 + width
            pp = f"PWL(0n 1.8 {ton-0.1:g}n 1.8 {ton:g}n {p_gate_on:g} {toff:g}n {p_gate_on:g} {toff+0.1:g}n 1.8 {end_ns:g}n 1.8)" if sign == "p" else "0"
            nn = f"PWL(0n 0 {ton-0.1:g}n 0 {ton:g}n {n_gate_on:g} {toff:g}n {n_gate_on:g} {toff+0.1:g}n 0 {end_ns:g}n 0)" if sign == "p" else "0"
            pn = f"PWL(0n 1.8 {ton-0.1:g}n 1.8 {ton:g}n {p_gate_on:g} {toff:g}n {p_gate_on:g} {toff+0.1:g}n 1.8 {end_ns:g}n 1.8)" if sign == "p" else "0"
            np = f"PWL(0n 0 {ton-0.1:g}n 0 {ton:g}n {n_gate_on:g} {toff:g}n {n_gate_on:g} {toff+0.1:g}n 0 {end_ns:g}n 0)" if sign == "n" else "0"
        lines += [f"Vpp_{name} pp_{name} 0 {pp}", f"Vnp_{name} np_{name} 0 {np}",
                  f"Vpn_{name} pn_{name} 0 {pn}", f"Vnn_{name} nn_{name} 0 {nn}",
                  f"Xinj_{name} {vp} {vn} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject"]
    lines += [".control", "set numdgt=15", f"tran {max_step_ns:g}n {end_ns:g}n uic"]
    for name, _, _ in cases:
        lines += [f"meas tran vp_{name} find v(vp_{name}) at={measure_ns:g}n",
                  f"meas tran vn_{name} find v(vn_{name}) at={measure_ns:g}n"]
    lines += ["quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = "c" + "-".join(f"{v:g}" for v in caps) + f"_cm{initial_cm:g}v_w" + "-".join(f"{v:g}" for v in widths_ns) + f"_s{max_step_ns:g}n"
    deck = BENCH / f"sky130_ms_diff_pulse_width_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", str(timeout_s), "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 20)
    log = proc.stdout + proc.stderr
    (RESULTS / f"sky130_ms_diff_pulse_width_{tag}.log").write_text(log, encoding="utf-8")
    node_values = {(node, case): float(value) for node, case, value in re.findall(r"(?im)^\s*(vp|vn)_([\w.]+)\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and len(node_values) == 2 * len(cases)
    by_cap: dict[str, dict[str, object]] = {}
    if complete:
        for cap in caps:
            base = f"c{cap:g}_ref"
            ref_d = node_values["vp", base] - node_values["vn", base]
            points = []
            for width in widths_ns:
                row: dict[str, object] = {"pulse_width_ns": width}
                for sign in ("p", "n"):
                    case = f"c{cap:g}_w{width:g}_{sign}"
                    delta = (node_values["vp", case] - node_values["vn", case]) - ref_d
                    row[f"{sign}_delta_v"] = delta
                points.append(row)
            by_cap[f"{cap:g}"] = {"reference_vp_vn_v": [node_values["vp", base], node_values["vn", base]], "points": points}
    result = {"test": "sky130_tt_direct_differential_injector_pulse_width_sweep",
              "simulation_completed": complete, "return_code": proc.returncode,
              "measurement_count": len(node_values), "membrane_cap_square_widths_um": caps,
              "pulse_width_ns": widths_ns, "p_gate_on_v": p_gate_on, "n_gate_on_v": n_gate_on,
              "injector_length_um": 10.0, "max_step_ns": max_step_ns,
              "same_phase_no_event_subtracted_transfer": by_cap,
              "scope": "Single isolated gate pulse into matched MIM node pair; TT schematic only. No DAC, width-generator jitter, weight mapping, full-float replay, threshold/readout, PVT, mismatch, noise, extraction, or network feedback."}
    out = RESULTS / f"sky130_ms_diff_pulse_width_{tag}.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "simulation_completed": complete,
                      "measurement_count": len(node_values), "transfer": by_cap}, indent=2))
    return 0 if complete else 2


def _arg(key: str, default: str) -> str:
    import sys
    return next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith(key + "=")), default)


if __name__ == "__main__":
    raise SystemExit(main())
