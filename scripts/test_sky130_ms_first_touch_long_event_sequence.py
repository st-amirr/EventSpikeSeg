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
    gate_fraction = float(arg("--gate-fraction", .95))
    positive_gate_fraction = float(arg("--positive-gate-fraction", gate_fraction))
    negative_gate_fraction = float(arg("--negative-gate-fraction", gate_fraction))
    geometry_scale = float(arg("--injector-geometry-scale", 1))
    release_lead_ns = float(arg("--release-lead-ns", .1))
    gate_slew_ns = float(arg("--gate-slew-ns", .1))
    shared_bank_load = "--shared-bank-load" in sys.argv[1:]
    initial_diff_v = float(arg("--initial-diff-v", 0))
    if count <= 0 or count % 2 or width_ns <= 0 or period_ns <= width_ns + 1:
        raise ValueError("event count must be positive/even and period exceed pulse width")
    if not 0 < gate_fraction < 1 or not .5 <= geometry_scale <= 4 or not .1 <= release_lead_ns <= 10:
        raise ValueError("gate/geometry/release outside bounded screen")
    if not 0 < positive_gate_fraction < 1 or not 0 < negative_gate_fraction < 1:
        raise ValueError("polarity gate fractions must be inside 0-1")
    if not .1 <= gate_slew_ns <= 2:
        raise ValueError("gate slew outside bounded 0.1-2ns screen")
    if abs(initial_diff_v) > 1.2:
        raise ValueError("initial differential exceeds bounded state-bias screen")
    width_us, period_us, start_us = width_ns / 1000, period_ns / 1000, 3.0
    stop_us = start_us + (count - 1) * period_us + width_us + 0.65
    tag = ("" if (count, width_ns, period_ns) == (10, 450, 600) else
           f"_n{count}_w{width_ns:g}n_p{period_ns:g}n".replace(".", "p"))
    if gate_fraction != .95:
        tag += f"_g{gate_fraction:g}".replace(".", "p")
    if positive_gate_fraction != gate_fraction:
        tag += f"_pg{positive_gate_fraction:g}".replace(".", "p")
    if negative_gate_fraction != gate_fraction:
        tag += f"_ng{negative_gate_fraction:g}".replace(".", "p")
    if geometry_scale != 1:
        tag += f"_geom{geometry_scale:g}".replace(".", "p")
    if release_lead_ns != .1:
        tag += f"_lead{release_lead_ns:g}n".replace(".", "p")
    if initial_diff_v:
        tag += f"_d{initial_diff_v:g}v".replace("-", "m").replace(".", "p")
    if gate_slew_ns != .1:
        tag += f"_rise{gate_slew_ns:g}n".replace(".", "p")
    if shared_bank_load:
        tag += "_banked"
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
             ]
    geometries = ((0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0,
                   2.5, 3.0, 3.5, 4.0) if shared_bank_load else (geometry_scale,))
    lines.append(".subckt diff_inject vp vn " + " ".join(
        f"{pin}{index}" for index in range(len(geometries))
        for pin in ("pp", "np", "pn", "nn")) + " vdd vss")
    for index, geom in enumerate(geometries):
        lines += [f"Xp_pos{index} vp pp{index} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom:g} l=10",
                  f"Xn_neg{index} vn nn{index} vss vss sky130_fd_pr__nfet_01v8 w={geom:g} l=10",
                  f"Xp_neg{index} vn pn{index} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom:g} l=10",
                  f"Xn_pos{index} vp np{index} vss vss sky130_fd_pr__nfet_01v8 w={geom:g} l=10"]
    lines.append(".ends diff_inject")
    if initial_diff_v:
        lines += [f"Vstate_init_p state_init_p 0 {0.9 + initial_diff_v/2:.12g}",
                  f"Vstate_init_n state_init_n 0 {0.9 - initial_diff_v/2:.12g}"]
    init_p, init_n = (("state_init_p", "state_init_n") if initial_diff_v else ("vcm", "vcm"))

    def gate_wave(sequence: str, polarity: str, gate_kind: str) -> str:
        active_fraction = positive_gate_fraction if polarity == "p" else negative_gate_fraction
        off, active = ((1.8, 1.8 - active_fraction * 1.08) if gate_kind == "p" else
                       (0.0, active_fraction * 0.6))
        points = [(0.0, off)]
        for index, sign in enumerate(sequence):
            if sign != polarity:
                continue
            at = start_us + index * period_us
            rise_us = gate_slew_ns / 1000
            points.extend(((at - 0.0001, off), (at + rise_us, active),
                           (at + width_us, active), (at + width_us + rise_us, off)))
        points.append((stop_us, off))
        return "PWL(" + " ".join(f"{at:.9g}u {level:.9g}" for at, level in points) + ")"

    for name, sequence in cases.items():
        release_end = start_us - release_lead_ns / 1000
        release_begin = release_end - .0001
        lines += [f"Xmem_p_{name} vp_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Xmem_n_{name} vn_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Vcl_{name} cl_{name} 0 PWL(0 1.8 {release_begin:.9g}u 1.8 {release_end:.9g}u 0 {stop_us:g}u 0)",
                  f"Vclb_{name} clb_{name} 0 PWL(0 0 {release_begin:.9g}u 0 {release_end:.9g}u 1.8 {stop_us:g}u 1.8)",
                  f"Xcl_p_{name} {init_p} vp_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Xcl_n_{name} {init_n} vn_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  ]
        gate_nodes = []
        for index, geom in enumerate(geometries):
            for pin, sign, mos in (("pp", "p", "p"), ("np", "n", "n"),
                                   ("pn", "n", "p"), ("nn", "p", "n")):
                node = f"{pin}{index}_{name}"
                signal = (gate_wave(sequence, sign, mos) if geom == geometry_scale
                          else ("1.8" if mos == "p" else "0"))
                lines.append(f"V{node} {node} 0 {signal}")
                gate_nodes.append(node)
        lines.append(f"Xinj_{name} vp_{name} vn_{name} " + " ".join(gate_nodes) + " vdd 0 diff_inject")
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
              "gate_fraction": gate_fraction, "injector_geometry_scale": geometry_scale,
              "positive_gate_fraction": positive_gate_fraction,
              "negative_gate_fraction": negative_gate_fraction,
              "shared_bank_load": shared_bank_load,
              "initial_differential_v": initial_diff_v,
              "release_lead_ns": release_lead_ns, "event_width_ns": width_us * 1000,
              "gate_slew_ns": gate_slew_ns,
              "event_count": count, "event_spacing_ns": period_ns,
              "final_differential_change_from_no_event_mv": values,
              "same_sign_relative_error_vs_ten_isolated_events": (
                  {"positive": (values["p_train"] - count * one_p) / (count * one_p),
                   "negative": (values["n_train"] - count * one_n) / (count * one_n)}
                  if complete else None),
              "alternating_residual_mv": (
                  {name: values[name] - count / 2 * (one_p + one_n)
                   for name in ("pn_alt", "np_alt")} if complete else None),
              "scope": "Bounded physical positive/negative MOS event sequences on a10um MIM pair with physical first-touch TG initialization, selected SS/0C MOS and typical passive devices. Optional shared13-geometry bank load keeps inactive branches connected. Ideal gate timing/voltage, no noise/mismatch, weight variation, readout, beta/reset/adaptation, extraction or full graph."}
    (RES / f"sky130_ms_first_touch_long_event_sequence_ss0{tag}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
