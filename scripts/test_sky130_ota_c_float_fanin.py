"""Replay one frozen original-float high-cancellation fan-in through OTA-C."""
from __future__ import annotations

import json
import random
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
RES = OUT / "results"
BENCH = OUT / "benches"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
IMAGE = "eventspikeseg:analog-ngspice36"
CHECKPOINT = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
V_PER_WEIGHT = 6.521267959225942e-5
C_NOM = 21.8e-12


def load_events(order: str) -> list[float]:
    ref = OUT / "model_reference"
    meta = json.loads((ref / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    src = RES / "sky130_ms_first_touch_float_fanin_ss0_high_cancellation_stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly_deck.json"
    source = json.loads(src.read_text(encoding="utf-8"))
    if meta["checkpoint_sha256"] != CHECKPOINT or source["qat_or_quantized_reference_used"]:
        raise RuntimeError("Expected frozen original full-float checkpoint without QAT")
    trace = np.load(ref / meta["trace_archive"])
    params = np.load(ref / "eventspikeseg140k_float_parameters.npz")
    inputs = trace["presynaptic_input__final_fuse__standard"]
    weights = params["weight__final_fuse__standard"]
    batch, channel = source["selected_flat_batch"], source["selected_output_channel"]
    y, x = source["selected_yx"]
    expanded: list[float] = []
    for ic in range(weights.shape[1]):
        for ky in range(weights.shape[2]):
            for kx in range(weights.shape[3]):
                iy, ix = y + ky - 1, x + kx - 1
                if 0 <= iy < inputs.shape[-2] and 0 <= ix < inputs.shape[-1]:
                    expanded.extend([float(weights[channel, ic, ky, kx])] * int(inputs[batch, ic, iy, ix]))
    if len(expanded) != source["event_count"] or abs(sum(expanded) - source["sum_folded_float_event_weights"]) > 1e-9:
        raise RuntimeError("Expanded float event sequence does not match its archived source")
    ascending = sorted(expanded, key=lambda value: (value > 0, abs(value)))
    if order == "forward":
        return ascending
    if order == "reverse":
        return list(reversed(ascending))
    if order == "shuffle":
        result = list(ascending)
        random.Random(140).shuffle(result)
        return result
    raise ValueError("order must be forward, reverse, or shuffle")


def main() -> int:
    import sys
    arg = lambda key, default: next((v.split("=", 1)[1] for v in sys.argv[1:] if v.startswith(key + "=")), str(default))
    corner = arg("--corner", "tt").lower()
    order = arg("--order", "shuffle")
    scale = float(arg("--analog-scale", "1000"))
    pulse_ns = float(arg("--pulse-ns", "10"))
    edge_ns = float(arg("--edge-ns", "200"))
    cc = arg("--cc", "50p")
    architecture = arg("--architecture", "differential")
    vbiasn = float(arg("--vbiasn", "0.65"))
    vbiasp = float(arg("--vbiasp", "0.75"))
    rdc = float(arg("--rdc-ohm", "1e12"))
    polarity = arg("--polarity", "both")
    warmup_ms = float(arg("--warmup-ms", "0.5"))
    initial_state_v = float(arg("--initial-state-v", "0.9"))
    event_gated = "--event-gated" in sys.argv[1:]
    use_uic = "--uic" in sys.argv[1:]
    positive_gain = float(arg("--positive-gain", "1"))
    negative_gain = float(arg("--negative-gain", "1"))
    temp = {"tt": 27, "ss": 0, "ff": 85}.get(corner)
    if temp is None or scale < 0 or pulse_ns <= 0 or edge_ns <= 0 or warmup_ms < 0 or not 0 <= initial_state_v <= 1.8 or positive_gain <= 0 or negative_gain <= 0 or architecture not in ("differential", "single-ended") or polarity not in ("both", "positive", "negative", "none"):
        raise ValueError("invalid corner or negative scale/nonpositive pulse/edge")
    events = load_events(order)
    spacing = 4e-3 / (len(events) - 1)
    cap = C_NOM
    source_weights = [weight if polarity == "both" or (polarity == "positive" and weight > 0)
                      or (polarity == "negative" and weight < 0) else 0.0 for weight in events]
    # The differential bench drives one equal/opposite current into each rail,
    # so each branch supplies half the differential charge. The single-ended
    # bench has only one storage capacitor and needs the full charge per branch.
    branch_divisor = 2.0 if architecture == "differential" else 1.0
    amps = [weight * V_PER_WEIGHT * cap / (branch_divisor * pulse_ns * 1e-9) * scale *
            (positive_gain if weight > 0 else negative_gain if weight < 0 else 1.0)
            for weight in source_weights]
    prefix_counts = (40, 80, 120, 160, 200, 240, 280, 320, len(events))
    warmup_s = warmup_ms * 1e-3
    prefix_times = {n: warmup_s + 500e-6 + (n - 1) * spacing + 2e-6 for n in prefix_counts}
    stop_s = warmup_s + 5e-3
    event_starts = [warmup_s + 500e-6 + i * spacing for i in range(len(events))]
    if event_gated and architecture != "single-ended":
        raise ValueError("event-gated OTA test currently supports single-ended architecture only")
    gate_pwl = gateb_pwl = vbiasn_pwl = vbiasp_pwl = ""
    if event_gated:
        rise_s, lead_s, tail_s = 100e-9, 1.1e-6, 1.0e-6
        gate_pts, gateb_pts = [(0.0, 0.0)], [(0.0, 1.8)]
        n_pts, p_pts = [(0.0, 0.0)], [(0.0, 1.8)]
        for start in event_starts:
            on, off = start - lead_s, start + pulse_ns * 1e-9 + tail_s
            gate_pts += [(on, 0.0), (on + rise_s, 1.8), (off, 1.8), (off + rise_s, 0.0)]
            gateb_pts += [(on, 1.8), (on + rise_s, 0.0), (off, 0.0), (off + rise_s, 1.8)]
            n_pts += [(on, 0.0), (on + rise_s, vbiasn), (off, vbiasn), (off + rise_s, 0.0)]
            p_pts += [(on, 1.8), (on + rise_s, vbiasp), (off, vbiasp), (off + rise_s, 1.8)]
        def pwl(points: list[tuple[float, float]]) -> str:
            return "PWL(" + " ".join(f"{t:.12g} {v:.12g}" for t, v in points) + ")"
        gate_pwl, gateb_pwl = pwl(gate_pts), pwl(gateb_pts)
        vbiasn_pwl, vbiasp_pwl = pwl(n_pts), pwl(p_pts)
    name = f"sky130_ota_c_float_fanin_{architecture}{'_gated' if event_gated else ''}{'_uic' if use_uic else ''}_{corner}_{order}_{polarity}_s{scale:g}_w{pulse_ns:g}n_e{edge_ns:g}n_u{warmup_ms:g}m_x{initial_state_v:g}_cc{cc}_bn{vbiasn:g}_bp{vbiasp:g}_gp{positive_gain:g}_gn{negative_gain:g}_r{rdc:g}"
    deck = BENCH / f"{name}.cir"
    lines = [
        f"* Original-float high-cancellation fan-in, OTA-C {corner.upper()}/{temp}C",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
        f".temp {temp}",
        f'.include "{MODEL}/models/parameters/invariant.spice"',
        f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
        f'.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
        f'.include "{MODEL}/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        '.include "/workspace/asic/analog/modules.spice"',
        '.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"',
        ".subckt membrane_mim state vcm params: w_um=100 l_um=100",
        "Xmim state vcm sky130_fd_pr__cap_mim_m3_2 w={w_um} l={l_um} mf=1",
        ".ends membrane_mim",
        f"Vdd vdd 0 1.8", "Vcm vcm 0 0.9", f"Vstate0 state0 0 {initial_state_v:g}",
        (f"Vbn_p vbnp 0 DC 0 {vbiasn_pwl}" if event_gated else f"Vbn_p vbnp 0 {vbiasn:g}"),
        (f"Vbp_p vbpp 0 DC 1.8 {vbiasp_pwl}" if event_gated else f"Vbp_p vbpp 0 {vbiasp:g}"),
        # Hold both storage terminals at VCM during power-up, then release
        # the physical TG with a smooth edge before the event sequence.
        f"Binit init 0 V={{0.9*(1-tanh((time-{warmup_s:.14g})/{edge_ns*1e-9:.14g}))}}",
        "Binitb initb 0 V={1.8-v(init)}",
        "Xinit_out_p out_p state0 init initb vdd 0 transmission_gate",
        "Xinit_sum_p sum_p vcm init initb vdd 0 transmission_gate",
        ("Xota_p sum_p vcm ota_out_p vbnp vbpp vdd 0 sky130_sc_ota cc=" + cc if event_gated else
         "Xota_p sum_p vcm out_p vbnp vbpp vdd 0 sky130_sc_ota cc=" + cc),
        "Xcfb_p out_p sum_p membrane_mim w_um=100 l_um=100 mf=1",
        f"Rdc_p out_p sum_p {rdc:g}",
    ]
    if event_gated:
        lines += [f"Vamp amp 0 DC 0 {gate_pwl}", f"Vampb ampb 0 DC 1.8 {gateb_pwl}",
                  "Xota_output_connect out_p ota_out_p amp ampb vdd 0 transmission_gate",
                  "Xota_output_init ota_out_p vcm init initb vdd 0 transmission_gate",
                  "Xsum_hold sum_p vcm ampb amp vdd 0 transmission_gate"]
    if architecture == "differential":
        lines += ["Xinit_out_n out_n state0 init initb vdd 0 transmission_gate",
                  "Xinit_sum_n sum_n vcm init initb vdd 0 transmission_gate",
                  f"Vbn_n vbnn 0 {vbiasn:g}", f"Vbp_n vbpn 0 {vbiasp:g}",
                  "Xota_n sum_n vcm out_n vbnn vbpn vdd 0 sky130_sc_ota cc=" + cc,
                  "Xcfb_n out_n sum_n membrane_mim w_um=100 l_um=100 mf=1",
                  f"Rdc_n out_n sum_n {rdc:g}"]
    for i, (amp, weight) in enumerate(zip(amps, events)):
        if amp == 0.0:
            continue
        start = event_starts[i]
        edge = edge_ns * 1e-9
        end = start + pulse_ns * 1e-9
        envelope = f"{amp:.14g}*0.5*(tanh((time-{start:.14g})/{edge:.14g})-tanh((time-{end:.14g})/{edge:.14g}))"
        lines.append(f"BEventP{i:04d} sum_p 0 I={{{envelope}}}")
        if architecture == "differential":
            lines.append(f"BEventN{i:04d} 0 sum_n I={{{envelope}}}")
    if use_uic:
        lines += [f".ic v(out_p)={initial_state_v:g} v(sum_p)=0.9"]
        if architecture == "differential":
            lines += [f".ic v(out_n)={initial_state_v:g} v(sum_n)=0.9"]
    lines += [".control", "set noaskquit", "set numdgt=15",
              f"tran 100n {stop_s:g} 0 100n{' uic' if use_uic else ''}"]
    if architecture == "differential":
        lines += ["let state=v(out_p)-v(out_n)", "let cm=(v(out_p)+v(out_n))/2"]
        lines.append(f"meas tran state_pre find state at={warmup_s + 499e-6:.12g}")
        for n, t in prefix_times.items():
            lines.append(f"meas tran state_{n} find state at={t:.12g}")
        lines.append(f"meas tran cm_5ms find cm at={stop_s:.12g}")
    else:
        lines.append("let state=v(out_p)")
        lines.append(f"meas tran state_pre find state at={warmup_s + 499e-6:.12g}")
        for n, t in prefix_times.items():
            lines.append(f"meas tran state_{n} find state at={t:.12g}")
        lines.append(f"meas tran cm_5ms find v(out_p) at={stop_s:.12g}")
    for label, elapsed in (("post_release_0p1ms", 0.6e-3), ("post_release_0p5ms", 1.0e-3),
                           ("post_release_1p5ms", 2.0e-3), ("post_release_3p5ms", 4.0e-3),
                           ("post_release_4p5ms", 5.0e-3)):
        lines.append(f"meas tran {label} find v(out_p) at={warmup_s + elapsed:.12g}")
    lines.append(f"meas tran sum_pre find v(sum_p) at={warmup_s + 499e-6:.12g}")
    for n, t in prefix_times.items():
        lines.append(f"meas tran sum_{n} find v(sum_p) at={t:.12g}")
    lines += ["quit", ".endc", ".end", ""]
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", IMAGE,
           "240", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=255)
    log = proc.stdout + proc.stderr
    (RES / f"{name}.log").write_text(log, encoding="utf-8")
    values = {int(n): float(value) for n, value in re.findall(r"(?im)^\s*state_(40|80|120|160|200|240|280|320|322)\s*=\s*([-+0-9.eE]+)", log)}
    cm_match = re.search(r"(?im)^\s*cm_5ms\s*=\s*([-+0-9.eE]+)", log)
    pre_match = re.search(r"(?im)^\s*state_pre\s*=\s*([-+0-9.eE]+)", log)
    sum_values = {int(n): float(value) for n, value in re.findall(r"(?im)^\s*sum_(40|80|120|160|200|240|280|320|322)\s*=\s*([-+0-9.eE]+)", log)}
    sum_pre_match = re.search(r"(?im)^\s*sum_pre\s*=\s*([-+0-9.eE]+)", log)
    output_track = {key: float(value) for key, value in re.findall(
        r"(?im)^\s*(post_release_0p1ms|post_release_0p5ms|post_release_1p5ms|post_release_3p5ms|post_release_4p5ms)\s*=\s*([-+0-9.eE]+)", log)}
    completed = proc.returncode == 0 and len(values) == len(prefix_counts) and len(sum_values) == len(prefix_counts) and cm_match is not None and pre_match is not None and sum_pre_match is not None and "Timestep too small" not in log
    prefixes = []
    running = 0.0
    for n, weight in enumerate(events, 1):
        running += source_weights[n - 1]
        if n in prefix_counts:
            measured_absolute = values.get(n)
            measured = None if measured_absolute is None or pre_match is None else measured_absolute - float(pre_match.group(1))
            target = running * V_PER_WEIGHT * scale
            prefixes.append({"event_count": n, "float_target_v": target, "measured_state_change_v": measured,
                             "summing_node_v": sum_values.get(n),
                             "error_v": None if measured is None else measured - target})
    report = {"test": "sky130_OTA_C_original_full_float_high_cancellation_sequence", "simulation_completed": completed,
              "state_architecture": architecture,
              "corner": corner.upper(), "temperature_c": temp, "event_order": order, "event_count": len(events),
              "checkpoint_sha256": CHECKPOINT, "qat_or_quantized_reference_used": False,
              "analog_state_scale": scale, "event_polarity_included": polarity,
              "positive_event_gain": positive_gain, "negative_event_gain": negative_gain,
              "initialization_clamp_release_ms": warmup_ms,
              "initial_state_v": initial_state_v,
              "event_gated_ota_enabled": event_gated,
              "transient_uic_enabled": use_uic,
              "pulse_width_ns": pulse_ns, "smooth_edge_tau_ns": edge_ns,
              "feedback_cap_f_each": cap, "dc_feedback_resistance_ohm": rdc,
              "vbiasn_v": vbiasn, "vbiasp_v": vbiasp,
              "ota_compensation_capacitance": cc, "ideal_target_v": sum(source_weights) * V_PER_WEIGHT * scale,
              "max_abs_event_current_a": max(map(abs, amps)), "prefixes": prefixes,
              "summing_node_pre_v": None if sum_pre_match is None else float(sum_pre_match.group(1)),
              "max_summing_node_excursion_from_vcm_v": max((abs(v - 0.9) for v in sum_values.values()), default=None),
              "startup_output_track_v": output_track,
              "output_or_common_mode_at_5ms_v": None if cm_match is None else float(cm_match.group(1)),
              "scope": "One selected final_fuse high-cancellation neuron from epoch58 original float32 checkpoint. Ideal behavioral current sources deliver signed original float event weights through the direct-current OTA-C summing nodes; physical weight DAC, comparator, reset/beta, noise/mismatch, extraction and actor service are not included.",
              "deck": deck.name, "log": f"{name}.log"}
    (RES / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if completed else 2


if __name__ == "__main__":
    raise SystemExit(main())
