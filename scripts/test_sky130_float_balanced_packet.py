"""Replay original float fan-in through a matched differential PEX packet cell."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from test_sky130_float_dual_reservoir import CHECKPOINT, OUT, RES, BENCH, IMAGE, load_weights

ROOT = Path(__file__).resolve().parents[1]


def arg(name: str, default: str) -> str:
    return next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith(name + "=")), default)


def wave(points: list[tuple[float, float]]) -> str:
    values: dict[float, float] = {}
    for t, v in points:
        values[t] = v
    return "PWL(" + " ".join(f"{t:.9f}u {v:.12g}" for t, v in sorted(values.items())) + ")"


def main() -> int:
    site, order = arg("--site", "high_cancellation"), arg("--order", "shuffle")
    corner = arg("--corner", "tt")
    temp = {"ss": 0, "tt": 27, "ff": 85}.get(corner)
    if temp is None:
        raise ValueError("corner must be ss/tt/ff")
    scale = float(arg("--state-scale", "1000"))
    event_gain = float(arg("--event-gain", "1"))
    polarity = int(arg("--polarity", "1"))
    if polarity not in (-1, 1) or event_gain <= 0:
        raise ValueError("polarity must be ±1 and event gain positive")
    events, source = load_weights(site, order)
    limit = int(arg("--event-limit", "0"))
    if limit:
        events = events[:limit]
    source_event_count = len(events)
    subdivisions = int(arg("--subdivisions", "1"))
    if subdivisions < 1:
        raise ValueError("subdivisions must be positive")
    if subdivisions > 1:
        events = [weight / subdivisions for weight in events for _ in range(subdivisions)]
    state_cap, packet_cap = 21.83739e-12, 9.30225e-15
    factor = 6.521267959225942e-5 * scale * state_cap / packet_cap
    slot_ns, start_us = float(arg("--slot-ns", "50.253")), 500.0
    event_us = [start_us + i * slot_ns / 1000 for i in range(len(events))]
    top_p, top_n = [(0.0, .9)], [(0.0, .9)]
    conn_windows, reset_windows = [], []
    for t, weight in zip(event_us, events):
        full = abs(weight) * factor
        if full * event_gain / 2 > .85:
            raise ValueError(f"differential packet step {full*event_gain/2:.4g}V per side exceeds 0.85V")
        signed_half = polarity * (1 if weight >= 0 else -1) * full * event_gain / 2
        # Precharge while isolated. Settle both top plates before connecting;
        # disconnect before returning them to VCM, then reset the packet node.
        top_p += [(t-.015, .9), (t-.010, .9+signed_half), (t+.010, .9+signed_half), (t+.015, .9)]
        top_n += [(t-.015, .9), (t-.010, .9-signed_half), (t+.010, .9-signed_half), (t+.015, .9)]
        conn_windows.append((t-.005, t+.005))
        reset_windows.append((t+.018, t+.030))
    stop_us = float(arg("--stop-us", "5000"))
    max_step_ns = float(arg("--tstep-ns", "100"))
    timeout_s = int(arg("--timeout-s", "600"))
    end = max(stop_us + .1, (event_us[-1] if event_us else start_us)+.1)
    top_p.append((end, .9)); top_n.append((end, .9))
    # Smooth behavioral switch controls avoid discontinuous ideal voltage
    # sources that previously made ngspice timestep-collapse at TG edges.
    edge = 1e-9
    conn_expr = "+".join(f"0.9*(tanh((time-{a*1e-6:.12g})/{edge:.12g})-tanh((time-{b*1e-6:.12g})/{edge:.12g}))" for a,b in conn_windows)
    reset_terms = [f"0.9*(tanh((time+3e-9)/{edge:.12g})-tanh((time-1e-7)/{edge:.12g}))"]
    reset_terms += [f"0.9*(tanh((time-{a*1e-6:.12g})/{edge:.12g})-tanh((time-{b*1e-6:.12g})/{edge:.12g}))" for a,b in reset_windows]
    reset_expr = "+".join(reset_terms)
    tag = f"{site}_{order}_{corner}_s{scale:g}_g{event_gain:g}_pol{polarity}_n{len(events)}_stop{stop_us:g}u".replace(".", "p")
    deck = BENCH / f"sky130_float_balanced_packet_{tag}.cir"
    lines = ["* Matched differential passive charge packet; original full-float weights",
        ".option scale=1u reltol=1e-4 abstol=1e-15 vntol=1e-8 method=gear maxord=2",
        f".temp {temp}",
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
        f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
        '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        '.include "/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"',
        '.include "/workspace/artifacts/analog_asic/layout/sky130_mim_packet_2x2/packet_cap_mim_2x2um.spice"',
        '.include "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"',
        '.subckt sky130_pex_tg a b en enb vdd vss',
        'Xtg a b en enb vdd vss sky130_transmission_gate_raw', '.ends sky130_pex_tg',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
        "Xstate_p state_p vcm mim_state_square_3x4_w30_l30", "Xstate_n state_n vcm mim_state_square_3x4_w30_l30",
        "Xpacket_p top_p packet_p packet_cap_mim_2x2um", "Xpacket_n top_n packet_n packet_cap_mim_2x2um",
        f"Vtop_p top_p 0 {wave(top_p)}", f"Vtop_n top_n 0 {wave(top_n)}",
        f"Bconn conn 0 V={{{conn_expr}}}", "Bconnb connb 0 V={1.8-V(conn)}",
        f"Breset reset 0 V={{{reset_expr}}}", "Bresetb resetb 0 V={1.8-V(reset)}",
        "Xconnect_p packet_p state_p conn connb vdd 0 sky130_pex_tg",
        "Xconnect_n packet_n state_n conn connb vdd 0 sky130_pex_tg",
        "Xreset_p packet_p vcm reset resetb vdd 0 sky130_pex_tg",
        "Xreset_n packet_n vcm reset resetb vdd 0 sky130_pex_tg",
        f"Vinit init 0 PWL(0 1.8 1.9u 1.8 2u 0 {stop_us+.1:g}u 0)",
        f"Vinitb initb 0 PWL(0 0 1.9u 0 2u 1.8 {stop_us+.1:g}u 1.8)",
        *[line for i in range(10) for line in (
            f"Xstate_reset_p{i} state_p vcm init initb vdd 0 sky130_pex_tg",
            f"Xstate_reset_n{i} state_n vcm init initb vdd 0 sky130_pex_tg")],
        "Bdiff diff 0 V=V(state_p)-V(state_n)",
        ".ic v(state_p)=0.9 v(state_n)=0.9 v(packet_p)=0.9 v(packet_n)=0.9",
        ".control", "set noaskquit", "set numdgt=15", f"tran {max_step_ns:g}n {stop_us:g}u uic",
        "meas tran state_p_early find v(state_p) at=1u", "meas tran state_n_early find v(state_n) at=1u",
        "meas tran state_p_pre find v(state_p) at=499u", "meas tran state_n_pre find v(state_n) at=499u",
        f"meas tran state_p_end find v(state_p) at={stop_us:g}u", f"meas tran state_n_end find v(state_n) at={stop_us:g}u",
        f"meas tran diff_end find v(diff) at={stop_us:g}u", f"meas tran diff_49 find v(diff) at={max(0,stop_us-100):g}u",
        "quit", ".endc", ".end", ""]
    deck.write_text("\n".join(lines), encoding="ascii")
    proc = subprocess.run(["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
        "-w", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", IMAGE, str(timeout_s), "ngspice", "-b", deck.name],
        cwd=ROOT, capture_output=True, text=True, timeout=timeout_s+15)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_float_balanced_packet_{tag}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k, v in re.findall(r"(?im)^\s*(state_p_early|state_n_early|state_p_pre|state_n_pre|state_p_end|state_n_end|diff_end|diff_49)\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and len(vals) == 8 and "ngspice-36 done" in log
    target = sum(events)*6.521267959225942e-5*scale
    report = {"test": "sky130_extracted_balanced_differential_passive_packet",
        "simulation_completed": complete, "corner": corner.upper(), "temperature_c": temp,
        "site": site, "event_order": order, "event_count": len(events), "checkpoint_sha256": CHECKPOINT,
        "source_event_count": source_event_count, "packet_subdivisions_per_source_event": subdivisions,
        "qat_or_quantized_reference_used": False, "state_scale": scale,
        "target_differential_change_v": target, "source_step_factor_v_per_weight": factor,
        "event_gain_trim": event_gain, "event_polarity": polarity,
        "max_transient_step_ns": max_step_ns,
        "extracted_state_cap_f": state_cap, "extracted_packet_cap_f": packet_cap,
        "measurements_v": vals, "update_error_v": vals.get("diff_end",0)-target if complete else None,
        "hold_change_100us_v": vals.get("diff_end",0)-vals.get("diff_49",0) if complete else None,
        "scope": "Two extracted MIM state banks, extracted MIM packet cells, and TG PEX. Each original full-float event drives symmetric opposite top-plate steps on both state rails; gate timing and float-to-voltage mapping are ideal. No physical weight DAC, noise/mismatch, threshold/reset/beta/readout, or population service."}
    (RES/f"sky130_float_balanced_packet_{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if not complete: print(log[-3000:],file=sys.stderr)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
