"""Replay the verified epoch58 full-float high-cancellation fan-in through paired SC state caps."""
from __future__ import annotations

import json
import random
import re
import subprocess
import sys
import runpy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RES = ROOT / "artifacts/analog_asic/results"
OUT = RES / "sky130_float_differential_cap_packet"
IMAGE = "eventspikeseg:analog-ngspice36"
CORNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--corner=")), "tt").lower()
ORDER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--order=")), "shuffle")
SITE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--site=")), "high_cancellation")
DT_NS = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--max-step-ns=")), "25"))
LIMIT = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--limit-events=")), "0"))
ZERO_INPUTS = "--zero-inputs" in sys.argv
STATE_RESET_TGS = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--state-reset-tgs=")), "10"))
STATE_RESET_STACK = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--state-reset-stack=")), "1"))
EVENT_SPAN_US = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--event-span-us=")), "4890"))
STATE_BANK_COPIES = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--state-bank-copies=")), "1"))
PACKET_BANK_COPIES = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--packet-bank-copies=")), "1"))
PULSE_US = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--event-pulse-us=")), "1.7"))
CAL_PHASE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--calibration-phase=")), "mid").lower()
TEMPS = {"tt": 27, "ss": 0, "ff": 85}
VPU = 6.521267959225942e-5
STATE_GAIN = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--state-gain=")), "1"))
CAL_STEP_V = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--calibration-step-v=")), "0.3"))
INJECTOR_GAIN = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--injector-gain=")), "1"))
TGPEX = "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
STATECAP = "/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"
PACKETCAP = "/workspace/artifacts/analog_asic/layout/sky130_mim_packet_2x2/packet_cap_mim_2x2um.spice"
STATEPAIRPEX = "/workspace/artifacts/analog_asic/layout/sky130_differential_mim_state_pair/sky130_differential_mim_state_pair_pex.spice"
PAIR_MACRO = "--state-pair-pex" in sys.argv


def event_weights() -> tuple[list[float], dict]:
    trace_meta = json.loads((REF / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    expected = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
    if trace_meta.get("checkpoint_sha256") != expected or trace_meta.get("qat_or_quantized_reference_used"):
        raise RuntimeError("full-float trace identity/quantization provenance mismatch")
    arrays = np.load(REF / trace_meta["trace_archive"])
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    meta = json.loads((REF / "eventspikeseg140k_float_reference.json").read_text(encoding="utf-8"))
    geom = next(x for x in meta["effective_folded_weight_and_neuron_parameters"]
                if x["name"] == "final_fuse.standard")
    weight = params["weight__final_fuse__standard"].astype(np.float32)
    inputs = arrays["presynaptic_input__final_fuse__standard"].astype(np.float32)
    # The trace archive stores 10 frames x 3 temporal bins for the neuron
    # outputs, while presynaptic inputs are flattened across those 30 bins.
    candidate = arrays["candidate__final_fuse__standard"].reshape(-1, *arrays["candidate__final_fuse__standard"].shape[-3:])
    current = arrays["current__final_fuse__standard"].reshape(-1, *arrays["current__final_fuse__standard"].shape[-3:])
    conv2d = runpy.run_path(str(ROOT / "scripts/analyze_sky130_passive_float_mapping.py"))["conv2d"]
    fanin = conv2d(inputs, np.ones_like(weight), candidate.shape[-2:],
                   groups=geom["conv_groups"], dilation=tuple(geom["conv_dilation"]),
                   padding=tuple(geom["conv_padding"]))
    eligible = fanin >= np.percentile(fanin[fanin > 0], 99)
    if SITE == "high_cancellation":
        rank_score = np.abs(current.reshape(fanin.shape))
    elif SITE == "near_threshold":
        threshold = np.repeat(arrays["threshold__final_fuse__standard"][:, 0, :, 0, 0], 3, axis=0)[:, :, None, None]
        rank_score = np.abs(candidate.reshape(fanin.shape) - threshold)
    else:
        raise ValueError("site must be high_cancellation or near_threshold")
    rank = np.where(eligible, rank_score, np.inf)
    selection = int(np.argmin(rank))
    ni, oi, yy, xx = np.unravel_index(selection, fanin.shape)
    pad_y, pad_x = geom["conv_padding"]
    dy, dx = geom["conv_dilation"]
    sy = max(1, round(inputs.shape[-2] / candidate.shape[-2]))
    sx = max(1, round(inputs.shape[-1] / candidate.shape[-1]))
    counts: list[float] = []
    for ic in range(weight.shape[1]):
        for ky in range(weight.shape[2]):
            for kx in range(weight.shape[3]):
                iy, ix = yy * sy + ky * dy - pad_y, xx * sx + kx * dx - pad_x
                if 0 <= iy < inputs.shape[-2] and 0 <= ix < inputs.shape[-1]:
                    counts.extend([float(weight[oi, ic, ky, kx])] * int(inputs[ni, ic, iy, ix]))
    if len(counts) != int(fanin[ni, oi, yy, xx]) or (SITE == "high_cancellation" and len(counts) != 322):
        raise RuntimeError(f"selected trace fan-in mismatch: {len(counts)}")
    if ORDER == "forward": ordered = sorted(counts, key=lambda x: (x > 0, abs(x)))
    elif ORDER == "reverse": ordered = list(reversed(sorted(counts, key=lambda x: (x > 0, abs(x)))) )
    elif ORDER == "shuffle":
        ordered = sorted(counts, key=lambda x: (x > 0, abs(x)))
        random.Random(140).shuffle(ordered)
    else: raise ValueError("order must be forward/reverse/shuffle")
    info = {"checkpoint_sha256": expected, "trace_index": [int(ni), int(oi), int(yy), int(xx)],
            "site": SITE, "events": len(ordered),
            "event_weight_sum": float(sum(ordered)),
            "float_candidate": float(candidate[ni, oi, yy, xx]),
            "float_current": float(current[ni, oi, yy, xx]),
            "float_threshold": float(arrays["threshold__final_fuse__standard"][ni // 3, 0, oi, 0, 0])
            if "threshold__final_fuse__standard" in arrays else None}
    return ordered, info


def make_pwl(weights: list[float], rail: int, slope: float, times: list[float]) -> str:
    pairs = [(0.0, 0.9)]
    for w, t in zip(weights, times):
        level = 0.9 + rail * (w * VPU * STATE_GAIN * INJECTOR_GAIN / slope)
        pairs.extend([(t - 0.1, 0.9), (t, level), (t + PULSE_US, level), (t + PULSE_US + 0.1, 0.9)])
    pairs.append((5005.0, 0.9))
    return "PWL(" + " ".join(f"{t:.9g}u {v:.12g}" for t, v in pairs) + ")"


def gate_pwl(kind: str, times: list[float]) -> str:
    base = kind[:-1] if kind.endswith("b") else kind
    points = [(0.0, 0.0 if base == "connect" else 1.8)]
    for t in times:
        if base == "connect":
            points += [(t - 0.4, 0.0), (t - 0.3, 1.8), (t + PULSE_US, 1.8), (t + PULSE_US + 0.1, 0.0)]
        else:
            points += [(t - 1.0, 1.8), (t - 0.4, 0.0), (t + PULSE_US + 0.3, 0.0), (t + PULSE_US + 0.4, 1.8)]
    points.append((5005.0, points[-1][1]))
    if kind.endswith("b"): points = [(t, 1.8-v) for t,v in points]
    return "PWL(" + " ".join(f"{t:.9g}u {v:g}" for t,v in points) + ")"


def main() -> None:
    if not np.isfinite(STATE_GAIN) or not 1.0 <= STATE_GAIN <= 32.0:
        raise ValueError("state gain must be finite and within 1..32 to keep the sampled event weights rail-safe")
    if not np.isfinite(CAL_STEP_V) or not 0.001 <= CAL_STEP_V <= 0.6:
        raise ValueError("calibration step must be finite and within 1mV..600mV")
    if not np.isfinite(INJECTOR_GAIN) or not 0.5 <= INJECTOR_GAIN <= 2.0:
        raise ValueError("injector gain must be finite and within 0.5..2")
    if CORNER not in TEMPS: raise ValueError("corner must be tt/ss/ff")
    if not 1 <= STATE_RESET_TGS <= 10: raise ValueError("state-reset-tgs must be 1..10")
    if not 1 <= STATE_RESET_STACK <= 3: raise ValueError("state-reset-stack must be 1..3")
    if not 1 <= STATE_BANK_COPIES <= 8: raise ValueError("state-bank-copies must be 1..8")
    if not 1 <= PACKET_BANK_COPIES <= 16: raise ValueError("packet-bank-copies must be 1..16")
    if not 0.5 <= PULSE_US <= 10: raise ValueError("event-pulse-us must be 0.5..10")
    if CAL_PHASE not in ("mid", "end"): raise ValueError("calibration-phase must be mid or end")
    weights, info = event_weights()
    if LIMIT:
        if not 1 <= LIMIT <= len(weights): raise ValueError("limit-events must be 1..322")
        info["trace_events"] = len(weights)
        weights = weights[:LIMIT]
    info["events"] = len(weights)
    info["events_simulated"] = len(weights)
    if ZERO_INPUTS:
        weights = [0.0] * len(weights)
        info["zero_input_control"] = True
    if EVENT_SPAN_US <= 0 or EVENT_SPAN_US > 4890:
        raise ValueError("event-span-us must be >0 and <=4890")
    # Default places updates across the full 5ms bin; shorter spans probe batching.
    times = np.linspace(10.0, 10.0 + EVENT_SPAN_US, len(weights)).tolist()
    event_slot_us = times[1] - times[0] if len(times) > 1 else 3.0
    sample_offset_us = PULSE_US + 1.2
    if sample_offset_us >= event_slot_us:
        raise ValueError("event pulse and packet reset do not fit in the event slot")
    stop_us = 5000.0 if not LIMIT else max(30.0, times[-1] + 10.0)
    stop_token = "5m" if stop_us >= 1000 else f"{stop_us:g}u"
    step_tag = f"s{DT_NS:g}n".replace(".", "p")
    packet_tag = f"_pkt{PACKET_BANK_COPIES}" if PACKET_BANK_COPIES > 1 else ""
    pair_tag = "_pairpex" if PAIR_MACRO else ""
    pulse_tag = f"_pw{PULSE_US:g}u".replace(".", "p") if PULSE_US != 1.7 else ""
    phase_tag = "_cend" if CAL_PHASE == "end" else ""
    cal_tag = f"pz_{CORNER}_t{TEMPS[CORNER]}_t110_t24500_cm100_cp1_step{CAL_STEP_V:g}_{step_tag}_pextg_r{STATE_RESET_TGS}_physmim_b{STATE_BANK_COPIES}{packet_tag}{pulse_tag}{phase_tag}.json"
    cal_path = RES / "sky130_differential_cap_packet" / cal_tag
    # The calibration runner omits the bank suffix for its default single-copy
    # cell, while multi-copy reports include it. Accept both canonical names.
    if not cal_path.is_file() and STATE_BANK_COPIES == 1:
        cal_path = cal_path.with_name(cal_path.name.replace("_b1.json", ".json"))
    cal = json.loads(cal_path.read_text(encoding="utf-8"))
    single_step_v = cal["measurements"][CAL_PHASE]["diff_v"]
    slope = single_step_v / CAL_STEP_V
    OUT.mkdir(parents=True, exist_ok=True)
    tag = f"{CORNER}_{ORDER}_{SITE}_{len(weights)}_span{EVENT_SPAN_US:g}us_{step_tag}_g{STATE_GAIN:g}_ig{INJECTOR_GAIN:g}_cal{CAL_STEP_V:g}v{'_zeroin' if ZERO_INPUTS else ''}_pextg_r{STATE_RESET_TGS}s{STATE_RESET_STACK}_physmim_b{STATE_BANK_COPIES}{packet_tag}{pulse_tag}{phase_tag}{pair_tag}"
    deck = OUT / f"{tag}.cir"
    prefixes = sorted(set(n for n in [1, 10, 40, 100, 200, 300, len(weights)] if n <= len(weights)))
    reset_lines_list = []
    for rail in ("p", "n"):
        left = f"out{rail}"
        for stage in range(STATE_RESET_STACK):
            right = "vcm" if stage == STATE_RESET_STACK - 1 else f"rst{rail}_{stage}"
            for copy in range(STATE_RESET_TGS):
                reset_lines_list.append(
                    f"Xrst{rail}_s{stage}_{copy} {left} {right} state_init state_initb vdd 0 sky130_pex_tg")
            left = right
    reset_lines = "\n".join(reset_lines_list)
    reset_ics = " ".join(
        f"v(rst{rail}_{stage})=0.9" for rail in ("p", "n")
        for stage in range(STATE_RESET_STACK - 1))
    if PAIR_MACRO:
        state_lines = "Xmem_pair outp outn vcm sky130_differential_mim_state_pair_raw"
    else:
        state_lines = "\n".join(
            f"Xmemp{i} outp vcm mim_state_square_3x4_w30_l30\n"
            f"Xmemn{i} outn vcm mim_state_square_3x4_w30_l30" for i in range(STATE_BANK_COPIES))
    packet_lines = "\n".join(
        f"Xpktp{i} topp botp packet_cap_mim_2x2um\n"
        f"Xpktn{i} topn botn packet_cap_mim_2x2um" for i in range(PACKET_BANK_COPIES))
    measure_lines = "\n".join(
        f"meas tran diff_n{n} find v(diff) at={times[n-1]+sample_offset_us:.9g}u" for n in prefixes)
    deck.write_text(f'''* Epoch58 original-float high-cancellation fan-in, direct differential packet cell
.option scale=1u rshunt=1e12 reltol=1e-4 abstol=1e-16 vntol=1e-9 numdgt=15 method=trap maxord=2 gmin=1e-12 itl1=200 itl2=100 itl4=100
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{CORNER}.corner.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{CORNER}.corner.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "/workspace/asic/analog/modules.spice"
.include "{TGPEX}"
.include "{STATECAP}"
.include "{PACKETCAP}"
{f'.include "{STATEPAIRPEX}"' if PAIR_MACRO else ''}
.subckt sky130_pex_tg a b en enb vdd vss
Xphysical a b en enb vdd vss sky130_transmission_gate_raw
.ends sky130_pex_tg
Vdd vdd 0 1.8
Vcm vcm 0 0.9
{state_lines}
Bdiff diff 0 V=V(outp)-V(outn)
{packet_lines}
Vstate_init_drv state_init_drv 0 PWL(0 1.8 1.9u 1.8 2u 0 5005u 0)
Vstate_initb_drv state_initb_drv 0 PWL(0 0 1.9u 0 2u 1.8 5005u 1.8)
Rstate_init_drv state_init_drv state_init 100
Rstate_initb_drv state_initb_drv state_initb 100
{reset_lines}
Vconn_drv conn_drv 0 {gate_pwl("connect", times)}
Vconnb_drv connb_drv 0 {gate_pwl("connectb", times)}
Vreset_drv reset_drv 0 {gate_pwl("reset", times)}
Vresetb_drv resetb_drv 0 {gate_pwl("resetb", times)}
Rconn_drv conn_drv conn 100
Rconnb_drv connb_drv connb 100
Rreset_drv reset_drv reset 100
Rresetb_drv resetb_drv resetb 100
Xconp botp outp conn connb vdd 0 sky130_pex_tg
Xconn botn outn conn connb vdd 0 sky130_pex_tg
Xrstp botp vcm reset resetb vdd 0 sky130_pex_tg
Xrstn botn vcm reset resetb vdd 0 sky130_pex_tg
Vtop_p topp 0 {make_pwl(weights,1,slope,times)}
Vtop_n topn 0 {make_pwl(weights,-1,slope,times)}
.ic v(outp)=0.9 v(outn)=0.9 v(botp)=0.9 v(botn)=0.9 {reset_ics}
.temp {TEMPS[CORNER]}
.control
set noaskquit
tran {DT_NS:g}n {stop_token} uic
meas tran diff_pre find v(diff) at=8u
{measure_lines}
meas tran diff_end find v(diff) at={stop_token}
quit
.endc
.end
''', encoding="ascii")
    proc = subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
                           "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models", "--entrypoint",
                           "ngspice", IMAGE, "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"],
                          capture_output=True, text=True, timeout=300, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUT / f"{tag}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k,v in re.findall(
        r"(?im)^\s*(diff_pre|diff_end|diff_n\d+)\s*=\s*([-+0-9.eE]+)", log)}
    expected_keys = 2 + len(prefixes)
    if proc.returncode or len(vals) != expected_keys or "ngspice-36 done" not in log:
        raise RuntimeError(log[-5000:])
    base = vals["diff_pre"]
    reports = []
    for n in prefixes:
        measured = vals[f"diff_n{n}"] - base
        ideal = sum(weights[:n]) * VPU * STATE_GAIN
        reports.append({"events":n,"ideal_diff_v":ideal,"measured_diff_v":measured,
                        "error_v":measured-ideal,"ordered_weight_sum":sum(weights[:n])})
    end = vals["diff_end"]-base
    ideal_end = sum(weights)*VPU*STATE_GAIN
    float_margin_v = (info["float_candidate"] - info["float_threshold"]) * VPU * STATE_GAIN
    float_pre_event_state_v = (info["float_candidate"] - info["float_current"]) * VPU * STATE_GAIN
    measured_candidate_v = float_pre_event_state_v + end
    threshold_v = info["float_threshold"] * VPU * STATE_GAIN
    report = {"test":"sky130_epoch58_float_fanin_direct_differential_packet","simulation_completed":True,
              **info,"corner":CORNER.upper(),"temperature_c":TEMPS[CORNER],"order":ORDER,
              "qat_or_quantized_reference_used":False,"volts_per_model_unit":VPU,
              "analog_state_range_gain": STATE_GAIN,
              "analog_injector_gain_trim": INJECTOR_GAIN,
              "packet_top_step_calibration_v_per_v":slope,"single_event_calibration_diff_v":single_step_v,
              "calibration_top_step_v": CAL_STEP_V,
              "event_service_window_us":[times[0],times[-1]],"event_slot_us":event_slot_us if len(times)>1 else None,
              "prefix_measure_offset_us":sample_offset_us,
              "event_span_us":EVENT_SPAN_US,
              "simulation_stop_us":stop_us,
              "numerical_shunt_resistance_ohm":1e12,
              "max_step_ns":DT_NS,"ideal_final_diff_v":ideal_end,"measured_final_diff_v":end,
              "final_error_v":end-ideal_end,"prefixes":reports,
              "float_candidate_threshold_margin_v":float_margin_v,
              "float_pre_event_state_v":float_pre_event_state_v,
              "ideal_threshold_voltage_v":threshold_v,
              "predicted_candidate_from_measured_increment_v":measured_candidate_v,
              "predicted_margin_after_measured_increment_v":measured_candidate_v-threshold_v,
              "predicted_decision_matches_float":(measured_candidate_v >= threshold_v) == (info["float_candidate"] >= info["float_threshold"]),
              "decision_scope":"Arithmetic comparison using the measured event increment and float-derived pre-event state/threshold; no transistor comparator, threshold trim, noise or mismatch is included.",
              "state_reset_tgs_per_stage_per_rail":STATE_RESET_TGS,"state_reset_series_stages":STATE_RESET_STACK,
              "state_bank_layout_copies_per_rail":STATE_BANK_COPIES,
              "packet_cap_layout_copies_per_rail":PACKET_BANK_COPIES,
              "integrated_state_pair_layout_pex":PAIR_MACRO,
              "event_pulse_width_us":PULSE_US,
              "calibration_phase":CAL_PHASE,
              "scope":"Selected original full-float final-fusion weighted events drive ideal analog packet amplitudes calibrated per corner using extracted PEX-switch transient response. State capacitors use the DRC/LVS-qualified 3x4 array layout; optionally the two-rail pair and shared VCM strap use their composite layout PEX. The 2x2um packet capacitors use the DRC/LVS-qualified minimum PCell layout; transfer/reset switches use extracted TG PEX. A 1Tohm ngspice numerical shunt is present. Top-level routing RC, analog weight storage/DAC, mismatch/noise, neuron threshold/beta/reset, and population service are not included."}
    (OUT / f"{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__": main()
