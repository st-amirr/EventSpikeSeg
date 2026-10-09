#!/usr/bin/env python3
"""Test active state-voltage precharge before adding a differential MIM range cap."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import BENCH, COMMON, RES, ROOT

IMAGE = "eventspikeseg:analog-ngspice36"
SAMPLES = {"state_before_precharge": 0.49, "ext_after_precharge": 1.09,
           "state_before_connect": 1.19, "state_after_connect": 1.21,
           "state_after_settle": 1.5, "ref_after_settle": 1.5}


def main() -> int:
    edge_ns = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
    state_diff_mv = float(sys.argv[2]) if len(sys.argv) > 2 else 112.5
    input_pair_um = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    vbiasp_v = float(sys.argv[4]) if len(sys.argv) > 4 else 0.75
    switch_high_v = float(sys.argv[5]) if len(sys.argv) > 5 else 1.8
    switch_low_v = 1.8 - switch_high_v
    edge_us = edge_ns / 1000.0
    SAMPLES["state_after_connect"] = 1.2 + edge_us + 0.01
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    p = 0.9 + state_diff_mv / 2000.0
    n = 0.9 - state_diff_mv / 2000.0
    until = "2u"
    lines = ["SKY130 TT differential MIM range addition with OTA precharge buffer",
             COMMON, "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             f"Vinitp initp 0 {p:.9f}", f"Vinitn initn 0 {n:.9f}",
             f"Vinit init 0 PWL(0 1.8 {0.2-edge_us/2:g}u 1.8 {0.2+edge_us/2:g}u 0 2u 0)",
             f"Vinitb initb 0 PWL(0 0 {0.2-edge_us/2:g}u 0 {0.2+edge_us/2:g}u 1.8 2u 1.8)",
             f"Vpre pre 0 PWL(0 0 {0.5-edge_us/2:g}u 0 {0.5+edge_us/2:g}u {switch_high_v:g} {1-edge_us/2:g}u {switch_high_v:g} {1+edge_us/2:g}u 0 2u 0)",
             f"Vpreb preb 0 PWL(0 1.8 {0.5-edge_us/2:g}u 1.8 {0.5+edge_us/2:g}u {switch_low_v:g} {1-edge_us/2:g}u {switch_low_v:g} {1+edge_us/2:g}u 1.8 2u 1.8)",
             f"Vconnect connect 0 PWL(0 0 {1.2-edge_us/2:g}u 0 {1.2+edge_us/2:g}u {switch_high_v:g} 2u {switch_high_v:g})",
             f"Vconnectb connectb 0 PWL(0 1.8 {1.2-edge_us/2:g}u 1.8 {1.2+edge_us/2:g}u {switch_low_v:g} 2u {switch_low_v:g})",
             ".ic v(event_p_ext)=0.9 v(event_n_ext)=0.9"]
    for branch in ("event", "reference"):
        for side, level in (("p", p), ("n", n)):
            state = f"{branch}_{side}"
            lines += [f"Xinit_{state} init{side} {state} init initb vdd 0 transmission_gate",
                      f"Xfine_{state} {state} vcm sky130_fd_pr__cap_mim_m3_2 w=10 l=10 mf=1"]
        if branch == "event":
            lines += [
                f"Xbuf_p bufp event_p bufp vbnn vbpp vdd 0 sky130_sc_ota win={input_pair_um:g} wn3=20 wp3=100 cc=500f",
                f"Xbuf_n bufn event_n bufn vbnn vbpp vdd 0 sky130_sc_ota win={input_pair_um:g} wn3=20 wp3=100 cc=500f",
                "Vbn vbnn 0 0.65", f"Vbp vbpp 0 {vbiasp_v:g}",
                "Xpre_p bufp event_p_ext pre preb vdd 0 transmission_gate",
                "Xpre_n bufn event_n_ext pre preb vdd 0 transmission_gate",
                "Xconnect_p event_p event_p_ext connect connectb vdd 0 transmission_gate",
                "Xconnect_n event_n event_n_ext connect connectb vdd 0 transmission_gate",
                "Xextension_p event_p_ext vcm sky130_fd_pr__cap_mim_m3_2 w=13.3 l=13.3 mf=1",
                "Xextension_n event_n_ext vcm sky130_fd_pr__cap_mim_m3_2 w=13.3 l=13.3 mf=1",
            ]
    lines += [".ic v(event_p)=0.95625 v(event_n)=0.84375 v(reference_p)=0.95625 v(reference_n)=0.84375",
              ".control", "set numdgt=15", "tran 0.5n 2u uic",
              "let d_event=v(event_p)-v(event_n)",
              "let d_ext=v(event_p_ext)-v(event_n_ext)",
              "let d_ref=v(reference_p)-v(reference_n)",
              "let d_buf=v(bufp)-v(bufn)"]
    for name, time in SAMPLES.items():
        if name.startswith("state_"):
            node = "event_p"
            node_n = "event_n"
            lines += [f"meas tran {name} find d_event at={time:g}u"]
        elif name.startswith("ext_"):
            lines += [f"meas tran {name} find d_ext at={time:g}u"]
        else:
            lines += [f"meas tran {name} find d_ref at={time:g}u"]
    lines += ["meas tran buffer_differential find d_buf at=1.09u",
              "meas tran buffer_p find v(bufp) at=1.09u",
              "meas tran buffer_n find v(bufn) at=1.09u"]
    lines += ["quit", ".endc", ".end", ""]
    stem = f"sky130_active_mim_range_precharge_tt_edge{edge_ns:g}ns_diff{state_diff_mv:g}mv_win{input_pair_um:g}um_vbp{vbiasp_v:g}_sw{switch_high_v:g}v"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           IMAGE, "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {key: float(value) for key, value in re.findall(
        r"(?im)^\s*(state_[a-z_]+|ext_after_precharge|ref_after_settle|buffer_differential|buffer_p|buffer_n)\s*=\s*([-+0-9.eE]+)", log)}
    complete = (run.returncode == 0 and "ngspice-36 done" in log
                and all(key in values for key in SAMPLES))
    report = {"test": "sky130_active_buffered_extension_cap_precharge",
              "simulation_completed": complete,
              "corner": "TT", "temperature_c": 27,
              "control_edge_ns": edge_ns,
              "initial_state_differential_mv": state_diff_mv,
              "ota_input_pair_width_um": input_pair_um,
              "ota_vbiasp_v": vbiasp_v,
              "switch_on_levels_v": [switch_high_v, switch_low_v],
              "fine_cap_drawn_um": [10, 10], "extension_cap_drawn_um": [13.3, 13.3],
              "precharge_window_us": [0.5, 1.0], "connect_midpoint_us": 1.2,
              "buffer": f"SKY130 PDK OTA with win={input_pair_um:g}um, wn3=20um, wp3=100um, cc=500f; schematic, no layout/PEX",
              "measurements_v": values,
              "scope": "Differential TT schematic PDK MIM pair and PDK TG switches. Extension top plates are precharged from live state-following OTA outputs, isolated, then connected. State initialized ideally. No event pulse, sampled noise, mismatch, PVT, extracted TG/interconnect, full-float mapping, or threshold/reset circuitry."}
    if complete:
        report["extension_precharge_error_vs_live_state_uv"] = (
            values["ext_after_precharge"] - values["state_before_precharge"])*1e6
        before = values["state_before_connect"]
        after = values["state_after_connect"]
        reference = values["ref_after_settle"]
        report["differential_state_kick_10ns_after_control_edge_uv"] = (after-before)*1e6
        report["differential_state_kick_300ns_after_control_edge_uv"] = (values["state_after_settle"]-before)*1e6
        report["state_error_vs_reference_after_settle_uv"] = (values["state_after_settle"]-reference)*1e6
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
