#!/usr/bin/env python3
"""Transiently test live two-range gain switching on one fixed MIM state cap."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import BENCH, COMMON, RES, ROOT

IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    branch_probes = "--branch-probes" in sys.argv[1:]
    negative = "--negative" in sys.argv[1:]
    argv = [arg for arg in sys.argv[1:] if arg not in ("--branch-probes", "--negative")]
    threshold = 0.75 if negative else 1.05
    trim_uv = float(argv[0]) if len(argv) > 0 else 0.0
    corner = argv[1].lower() if len(argv) > 1 else "tt"
    temperature = float(argv[2]) if len(argv) > 2 else {"tt": 27, "ss": 0, "ff": 85}.get(corner, 27)
    pulse_level = float(argv[3]) if len(argv) > 3 else 1.0
    pulse_width_us = float(argv[4]) if len(argv) > 4 else 1.5
    initial = float(argv[5]) if len(argv) > 5 else (0.756 if negative else 1.044)
    event_end_us = 1.0 + pulse_width_us
    stop_us = max(event_end_us + 0.5, 2.7)
    if corner not in {"tt", "ss", "ff"}:
        raise ValueError("corner must be tt, ss or ff")
    common = COMMON.replace("__tt.corner.spice", f"__{corner}.corner.spice")
    comparator_reference = threshold + trim_uv * 1e-6
    lines = [f"SKY130 {corner.upper()} fixed-cap two-range live gain switch crossing transient",
             common, f".temp {temperature:g}", "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbias vbias 0 0.7",
             f"Vboundary boundary 0 {comparator_reference:.12g}",
             f"Vinitp initp 0 {initial:g}",
             "Vinit init 0 PWL(0 1.8 0.1999u 1.8 0.2u 0 2u 0)",
             "Vinitb initb 0 PWL(0 0 0.1999u 0 0.2u 1.8 2u 1.8)",
             (f"Vpulse pulse 0 PWL(0 0 0.9999u 0 1u {pulse_level:g} {event_end_us-0.0001:g}u {pulse_level:g} {event_end_us:g}u 0 {stop_us:g}u 0)"
              if negative else f"Vpulse pulse 0 PWL(0 1.8 0.9999u 1.8 1u {pulse_level:g} {event_end_us-0.0001:g}u {pulse_level:g} {event_end_us:g}u 1.8 {stop_us:g}u 1.8)"),
             ".subckt range_compare inp inn output vbias vdd vss",
             "Xip d1 inp tail vss sky130_fd_pr__nfet_01v8 w=10 l=0.5",
             "Xin d2 inn tail vss sky130_fd_pr__nfet_01v8 w=10 l=0.5",
             "Xtail tail vbias vss vss sky130_fd_pr__nfet_01v8 w=5 l=1",
             "Xload1 d1 d1 vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
             "Xload2 d2 d1 vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
             "Xb1p invnode d2 vdd vdd sky130_fd_pr__pfet_01v8 w=10 l=0.5",
             "Xb1n invnode d2 vss vss sky130_fd_pr__nfet_01v8 w=5 l=0.5",
             "Xb2p output invnode vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
             "Xb2n output invnode vss vss sky130_fd_pr__nfet_01v8 w=10 l=0.5",
             ".ends range_compare",
             ".subckt range_select_tg a b en enb vdd vss",
             "Xrn a en b vss sky130_fd_pr__nfet_01v8 w=0.42 l=0.5",
             "Xrp a enb b vdd sky130_fd_pr__pfet_01v8 w=0.84 l=0.5", ".ends range_select_tg",
             ".subckt selectable_pulse state pulse vdd vss vcm range_out range_bar",
             "* Before the first boundary use the larger event current; after it use the smaller branch.",
             ("Xfast fast_d pulse vss vss sky130_fd_pr__nfet_01v8 w=4.24 l=2" if negative else
              "Xfast fast_d pulse vdd vdd sky130_fd_pr__pfet_01v8 w=4.24 l=2"),
             ("Vfast_probe fast_d fast_sel 0" if branch_probes else "* no fast branch probe"),
             f"Xfast_sel state {'fast_sel' if branch_probes else 'fast_d'} range_bar range_out vdd vss range_select_tg",
             ("Xslow slow_d pulse vss vss sky130_fd_pr__nfet_01v8 w=1.5 l=2" if negative else
              "Xslow slow_d pulse vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=2"),
             ("Vslow_probe slow_d slow_sel 0" if branch_probes else "* no slow branch probe"),
             f"Xslow_sel state {'slow_sel' if branch_probes else 'slow_d'} range_out range_bar vdd vss range_select_tg",
             ".ends selectable_pulse",
             ("Xrange boundary state range_out vbias vdd 0 range_compare" if negative else
              "Xrange state boundary range_out vbias vdd 0 range_compare"),
             "Xrange_inv range_out range_bar vdd 0 inv", "Crange range_out 0 30f",
             "Xmem state vcm membrane_mim w_um=20 l_um=20", "Xref memref vcm membrane_mim w_um=20 l_um=20",
             "Xmem_fast memfast vcm membrane_mim w_um=20 l_um=20",
             "Xmem_slow memslow vcm membrane_mim w_um=20 l_um=20",
             "Xinit state initp init initb vdd 0 transmission_gate",
             "Xinit_ref memref initp init initb vdd 0 transmission_gate",
             "Xinit_fast memfast initp init initb vdd 0 transmission_gate",
             "Xinit_slow memslow initp init initb vdd 0 transmission_gate",
             ".ic v(range_out)=0 v(range_bar)=1.8",
             "Xgain state pulse vdd 0 vcm range_out range_bar selectable_pulse",
             ("Xstatic_fast memfast pulse 0 0 sky130_fd_pr__nfet_01v8 w=4.24 l=2" if negative else
              "Xstatic_fast memfast pulse vdd vdd sky130_fd_pr__pfet_01v8 w=4.24 l=2"),
             ("Xstatic_slow memslow pulse 0 0 sky130_fd_pr__nfet_01v8 w=1.5 l=2" if negative else
              "Xstatic_slow memslow pulse vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=2"),
             ".control", "set numdgt=15", f"tran 20p {stop_us:g}u uic",
             "meas tran state_before find v(state) at=0.9u",
             f"meas tran state_after find v(state) at={event_end_us+0.2:g}u",
             "meas tran reference_before find v(memref) at=0.9u",
             f"meas tran reference_after find v(memref) at={event_end_us+0.2:g}u",
             "meas tran fast_before find v(memfast) at=0.9u",
             f"meas tran fast_after find v(memfast) at={event_end_us+0.2:g}u",
             "meas tran slow_before find v(memslow) at=0.9u",
             f"meas tran slow_after find v(memslow) at={event_end_us+0.2:g}u",
             "meas tran state_at_1005 find v(state) at=1.005u",
             "meas tran state_at_1001 find v(state) at=1.001u",
             "meas tran state_at_1010 find v(state) at=1.010u",
             "meas tran state_at_1020 find v(state) at=1.020u",
             "meas tran state_at_1040 find v(state) at=1.040u",
             "meas tran state_at_1100 find v(state) at=1.1u",
             "meas tran state_at_1500 find v(state) at=1.5u",
             "meas tran state_at_2000 find v(state) at=2.0u",
             "meas tran state_at_2600 find v(state) at=2.6u",
             "meas tran state_at_2270 find v(state) at=2.270u",
             "meas tran state_at_2280 find v(state) at=2.280u",
             "meas tran state_at_2300 find v(state) at=2.300u",
             "meas tran state_at_2400 find v(state) at=2.400u",
             "meas tran state_at_2490 find v(state) at=2.490u",
             "meas tran selector_before find v(range_out) at=0.9u",
             "meas tran pulse_at_1001 find v(pulse) at=1.001u",
             "meas tran fast_d_at_1001 find v(xgain.fast_d) at=1.001u",
             "meas tran slow_d_at_1001 find v(xgain.slow_d) at=1.001u",
             "meas tran selector_at_1005 find v(range_out) at=1.005u",
             "meas tran selector_at_1010 find v(range_out) at=1.010u",
             "meas tran selector_at_1020 find v(range_out) at=1.020u",
             "meas tran selector_at_1040 find v(range_out) at=1.040u",
             "meas tran selector_at_1100 find v(range_out) at=1.1u",
             "meas tran selector_at_1500 find v(range_out) at=1.5u",
             "meas tran selector_at_2000 find v(range_out) at=2.0u",
             "meas tran selector_at_2270 find v(range_out) at=2.270u",
             "meas tran selector_at_2280 find v(range_out) at=2.280u",
             "meas tran selector_at_2300 find v(range_out) at=2.300u",
             "meas tran selector_at_2400 find v(range_out) at=2.400u",
             ("meas tran threshold_cross when v(state)=0.75 fall=1" if negative else
              "meas tran threshold_cross when v(state)=1.05 rise=1"),
             "meas tran selector_cross when v(range_out)=0.9 rise=2",
             "meas tran state_at_selector find v(state) when v(range_out)=0.9 rise=2",
             "meas tran selector_at_1015 find v(range_out) at=1.015u",
             "meas tran selector_at_1030 find v(range_out) at=1.030u",
             *( [f"meas tran {branch}_charge_c integ i(v.xgain.v{branch}_probe) from=1u to={event_end_us:g}u"
                 for branch in ("fast", "slow")] if branch_probes else []),
             "quit", ".endc", ".end", ""]
    stem = f"sky130_piecewise_fixedcap_crossing_{corner}_temp{temperature:g}_trim{trim_uv:g}uv_gate{pulse_level:g}_width{pulse_width_us:g}us"
    if len(argv) > 5:
        stem += f"_init{(initial-threshold)*1e6:+g}uv"
    if branch_probes:
        stem += "_branchprobes"
    if negative:
        stem += "_negative"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume",
           f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           IMAGE, "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {key: float(value) for key, value in re.findall(
        r"(?im)^\s*(state_(?:before|after|at_\d+)|reference_(?:before|after)|fast_(?:before|after|charge_c)|slow_(?:before|after|charge_c)|pulse_at_\d+|fast_d_at_\d+|slow_d_at_\d+|threshold_cross|state_at_selector|selector_(?:before|cross|at_\d+))\s*=\s*([-+0-9.eE]+)", log)}
    required = {"state_before", "state_after", "reference_before", "reference_after",
                "fast_before", "fast_after", "slow_before", "slow_after",
                "threshold_cross", "selector_cross", "state_at_selector", "selector_before", "selector_at_1005",
                "pulse_at_1001", "fast_d_at_1001", "slow_d_at_1001", "state_at_1001",
                "selector_at_1010", "selector_at_1015", "selector_at_1020", "selector_at_1030",
                "selector_at_1040", "selector_at_1100", "selector_at_1500", "selector_at_2000",
                "selector_at_2270", "selector_at_2280", "selector_at_2300", "selector_at_2400",
                "state_at_1005", "state_at_1010", "state_at_1020", "state_at_1040",
                "state_at_1100", "state_at_1500", "state_at_2000", "state_at_2600",
                "state_at_2270", "state_at_2280", "state_at_2300", "state_at_2400", "state_at_2490"}
    if branch_probes:
        required.update(("fast_charge_c", "slow_charge_c"))
    complete = run.returncode == 0 and "ngspice-36 done" in log and required <= values.keys()
    report = {"test": "sky130_fixed_mim_two_range_live_event_gain_crossing",
              "simulation_completed": complete, "corner": corner.upper(), "temperature_c": temperature,
              "state_cap": "PDK MIM 20x20um per state node, fixed throughout event",
              "range_boundary_v": threshold, "initial_state_v": initial,
              "comparator_reference_v": comparator_reference,
              "analog_reference_trim_uv": trim_uv,
              "pulse_gate_level_v": pulse_level,
              "event": f"{pulse_width_us:g}us {'NFET sink' if negative else 'PFET source'} gate pulse at{pulse_level:g}V, selectable PDK device widths4.24/1.5um; one comparator changes selected current branch during event",
              "pulse_width_us": pulse_width_us,
              "event_sign": "negative" if negative else "positive",
              "branch_current_probes_enabled": branch_probes,
              "measurements": values,
              "scope": f"One {'negative transition across -150mV with NFET sinking' if negative else 'positive transition across +150mV with PFET sourcing'} from VCM, fixed MIM state and physical SKY130 injection/TGs/comparator. Gate pulse and boundary reference are ideal; no physical range DAC, PEX, PVT, mismatch/noise, multiple boundaries, weight map, full-float loop, hold, reset or readout."}
    if complete:
        report["event_change_v"] = values["state_after"] - values["state_before"]
        report["reference_drift_v"] = values["reference_after"] - values["reference_before"]
        report["dynamic_final_vs_no_event_v"] = values["state_after"] - values["reference_after"]
        report["static_fast_change_vs_reference_v"] = values["fast_after"] - values["reference_after"]
        report["static_slow_change_vs_reference_v"] = values["slow_after"] - values["reference_after"]
        report["net_event_change_vs_no_event_v"] = report["dynamic_final_vs_no_event_v"]
        controls = (report["static_fast_change_vs_reference_v"],
                    report["static_slow_change_vs_reference_v"])
        report["dynamic_within_static_control_bracket"] = (
            min(controls) <= report["dynamic_final_vs_no_event_v"] <= max(controls))
        report["selector_latency_after_state_cross_ns"] = (values["selector_cross"] - values["threshold_cross"])*1e9
        report["comparator_trip_state_offset_vs_target_uv"] = (
            values["state_at_selector"] - threshold) * 1e6
        report["comparator_trip_state_offset_vs_reference_uv"] = (
            values["state_at_selector"] - comparator_reference) * 1e6
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
