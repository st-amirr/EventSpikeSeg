"""Export one full-float weighted final-fusion fan-in to a physical SS SPICE deck."""
from __future__ import annotations

import json
import random
import runpy
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
REF = OUT / "model_reference"
RES = OUT / "results"
BENCH = OUT / "benches"


def main() -> int:
    corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                   if arg.startswith("--corner=")), "ss")
    temperature_c = {"ss": 0, "tt": 27, "ff": 85}.get(corner)
    if temperature_c is None:
        raise ValueError("corner must be ss, tt or ff")
    map_corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                       if arg.startswith("--map-corner=")), corner)
    if map_corner not in ("ss", "tt", "ff"):
        raise ValueError("map corner must be ss, tt or ff")
    site = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                 if arg.startswith("--site=")), "max_fanin")
    if site not in ("max_fanin", "high_cancellation", "near_threshold_scale"):
        raise ValueError("unknown trace site selection")
    order_set = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                      if arg.startswith("--orders=")), "all")
    if order_set not in ("all", "forward", "reverse", "shuffle"):
        raise ValueError("unknown event order selection")
    mapping = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                    if arg.startswith("--mapping=")), "short_linear")
    if mapping not in ("short_linear", "stage_linear", "stage_log"):
        raise ValueError("unknown weight-to-gate interpolation")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    trace = json.loads((REF / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    expected = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
    if trace["checkpoint_sha256"] != expected or trace["qat_or_quantized_reference_used"]:
        raise RuntimeError("unexpected float reference")
    arrays = np.load(REF / trace["trace_archive"])
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    meta = json.loads((REF / "eventspikeseg140k_float_reference.json").read_text(encoding="utf-8"))
    geom = next(row for row in meta["effective_folded_weight_and_neuron_parameters"]
                if row["name"] == "final_fuse.standard")
    weight = params["weight__final_fuse__standard"].astype(np.float32)
    inputs = arrays["presynaptic_input__final_fuse__standard"].astype(np.float32)
    candidate = arrays["candidate__final_fuse__standard"]
    current = arrays["current__final_fuse__standard"]
    conv2d = runpy.run_path(str(ROOT / "scripts/analyze_sky130_passive_float_mapping.py"))["conv2d"]
    fanin = conv2d(inputs, np.ones_like(weight), candidate.shape[-2:],
                   groups=geom["conv_groups"], dilation=tuple(geom["conv_dilation"]),
                   padding=tuple(geom["conv_padding"]))
    if site == "max_fanin":
        selection_index = int(np.argmax(fanin))
    else:
        eligible = fanin >= np.percentile(fanin[fanin > 0], 99)
        target = 0.0 if site == "high_cancellation" else 0.5
        rank = np.where(eligible, np.abs(np.abs(current.reshape(fanin.shape)) - target), np.inf)
        selection_index = int(np.argmin(rank))
    ni, oi, yy, xx = np.unravel_index(selection_index, fanin.shape)
    counts = []
    pad_y, pad_x = geom["conv_padding"]
    dy, dx = geom["conv_dilation"]
    sy = max(1, round(inputs.shape[-2] / candidate.shape[-2]))
    sx = max(1, round(inputs.shape[-1] / candidate.shape[-1]))
    for ic in range(weight.shape[1]):
        for ky in range(weight.shape[2]):
            for kx in range(weight.shape[3]):
                iy = yy * sy + ky * dy - pad_y
                ix = xx * sx + kx * dx - pad_x
                if 0 <= iy < inputs.shape[-2] and 0 <= ix < inputs.shape[-1]:
                    multiplicity = int(inputs[ni, ic, iy, ix])
                    counts.extend([float(weight[oi, ic, ky, kx])] * multiplicity)
    if len(counts) != int(fanin[ni, oi, yy, xx]):
        raise RuntimeError("weighted-event multiplicity differs from active fan-in")
    cmax = float(np.max(np.abs(candidate)))
    vpu = 0.9 / cmax
    width_report = json.loads((RES / "sky130_ms_pvt_float_weight_charge_coverage.json").read_text(encoding="utf-8"))
    stage = next(row for row in width_report["stages"] if row["stage"] == "final_fuse.standard")
    width_ns = float(stage["illustrative_worst_corner_width_ns_to_cover_max_weight"])
    if mapping == "short_linear":
        curve = json.loads((RES / "sky130_ms_first_event_pvt_transfer_curve_tight.json").read_text(encoding="utf-8"))
        condition = next(row for row in curve["conditions"] if row["mos_corner"] == map_corner)
        points = condition["points"]
        delivered_v = np.array([row["event_step_uv"] for row in points]) * 1e-6 * width_ns / 10.5
    else:
        curve = json.loads((RES / f"sky130_ms_first_event_{map_corner}_stage_width_transfer.json").read_text(encoding="utf-8"))
        if abs(curve["pulse_width_ns"] - width_ns) > 0.001 or not curve["simulation_completed"]:
            raise RuntimeError("stage pulse-width curve mismatch")
        points = curve["points"]
        delivered_v = np.array([row["event_step_uv"] for row in points]) * 1e-6
    fractions = np.array([row["gate_fraction"] for row in points])
    if not np.all(np.diff(delivered_v) > 0):
        raise RuntimeError("non-monotone charge transfer")
    floor_v, ceiling_v = float(delivered_v[0]), float(delivered_v[-1])
    mapped = []
    for value in counts:
        requested_v = abs(value) * vpu
        if mapping == "stage_log":
            fraction = float(np.interp(np.log(max(requested_v, floor_v)), np.log(delivered_v), fractions))
        else:
            fraction = float(np.interp(requested_v, delivered_v, fractions))
        mapped.append((value, fraction, requested_v))
    ascending = sorted(mapped, key=lambda item: (item[0] > 0, abs(item[0])))
    shuffled = list(ascending)
    random.Random(140).shuffle(shuffled)
    sequences = {"forward": ascending, "reverse": list(reversed(ascending)), "shuffle": shuffled}
    if order_set != "all":
        sequences = {order_set: sequences[order_set]}
    width_us = width_ns / 1000
    period_us = width_us + 0.010
    first_us = 3.0
    stop_us = first_us + (len(counts) - 1) * period_us + width_us + 0.5
    lines = [f"SKY130 {corner.upper()} {temperature_c}C first-touch full-float final-fusion weighted fan-in",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9", f".temp {temperature_c}",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
             f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
             '.include "../../../asic/analog/modules.spice"',
             '.include "../../../asic/analog/sky130_ms_plif.spice"',
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
             ".subckt diff_inject vp vn pp np pn nn vdd vss",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w=1 l=10",
             "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10",
             "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w=1 l=10",
             ".ends diff_inject"]

    def wave(sequence: list[tuple[float, float, float]], sign: str, mos: str) -> str:
        off = 1.8 if mos == "p" else 0.0
        points = [(0.0, off)]
        for index, (value, fraction, _) in enumerate(sequence):
            if (value > 0) != (sign == "p"):
                continue
            at = first_us + index * period_us
            active = 1.8 - fraction * 1.08 if mos == "p" else fraction * 0.6
            points.extend(((at - 0.0001, off), (at, active),
                           (at + width_us, active), (at + width_us + 0.0001, off)))
        points.append((stop_us, off))
        return "PWL(" + " ".join(f"{t:.12g}u {v:.12g}" for t, v in points) + ")"

    for name in ("ref", *sequences):
        sequence = sequences.get(name, [])
        lines += [f"Xmem_p_{name} vp_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Xmem_n_{name} vn_{name} vcm membrane_mim w_um=10 l_um=10",
                  f"Vcl_{name} cl_{name} 0 PWL(0 1.8 2.9998u 1.8 2.9999u 0 {stop_us:.12g}u 0)",
                  f"Vclb_{name} clb_{name} 0 PWL(0 0 2.9998u 0 2.9999u 1.8 {stop_us:.12g}u 1.8)",
                  f"Xcl_p_{name} vcm vp_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Xcl_n_{name} vcm vn_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Vpp_{name} pp_{name} 0 {wave(sequence, 'p', 'p')}",
                  f"Vnn_{name} nn_{name} 0 {wave(sequence, 'p', 'n')}",
                  f"Vpn_{name} pn_{name} 0 {wave(sequence, 'n', 'p')}",
                  f"Vnp_{name} np_{name} 0 {wave(sequence, 'n', 'n')}",
                  f"Xinj_{name} vp_{name} vn_{name} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject"]
    lines += [".control", "set numdgt=15", f"tran 0.5n {stop_us:.12g}u uic"]
    for name in ("ref", *sequences):
        lines.append(f"let diff_{name}=v(vp_{name})-v(vn_{name})")
        lines.append(f"meas tran final_{name} find diff_{name} at={stop_us-0.1:.12g}u")
    lines += ["quit", ".endc", ".end"]
    stem = f"sky130_ms_first_touch_float_fanin_{corner}{temperature_c}"
    if map_corner != corner:
        stem += f"_map{map_corner}"
    if site != "max_fanin":
        stem += "_" + site
    if mapping != "short_linear":
        stem += "_" + mapping
    if order_set != "all":
        stem += f"_{order_set}only"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    chosen_current = float(current.reshape(30, 16, 64, 64)[ni, oi, yy, xx])
    metadata = {"test": "sky130_first_touch_full_float_fanin_deck",
                "checkpoint_sha256": expected, "qat_or_quantized_reference_used": False,
                "selected_flat_batch": int(ni), "selected_output_channel": int(oi),
                "selected_yx": [int(yy), int(xx)], "event_count": len(counts),
                "site_selection": site,
                "sum_folded_float_event_weights": float(sum(counts)),
                "recorded_float_current_model_units": chosen_current,
                "volts_per_model_unit": vpu,
                "ideal_event_sum_v": float(sum(counts) * vpu),
                "ideal_recorded_current_v": chosen_current * vpu,
                "width_ns": width_ns, "period_ns": period_us * 1000,
                "gate_mapping": mapping, "mos_corner": corner, "temperature_c": temperature_c,
                "gate_map_corner": map_corner,
                "event_orders": list(sequences),
                "requested_below_measured_floor_count": sum(item[2] < floor_v for item in mapped),
                "requested_above_measured_ceiling_count": sum(item[2] > ceiling_v for item in mapped),
                "measured_floor_v_at_width": floor_v, "measured_ceiling_v_at_width": ceiling_v,
                "deck": deck.name,
                "scope": f"One {site} final-fusion output from the original epoch58 float trace. Static folded weights and raw multiplicity expanded into events. Ideal per-weight gate voltage uses {mapping} interpolation of {map_corner} single-event curve while devices are {corner}/{temperature_c}C. Physical TG/MIM/MOS deck; no on-chip gate DAC, calibration, noise, mismatch, beta/reset/adaptation, threshold/readout, full graph or extracted layout."}
    (RES / f"{stem}_deck.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
