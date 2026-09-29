"""Compare direct MOS pulse-current accumulation with packet-cap sharing.

The test holds one MIM membrane and applies isolated current pulses at the
full-float event multiplicity of a representative layer. It is a TT schematic
screen, not a complete neuron or an extracted implementation.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

COMMON = """.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
"""


def main() -> int:
    arg = lambda name, default: next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith(name + "=")), str(default))
    count = int(arg("--events", 100))
    cap_um = float(arg("--membrane-cap-um", 20))
    logical_width_us = float(arg("--logical-width-us", 0.02))
    period_us = float(arg("--period-us", 49.0))
    negative_width_scale = float(arg("--negative-width-scale", 1.0))
    injector_length_um = float(arg("--injector-length-um", 2.0))
    injector_width_scale = float(arg("--injector-width-scale", 1.0))
    stack_depth = int(arg("--stack-depth", 1))
    isolation_length_um = float(arg("--isolation-length-um", 10.0))
    isolation_stack_depth = int(arg("--isolation-stack-depth", 1))
    injector_mode = arg("--injector-mode", "rail_switch")
    source_deg_ohm = float(arg("--source-degeneration-ohm", 0.0))
    max_step_ns = float(arg("--max-step-ns", 10))
    timeout_s = int(arg("--timeout-s", 180))
    if count < 1 or cap_um <= 0 or logical_width_us <= 0 or period_us <= 0 or injector_length_um <= 0 or injector_width_scale < 0.42 or source_deg_ohm < 0 or stack_depth < 1 or isolation_length_um <= 0 or isolation_stack_depth < 1:
        raise ValueError("events, membrane cap, logical pulse width, and period must be positive")
    positive_physical_width = logical_width_us * 7.0
    negative_physical_width = logical_width_us * negative_width_scale
    if min(positive_physical_width, negative_physical_width) <= 2 * max_step_ns * 1e-3:
        raise ValueError("pulse widths must exceed two transient time steps")
    if injector_mode not in {"rail_switch", "biased_saturation"}:
        raise ValueError("injector mode must be rail_switch or biased_saturation")
    event_times = [100.0 + i * period_us for i in range(count)]
    if event_times[-1] + positive_physical_width + 0.01 >= 5000:
        raise ValueError("event train must finish before the 5ms read point")

    def gate_waveform(polarity: str, active_events: list[int]) -> str:
        if polarity == "p":
            off, on = (1.8, 1.0 if injector_mode == "rail_switch" else 1.2)
        else:
            off, on = (0.0, 0.525 if injector_mode == "rail_switch" else 0.6)
        width = positive_physical_width if polarity == "p" else negative_physical_width
        points = [(0.0, off)]
        for i in active_events:
            start = event_times[i]
            points += [(start - 0.01, off), (start, on), (start + width, on), (start + width + 0.01, off)]
        points.append((5005.0, off))
        return "PWL(" + " ".join(f"{t:g}u {v:g}" for t, v in points) + ")"

    lines = ["SKY130 direct pulse-current accumulation over many presynaptic events", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vpg_off pg_off 0 1.8", "Vng_off ng_off 0 0",
             f".subckt synapse_pulse_width_mos_test state p_gate n_gate vdd vss params: wp=1 wn=0.42 l={injector_length_um:g} width_scale={injector_width_scale:g}"]
    p_rail, n_rail = "vdd", "vss"
    if source_deg_ohm > 0:
        p_rail, n_rail = "vdd_deg", "vss_deg"
        lines += [f"Rpdeg vdd_deg vdd {source_deg_ohm:g}", f"Rndeg vss_deg vss {source_deg_ohm:g}"]
    for i in range(stack_depth):
        pdrain=f"state" if i==stack_depth-1 else f"pstack{i}"
        psource=p_rail if i==0 else f"pstack{i-1}"
        ndrain=f"state" if i==stack_depth-1 else f"nstack{i}"
        nsource=n_rail if i==0 else f"nstack{i-1}"
        lines += [f"Xp_width{i} {pdrain} p_gate {psource} vdd sky130_fd_pr__pfet_01v8 w={{wp*width_scale}} l={{l}}",
                  f"Xn_width{i} {ndrain} n_gate {nsource} vss sky130_fd_pr__nfet_01v8 w={{wn*width_scale}} l={{l}}"]
    lines += [".ends synapse_pulse_width_mos_test",
              f".subckt transmission_gate_long a b en enb vdd vss params: wn=1 wp=2 l={isolation_length_um:g}",
              "Xn a en b vss sky130_fd_pr__nfet_01v8 w={wn} l={l}",
              "Xp a enb b vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}",
              ".ends transmission_gate_long"]
    rows = []
    cases = {"ref": ([], []), "p_one": ([0], []), "n_one": ([], [0]),
             "p_train": (list(range(count)), []), "n_train": ([], list(range(count)))}
    mixed_p = list(range(0, count, 2)); mixed_n = list(range(1, count, 2))
    cases["mixed_train"] = (mixed_p, mixed_n)
    for case, (p_events, n_events) in cases.items():
        state = f"state_{case}"
        inj = f"injector_{case}"
        active_times = [(event_times[i], positive_physical_width) for i in p_events] + [(event_times[i], negative_physical_width) for i in n_events]
        iso_points = [(0.0, 0.0)]
        clamp_points = [(0.0, 1.8)]
        for start, width in sorted(active_times):
            clamp_points += [(start - 0.01, 1.8), (start - 0.005, 0.0),
                             (start + width + 0.02, 0.0), (start + width + 0.03, 1.8)]
            iso_points += [(start - 0.005, 0.0), (start, 1.8), (start + width + 0.015, 1.8), (start + width + 0.02, 0.0)]
        iso_points.append((5005.0, 0.0))
        clamp_points.append((5005.0, 1.8))
        iso_wave = "PWL(" + " ".join(f"{t:g}u {v:g}" for t, v in iso_points) + ")"
        isob_wave = "PWL(" + " ".join(f"{t:g}u {1.8-v:g}" for t, v in iso_points) + ")"
        clamp_wave = "PWL(" + " ".join(f"{t:g}u {v:g}" for t, v in clamp_points) + ")"
        clampb_wave = "PWL(" + " ".join(f"{t:g}u {1.8-v:g}" for t, v in clamp_points) + ")"
        iso_nodes = [inj] + [f"iso_mid_{case}_{i}" for i in range(isolation_stack_depth - 1)] + [state]
        iso_instances = [f"Xiso_{case}_{i} {iso_nodes[i]} {iso_nodes[i+1]} iso_{case} isob_{case} vdd 0 transmission_gate_long"
                        for i in range(isolation_stack_depth)]
        lines += [f"Xmem_{case} {state} vcm membrane_mim w_um={cap_um:g} l_um={cap_um:g}",
                  f".ic v({state})=0",
                  f"Viso_{case} iso_{case} 0 {iso_wave}", f"Visob_{case} isob_{case} 0 {isob_wave}",
                  f"Vclamp_{case} clamp_{case} 0 {clamp_wave}", f"Vclampb_{case} clampb_{case} 0 {clampb_wave}",
                  *iso_instances,
                  f"Xclamp_{case} {inj} vcm clamp_{case} clampb_{case} vdd 0 transmission_gate",
                  f"Vpg_{case} pg_{case} 0 {gate_waveform('p', p_events)}",
                  f"Vng_{case} ng_{case} 0 {gate_waveform('n', n_events)}",
                  f"Xw_{case} {inj} pg_{case} ng_{case} vdd 0 synapse_pulse_width_mos_test"]
    lines += [".control", "set numdgt=15", f"tran {max_step_ns:g}n 5.005m uic"]
    for phase, time in (("early", "1u"), ("mid", "1m"), ("final", "5m")):
        for case in cases:
            lines += [f"meas tran {phase}_{case} find v(state_{case}) at={time}"]
    lines += ["quit", ".endc", ".end"]
    tag = f"n{count}_w{logical_width_us:g}u_cm{cap_um:g}_period{period_us:g}u_nscale{negative_width_scale:g}_l{injector_length_um:g}_ws{injector_width_scale:g}_{injector_mode}_rs{source_deg_ohm:g}_stack{stack_depth}_iso{isolation_length_um:g}x{isolation_stack_depth}_s{max_step_ns:g}n"
    deck = BENCH / f"sky130_ms_pulse_width_many_events_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", str(timeout_s), "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 15)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_ms_pulse_width_many_events_{tag}.log").write_text(log, encoding="utf-8")
    measured = {f"{phase}_{case}": float(v) for phase,case,v in __import__("re").findall(r"(?im)^\s*(early|mid|final)_([a-z_]+)\s*=\s*([-+0-9.eE]+)", log)}
    completed = proc.returncode == 0 and len(measured) == 3 * len(cases)
    deltas = ({k: (measured[f"final_{k}"] - measured["final_ref"]) * 1e3 for k in cases if k != "ref"}
              if completed else {})
    p_linear = count * deltas.get("p_one", 0.0)
    n_linear = count * deltas.get("n_one", 0.0)
    report = {
        "test": "sky130_tt_pulse_width_many_event_charge_accumulation",
        "simulation_completed": completed,
        "return_code": proc.returncode,
        "measurement_count": len(measured),
        "event_count_per_train": count,
        "mixed_train_positive_event_count": len(mixed_p),
        "mixed_train_negative_event_count": len(mixed_n),
        "membrane_cap_square_width_um": cap_um,
        "logical_pulse_width_us": logical_width_us,
        "positive_physical_pulse_width_us": positive_physical_width,
        "negative_physical_pulse_width_us": negative_physical_width,
        "negative_width_scale": negative_width_scale,
        "injector_length_um": injector_length_um,
        "injector_width_scale": injector_width_scale,
        "injector_mode": injector_mode,
        "source_degeneration_ohm": source_deg_ohm,
        "injector_stack_depth": stack_depth,
        "injection_isolation_length_um": isolation_length_um,
        "injection_isolation_stack_depth": isolation_stack_depth,
        "membrane_injection_isolation_gate": True,
        "event_period_us": period_us,
        "no_pulse_reference_state_v_early_mid_final": [measured.get(f"{phase}_ref") for phase in ("early", "mid", "final")],
        "no_pulse_reference_hold_drift_mv": (measured.get("final_ref", 0.0) - measured.get("early_ref", 0.0)) * 1e3,
        "final_state_change_from_no_pulse_reference_mv": deltas,
        "same_sign_expected_linear_change_mv": {"positive": p_linear, "negative": n_linear},
        "same_sign_relative_error": ({
            "positive": abs(deltas.get("p_train", 0.0) - p_linear) / max(abs(p_linear), 1e-15),
            "negative": abs(deltas.get("n_train", 0.0) - n_linear) / max(abs(n_linear), 1e-15),
        } if completed else {}),
        "scope": "TT schematic, MOS current injector isolated from a SKY130 MIM state capacitor between pulse events by a long-channel transmission gate, with its internal node clamped to VCM while idle; gate drive selects rail_switch or nominal saturation bias, isolated pulses over a 5ms bin, no reset, leak, comparator, PVT, mismatch, noise, extraction, weight DAC, or network feedback.",
    }
    RES.mkdir(parents=True, exist_ok=True)
    output = RES / f"sky130_ms_pulse_width_many_events_{tag}.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if completed else 2


if __name__ == "__main__":
    raise SystemExit(main())

