#!/usr/bin/env python3
"""Compare equal early/late charge on an isolated routed minimum MIM/TG."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
PAIR = BENCH / "sky130_min_mim_pair_pex_reducedmim_subground.spice"
TG = "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"
BASE_STEM = "sky130_min_mim_routed_tg_event_time_decay_ss0"


def main() -> int:
    maxstep_ns = float(sys.argv[1]) if len(sys.argv) > 1 else 1000
    if not 10 <= maxstep_ns <= 1000:
        raise ValueError("maxstep must be in [10, 1000] ns")
    stem = BASE_STEM + (f"_step{maxstep_ns:g}ns" if maxstep_ns != 1000 else "")
    model = PAIR.read_text(encoding="ascii")
    if "Vsubstrate VSUBS 0 0" not in model or "Cunit0" not in model:
        raise RuntimeError("expected grounded-substrate reduced MIM diagnostic PEX")
    lines = ["* 2x2um MIM PEX, off routed TG, identical early/late ideal charges",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
             f'.lib "{LIB}" ss',
             f'.include "/workspace/{PAIR.relative_to(ROOT).as_posix()}"',
             f'.include "{TG}"', ".temp 0",
             "Vcm vcm 0 0.9", "Vdd vdd 0 1.8", "Vsource source 0 0.9",
             "Vgn gn 0 0", "Vgp gp 0 1.8",
             "Vinit_en init_en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)",
             ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)"]
    for label in ("control", "early", "late"):
        state = f"state_{label}"
        unused = f"unused_{label}"
        lines.extend((f"Xpair_{label} vcm {state} vcm {unused} sky130_differential_trim_cap_pair",
                      f"Sinit_{label} source {state} init_en 0 ideal_init",
                      f"Sinit_unused_{label} source {unused} init_en 0 ideal_init",
                      f"Xsw_{label} source {state} gn gp vdd 0 sky130_transmission_gate_raw"))
        if label != "control":
            start = 0.5 if label == "early" else 4.5
            lines.append(f"Ievent_{label} 0 {state} PWL(0 0 {start-0.000001:g}m 0 {start:g}m 11p "
                         f"{start+0.001:g}m 11p {start+0.001001:g}m 0 5.01m 0)")
    lines.extend((".control", "set numdgt=15", f"tran {maxstep_ns:g}n 5m"))
    for label in ("control", "early", "late"):
        lines.append(f"meas tran {label}_start find v(state_{label}) at=0.4m")
        lines.append(f"meas tran {label}_after_early find v(state_{label}) at=0.502m")
        lines.append(f"meas tran {label}_after_late find v(state_{label}) at=4.502m")
        lines.append(f"meas tran {label}_final find v(state_{label}) at=5m")
    lines.extend(("quit", ".endc", ".end", ""))
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
           "180", "ngspice", "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=195)
    log = run.stdout + run.stderr
    (RESULTS / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*((?:control|early|late)_(?:start|after_early|after_late|final))\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and "ngspice-36 done" in log and len(values) == 12
    report = {"test": "sky130_min_mim_routed_tg_event_time_decay",
              "simulation_completed": complete, "corner": "SS", "temperature_c": 0,
              "max_transient_step_ns": maxstep_ns,
              "ideal_current_pulse_na": 0.011, "ideal_pulse_width_ns": 1000,
              "event_times_ms": {"early": 0.5, "late": 4.5},
              "measurements": values,
              "scope": "Grounded-substrate reduced PEX minimum MIM pair, routed TG held off, ideal exact equal charge impulses into one state at two times; matched no-event branch. No physical event driver, PEX signoff, noise/mismatch, beta, reset, float weight, readout or network service."}
    if complete:
        report["early_immediate_increment_mv"] = (values["early_after_early"] - values["control_after_early"]) * 1e3
        report["late_immediate_increment_mv"] = (values["late_after_late"] - values["control_after_late"]) * 1e3
        report["early_final_increment_mv"] = (values["early_final"] - values["control_final"]) * 1e3
        report["late_final_increment_mv"] = (values["late_final"] - values["control_final"]) * 1e3
        report["immediate_early_to_late_ratio"] = report["early_immediate_increment_mv"] / report["late_immediate_increment_mv"]
        if abs(report["late_final_increment_mv"]) > 1e-9:
            report["early_to_late_final_ratio"] = report["early_final_increment_mv"] / report["late_final_increment_mv"]
        else:
            complete = False
            report["simulation_completed"] = False
            report["failure_reason"] = "ideal event charge not observed at final state"
    (RESULTS / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
