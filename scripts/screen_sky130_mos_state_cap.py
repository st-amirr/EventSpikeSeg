"""Bounded SKY130 MOS-gate versus MIM state-capacitor screen.

This compares equal drawn capacitor areas in a nominal PDK transient. It does
not establish a legal MOS capacitor layout, noise yield, or an analog PLIF.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RESULTS = OUT / "results"
BIAS_V = (0.6, 0.9, 1.2)
PULSE_A = 10e-9
PULSE_S = 0.2e-6
GEOMETRY_UM2 = 100.0
STATE_COUNT = 30_976_000
BOLTZMANN_J_PER_K = 1.380649e-23
TEMPERATURE_K_FOR_PROXY = 300.0

HEADER = """SKY130 equal-drawn-area MOS gate and MIM storage probe
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 rm4=0.047 rcvia4=0.38 tc1rvia4=0 tc2rvia4=0
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
Vdd vdd 0 1.8
"""


def deck(bias: float) -> str:
    lines = [HEADER, f"Vprogram src 0 {bias}",
             "Von on 0 PWL(0 1.8 1u 1.8 1.001u 0 5.01m 0)",
             "Voff off 0 PWL(0 0 1u 0 1.001u 1.8 5.01m 1.8)"]
    for kind in ("mos", "mim"):
        for trial in ("pulse", "ref"):
            node = f"{kind}_{trial}"
            lines.append(f"Xsw_{node} src {node} on off vdd 0 transmission_gate")
            if kind == "mos":
                # Ten 10um x 1um gate fingers; D/S/B fixed at ground.
                for finger in range(10):
                    lines.append(f"Xcap_{node}_{finger} 0 {node} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1")
            else:
                lines.append(f"Xcap_{node} {node} 0 sky130_fd_pr__cap_mim_m3_2 w=10 l=10 mf=1")
            if trial == "pulse":
                lines.append(f"Iinject_{node} 0 {node} PWL(0 0 2u 0 2.001u {PULSE_A} 2.201u {PULSE_A} 2.202u 0 5.01m 0)")
    lines += [".control", "tran 1u 5.01m 0 1u",
              "meas tran mos_before find v(mos_pulse) at=1.9u",
              "meas tran mos_after find v(mos_pulse) at=2.3u",
              "meas tran mos_end find v(mos_pulse) at=5m",
              "meas tran mos_ref_before find v(mos_ref) at=1.9u",
              "meas tran mos_ref_after find v(mos_ref) at=2.3u",
              "meas tran mos_ref_end find v(mos_ref) at=5m",
              "meas tran mim_before find v(mim_pulse) at=1.9u",
              "meas tran mim_after find v(mim_pulse) at=2.3u",
              "meas tran mim_end find v(mim_pulse) at=5m",
              "meas tran mim_ref_before find v(mim_ref) at=1.9u",
              "meas tran mim_ref_after find v(mim_ref) at=2.3u",
              "meas tran mim_ref_end find v(mim_ref) at=5m",
              "quit", ".endc", ".end"]
    return "\n".join(lines) + "\n"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for bias in BIAS_V:
        tag = f"sky130_mos_state_cap_{str(bias).replace('.', 'p')}v"
        (BENCH / f"{tag}.cir").write_text(deck(bias), encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro",
               "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
               "--workdir", "/workspace/artifacts/analog_asic/benches",
               "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
               "120", "ngspice", "-b", f"{tag}.cir"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        log = proc.stdout + proc.stderr
        (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
        values = {k.lower(): float(v) for k, v in re.findall(
            r"^((?:mos|mim)_(?:ref_)?(?:before|after|end))\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}
        row = {"program_v": bias, "simulation_completed": proc.returncode == 0 and len(values) == 12,
               "exit_code": proc.returncode}
        for kind in ("mos", "mim"):
            if all(f"{kind}_{suffix}" in values for suffix in
                   ("before", "after", "end", "ref_before", "ref_after", "ref_end")):
                delta = (values[f"{kind}_after"] - values[f"{kind}_before"]
                         - values[f"{kind}_ref_after"] + values[f"{kind}_ref_before"])
                row[kind] = {
                    "measured_increment_v": delta,
                    "effective_capacitance_f": PULSE_A * PULSE_S / delta if delta > 0 else None,
                    "program_error_v": values[f"{kind}_ref_before"] - bias,
                    "no_pulse_hold_drift_v": values[f"{kind}_ref_end"] - values[f"{kind}_ref_after"],
                    "pulse_branch_hold_drift_v": values[f"{kind}_end"] - values[f"{kind}_after"],
                }
                cap = row[kind]["effective_capacitance_f"]
                if cap is not None:
                    row[kind]["independent_pair_ktc_proxy_uv_at_300k"] = (
                        math.sqrt(2 * BOLTZMANN_J_PER_K * TEMPERATURE_K_FOR_PROXY / cap) * 1e6)
        if "mos" in row and "mim" in row:
            ratio = (row["mos"]["effective_capacitance_f"] /
                     row["mim"]["effective_capacitance_f"])
            row["mos_to_mim_equal_drawn_area_capacitance_ratio"] = ratio
            row["optimistic_two_mos_gate_area_mm2_for_all_states_at_10um_mim_pair_capacitance"] = (
                2 * STATE_COUNT * GEOMETRY_UM2 / ratio / 1e6)
        rows.append(row)
    report = {
        "scope": "SKY130 TT nominal transistor gate (10 x 10um/1um) versus 10um x 10um MIM; physical TG sample, ideal 10nA x 0.2us current pulse, 5ms hold. Drawn capacitor geometry only; MOS diffusion, contacts, switch and routing excluded. No noise, mismatch, extraction or legal MOSCAP layout.",
        "injected_charge_c": PULSE_A * PULSE_S,
        "drawn_capacitor_area_um2_each": GEOMETRY_UM2,
        "logical_state_count": STATE_COUNT,
        "results": rows,
        "all_simulations_completed": all(row["simulation_completed"] for row in rows),
    }
    (RESULTS / "sky130_mos_state_cap_boundary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_simulations_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
