"""Screen charge conservation when a SKY130 differential MIM range is enlarged."""
from __future__ import annotations

import json
import re
import subprocess
import sys

from test_sky130_sc_physical_accumulation import BENCH, COMMON, RES, ROOT


def main() -> int:
    long_hold = "--long-hold" in sys.argv
    crossing = "--crossing-event" in sys.argv
    mode = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                 if arg.startswith("--extension-precharge=")), "matched")
    precharge_error_mv = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                     if arg.startswith("--precharge-error-mv=")), "0"))
    if mode not in ("matched", "vcm"):
        raise ValueError("extension-precharge must be matched or vcm")
    if crossing and mode != "matched":
        raise ValueError("the crossing-event diagnostic requires boundary-matched extension precharge")
    if abs(precharge_error_mv) > 2 or (mode != "matched" and precharge_error_mv):
        raise ValueError("bounded precharge error requires matched mode and +/-2mV")
    until = "5.2m" if long_hold else "2u"
    step = "50n" if long_hold else "0.5n"
    ext_p = 0.95625 + precharge_error_mv / 2000 if mode == "matched" else 0.9
    ext_n = 0.84375 - precharge_error_mv / 2000 if mode == "matched" else 0.9
    error_tag = (f"_err{precharge_error_mv:g}mv".replace("-", "m").replace(".", "p")
                 if precharge_error_mv else "")
    stem = (f"sky130_piecewise_range_switch_{mode}_"
            f"{'crossing_' if crossing else ''}{'5ms' if long_hold else 'short'}{error_tag}")
    fine_p, fine_n = (0.95, 0.85) if crossing else (0.95625, 0.84375)
    switch_lead = "1.2129u" if crossing else "1.0999u"
    switch_at = "1.213u" if crossing else "1.1u"
    before_switch_at = "1.2128u" if crossing else "1.099u"
    after_switch_at = "1.2132u" if crossing else "1.15u"
    lines = [f"SKY130 TT differential MIM piecewise range switch {stem}", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             f"Vinitp initp 0 {fine_p:g}", f"Vinitn initn 0 {fine_n:g}",
             f"Vextp extp_src 0 {ext_p:g}", f"Vextn extn_src 0 {ext_n:g}",
             f"Vinit init 0 PWL(0 1.8 0.9999u 1.8 1u 0 {until} 0)",
             f"Vinitb initb 0 PWL(0 0 0.9999u 0 1u 1.8 {until} 1.8)",
             f"Vconnect connect 0 PWL(0 0 {switch_lead} 0 {switch_at} 1.8 {until} 1.8)",
             f"Vconnectb connectb 0 PWL(0 1.8 {switch_lead} 1.8 {switch_at} 0 {until} 0)"]
    for branch in ("event", "reference"):
        for side, source in (("p", "initp"), ("n", "initn")):
            state = f"{branch}_{side}"
            extension = f"{branch}_{side}_ext"
            ext_source = f"ext{side}_src"
            lines += [
                f"Xinit_{state} {source} {state} init initb vdd 0 transmission_gate",
                f"Xpre_{extension} {ext_source} {extension} init initb vdd 0 transmission_gate",
                f"Xconnect_{state} {state} {extension} connect connectb vdd 0 transmission_gate",
                f"Xfine_{state} {state} vcm sky130_fd_pr__cap_mim_m3_2 w=10 l=10 mf=1",
                f"Xextension_{extension} {extension} vcm sky130_fd_pr__cap_mim_m3_2 w=13.3 l=13.3 mf=1",
            ]
        if branch == "event":
            pulse = (f"PWL(0 0 1.1999u 0 1.2u 100n 1.25u 100n "
                     f"1.2501u 0 {until} 0)")
            lines += [f"Ip_event 0 event_p {pulse}",
                      f"In_event event_n 0 {pulse}"]
    lines += [".control", f"tran {step} {until} uic",
              "let event_diff=v(event_p)-v(event_n)",
              "let reference_diff=v(reference_p)-v(reference_n)",
              f"meas tran before_switch_event find event_diff at={before_switch_at}",
              f"meas tran after_switch_event find event_diff at={after_switch_at}",
              f"meas tran after_switch_reference find reference_diff at={after_switch_at}",
              "meas tran before_pulse_event find event_diff at=1.199u",
              "meas tran before_pulse_reference find reference_diff at=1.199u",
              "meas tran after_pulse_event find event_diff at=1.35u",
              "meas tran after_pulse_reference find reference_diff at=1.35u"]
    if long_hold:
        lines += ["meas tran final_event find event_diff at=5.1m",
                  "meas tran final_reference find reference_diff at=5.1m"]
    lines += ["quit", ".endc", ".end"]
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "180", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=195)
    log = proc.stdout + proc.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    names = ("before_switch_event", "after_switch_event", "after_switch_reference",
             "before_pulse_event", "before_pulse_reference", "after_pulse_event",
             "after_pulse_reference") + (("final_event", "final_reference") if long_hold else ())
    measured = {}
    for name in names:
        match = re.search(rf"(?im)^\s*{name}\s*=\s*([-+0-9.eE]+)", log)
        if match:
            measured[name] = float(match.group(1))
    complete = (proc.returncode == 0 and len(measured) == len(names) and
                "ngspice-36 done" in log and "timestep too small" not in log.lower())
    cf = (2 * 10**2 + 0.76 * 10) * 1e-15
    ce = (2 * 13.3**2 + 0.76 * 13.3) * 1e-15
    report = {"test": "sky130_physical_differential_mim_range_switch",
              "simulation_completed": complete, "return_code": proc.returncode,
              "extension_precharge": mode, "long_hold": long_hold,
              "extension_differential_precharge_error_mv": precharge_error_mv,
              "fine_capacitance_model_estimate_f_each": cf,
              "extension_capacitance_model_estimate_f_each": ce,
              "ideal_unprecharged_charge_share_factor": cf / (cf + ce),
              "initial_differential_v": fine_p - fine_n,
              "crossing_event": crossing,
              "event_current_each_a": 100e-9, "event_plateau_s": 50e-9,
              "ideal_event_differential_step_v_from_capacitance": 2 * 100e-9 * 50e-9 / (cf + ce),
              "measurements_v": measured,
              "scope": "TT/27C physical PDK MIM/TG, two differential branches, ideal state/extension voltage sources for 1us initialization, ideal matched or VCM extension precharge, one signed 100nA/50ns current event. In crossing mode a manually timed range switch occurs 13ns into the ideal current pulse. Matched extension precharge and switch timing are ideal external operations, not circuit solutions. No state-dependent weighted MOS event, range detector, physical precharge buffer, mismatch, transient noise, extracted layout or full model."}
    if complete:
        before = measured["before_switch_event"]
        after = measured["after_switch_event"]
        pulse = ((measured["after_pulse_event"] - measured["after_pulse_reference"]) -
                 (measured["before_pulse_event"] - measured["before_pulse_reference"]))
        report.update({"state_change_across_switch_measurement_window_uv": (after - before) * 1e6,
                       "differential_after_switch_mv": after * 1e3,
                       "event_minus_reference_step_mv": pulse * 1e3})
        if crossing:
            report["ideal_piecewise_final_state_v_with_13ns_switch"] = (
                fine_p - fine_n + 2 * 100e-9 * 13e-9 / cf +
                2 * 100e-9 * 37e-9 / (cf + ce))
            report["physical_final_minus_piecewise_ideal_mv"] = (
                measured["after_pulse_event"] - report["ideal_piecewise_final_state_v_with_13ns_switch"]) * 1e3
        else:
            report["event_step_relative_error_vs_ideal"] = (
                pulse / report["ideal_event_differential_step_v_from_capacitance"] - 1)
        if long_hold:
            final_relative = measured["final_event"] - measured["final_reference"]
            post_relative = measured["after_pulse_event"] - measured["after_pulse_reference"]
            report["event_difference_hold_change_mv_over_5ms"] = (final_relative - post_relative) * 1e3
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
