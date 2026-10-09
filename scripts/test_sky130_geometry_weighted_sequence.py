"""Replay one original-float fan-in using static MOS geometry-coded weights.

Weight magnitude selects the fixed p/n device widths at design time. A common
gate pulse carries presynaptic activity, so the test needs no per-weight analog
sample-and-hold or per-event analog gate-amplitude command.
"""
from __future__ import annotations

import json
import random
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
REF = OUT / "model_reference"
BENCH = OUT / "benches"
RES = OUT / "results"
MAP_FILE = RES / "sky130_ms_static_geometry_float_mapping_screen.json"

COMMON = '''.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
'''


def main() -> int:
    import sys

    site = tuple(map(int, next((a.split("=", 1)[1] for a in sys.argv[1:]
                                if a.startswith("--site-index=")), "16,0,61,1").split(",")))
    if len(site) != 4:
        raise ValueError("site index must be flattened_time, output_channel, y, x")
    ni, oi, yy, xx = site
    order = next((a.split("=", 1)[1] for a in sys.argv[1:]
                  if a.startswith("--order=")), "shuffle")
    if order not in {"shuffle", "forward", "reverse"}:
        raise ValueError("order must be shuffle, forward or reverse")
    seed = int(next((a.split("=", 1)[1] for a in sys.argv[1:]
                     if a.startswith("--seed=")), "140"))
    event_offset = int(next((a.split("=", 1)[1] for a in sys.argv[1:]
                             if a.startswith("--event-offset=")), "0"))
    event_count = int(next((a.split("=", 1)[1] for a in sys.argv[1:]
                           if a.startswith("--event-count=")), "370"))
    initial_vp = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                            if a.startswith("--initial-vp=")), "0.9"))
    initial_vn = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                            if a.startswith("--initial-vn=")), "0.9"))
    spacing_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                             if a.startswith("--event-spacing-us=")), "0.015"))
    stop_us_arg = next((a.split("=", 1)[1] for a in sys.argv[1:]
                        if a.startswith("--stop-us=")), None)
    cap_um = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                         if a.startswith("--state-cap-um=")), "10"))
    fraction = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                           if a.startswith("--gate-fraction=")), "0.8"))
    headroom = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                           if a.startswith("--headroom-v=")), "0.9"))
    series_isolation = next((a.split("=", 1)[1].lower() for a in sys.argv[1:]
                             if a.startswith("--series-isolation=")), "false") in {"1", "true", "yes"}
    reverse_polarity = next((a.split("=", 1)[1].lower() for a in sys.argv[1:]
                             if a.startswith("--reverse-polarity=")), "false") in {"1", "true", "yes"}
    device_scale = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                               if a.startswith("--device-scale=")), "1"))
    isolation_width = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                                  if a.startswith("--isolation-width-um=")), "3"))
    instantiate_all = next((a.split("=", 1)[1].lower() for a in sys.argv[1:]
                            if a.startswith("--instantiate-all=")), "false") in {"1", "true", "yes"}
    instantiate_count = int(next((a.split("=", 1)[1] for a in sys.argv[1:]
                                  if a.startswith("--instantiate-count=")), "0"))
    if not 0.5 <= fraction <= 0.95 or spacing_us < 0.012 or not 3 <= cap_um <= 100:
        raise ValueError("gate fraction, event spacing or MIM size is outside the bounded screen")

    trace_meta = json.loads((REF / "float_patch_trace_all.json").read_text())
    archive = np.load(REF / trace_meta["trace_archive"])
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    meta = json.loads((REF / "eventspikeseg140k_float_reference.json").read_text())
    conv2d = __import__("runpy").run_path(str(ROOT / "scripts/analyze_sky130_passive_float_mapping.py"))["conv2d"]
    x = archive["presynaptic_input__final_fuse__standard"].astype(np.float32)
    w = params["weight__final_fuse__standard"].astype(np.float32)
    candidate = archive["candidate__final_fuse__standard"]
    current = archive["current__final_fuse__standard"]
    geom_meta = next(z for z in meta["effective_folded_weight_and_neuron_parameters"]
                     if z["name"] == "final_fuse.standard")
    active = conv2d(x, np.ones_like(w), candidate.shape[-2:],
                    groups=geom_meta["conv_groups"],
                    dilation=tuple(geom_meta["conv_dilation"]),
                    padding=tuple(geom_meta["conv_padding"]))
    if not (0 <= ni < active.shape[0] and 0 <= oi < active.shape[1]
            and 0 <= yy < active.shape[2] and 0 <= xx < active.shape[3]):
        raise ValueError(f"site {site} is outside active-fanin array {active.shape}")

    pad_y, pad_x = geom_meta["conv_padding"]
    dy, dx = geom_meta["conv_dilation"]
    synapses: dict[tuple[int, int, int], float] = {}
    events: list[tuple[float, tuple[int, int, int]]] = []
    for ic in range(w.shape[1]):
        for ky in range(w.shape[2]):
            for kx in range(w.shape[3]):
                iy = yy * max(1, round(x.shape[-2] / candidate.shape[-2])) + ky * dy - pad_y
                ix = xx * max(1, round(x.shape[-1] / candidate.shape[-1])) + kx * dx - pad_x
                if 0 <= iy < x.shape[-2] and 0 <= ix < x.shape[-1]:
                    value = float(w[oi, ic, ky, kx])
                    key = (ic, ky, kx)
                    if value:
                        synapses[key] = value
                        events.extend((value, key) for _ in range(int(x[ni, ic, iy, ix])))
    if not events:
        raise ValueError("selected trace site has no active weighted events")

    mapping = json.loads(MAP_FILE.read_text())
    fractions = mapping["measured_positive_event_uv_by_gate_fraction"][f"{fraction:g}"]
    geometries = np.asarray(mapping["geometry_scale_factors"], dtype=float)
    transfers_uv = np.asarray(fractions["charge_uv"], dtype=float)
    if fraction == 0.8:
        wide_g = np.asarray([8.0, 16.0, 32.0, 64.0])
        wide_q = []
        for geom in wide_g.astype(int):
            report = next(RES.glob(f"sky130_ms_first_event_clamp_ss_temp0_g0p8_geom{geom}_tight_s0p2n_onlybefore_0p2ns.json"))
            wide_q.append(float(json.loads(report.read_text())["cases"][0]["end_event_minus_no_event_uv"]))
        geometries = np.concatenate((geometries, wide_g))
        transfers_uv = np.concatenate((transfers_uv, np.asarray(wide_q)))
    # The measured curve has small width-response reversals; use a monotone
    # envelope for a stable inverse and report the resulting transfer residual.
    monotone_uv = np.maximum.accumulate(transfers_uv)
    qmin_uv, qmax_uv = float(monotone_uv[0]), float(monotone_uv[-1])
    cmax = float(np.max(np.abs(candidate)))
    if not 0 < headroom <= 1.6:
        raise ValueError("headroom must be within the 1.8V differential operating range")
    gain_v_per_model = headroom / cmax
    geom_by_key: dict[tuple[int, int, int], float | None] = {}
    suppressed = set()
    for key, value in synapses.items():
        desired = abs(value) * gain_v_per_model * 1e6
        if desired < qmin_uv:
            geom_by_key[key] = None
            suppressed.add(key)
        else:
            geom_by_key[key] = float(np.interp(min(desired, qmax_uv), monotone_uv, geometries))

    original_events = list(events)
    if order == "forward":
        scheduled = sorted(events, key=lambda z: (1 if z[0] > 0 else -1, abs(z[0])))
    elif order == "reverse":
        scheduled = list(reversed(sorted(events, key=lambda z: (1 if z[0] > 0 else -1, abs(z[0])))))
    else:
        scheduled = list(events)
        random.Random(seed).shuffle(scheduled)
    if event_offset < 0 or event_count <= 0 or event_offset >= len(scheduled):
        raise ValueError("event segment is outside the selected full-fan-in sequence")
    chunk = scheduled[event_offset:event_offset + event_count]
    chunk_keys = set(synapses) if instantiate_all else {key for _, key in chunk}
    if instantiate_count:
        chunk_keys |= set(sorted(synapses)[:instantiate_count])

    target = float(current.reshape(30, 16, 64, 64)[ni, oi, yy, xx]) * gain_v_per_model
    event_target = sum(value for value, _ in original_events) * gain_v_per_model
    chunk_target = sum(value for value, _ in chunk) * gain_v_per_model
    ev_times: dict[tuple[int, int, int], list[float]] = {k: [] for k in chunk_keys}
    first_us = 0.1
    pulse_ns = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                           if a.startswith("--pulse-width-ns=")), "10.5"))
    settle_ns = float(next((a.split("=", 1)[1] for a in sys.argv[1:]
                            if a.startswith("--settle-after-event-ns=")), "100"))
    for i, (_, key) in enumerate(chunk):
        ev_times[key].append(first_us + i * spacing_us)
    last_us = first_us + spacing_us * (len(chunk) - 1)
    stop_us = float(stop_us_arg) if stop_us_arg else last_us + 1.0
    if stop_us <= last_us + pulse_ns / 1000 + 0.1:
        raise ValueError("stop time must follow the final event pulse")

    def waveform(key: tuple[int, int, int], gate: str) -> str:
        if gate in {"access", "accessb"}:
            off, on = ((0.0, 1.8) if gate == "access" else (1.8, 0.0))
        else:
            off = 1.8 if gate == "p" else 0.0
            on = 1.8 - fraction * 1.08 if gate == "p" else fraction * 0.6
        pts = [f"0 {off:.12g}"]
        for t in ev_times[key]:
            pts.extend((f"{t - .001:.12g}u {off:.12g}", f"{t:.12g}u {on:.12g}",
                        f"{t + pulse_ns/1000:.12g}u {on:.12g}",
                        f"{t + pulse_ns/1000 + .001:.12g}u {off:.12g}"))
        pts.append(f"{stop_us:g}u {off:.12g}")
        return "PWL(" + " ".join(pts) + ")"

    rows = ["SKY130 full-float fan-in with static geometry-coded MOS weights",
            COMMON, ".temp 0", "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
            f"Xmem_p vp vcm membrane_mim w_um={cap_um:g} l_um={cap_um:g}",
            f"Xmem_n vn vcm membrane_mim w_um={cap_um:g} l_um={cap_um:g}",
            f".ic v(vp)={initial_vp:.12g}", f".ic v(vn)={initial_vn:.12g}",
            ".ic v(xmem_p.xmim.a)=0.9", ".ic v(xmem_n.xmim.a)=0.9"]
    for i, key in enumerate(sorted(chunk_keys)):
        value = synapses[key]
        geom = geom_by_key[key]
        if geom is None:
            continue
        gp, gn = f"g_a_p_{i}", f"g_a_n_{i}"
        rows.extend((f"V{gp} {gp} 0 {waveform(key, 'p')}",
                     f"V{gn} {gn} 0 {waveform(key, 'n')}"))
        drain_p, drain_n = ("vp", "vn") if value > 0 else ("vn", "vp")
        if reverse_polarity:
            drain_p, drain_n = drain_n, drain_p
        rows.extend((f"Xp_a_{i} {('ip_'+str(i)) if series_isolation else drain_p} {gp} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom:.9g} l=10 nf={int(device_scale)}",
                     f"Xn_a_{i} {('in_'+str(i)) if series_isolation else drain_n} {gn} 0 0 sky130_fd_pr__nfet_01v8 w={geom:.9g} l=10 nf={int(device_scale)}"))
        if series_isolation:
            ga = f"g_a_iso_{i}"
            gab = f"g_ab_iso_{i}"
            rows.extend((f"V{ga} {ga} 0 {waveform(key, 'access')}",
                         f"V{gab} {gab} 0 {waveform(key, 'accessb')}",
                         f"Xisopn_{i} ip_{i} {ga} {drain_p} 0 sky130_fd_pr__nfet_01v8 w={isolation_width:g} l=0.15",
                         f"Xisop_p_{i} ip_{i} {gab} {drain_p} vdd sky130_fd_pr__pfet_01v8 w={isolation_width:g} l=0.15",
                         f"Xisonn_{i} in_{i} {ga} {drain_n} 0 sky130_fd_pr__nfet_01v8 w={isolation_width:g} l=0.15",
                         f"Xison_p_{i} in_{i} {gab} {drain_n} vdd sky130_fd_pr__pfet_01v8 w={isolation_width:g} l=0.15"))
    pre_us = first_us - 0.01
    sample_us = last_us + (pulse_ns + settle_ns) / 1000
    rows += [".control", "set numdgt=15", f"tran 10n {stop_us:g}u 0 2n uic",
             "let d=v(vp)-v(vn)", "let cm=(v(vp)+v(vn))/2",
             f"meas tran pre_diff find d at={pre_us:g}u", f"meas tran final_diff find d at={sample_us:g}u",
             f"meas tran final_cm find cm at={sample_us:g}u",
             "quit", ".endc", ".end"]

    tag = (f"n{len(events)}_site{'_'.join(map(str, site))}_ord{order}_seed{seed}"
           f"_g{fraction:g}_H{headroom:g}_c{cap_um:g}_p{spacing_us*1000:g}n_s2n_iso{int(series_isolation)}_rp{int(reverse_polarity)}_ds{device_scale:g}_iw{isolation_width:g}_all{int(instantiate_all)}_cnt{instantiate_count}_pw{pulse_ns:g}_settle{settle_ns:g}")
    tag += f"_t{stop_us:g}u"
    if event_offset or len(chunk) < len(scheduled):
        tag += f"_seg{event_offset}-{event_offset+len(chunk)}"
    deck = BENCH / f"sky130_geometry_weighted_sequence_{tag}.cir"
    deck.write_text("\n".join(rows) + "\n")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "240", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=255)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_geometry_weighted_sequence_{tag}.log").write_text(log)
    vals = {k: float(v) for k, v in re.findall(
        r"(?im)^\s*(pre_diff|final_diff|final_cm)\s*=\s*([-+0-9.eE]+)", log)}
    complete = (proc.returncode == 0 and len(vals) == 3
                and "ngspice-36 done" in log and "tran simulation(s) aborted" not in log)
    measured = vals.get("final_diff", 0) - vals.get("pre_diff", 0)
    report = {"simulation_completed": complete, "return_code": proc.returncode,
              "mos_corner": "ss", "temperature_c": 0,
              "checkpoint_sha256": trace_meta["checkpoint_sha256"],
              "qat_or_quantized_reference_used": False,
              "selected_site_index": list(site), "fan_in_events": len(events),
              "segment_offset": event_offset, "segment_event_count": len(chunk),
              "initial_vp_v": initial_vp, "initial_vn_v": initial_vn,
              "segment_float_target_v": chunk_target,
              "active_synapse_count": len(synapses), "suppressed_synapse_count": len(suppressed),
              "suppressed_event_count": sum(1 for _, k in events if k in suppressed),
              "suppressed_absolute_event_weight_mass_fraction": (
                  sum(abs(v) for v, k in events if k in suppressed)
                  / max(sum(abs(v) for v, _ in events), 1e-30)),
              "event_order": order, "random_seed": seed if order == "shuffle" else None,
              "state_cap_square_width_um": cap_um, "common_gate_fraction": fraction, "series_isolation": series_isolation, "reverse_polarity": reverse_polarity, "device_scale": device_scale, "isolation_width_um": isolation_width, "instantiated_all_active_synapses": instantiate_all, "instantiated_synapse_count": len(chunk_keys),
              "candidate_headroom_v": headroom, "candidate_max_abs_model_units": cmax,
              "event_spacing_us": spacing_us, "pulse_width_ns": pulse_ns, "settle_after_event_ns": settle_ns,
              "stop_time_us": stop_us, "measurement_time_us": sample_us,
              "minimum_and_maximum_device_geometry_scale": [
                  float(min((v for v in geom_by_key.values() if v is not None), default=0)),
                  float(max((v for v in geom_by_key.values() if v is not None), default=0))],
              "geometry_curve_source": str(MAP_FILE.relative_to(ROOT)),
              "geometry_curve_gate_fraction": fraction,
              "geometry_curve_widths": geometries.tolist(),
              "geometry_curve_event_charge_uv": transfers_uv.tolist(),
              "volts_per_model_weight_unit": gain_v_per_model,
              "ideal_full_float_event_sum_v": event_target,
              "ideal_trace_current_target_v": target,
              "measured_event_sum_v": measured if complete else None,
              "forward_or_order_relative_error": (measured-chunk_target)/max(abs(chunk_target), 1e-30) if complete else None,
              "raw_measurements_v": vals if complete else {},
              "scope": "One frozen epoch58 full-float final-fusion location. Each deployed float weight maps to a fixed p/n MOS width via the measured SS/0C width-response curve; all devices share one ideal gate pulse level and only presynaptic activity gates events. This avoids per-weight analog sample/hold in the schematic model. Only the selected contiguous event segment's synapse devices are instantiated, with membrane state carried across segments as initial voltages; other idle synapses are omitted. The curve has small width-response reversals handled with a monotone envelope. No physical PCell layout of custom widths, routing, mismatch/noise, measured analog pulse driver, PLIF threshold/reset/beta, full-frame task replay or population service is included."}
    if complete:
        report["final_vp_v"] = vals["final_cm"] + vals["final_diff"] / 2
        report["final_vn_v"] = vals["final_cm"] - vals["final_diff"] / 2
    path = RES / f"sky130_geometry_weighted_sequence_{tag}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
