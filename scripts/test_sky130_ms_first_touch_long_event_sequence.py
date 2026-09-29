"""Bounded physically clamped differential MIM repeated signed MOS events."""
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
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    arg = lambda name, default: next((item.split("=", 1)[1] for item in sys.argv[1:]
                                      if item.startswith(name + "=")), str(default))
    count = int(arg("--events", 10))
    width_ns = float(arg("--event-width-ns", 450))
    period_ns = float(arg("--event-period-ns", 600))
    if count <= 0 or count % 2 or width_ns <= 0 or period_ns <= width_ns + 1:
        raise ValueError("event count must be positive/even and period exceed pulse width")
    width_us, period_us, start_us = width_ns / 1000, period_ns / 1000, 3.0
    stop_us = start_us + (count - 1) * period_us + width_us + 0.65
    tag = ("" if (count, width_ns, period_ns) == (10, 450, 600) else
           f"_n{count}_w{width_ns:g}n_p{period_ns:g}n".replace(".", "p"))
    cases = {
        "ref": "", "p_one": "p", "n_one": "n",
        "p_train": "p" * count, "n_train": "n" * count,
        "pn_alt": "pn" * (count // 2), "np_alt": "np" * (count // 2),
    }
    lines = ["SKY130 SS 0C physical TG first-touch repeated signed events",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9", ".temp 0",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
             '.include "../../../asic/analog/modules.spice"',
             '.include "../../../asic/analog/sky130_ms_plif.spice"',
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             ".subckt diff_inject vp vn pp np pn nn vdd vss",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w=1 l=10",
             "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10",
             "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w=1 l=10",
             ".ends diff_inject"]

    def gate_wave(sequence: str, polarity: str, gate_kind: str) -> str:
        off, active = ((1.8, 1.8 - 0.95 * 1.08) if gate_kind == "p" else
                       (0.0, 0.95 * 0.6))
        points = [(0.0, off)]
        for index, sign in enumerate(sequence):
            if sign != polarity:
                continue
            at = start_us + index * period_us
            points.extend(((at - 0.0001, off), (at, active),
                           (at + width_us, active), (at + width_us + 0.0001, off)))
        points.append((stop_us, off))
        return "PWL(" + " ".join(f"{at:.9g}u {level:.9g}" for at, level in points) + ")"

    for name, sequence in cases.items():
        lines += [f"Xmem_p_{name} vp_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Xmem_n_{name} vn_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Vcl_{name} cl_{name} 0 PWL(0 1.8 2.9998u 1.8 2.9999u 0 {stop_us:g}u 0)",
                  f"Vclb_{name} clb_{name} 0 PWL(0 0 2.9998u 0 2.9999u 1.8 {stop_us:g}u 1.8)",
                  f"Xcl_p_{name} vcm vp_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Xcl_n_{name} vcm vn_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Vpp_{name} pp_{name} 0 {gate_wave(sequence, 'p', 'p')}",
                  f"Vnn_{name} nn_{name} 0 {gate_wave(sequence, 'p', 'n')}",
                  f"Vpn_{name} pn_{name} 0 {gate_wave(sequence, 'n', 'p')}",
                  f"Vnp_{name} np_{name} 0 {gate_wave(sequence, 'n', 'n')}",
                  f"Xinj_{name} vp_{name} vn_{name} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject"]
    lines += [".control", "set numdgt=15", f"tran 0.5n {stop_us:g}u uic"]
    for name in cases:
        lines.append(f"let diff_{name}=v(vp_{name})-v(vn_{name})")
        for phase, at in (("pre", "2.998u"),
                          ("first", f"{start_us+width_us+0.02:.9g}u"),
                          ("final", f"{stop_us-0.1:.9g}u")):
            lines.append(f"meas tran {phase}_{name} find diff_{name} at={at}")
    lines += ["quit", ".endc", ".end"]
    deck = BENCH / f"sky130_ms_first_touch_long_event_sequence_ss0{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (RES / f"sky130_ms_first_touch_long_event_sequence_ss0{tag}.log").write_text(log, encoding="utf-8")
    found = {(phase, name): float(value) for phase, name, value in re.findall(
        r"(?im)^\s*(pre|first|final)_([a-z_]+)\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and len(found) == 3 * len(cases)
    values = {}
    if complete:
        ref = found["final", "ref"]
        values = {name: (found["final", name] - ref) * 1e3 for name in cases if name != "ref"}
    one_p, one_n = values.get("p_one"), values.get("n_one")
    report = {"test": "sky130_first_touch_long_signed_event_sequence_ss0",
              "simulation_completed": complete, "return_code": run.returncode,
              "mos_corner": "ss", "temperature_c": 0, "mim_width_um": 10,
              "gate_fraction": 0.95, "event_width_ns": width_us * 1000,
              "event_count": count, "event_spacing_ns": period_ns,
              "final_differential_change_from_no_event_mv": values,
              "same_sign_relative_error_vs_ten_isolated_events": (
                  {"positive": (values["p_train"] - count * one_p) / (count * one_p),
                   "negative": (values["n_train"] - count * one_n) / (count * one_n)}
                  if complete else None),
              "alternating_residual_mv": (
                  {name: values[name] - count / 2 * (one_p + one_n)
                   for name in ("pn_alt", "np_alt")} if complete else None),
              "scope": "Ten physical positive/negative MOS events on a10um MIM pair with physical first-touch TG initialization, selected SS/0C MOS and typical passive devices. Ideal gate timing/voltage, no noise/mismatch, weight variation, readout, beta/reset/adaptation, extraction or full graph."}
    (RES / f"sky130_ms_first_touch_long_event_sequence_ss0{tag}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
