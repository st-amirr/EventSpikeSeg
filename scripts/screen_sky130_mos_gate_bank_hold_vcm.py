"""Measure extracted MOS-bank differential retention with VCM bias and injector loading."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
LAYOUT_NAME = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--layout-bank-name=")), "sky130_mos_gate_bank_100x10_nf10")
LAYOUT = OUT / "layout" / LAYOUT_NAME
if not re.fullmatch(r"sky130_mos_(?:gate_bank_[A-Za-z0-9p]+_nf10|gate_state_pair_[A-Za-z0-9p]+_nf10)", LAYOUT_NAME):
    raise ValueError("invalid --layout-bank-name")
LAYOUT_CELL = LAYOUT_NAME.removeprefix("sky130_")
PAIRED_LAYOUT = "gate_state_pair" in LAYOUT_NAME
BENCH = OUT / "benches"
RES = OUT / "results"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
GEOMETRIES = (0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0)
DIFF_OVERRIDE = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--diffs-mv=")), None)
DIFFS_MV = tuple(float(x) for x in (
    DIFF_OVERRIDE if DIFF_OVERRIDE is not None else
    "-900,-500,-100,0,100,500,900").split(","))
INJECTOR_LOADED = "--no-injector-load" not in sys.argv[1:]
ISOLATE_INJECTOR = "--isolate-injector" in sys.argv[1:]
STACKED_ACCESS = "--stacked-access" in sys.argv[1:]
HV_ACCESS = "--hv-access" in sys.argv[1:]
PHYSICAL_TG = "--physical-tg" in sys.argv[1:]
LONG_ACCESS = "--long-access" in sys.argv[1:]
CORNER = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--corner=")), "tt")
TEMP_C = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--temp=")), "27"))
WRITE_END_US = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--write-time-us=")), "2.99"))
SWITCH_OFF_US = WRITE_END_US + 0.001
HOLD_START_US = SWITCH_OFF_US + 1.0
TIME_SAMPLES_MS = tuple(float(x) for x in next(
    (a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--time-samples-ms=")), "").split(",") if x)
if CORNER not in ("ss", "tt", "ff"):
    raise ValueError("--corner must be ss, tt, or ff")


def main() -> int:
    if ISOLATE_INJECTOR and not INJECTOR_LOADED:
        raise ValueError("--isolate-injector requires the injector bank to remain present")
    if sum((PHYSICAL_TG, LONG_ACCESS, HV_ACCESS)) > 1:
        raise ValueError("choose only one access-switch option")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = [
        "* Extracted MOS gate state banks held at VCM with the inactive injector bank connected",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2 gmin=1e-12",
        f".temp {TEMP_C}",
        f'.include "{MODEL}/models/parameters/invariant.spice"',
        f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
        f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{CORNER}.corner.spice"',
        f'.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{CORNER}.corner.spice"',
        '.include "../../../asic/analog/modules.spice"',
        f'.include "../layout/{LAYOUT.name}/{LAYOUT_CELL}.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
    ]
    write_cell = "transmission_gate"
    isolation_cell = "transmission_gate"
    if PHYSICAL_TG:
        lines += ['.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"',
                  ".subckt transmission_gate_pex a b en enb vdd vss",
                  "Xpex a b en enb vdd vss sky130_transmission_gate_raw",
                  ".ends transmission_gate_pex"]
        write_cell = isolation_cell = "transmission_gate_pex"
    elif LONG_ACCESS:
        lines += [".subckt transmission_gate_long a b en enb vdd vss",
                  f"Xn a en b vss sky130_fd_pr__nfet_01v8 w=1 l=10",
                  f"Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=10",
                  ".ends transmission_gate_long"]
        isolation_cell = "transmission_gate_long"
    if HV_ACCESS:
        lines += [f'.include "{MODEL}/cells/nfet_g5v0d10v5/sky130_fd_pr__nfet_g5v0d10v5__tt.corner.spice"',
                  f'.include "{MODEL}/cells/pfet_g5v0d10v5/sky130_fd_pr__pfet_g5v0d10v5__tt.corner.spice"',
                  ".subckt transmission_gate_hv a b en enb vdd vss",
                  "Xn a en b vss sky130_fd_pr__nfet_g5v0d10v5 w=4 l=0.5",
                  "Xp a enb b vdd sky130_fd_pr__pfet_g5v0d10v5 w=8 l=0.5",
                  ".ends transmission_gate_hv"]
        write_cell = isolation_cell = "transmission_gate_hv"
    if INJECTOR_LOADED:
        lines.append(".subckt diff_inject vp vn " + " ".join(
            f"{pin}{i}" for i in range(len(GEOMETRIES)) for pin in ("pp", "np", "pn", "nn")) + " vdd vss")
        for i, geometry in enumerate(GEOMETRIES):
            lines += [f"Xp_pos{i} vp pp{i} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geometry:g} l=10",
                      f"Xn_neg{i} vn nn{i} vss vss sky130_fd_pr__nfet_01v8 w={geometry:g} l=10",
                      f"Xp_neg{i} vn pn{i} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geometry:g} l=10",
                      f"Xn_pos{i} vp np{i} vss vss sky130_fd_pr__nfet_01v8 w={geometry:g} l=10"]
        lines.append(".ends diff_inject")
        if ISOLATE_INJECTOR:
            # No presynaptic events occur in this retention screen. Keep the
            # injector bank disconnected while the independent state source
            # programs the membrane and throughout the hold interval.
            lines += ["Viso iso 0 0", "Visob isob 0 1.8"]
    measurements = []
    for diff_mv in DIFFS_MV:
        tag = f"d{str(diff_mv).replace('-', 'm').replace('.', 'p')}"
        vp0, vn0 = 0.9 + diff_mv / 2000, 0.9 - diff_mv / 2000
        lines += [f"Vinitp_{tag} initp_{tag} 0 {vp0:.9g}", f"Vinitn_{tag} initn_{tag} 0 {vn0:.9g}",
                  f"Vcl_{tag} cl_{tag} 0 PWL(0 1.8 {WRITE_END_US:g}u 1.8 {SWITCH_OFF_US:g}u 0 5.1m 0)",
                  f"Vclb_{tag} clb_{tag} 0 PWL(0 0 {WRITE_END_US:g}u 0 {SWITCH_OFF_US:g}u 1.8 5.1m 1.8)"]
        if STACKED_ACCESS:
            lines += [f"Xclp1_{tag} initp_{tag} midp_{tag} cl_{tag} clb_{tag} vdd 0 {write_cell}",
                      f"Xclp2_{tag} midp_{tag} vp_{tag} cl_{tag} clb_{tag} vdd 0 {write_cell}",
                      f"Xcln1_{tag} initn_{tag} midn_{tag} cl_{tag} clb_{tag} vdd 0 {write_cell}",
                      f"Xcln2_{tag} midn_{tag} vn_{tag} cl_{tag} clb_{tag} vdd 0 {write_cell}"]
        else:
            lines += [f"Xclp_{tag} initp_{tag} vp_{tag} cl_{tag} clb_{tag} vdd 0 {write_cell}",
                      f"Xcln_{tag} initn_{tag} vn_{tag} cl_{tag} clb_{tag} vdd 0 {write_cell}"]
        if PAIRED_LAYOUT:
            lines.append(f"Xcap_pair_{tag} vp_{tag} vn_{tag} vcm 0 {LAYOUT_CELL}")
        else:
            lines += [f"Xcap_p_{tag} vp_{tag} vcm 0 {LAYOUT_CELL}",
                      f"Xcap_n_{tag} vn_{tag} vcm 0 {LAYOUT_CELL}"]
        if INJECTOR_LOADED:
            pins = []
            for i in range(len(GEOMETRIES)):
                for pin, value in (("pp", 1.8), ("np", 0), ("pn", 1.8), ("nn", 0)):
                    node = f"{pin}{i}_{tag}"
                    lines.append(f"V{node} {node} 0 {value:g}")
                    pins.append(node)
            if ISOLATE_INJECTOR:
                lines += [f"Xiso_p_{tag} vp_{tag} injp_{tag} iso isob vdd 0 {isolation_cell}",
                          f"Xiso_n_{tag} vn_{tag} injn_{tag} iso isob vdd 0 {isolation_cell}"]
                injp, injn = f"injp_{tag}", f"injn_{tag}"
            else:
                injp, injn = f"vp_{tag}", f"vn_{tag}"
            lines.append(f"Xinj_{tag} {injp} {injn} " + " ".join(pins) + " vdd 0 diff_inject")
        measurements.append((tag, diff_mv, vp0 - vn0))
    lines += [".save " + " ".join(signal for tag, _, _ in measurements
                                  for signal in (f"v(vp_{tag})", f"v(vn_{tag})")),
              ".control", "set numdgt=15", "tran 5u 5.1m 0 5u uic"]
    for tag, _, _ in measurements:
        lines += [f"let diff_{tag}=v(vp_{tag})-v(vn_{tag})",
                  f"meas tran start_{tag} find diff_{tag} at={HOLD_START_US:g}u",
                  f"meas tran final_{tag} find diff_{tag} at=5m"]
        for sample_ms in TIME_SAMPLES_MS:
            sample_us = HOLD_START_US + sample_ms * 1000
            if sample_us > 5100:
                raise ValueError("time sample exceeds the current 5.1ms transient end")
            lines.append(f"meas tran ts{str(sample_ms).replace('.', 'p')}_{tag} find diff_{tag} at={sample_us:g}u")
    lines += ["quit", ".endc", ".end", ""]
    mode = ("loaded" if INJECTOR_LOADED else "isolated") + ("_injisolate" if ISOLATE_INJECTOR else "") + ("_stack" if STACKED_ACCESS else "") + ("_hv" if HV_ACCESS else "") + ("_pextg" if PHYSICAL_TG else "") + ("_long" if LONG_ACCESS else "")
    mode += f"_{CORNER}_temp{TEMP_C}"
    mode += f"_{LAYOUT_NAME.removeprefix('sky130_')}"
    if DIFF_OVERRIDE is not None:
        mode += "_diffs" + "_".join(str(x).replace("-", "m").replace(".", "p") for x in DIFFS_MV)
    deck = BENCH / f"sky130_mos_gate_bank_hold_vcm_{mode}_5ms.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace/artifacts/analog_asic/benches",
               "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
               "300", "ngspice", "-b", deck.name]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=330)
    log = proc.stdout + proc.stderr
    log_path = RES / f"sky130_mos_gate_bank_hold_vcm_{mode}_5ms.log"
    log_path.write_text(log, encoding="utf-8")
    measured = {name.lower(): float(value) for name, value in re.findall(
        r"(?im)^\s*(start_d\w+|final_d\w+|ts\w+_d\w+)\s*=\s*([-+0-9.eE]+)", log)}
    rows = []
    for tag, diff_mv, initial in measurements:
        start, final = measured.get(f"start_{tag}"), measured.get(f"final_{tag}")
        row = {"initial_differential_mv": diff_mv, "hold_start_time_us": HOLD_START_US,
               "measured_at_5ms_v": final,
               "drift_uv": (final - start) * 1e6 if start is not None and final is not None else None,
               "initial_setpoint_v": initial}
        row["measured_at_4us_v" if abs(HOLD_START_US - 4.0) < 1e-9 else "measured_at_hold_start_v"] = start
        if TIME_SAMPLES_MS:
            row["time_series"] = []
            for sample_ms in TIME_SAMPLES_MS:
                key = f"ts{str(sample_ms).replace('.', 'p')}_{tag}".lower()
                value = measured.get(key)
                row["time_series"].append({
                    "hold_elapsed_ms": sample_ms,
                    "differential_v": value,
                    "drift_uv_from_hold_start": (value - start) * 1e6 if value is not None and start is not None else None,
                })
        rows.append(row)
    completed = (proc.returncode == 0 and "ngspice-36 done" in log and
                 all(row["drift_uv"] is not None for row in rows))
    report = {"test": f"sky130_extracted_MOS_gate_bank_5ms_retention_at_VCM_{mode}",
              "layout_bank": LAYOUT_NAME,
              "time_samples_ms_after_hold_start": list(TIME_SAMPLES_MS),
              "temperature_c": TEMP_C, "mos_corner": CORNER, "channel_common_mode_v": 0.9,
              "state_differential_initial_mv": list(DIFFS_MV), "event_injector_geometry_bank_loaded": INJECTOR_LOADED,
              "injector_bank_isolated_during_retention": ISOLATE_INJECTOR,
              "write_end_time_us": WRITE_END_US, "hold_start_time_us": HOLD_START_US,
              "injector_gate_state": "all P gates at VDD; all N gates at VSS",
              "access_switch": (("two series " if STACKED_ACCESS else "") +
                                ("extracted-layout SKY130 1.8V transmission gate with capacitance PEX" if PHYSICAL_TG else
                                 "long-channel SKY130 1.8V transmission gate (Wn=1um/Wp=2um,L=10um)" if LONG_ACCESS else
                                 "schematic SKY130 5V transmission gate (Wn=4um/Wp=8um,L=0.5um)" if HV_ACCESS else
                                 "schematic SKY130 1.8V transmission gate") + ", opened at 2.991us"),
              "simulation_completed": completed, "simulator_exit_code": proc.returncode,
              "log": log_path.name, "rows": rows,
              "physical_access_switch_layout_and_noise_qualified": False,
              "scope": f"{('Paired differential-layout macro' if PAIRED_LAYOUT else 'Two extracted single-rail MOS gate-cap banks')} ({LAYOUT_NAME}) use GATE=membrane, tied channel terminals=VCM and BULK=0. Both differential rails are written through {('the extracted-layout TG PEX subcircuit' if PHYSICAL_TG else 'the standard 1.8V TG' if LONG_ACCESS else 'the selected access TG')}, then held for 5ms. {'The full 13-geometry injector bank remains attached with all devices off. ' if INJECTOR_LOADED else 'The injector network is disconnected to isolate intrinsic storage/access-switch hold. '}{'A ' + ('extracted-layout' if PHYSICAL_TG else 'long-channel' if LONG_ACCESS else 'schematic') + ' transmission-gate isolates the injector bank throughout this no-event state-program/hold screen. ' if ISOLATE_INJECTOR else ''}Deterministic {CORNER.upper()}/{TEMP_C}C hold only; no transient noise or mismatch."}
    out = RES / f"sky130_mos_gate_bank_hold_vcm_{mode}_5ms.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"simulation_completed": completed, "rows": rows}, indent=2))
    return 0 if completed else 2


if __name__ == "__main__":
    raise SystemExit(main())
