"""Test separate same-sign passive charge reservoirs on original float fan-in."""
from __future__ import annotations

import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
RES = OUT / "results"
BENCH = OUT / "benches"
IMAGE = "eventspikeseg:analog-ngspice36"
CHECKPOINT = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def arg(name: str, default: str) -> str:
    return next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith(name + "=")), default)


def load_weights(site: str, order: str) -> tuple[list[float], dict]:
    import numpy as np

    stems = {
        "high_cancellation": "sky130_ms_first_touch_float_fanin_ss0_high_cancellation_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly",
        "near_threshold_scale": "sky130_ms_first_touch_float_fanin_ss0_near_threshold_scale_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly",
        "max_fanin": "sky130_ms_first_touch_float_fanin_ss0_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n",
    }
    if site not in stems or order not in ("shuffle", "forward", "reverse"):
        raise ValueError("invalid site/order")
    meta = json.loads((OUT / "model_reference/float_patch_trace_all.json").read_text())
    source = json.loads((RES / f"{stems[site]}_deck.json").read_text())
    if meta["checkpoint_sha256"] != CHECKPOINT or meta["qat_or_quantized_reference_used"] or source["qat_or_quantized_reference_used"]:
        raise ValueError("source is not the authorized full-float checkpoint")
    archive = np.load(OUT / "model_reference" / meta["trace_archive"])
    params = np.load(OUT / "model_reference/eventspikeseg140k_float_parameters.npz")
    inputs = archive["presynaptic_input__final_fuse__standard"]
    weights = params["weight__final_fuse__standard"]
    batch, output, (y, x) = source["selected_flat_batch"], source["selected_output_channel"], source["selected_yx"]
    events: list[float] = []
    for ic in range(weights.shape[1]):
        for ky in range(weights.shape[2]):
            for kx in range(weights.shape[3]):
                iy, ix = y + ky - 1, x + kx - 1
                if 0 <= iy < inputs.shape[-2] and 0 <= ix < inputs.shape[-1]:
                    events.extend([float(weights[output, ic, ky, kx])] * int(inputs[batch, ic, iy, ix]))
    if len(events) != source["event_count"] or abs(sum(events) - source["sum_folded_float_event_weights"]) > 1e-4:
        raise ValueError("expanded event sequence differs from the frozen float trace")
    if order == "forward":
        events.sort(key=lambda v: (v < 0, abs(v)))
    elif order == "reverse":
        events.sort(key=lambda v: (v < 0, abs(v)), reverse=True)
    else:
        random.Random(140).shuffle(events)
    return events, source


def main() -> int:
    site, order = arg("--site", "high_cancellation"), arg("--order", "shuffle")
    corner = arg("--corner", "tt")
    temp = {"ss": 0, "tt": 27, "ff": 85}.get(corner)
    if temp is None:
        raise ValueError("corner must be ss/tt/ff")
    scale = float(arg("--state-scale", "1000"))
    events, source = load_weights(site, order)
    # Physical extracted cells: 12-unit 30um MIM state bank, 2um packet MIM, TG PEX.
    c_state = 21.83739e-12
    c_packet = 9.30225e-15
    slot_ns = float(arg("--slot-ns", "50.253"))
    start_us = 500.0
    event_us = [start_us + i * slot_ns / 1000.0 for i in range(len(events))]
    pulse_scale = 6.521267959225942e-5 * scale * c_state / c_packet
    paces = {"p": [], "n": []}
    all_events = []
    for t, w in zip(event_us, events):
        side = "p" if w >= 0 else "n"
        amp = abs(w) * pulse_scale
        if amp > 0.85:
            raise ValueError(f"required packet step {amp:.4g}V exceeds the bounded 0.85V span")
        paces[side].append((t, amp))
        all_events.append((t, side, amp))

    def wave_for(side: str) -> tuple[str, str, str, str]:
        tops = [(0.0, 0.9)]
        conn = [(0.0, 0.0)]
        # Reset is inactive low; its complement is high. Assert it only after
        # the packet disconnects from the state node.
        reset = [(0.0, 0.0)]
        for t, event_side, event_amp in all_events:
            # Toggle both reservoirs on every logical event. The unselected
            # reservoir sees a zero packet step, balancing TG clock injection.
            amp = event_amp if event_side == side else 0.0
            # Start from an initialized packet, settle the top plate, transfer
            # charge, disconnect, return the top plate, then reset the packet.
            tops += [(t - 0.006, 0.9), (t, 0.9 + amp), (t + 0.010, 0.9 + amp), (t + 0.011, 0.9)]
            conn += [(t - 0.001, 0.0), (t, 1.8), (t + 0.008, 1.8), (t + 0.009, 0.0)]
            reset += [(t + 0.012, 1.8), (t + 0.013, 0.0), (t + 0.018, 0.0), (t + 0.019, 1.8)]
        end = max(5000.1, (event_us[-1] if event_us else start_us) + 0.1)
        tops.append((end, 0.9)); conn.append((end, 0.0)); reset.append((end, 1.8))
        def pwl(points):
            # Remove coincident points while keeping the last commanded value.
            dedup = {}
            for tm, val in points: dedup[tm] = val
            return "PWL(" + " ".join(f"{tm:.9f}u {val:.12g}" for tm, val in sorted(dedup.items())) + ")"
        c = pwl(conn)
        return pwl(tops), c, pwl([(t, 1.8-v) for t, v in sorted({tm: val for tm, val in conn}.items())]), pwl(reset)

    BENCH.mkdir(parents=True, exist_ok=True); RES.mkdir(parents=True, exist_ok=True)
    tag = f"{site}_{order}_{corner}_s{scale:g}_n{len(events)}"
    deck = BENCH / f"sky130_float_dual_reservoir_{tag}.cir"
    cells = []
    for side in ("p", "n"):
        top, connect, connect_b, reset = wave_for(side)
        reset_b = "PWL(" + " ".join(
            f"{float(tm[:-1]):.9f}u {1.8-float(v):.12g}" for tm, v in re.findall(r"([0-9.]+u) ([0-9.eE+-]+)", reset)
        ) + ")"
        cells += [f"Vtop_{side} top_{side} 0 {top}", f"Vconn_{side} conn_{side} 0 {connect}",
                  f"Vconnb_{side} connb_{side} 0 {connect_b}", f"Vreset_{side} reset_{side} 0 {reset}",
                  f"Vresetb_{side} resetb_{side} 0 {reset_b}",
                  f"Xstate_{side} state_{side} vcm mim_state_square_3x4_w30_l30",
                  f"Xpacket_{side} top_{side} packet_{side} packet_cap_mim_2x2um",
                  f"Xconnect_{side} packet_{side} state_{side} conn_{side} connb_{side} vdd 0 sky130_pex_tg",
                  f"Xreset_{side} packet_{side} vcm reset_{side} resetb_{side} vdd 0 sky130_pex_tg"]
    header = ["* Dual same-sign passive reservoir: original float event fan-in",
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
              '.subckt sky130_pex_tg a b en enb vdd vss', 'Xtg a b en enb vdd vss sky130_transmission_gate_raw', '.ends sky130_pex_tg',
              '.subckt transmission_gate a b en enb vdd vss', 'Xtg a b en enb vdd vss sky130_transmission_gate_raw', '.ends transmission_gate',
              "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", *cells,
              "Bdiff diff 0 V=V(state_p)-V(state_n)", ".ic v(state_p)=0.9 v(state_n)=0.9"]
    deck.write_text("\n".join(header + [".ic v(packet_p)=0.9 v(packet_n)=0.9", ".control", "set noaskquit", "set numdgt=15", "tran 20n 5m uic",
        "meas tran pos_end find v(state_p) at=5m", "meas tran neg_end find v(state_n) at=5m",
        "meas tran diff_end find v(diff) at=5m", "meas tran diff_late find v(diff) at=4.9m",
        "quit", ".endc", ".end", ""]), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
           "-w", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", IMAGE, "240", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=260)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_float_dual_reservoir_{tag}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k, v in re.findall(r"(?im)^\s*(pos_end|neg_end|diff_end|diff_late)\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and len(vals) == 4 and "ngspice-36 done" in log
    target = sum(events) * 6.521267959225942e-5 * scale
    report = {"test": "sky130_extracted_dual_same_sign_passive_charge_reservoir",
              "simulation_completed": complete, "corner": corner.upper(), "temperature_c": temp,
              "site": site, "order": order, "event_count": len(events),
              "positive_events": len(paces["p"]), "negative_events": len(paces["n"]),
              "checkpoint_sha256": CHECKPOINT, "qat_or_quantized_reference_used": False,
              "state_scale": scale, "target_differential_change_v": target,
              "source_step_factor_v_per_weight": pulse_scale,
              "extracted_state_cap_nominal_f": c_state, "extracted_packet_cap_nominal_f": c_packet,
              "measurements_v": vals, "event_update_error_v": vals.get("diff_end", 0.0)-target if complete else None,
              "hold_change_100us_v": vals.get("diff_end", 0.0)-vals.get("diff_late", 0.0) if complete else None,
              "scope": "Two extracted MIM state banks and physical TG/MIM packet cells; positive and negative original epoch58 float events accumulate on separate passive reservoirs. Event amplitudes are ideal float-proportional top-plate voltages. No physical weight DAC, sampled readout, mismatch/noise, threshold/reset/beta, or population service is modeled."}
    (RES / f"sky130_float_dual_reservoir_{tag}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not complete: print(log[-3000:], file=sys.stderr)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
