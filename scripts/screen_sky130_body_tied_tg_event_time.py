"""Compare early/late equal charge on the diode-proxy body-tied state pair."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
PAIR = BENCH / "sky130_min_mim_pair_pex_reducedmim_subground.spice"
TG = BENCH / "sky130_body_tied_tg_pex_subground.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"
BASE_STEM = "sky130_body_tied_tg_event_time_tt27_dnw1p2_bothdiodes_sourcevcm"


def main() -> None:
    version = "47" if "--ngspice47" in sys.argv else "36"
    initial_condition = "--initial-condition" in sys.argv
    gmin = float(sys.argv[sys.argv.index("--gmin") + 1]) if "--gmin" in sys.argv else None
    if gmin is not None and not 0 < gmin <= 1e-12:
        raise ValueError("diagnostic gmin must be in (0,1e-12]")
    maxstep_ns = float(sys.argv[sys.argv.index("--maxstep-ns") + 1]) if "--maxstep-ns" in sys.argv else 50.0
    guard_ff = float(sys.argv[sys.argv.index("--guard-ff") + 1]) if "--guard-ff" in sys.argv else 0.0
    if not 10 <= maxstep_ns <= 100:
        raise ValueError("max step must be in [10,100] ns")
    if guard_ff not in (0.0, 10.0, 100.0):
        raise ValueError("guard capacitance must be 0, 10, or 100 fF")
    stem = f"{BASE_STEM}" + (f"_guard{guard_ff:g}ff" if guard_ff else "") + f"_step{maxstep_ns:g}ns"
    if version != "36":
        stem += f"_ngspice{version}"
    if gmin is not None:
        stem += f"_gmin{gmin:g}"
    if initial_condition:
        stem += "_initialcondition"
    if "Vsubstrate VSUBS 0 0" not in TG.read_text(encoding="ascii"):
        raise RuntimeError("body-tied TG substrate-grounded diagnostic PEX missing")
    lines = ["* Equal ideal early/late charge, body-tied TG PEX plus both PDK well diodes",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
             f'.lib "{LIB}" tt',
             f'.include "/workspace/{PAIR.relative_to(ROOT).as_posix()}"',
             f'.include "/workspace/{TG.relative_to(ROOT).as_posix()}"',
             ".temp 27", "Vcm vcm 0 0.9", "Vdnw dnw 0 1.2",
             "Vlow low 0 0.899", "Vhigh high 0 0.901",
             "Vgn gn 0 0", "Vgp gp 0 1.8",
             "Vinit_en init_en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)",
             ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)"]
    for label in ("control", "early", "late"):
        low, high = f"{label}_low", f"{label}_high"
        lines.append(f"Xpair_{label} vcm {low} vcm {high} sky130_differential_trim_cap_pair")
        for side, state in (("low", low), ("high", high)):
            if initial_condition:
                lines.append(f".ic v({state})={0.899 if side == 'low' else 0.901}")
            else:
                lines.append(f"Sinit_{label}_{side} {side} {state} init_en 0 ideal_init")
            source = "vcm"
            if guard_ff:
                guard = f"guard_{label}_{side}"
                source = guard
                if initial_condition:
                    lines.append(f".ic v({guard})={0.899 if side == 'low' else 0.901}")
                else:
                    lines.append(f"Sinit_guard_{label}_{side} {side} {guard} init_en 0 ideal_init")
                lines.append(f"Cguard_{label}_{side} {guard} vcm {guard_ff:g}f")
                lines.append(f"Xouter_{label}_{side} vcm {guard} gn gp dnw {guard} {guard} sky130_body_tied_transmission_gate_raw")
                lines.append(f"Douter_pw_{label}_{side} {guard} dnw sky130_fd_pr__model__parasitic__diode_pw2dn area=27.625 pj=21.5")
                lines.append(f"Douter_pf_{label}_{side} 0 {guard} sky130_fd_pr__model__parasitic__diode_ps2nw area=8.8409 pj=12.6")
            lines.append(f"Xsw_{label}_{side} {source} {state} gn gp dnw {state} {state} sky130_body_tied_transmission_gate_raw")
            lines.append(f"Dpw_{label}_{side} {state} dnw sky130_fd_pr__model__parasitic__diode_pw2dn area=27.625 pj=21.5")
            lines.append(f"Dpf_{label}_{side} 0 {state} sky130_fd_pr__model__parasitic__diode_ps2nw area=8.8409 pj=12.6")
        if label != "control":
            start = 0.5 if label == "early" else 4.5
            lines.append(f"Ievent_{label} 0 {high} PWL(0 0 {start-0.000001:.9f}m 0 {start:.9f}m 11p "
                         f"{start+0.001:.9f}m 11p {start+0.001001:.9f}m 0 5.01m 0)")
    if gmin is not None:
        lines.append(f".options gmin={gmin:g}")
    lines += [".control", "set numdgt=15", f"tran {maxstep_ns:g}n 5m"]
    for label in ("control", "early", "late"):
        for when, time in (("start", "0.4m"), ("after_early", "0.502m"),
                           ("after_late", "4.502m"), ("final", "5m")):
            for side in ("high", "low"):
                lines.append(f"meas tran {label}_{side}_{when} find v({label}_{side}) at={time}")
    lines += ["quit", ".endc", ".end", ""]
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace",
           "--env", "NGSPICE_MEAS_PRECISION=15",
           "--workdir", "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", f"eventspikeseg:analog-ngspice{version}", "180", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=195)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {k.lower(): float(v) for k, v in re.findall(
        r"(?im)^\s*((?:control|early|late)_(?:high|low)_(?:start|after_early|after_late|final))\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and f"ngspice-{version} done" in log and len(values) == 24
    report = {"test": "sky130_body_tied_tg_event_time_differential",
              "completed": complete, "return_code": proc.returncode, "corner": "TT", "temperature_c": 27,
              "simulation_completed": complete, "simulator": f"ngspice-{version}",
              "gmin_siemens_requested": gmin,
              "ideal_initial_condition_without_switch": initial_condition,
              "dnw_bias_v": 1.2, "pwell_area_um2": 27.625, "pfet_nwell_area_um2": 8.8409,
              "off_switch_source": "fixed 0.9V shared bus",
              "guard_capacitance_ff_per_rail": guard_ff,
              "ideal_pulse_current_pa": 11, "ideal_pulse_width_ns": 1000,
              "ideal_pulse_charge_c": 11.011e-18,
              "event_times_ms": {"early": 0.5, "late": 4.5},
              "maximum_step_ns": maxstep_ns, "measurements": values,
              "limitations": "Reduced nominal MIM with grounded substrate, physical body-tied TG capacitive PEX, drawn-region PDK well-diode proxies, ideal initialized state/guard and ideal event current. Nonzero guard capacitance adds a second physical TG plus ideal guard capacitor per rail, but no guard co-write. No physical write, injector, sensing, noise/mismatch, PVT, model replay or service qualification."}
    if complete:
        diff = lambda label, when: values[f"{label}_high_{when}"] - values[f"{label}_low_{when}"]
        report["early_immediate_increment_mv"] = (diff("early", "after_early") - diff("control", "after_early")) * 1000
        report["late_immediate_increment_mv"] = (diff("late", "after_late") - diff("control", "after_late")) * 1000
        report["early_final_increment_mv"] = (diff("early", "final") - diff("control", "final")) * 1000
        report["late_final_increment_mv"] = (diff("late", "final") - diff("control", "final")) * 1000
        report["early_to_late_final_ratio"] = report["early_final_increment_mv"] / report["late_final_increment_mv"]
    report["source_sha256"] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (PAIR, TG, deck, RESULTS / f"{stem}.log")}
    (RESULTS / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not complete:
        raise RuntimeError(f"ngspice incomplete: {log[-2000:]}")


if __name__ == "__main__":
    main()
