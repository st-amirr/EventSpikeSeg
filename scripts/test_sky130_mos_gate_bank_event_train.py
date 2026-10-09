"""Test repeated signed MOS injection on the extracted ten-device gate-bank pair."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "artifacts/analog_asic/layout/sky130_mos_gate_bank_100x10_nf10"
COUNT = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                  if arg.startswith("--count=")), "10"))
BENCH = OUTDIR / f"event_train_{COUNT}x4p4us.cir"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
CELL = "mos_gate_bank_100x10_nf10"
IMAGE = "eventspikeseg:analog-ngspice36"
PULSE_US = 4.4
PERIOD_US = 5.0
START_US = 2.0
RISE_US = 0.002
FRACTION = 0.9


def main() -> int:
    lines = [f"* {COUNT}-event signed injector train into extracted MOS gate-bank pair, TT/27C",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
             ".temp 27",
             f'.include "{MODEL}/models/parameters/invariant.spice"',
             f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
             f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
             f'.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             f'.include "/workspace/artifacts/analog_asic/layout/{OUTDIR.name}/{CELL}.spice"',
             "Vdd vdd 0 1.8",
             ".subckt diff_inject vp vn pp np pn nn vdd vss params: geom=1",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
             "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
             "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
             ".ends diff_inject"]
    cases = {"positive": [1] * COUNT, "alternating": [1 if i % 2 == 0 else -1 for i in range(COUNT)],
             "control": []}
    p_on, n_on = 1.8 - FRACTION * 1.08, FRACTION * 0.6
    final_us = START_US + (COUNT - 1) * PERIOD_US + PULSE_US + 0.02
    for tag, signs in cases.items():
        vp, vn = f"vp_{tag}", f"vn_{tag}"
        lines += [f"Xcap_p_{tag} {vp} 0 0 {CELL}", f"Xcap_n_{tag} {vn} 0 0 {CELL}",
                  f"Xinj_{tag} {vp} {vn} pp_{tag} np_{tag} pn_{tag} nn_{tag} vdd 0 diff_inject params: geom=1"]
        for pin in ("pp", "np", "pn", "nn"):
            off = 1.8 if pin in ("pp", "pn") else 0.0
            active_values = []
            for sign in signs:
                if pin == "pp": active = p_on if sign > 0 else 1.8
                elif pin == "nn": active = n_on if sign > 0 else 0.0
                elif pin == "pn": active = p_on if sign < 0 else 1.8
                else: active = n_on if sign < 0 else 0.0
                active_values.append(active)
            points = [(0.0, off)]
            for index, active in enumerate(active_values):
                start = START_US + index * PERIOD_US
                points += [(start - 0.001, off), (start + RISE_US, active),
                           (start + PULSE_US, active), (start + PULSE_US + RISE_US, off)]
            points.append((final_us, off))
            pwl = " ".join(f"{time:g}u {value:.12g}" for time, value in points)
            node = f"{pin}_{tag}"
            lines.append(f"V{node} {node} 0 PWL({pwl})")
    lines += [".ic " + " ".join(f"v(vp_{tag})=0.9 v(vn_{tag})=0.9" for tag in cases),
              ".control", "set numdgt=15", f"tran 1n {final_us:g}u 0 1n"]
    for tag in cases:
        lines += [f"let diff_{tag}=v(vp_{tag})-v(vn_{tag})",
                  f"meas tran result_{tag} find diff_{tag} at={final_us:g}u"]
    lines += ["quit", ".endc", ".end", ""]
    BENCH.write_text("\n".join(lines), encoding="ascii")
    proc = subprocess.run(["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
                           "-v", f"{ROOT}:/workspace", "-w", "/workspace",
                           "--entrypoint", "ngspice", IMAGE, "-b",
                           f"/workspace/artifacts/analog_asic/layout/{OUTDIR.name}/{BENCH.name}"],
                          capture_output=True, text=True, timeout=180, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUTDIR / f"event_train_{COUNT}x4p4us.log").write_text(log, encoding="utf-8")
    values = {name.lower(): float(value) for name, value in re.findall(
        r"(?im)^\s*result_(positive|alternating|control)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(values) != {"positive", "alternating", "control"}:
        raise RuntimeError(f"MOS gate bank event train failed:\n{log[-5000:]}")
    report = {"test": f"sky130_extracted_mos_gate_bank_{COUNT}_event_train",
              "corner": "tt", "temperature_c": 27, "event_count": COUNT,
              "pulse_width_us": PULSE_US, "pulse_period_us": PERIOD_US,
              "single_event_geometry": 1, "gate_fraction": FRACTION,
              "final_differential_v": values,
              "positive_average_step_per_event_v": (values["positive"]-values["control"])/COUNT,
              "alternating_final_residual_v": values["alternating"]-values["control"],
              "service_time_us": (COUNT-1)*PERIOD_US+PULSE_US,
              "fits_5ms_service_window": (COUNT-1)*PERIOD_US+PULSE_US < 5000,
              "simulation_completed": True,
              "limitations": ["ideal initial state", "schematic injector and no physical pulse drivers",
                              "TT only", "no threshold/reset/beta or full-float input sequence"]}
    (OUTDIR / f"event_train_{COUNT}x4p4us_qualification.json").write_text(
        json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
