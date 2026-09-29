"""Replay a full-float fan-in as signed passive switched-capacitor packets."""
from __future__ import annotations

import json
import random
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
REF = OUT / "model_reference"
RES = OUT / "results"
BENCH = OUT / "benches"

COMMON = '''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
'''


def arg(name: str, default: str) -> str:
    return next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith(name + "=")), default)


def pwl(points: list[tuple[float, float]], stop_us: float, off: float) -> str:
    points = [(0.0, off), *points, (stop_us, off)]
    return "PWL(" + " ".join(f"{t:.12g}u {v:.12g}" for t, v in points) + ")"


def build_events(order: list[tuple[float, float]], start_us: float, period_us: float,
                 ratio: float, vcm: float, stop_us: float, compensate_state: bool) -> tuple[str, str, str, str]:
    conn: list[tuple[float, float]] = []
    reset: list[tuple[float, float]] = []
    top: list[tuple[float, float]] = []
    ideal_state_offset = 0.0
    for i, (target_v, _weight) in enumerate(order):
        t = start_us + i * period_us
        # Reset the packet node, connect it to the membrane, step the top plate,
        # disconnect, then return the top plate to VCM.
        conn += [(t - 0.901, 0), (t - 0.900, 1.8), (t + 1.899, 1.8), (t + 1.900, 0)]
        reset += [(t - 1.501, 0), (t - 1.500, 1.8), (t - 1.101, 1.8), (t - 1.100, 0),
                  (t + 2.099, 0), (t + 2.100, 1.8), (t + 2.599, 1.8), (t + 2.600, 0)]
        top_step = target_v / ratio + (ideal_state_offset if compensate_state else 0.0)
        top_level = vcm + top_step
        if not 0.05 < top_level < 1.75:
            raise ValueError(f"packet top-plate voltage {top_level:g} V is outside safe test range")
        top += [(t - 0.001, vcm), (t, top_level), (t + 1.999, top_level), (t + 2.000, vcm)]
        ideal_state_offset += target_v
    return (pwl(conn, stop_us, 0), pwl([(t, 1.8 - v) for t, v in conn], stop_us, 1.8),
            pwl(reset, stop_us, 0), pwl(top, stop_us, vcm))


def main() -> int:
    cap = float(arg("--membrane-um", "10"))
    packet = float(arg("--packet-um", "1"))
    ratio = float(arg("--transfer-ratio", "0.0127"))
    headroom = float(arg("--headroom-v", "0.15"))
    rank = int(arg("--site-rank", "0"))
    period = float(arg("--event-period-us", "13.2"))
    tstep = float(arg("--tstep-ns", "2"))
    stop_ms = float(arg("--stop-ms", "5.1"))
    reset_to = arg("--packet-reset", "state")
    if reset_to not in {"state", "vcm"}:
        raise ValueError("--packet-reset must be state or vcm")
    compensate_state = "--state-offset-compensation" in sys.argv
    trace_meta = json.loads((REF / "float_patch_trace_all.json").read_text())
    trace = np.load(REF / trace_meta["trace_archive"])
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    reference = json.loads((REF / "eventspikeseg140k_float_reference.json").read_text())
    conv2d = __import__("runpy").run_path(str(ROOT / "scripts/analyze_sky130_passive_float_mapping.py"))["conv2d"]
    x = trace["presynaptic_input__final_fuse__standard"].astype(np.float32)
    w = params["weight__final_fuse__standard"].astype(np.float32)
    candidate = trace["candidate__final_fuse__standard"]
    current = trace["current__final_fuse__standard"]
    geom = next(z for z in reference["effective_folded_weight_and_neuron_parameters"] if z["name"] == "final_fuse.standard")
    active = conv2d(x, np.ones_like(w), candidate.shape[-2:], groups=geom["conv_groups"],
                    dilation=tuple(geom["conv_dilation"]), padding=tuple(geom["conv_padding"]))
    site = np.argsort(-active.reshape(-1), kind="stable")[rank]
    ni, oi, yy, xx = np.unravel_index(int(site), active.shape)
    pad_y, pad_x = geom["conv_padding"]
    dy, dx = geom["conv_dilation"]
    scale = headroom / float(np.max(np.abs(candidate)))
    contributions: list[tuple[float, float]] = []
    for ic in range(w.shape[1]):
        for ky in range(w.shape[2]):
            for kx in range(w.shape[3]):
                iy = yy * max(1, round(x.shape[-2] / candidate.shape[-2])) + ky * dy - pad_y
                ix = xx * max(1, round(x.shape[-1] / candidate.shape[-1])) + kx * dx - pad_x
                if 0 <= iy < x.shape[-2] and 0 <= ix < x.shape[-1]:
                    weight = float(w[oi, ic, ky, kx])
                    contributions.extend((weight * scale, weight) for _ in range(int(x[ni, ic, iy, ix])) if weight)
    forward = sorted(contributions, key=lambda z: (z[0] < 0, abs(z[0])))
    reverse = list(reversed(forward))
    random_order = list(forward)
    random.Random(140).shuffle(random_order)
    orders = {"f": forward, "r": reverse, "q": random_order}
    first_us = 50.0
    last_us = first_us + period * (len(forward) - 1)
    stop_us = stop_ms * 1000
    if last_us + 3.0 >= stop_us:
        raise ValueError("event sequence does not finish before the selected stop time")

    lines = ["SKY130 full-float weighted event sequence using passive SC charge packets", COMMON,
             ".subckt passive_membrane state init_level ptop conn conn_b init init_b rst rst_b rst_level vcm vdd params: cmem=10 cpacket=1",
             "Xmem state vcm membrane_mim w_um={cmem} l_um={cmem}",
             "Xpacket ptop pbot membrane_mim w_um={cpacket} l_um={cpacket}",
             "Xpacket_switch pbot state conn conn_b vdd 0 transmission_gate",
             "Xpacket_reset pbot rst_level rst rst_b vdd 0 transmission_gate",
             "Xstate_init state init_level init init_b vdd 0 transmission_gate",
             "Rleak state vcm 1e15", ".ends passive_membrane", "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    suffix = {"f": "forward", "r": "reverse", "q": "random"}
    for name in ["f", "r", "q", "z"]:
        # The matched zero-weight control still exercises the same packet-switch
        # sequence so TG charge injection and clock feedthrough are subtracted.
        events = orders.get(name, [(0.0, 0.0)] * len(forward))
        conn, connb, reset, top = build_events(events, first_us, period, ratio, 0.9, stop_us, compensate_state) if events else (pwl([], stop_us, 0), pwl([], stop_us, 1.8), pwl([], stop_us, 0), pwl([], stop_us, 0.9))
        reset_level = f"state_{name}" if reset_to == "state" else "vcm"
        lines += [f"Vinit_{name} init_{name} 0 PWL(0 1.8 2.499u 1.8 2.5u 0 {stop_us:g}u 0)",
                  f"Vinitb_{name} initb_{name} 0 PWL(0 0 2.499u 0 2.5u 1.8 {stop_us:g}u 1.8)",
                  f"Vinitlvl_{name} initlvl_{name} 0 0.9", f"Vconn_{name} conn_{name} 0 {conn}",
                  f"Vconnb_{name} conn_b_{name} 0 {connb}", f"Vrst_{name} rst_{name} 0 {reset}",
                  f"Vrstb_{name} rst_b_{name} 0 {pwl([(float(t[:-1]), 1.8-v) for t,v in []], stop_us, 1.8) if False else '0'}"]
        # Construct the exact complementary reset signal from its PWL points.
        if events:
            reset_pts = []
            for i in range(len(events)):
                t = first_us + i * period
                reset_pts += [(t-1.501,0),(t-1.500,1.8),(t-1.101,1.8),(t-1.100,0),(t+2.099,0),(t+2.100,1.8),(t+2.599,1.8),(t+2.600,0)]
            resetb = pwl([(t, 1.8-v) for t,v in reset_pts], stop_us, 1.8)
        else:
            resetb = pwl([], stop_us, 1.8)
        lines[-1] = f"Vrstb_{name} rst_b_{name} 0 {resetb}"
        lines += [f"Vpacket_{name} ptop_{name} 0 {top}",
                  f"Xcell_{name} state_{name} initlvl_{name} ptop_{name} conn_{name} conn_b_{name} init_{name} initb_{name} rst_{name} rst_b_{name} {reset_level} vcm vdd passive_membrane cmem={cap:g} cpacket={packet:g}"]
    end_of_train_us = last_us + 3.0
    lines += [".control", "set numdgt=15", f"tran {tstep:g}n {stop_ms:g}m uic"]
    for name in ["f", "r", "q", "z"]:
        lines += [f"let d_{name}=v(state_{name})-v(state_z)", f"meas tran m_{name} find v(state_{name}) at=5m",
                  f"meas tran m_{name}_end find v(state_{name}) at={end_of_train_us:.12g}u"]
    lines += ["meas tran m_z find v(state_z) at=5m",
              f"meas tran m_z_end find v(state_z) at={end_of_train_us:.12g}u", "quit", ".endc", ".end"]
    tag = f"n{len(forward)}_rank{rank}_idx{ni}_o{oi}_y{yy}_x{xx}_m{cap:g}_c{packet:g}_ratio{ratio:g}_H{headroom:g}_p{period:g}u_reset{reset_to}_statecomp{int(compensate_state)}_t{tstep:g}n"
    deck = BENCH / f"sky130_passive_sc_weighted_sequence_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "240", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=255)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_passive_sc_weighted_sequence_{tag}.log").write_text(log)
    vals = {k: float(v) for k, v in re.findall(r"(?im)^\s*m_([frqz](?:_end)?)\s*=\s*([-+0-9.eE]+)", log)}
    target = float(np.sum([v for v, _ in forward]))
    done = proc.returncode == 0 and len(vals) == 8
    top_steps = []
    cumulative = 0.0
    for value, _ in forward:
        top_steps.append(value / ratio + (cumulative if compensate_state else 0.0))
        cumulative += value
    result = {"simulation_completed": done, "return_code": proc.returncode, "site_rank_by_active_fanin": rank,
              "selected_time_index": int(ni), "selected_output_channel": int(oi), "selected_yx": [int(yy), int(xx)],
              "fan_in_events": len(forward), "membrane_cap_side_um": cap, "packet_cap_side_um": packet,
              "measured_single_packet_transfer_ratio": ratio, "packet_bottom_reset_reference": reset_to,
              "ideal_float_state_offset_compensation": compensate_state, "candidate_headroom_v": headroom,
              "event_spacing_us": period, "event_train_end_us": last_us, "ideal_target_event_sum_v": target,
              "topplate_step_peak_v": max(map(abs, top_steps)),
              "matched_zero_weight_control_sequence": True,
              "scope": "One final_fuse full-float fan-in, ideal packet top-plate levels and physical SKY130 TG/MIM packet cell, matched zero-weight switching reference, nominal TT; main packet bottom disconnects 100ns before top-plate return and is reset per packet to the selected reference; no DAC, noise, mismatch, PVT, extraction, threshold/readout/reset or network feedback."}
    if done:
        result["event_induced_state_change_v"] = {name: vals[name] - vals["z"] for name in ("f", "r", "q")}
        result["relative_error"] = {name: (vals[name] - vals["z"] - target) / max(abs(target), 1e-15) for name in ("f", "r", "q")}
        result["event_induced_state_change_at_train_end_v"] = {name: vals[name + "_end"] - vals["z_end"] for name in ("f", "r", "q")}
        result["relative_error_at_train_end"] = {name: (vals[name + "_end"] - vals["z_end"] - target) / max(abs(target), 1e-15) for name in ("f", "r", "q")}
        result["order_difference_v"] = vals["f"] - vals["r"]
        result["matched_no_event_final_state_v"] = vals["z"]
    out = RES / f"sky130_passive_sc_weighted_sequence_{tag}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if done else 2


if __name__ == "__main__":
    raise SystemExit(main())
