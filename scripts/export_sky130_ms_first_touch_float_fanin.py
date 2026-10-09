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
GEOMETRIES = (0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0)
BIAS_FRACTIONS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)


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
    per_synapse_devices = "--per-synapse-devices" in sys.argv[1:]
    isolate_inactive_synapses = "--isolate-inactive-synapses" in sys.argv[1:]
    isolation_precharge = "--isolation-precharge" in sys.argv[1:]
    isolation_switch_scale = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                         if arg.startswith("--isolation-switch-scale=")), "1"))
    event_width_scale = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                    if arg.startswith("--event-width-scale=")), "1"))
    map_width_override = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                               if arg.startswith("--transfer-map-width-ns=")), None)
    event_period_override = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                  if arg.startswith("--event-period-ns=")), None)
    banked_transfer_map = "--banked-transfer-map" in sys.argv[1:]
    layout_bank_duration_map = "--layout-bank-duration-map" in sys.argv[1:]
    variable_pulse_floor = "--variable-pulse-floor" in sys.argv[1:]
    piecewise_first_range = "--piecewise-first-range" in sys.argv[1:]
    ideal_state_polarity_correction = "--ideal-state-polarity-correction" in sys.argv[1:]
    measured_state_transfer_correction = "--measured-state-transfer-correction" in sys.argv[1:]
    physical_state_feedback = "--physical-state-feedback" in sys.argv[1:]
    bidirectional_state_feedback = "--bidirectional-state-feedback" in sys.argv[1:]
    state_correction_slope = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                         if arg.startswith("--state-correction-slope=")), "0.00193"))
    mos_layout_state_cap = "--mos-layout-state-cap" in sys.argv[1:]
    mos_state_cap = "--mos-state-cap" in sys.argv[1:] or mos_layout_state_cap
    event_limit = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                            if arg.startswith("--event-limit=")), "0"))
    tran_max_step_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                   if arg.startswith("--tran-max-step-ns=")), "0.5"))
    if tran_max_step_ns <= 0:
        raise ValueError("transient maximum step must be positive")
    prefix_measure_step = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                    if arg.startswith("--prefix-measure-step=")), "0"))
    if prefix_measure_step < 0:
        raise ValueError("prefix measure step must be zero or positive")
    if mapping not in ("short_linear", "stage_linear", "stage_log", "stage_discrete_geometry",
                       "stage_continuous_geometry"):
        raise ValueError("unknown weight-to-gate interpolation")
    if per_synapse_devices and mapping not in ("stage_discrete_geometry", "stage_continuous_geometry"):
        raise ValueError("per-synapse devices require the measured discrete geometry map")
    if banked_transfer_map and per_synapse_devices:
        raise ValueError("the bank-loaded transfer map applies only to the shared geometry bank")
    if variable_pulse_floor and (not banked_transfer_map or mapping != "stage_continuous_geometry"
                                 or per_synapse_devices):
        raise ValueError("variable pulse floor requires continuous mapping through the shared bank")
    if layout_bank_duration_map and (not mos_layout_state_cap or not banked_transfer_map
                                     or mapping != "stage_continuous_geometry" or per_synapse_devices):
        raise ValueError("layout-bank duration mapping requires the extracted shared MOS bank")
    if piecewise_first_range and (not banked_transfer_map or mapping != "stage_continuous_geometry"
                                  or per_synapse_devices):
        raise ValueError("piecewise first range requires continuous shared-bank mapping")
    if sum((ideal_state_polarity_correction, measured_state_transfer_correction,
            physical_state_feedback)) > 1:
        raise ValueError("choose only one state correction method")
    if (ideal_state_polarity_correction or measured_state_transfer_correction or
            physical_state_feedback) and not piecewise_first_range:
        raise ValueError("ideal state polarity correction is bounded to the first piecewise range")
    if measured_state_transfer_correction and not mos_state_cap:
        raise ValueError("measured state correction requires MOS state storage")
    if physical_state_feedback and (not mos_state_cap or not banked_transfer_map or per_synapse_devices):
        raise ValueError("physical state feedback requires shared MOS-state injector bank mode")
    if bidirectional_state_feedback and not physical_state_feedback:
        raise ValueError("bidirectional state correction requires the behavioral state sensor source")
    if isolate_inactive_synapses and not per_synapse_devices:
        raise ValueError("inactive-synapse isolation requires per-synapse devices")
    if isolation_precharge and not isolate_inactive_synapses:
        raise ValueError("isolation precharge requires inactive-synapse isolation")
    if not 1 <= isolation_switch_scale <= 16:
        raise ValueError("isolation switch scale must be between 1 and 16")
    if not 1 <= event_width_scale <= 1.12:
        raise ValueError("event-width scale must be between 1 and 1.12 for the fixed slot")
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
    if event_limit < 0:
        raise ValueError("event limit must be zero or positive")
    if event_limit:
        counts = counts[:event_limit]
    cmax = float(np.max(np.abs(candidate)))
    vpu = 0.9 / cmax
    first_range_limit = None
    if piecewise_first_range:
        frame = json.loads((RES / "sky130_float_state_saturation_validation_0_all_neurons_full_"
                            "none_g5000-10000_asinh_ideal.json").read_text(encoding="utf-8"))
        if frame["checkpoint_sha256"] != expected or frame["encoding"] != "asinh-ideal":
            raise RuntimeError("piecewise range and float checkpoint do not match")
        maximum = frame["actor_max_absolute_candidate_model_units"]["final_fuse.standard"]
        first_range_limit = float(maximum / 10000 * np.sinh(np.arcsinh(10000) / 8))
        vpu = float(0.9 / 8 / first_range_limit)
    width_report = json.loads((RES / "sky130_ms_pvt_float_weight_charge_coverage.json").read_text(encoding="utf-8"))
    stage = next(row for row in width_report["stages"] if row["stage"] == "final_fuse.standard")
    stage_width_ns = float(stage["illustrative_worst_corner_width_ns_to_cover_max_weight"])
    width_ns = float(map_width_override) if map_width_override else stage_width_ns
    if width_ns <= 0 or (map_width_override and mapping not in
                          ("stage_discrete_geometry", "stage_continuous_geometry")):
        raise ValueError("transfer-map width override requires measured discrete geometry")
    mapped = []
    effective_fraction = {}
    discrete_library = []
    measured_state_maps = None
    if mapping in ("stage_discrete_geometry", "stage_continuous_geometry"):
        if corner != "ss" or map_corner != "ss":
            raise ValueError("discrete geometry replay requires the measured SS/0C geometry library")
        curve_by_fraction = {}
        ideal_curve_by_fraction = {}
        layout_duration_widths_ns = []
        layout_duration_charge_v = []
        if mos_state_cap:
            transfer_stem = ("sky130_ms_mos_state_banked_transfer_ss0_layoutbank"
                             if mos_layout_state_cap else
                             "sky130_ms_mos_state_banked_transfer_ss0")
            default_transfer_width_ns = 4400.0 if mos_layout_state_cap else 42.2657
            if abs(width_ns - default_transfer_width_ns) > 0.001:
                transfer_stem += f"_w{width_ns:g}n".replace(".", "p")
            transfer_path = RES / f"{transfer_stem}.json"
            transfer_report = json.loads(transfer_path.read_text(encoding="utf-8"))
            if (not transfer_report["simulation_completed"] or
                    transfer_report["geometry_factors"] != list(GEOMETRIES) or
                    transfer_report["gate_fractions"] != list(BIAS_FRACTIONS) or
                    transfer_report["temperature_c"] != 0 or abs(width_ns - transfer_report["pulse_width_ns"]) > 0.001):
                raise RuntimeError("MOS state transfer map is missing, incomplete, or mismatched")
            table = transfer_report["transfer_delta_v_by_polarity_geometry_fraction"]["p"]
            if layout_bank_duration_map:
                duration_reports = [
                    (100.0, "sky130_ms_mos_state_dependence_ss0_layoutbank_dm500_0_500_w100n.json"),
                    (250.0, "sky130_ms_mos_state_dependence_ss0_layoutbank_dm500_0_500_w250n.json"),
                    (1000.0, "sky130_ms_mos_state_dependence_ss0_layoutbank_dm500_0_500_w1000n.json"),
                    (4400.0, "sky130_ms_mos_state_dependence_ss0_layoutbank_dm500_0_500.json"),
                ]
                for duration_ns, filename in duration_reports:
                    duration_report = json.loads((RES / filename).read_text(encoding="utf-8"))
                    if not duration_report.get("simulation_completed"):
                        raise RuntimeError(f"incomplete extracted-bank duration map: {filename}")
                    measured = next(row["delta_v"] for row in duration_report["rows"]
                                    if row["state_diff_mv"] == 0.0 and row["gate_fraction"] == 0.7
                                    and row["polarity"] == "p" and row["geometry"] == 4.0)
                    layout_duration_widths_ns.append(duration_ns)
                    layout_duration_charge_v.append(float(measured))
                if any(b <= a for a, b in zip(layout_duration_charge_v,
                                               layout_duration_charge_v[1:])):
                    raise RuntimeError("extracted-bank duration map is not monotone")
            if measured_state_transfer_correction:
                state_reports = {
                    -0.031: json.loads((RES / "sky130_ms_mos_state_banked_transfer_ss0_dm31mV.json").read_text(encoding="utf-8")),
                     0.0: transfer_report,
                     0.031: json.loads((RES / "sky130_ms_mos_state_banked_transfer_ss0_d31mV.json").read_text(encoding="utf-8")),
                }
                if any(not row.get("simulation_completed") for row in state_reports.values()):
                    raise RuntimeError("state-dependent MOS transfer map is incomplete")
                measured_state_maps = {state: row["transfer_delta_v_by_polarity_geometry_fraction"]["p"]
                                       for state, row in state_reports.items()}
            for fraction_index, fraction in enumerate(BIAS_FRACTIONS):
                values = [float(table[geometry_index][fraction_index]) * 1e6
                          for geometry_index in range(len(GEOMETRIES))]
                if not np.all(np.isfinite(values)):
                    raise RuntimeError(f"MOS state transfer contains a missing/non-finite value at fraction {fraction:g}")
                curve_by_fraction[fraction] = values
                ideal_curve_by_fraction[fraction] = values
                for geom_scale, value in zip(GEOMETRIES, values):
                    discrete_library.append((value * 1e-6, fraction, geom_scale))
            for geom_scale in GEOMETRIES:
                for fraction in BIAS_FRACTIONS:
                    effective_fraction[(geom_scale, fraction)] = fraction
        else:
            for fraction in BIAS_FRACTIONS:
                values = []
                ideal_values = []
                fraction_tag = "" if fraction == 0.6 else f"_g{fraction:g}".replace(".", "p")
                for geom_scale in GEOMETRIES:
                    geometry_tag = "" if geom_scale == 1 else f"_geom{geom_scale:g}".replace(".", "p")
                    width_tag = f"_w{width_ns:g}n".replace(".", "p")
                    bank_tag = "_banked" if banked_transfer_map else ""
                    path = RES / ("sky130_ms_first_event_clamp_ss_temp0" + fraction_tag + geometry_tag +
                                  f"_tight_s0p1n{width_tag}_post20n_rise2n{bank_tag}_onlybefore_10ns.json")
                    if not path.exists():
                        path = RES / ("sky130_ms_first_event_clamp_ss_temp0" + fraction_tag + geometry_tag +
                                      f"_tight_s0p1n{width_tag}_post20n_rise2n{bank_tag}.json")
                    row = json.loads(path.read_text(encoding="utf-8"))
                    if not row.get("simulation_completed") or abs(row.get("event_width_ns", 0) - width_ns) > 0.001:
                        raise RuntimeError(f"invalid discrete geometry measurement: {path}")
                    case = next(item for item in row["cases"] if item["case"] == "before_10ns")
                    ideal_q = float(case["post_event_minus_no_event_uv"])
                    rail_report = next((json.loads(p.read_text(encoding="utf-8"))
                                        for p in RES.glob("sky130_ms_static_bias_r2r_b12_event*.json")
                                        if json.loads(p.read_text(encoding="utf-8")).get("simulation_completed")
                                        and abs(json.loads(p.read_text(encoding="utf-8")).get("event_width_ns", 0) - width_ns) < 0.001
                                        and any(r["gate_fraction"] == fraction and r["injector_geometry_scale"] == 4
                                                for r in json.loads(p.read_text(encoding="utf-8")).get("event_transfer_rows", []))), None)
                    if rail_report is None:
                        raise RuntimeError(f"missing 12-bit R-2R correction at fraction {fraction:g}")
                    rail_row = next(r for r in rail_report["event_transfer_rows"] if r["gate_fraction"] == fraction)
                    correction = float(rail_row["r2r_event_delta_uv"] / rail_row["ideal_event_delta_uv"])
                    ideal_values.append(ideal_q)
                    values.append(ideal_q * correction)
                    discrete_library.append((ideal_q * correction * 1e-6, fraction, geom_scale))
                curve_by_fraction[fraction] = values
                ideal_curve_by_fraction[fraction] = ideal_values
        for geom_index, geom_scale in enumerate(GEOMETRIES):
            ideal_by_bias = np.asarray([ideal_curve_by_fraction[f][geom_index] for f in BIAS_FRACTIONS])
            corrected_by_bias = np.asarray([curve_by_fraction[f][geom_index] for f in BIAS_FRACTIONS])
            if not np.all(np.diff(ideal_by_bias) > 0):
                raise RuntimeError(f"gate-fraction transfer is not monotone at geometry {geom_scale:g}")
            for rail_index, fraction in enumerate(BIAS_FRACTIONS):
                effective_fraction[(geom_scale, fraction)] = float(np.interp(
                    np.log(corrected_by_bias[rail_index]), np.log(ideal_by_bias), BIAS_FRACTIONS))
        low_duration_widths_ns = (2.5, 4.0, 8.0, 16.0, 24.0, 32.0, 42.2657)
        low_duration_charge_v = []
        low_duration_r2r = None
        low_drive_fraction = None
        if variable_pulse_floor:
            for low_width in low_duration_widths_ns:
                width_tag = f"_w{low_width:g}n".replace(".", "p")
                path = RES / ("sky130_ms_first_event_clamp_ss_temp0_g0p4_geom0p5"
                              f"_tight_s0p1n{width_tag}_post20n_rise0p5n_banked_onlybefore_10ns.json")
                point = json.loads(path.read_text(encoding="utf-8"))
                if not point.get("simulation_completed"):
                    raise RuntimeError(f"invalid short-pulse transfer measurement: {path}")
                case = next(item for item in point["cases"] if item["case"] == "before_10ns")
                low_duration_charge_v.append(float(case["post_event_minus_no_event_uv"]) * 1e-6)
            r2r_report = next((json.loads(path.read_text(encoding="utf-8"))
                               for path in RES.glob("sky130_ms_static_bias_r2r_b12_event*.json")
                               if json.loads(path.read_text(encoding="utf-8")).get("simulation_completed")
                               and abs(json.loads(path.read_text(encoding="utf-8")).get("event_width_ns", 0) - low_duration_widths_ns[0]) < 0.001
                               and json.loads(path.read_text(encoding="utf-8")).get("gate_selection_slew_ns") == 0.5
                               and any(row["gate_fraction"] == 0.4 and row["injector_geometry_scale"] == 0.5
                                       for row in json.loads(path.read_text(encoding="utf-8")).get("event_transfer_rows", []))), None)
            if r2r_report is None:
                raise RuntimeError("missing short-pulse/0.5ns-edge R-2R correction for the low-pulse rail")
            r2r_row = next(row for row in r2r_report["event_transfer_rows"]
                           if row["gate_fraction"] == 0.4 and row["injector_geometry_scale"] == 0.5)
            low_duration_r2r = float(r2r_row["r2r_event_delta_uv"] / r2r_row["ideal_event_delta_uv"])
            low_duration_charge_v = [charge * low_duration_r2r for charge in low_duration_charge_v]
            low_base_curve = np.asarray([ideal_curve_by_fraction[f][0] for f in BIAS_FRACTIONS]) * 1e-6
            low_drive_fraction = float(np.interp(np.log(low_base_curve[0] * low_duration_r2r),
                                                 np.log(low_base_curve), BIAS_FRACTIONS))
        levels_uv = np.asarray([row[0] for row in discrete_library]) * 1e6
        floor_uv, ceiling_uv = float(levels_uv.min()), float(levels_uv.max())
        floor_v, ceiling_v = floor_uv * 1e-6, ceiling_uv * 1e-6
        for value in counts:
            requested_v = abs(value) * vpu
            if mapping == "stage_discrete_geometry":
                if requested_v < floor_uv * 1e-6:
                    mapped.append((value, 0.0, requested_v, 0.0, 0.0, 0.0))
                    continue
                selected_index = int(np.abs(levels_uv - requested_v * 1e6).argmin())
                level_v, fraction, geom_scale = discrete_library[selected_index]
                drive_fraction = effective_fraction[(geom_scale, fraction)]
                mapped.append((value, fraction, requested_v, geom_scale, drive_fraction, level_v))
                continue
            if layout_bank_duration_map and requested_v <= layout_duration_charge_v[-1]:
                if requested_v < layout_duration_charge_v[0]:
                    mapped.append((value, 0.0, requested_v, 0.0, 0.0, 0.0))
                else:
                    duration_ns = float(np.interp(requested_v, layout_duration_charge_v,
                                                  layout_duration_widths_ns))
                    mapped.append((value, 0.7, requested_v, 4.0, 0.7, requested_v,
                                   duration_ns, 2.0))
                continue
            if requested_v < floor_uv * 1e-6:
                if (mapping == "stage_continuous_geometry" and variable_pulse_floor and
                        requested_v >= low_duration_charge_v[0]):
                    low_width = float(np.interp(requested_v, low_duration_charge_v,
                                                low_duration_widths_ns))
                    mapped.append((value, BIAS_FRACTIONS[0], requested_v, GEOMETRIES[0],
                                   low_drive_fraction, requested_v, low_width, 0.5))
                    continue
                mapped.append((value, 0.0, requested_v, 0.0, 0.0, 0.0))
                continue
            candidates = []
            for geom_index, geom_scale in enumerate(GEOMETRIES):
                ideal_curve = np.asarray([ideal_curve_by_fraction[f][geom_index]
                                          for f in BIAS_FRACTIONS]) * 1e-6
                corrected_curve = np.asarray([curve_by_fraction[f][geom_index]
                                              for f in BIAS_FRACTIONS]) * 1e-6
                target = min(requested_v, float(corrected_curve[-1]))
                if corrected_curve[0] <= target <= corrected_curve[-1]:
                    target_fraction = float(np.interp(np.log(target), np.log(corrected_curve),
                                                      BIAS_FRACTIONS))
                    drive_fraction = float(np.interp(
                        target_fraction, BIAS_FRACTIONS,
                        [effective_fraction[(geom_scale, fraction)] for fraction in BIAS_FRACTIONS]))
                    candidates.append((abs(target_fraction - 0.675), geom_scale,
                                       target_fraction, drive_fraction, target))
            if candidates:
                _, geom_scale, fraction, drive_fraction, level_v = min(candidates)
            else:
                selected_index = int(np.abs(levels_uv - requested_v * 1e6).argmin())
                level_v, fraction, geom_scale = discrete_library[selected_index]
                drive_fraction = effective_fraction[(geom_scale, fraction)]
            mapped.append((value, fraction, requested_v, geom_scale, drive_fraction, level_v))
    elif mapping == "short_linear":
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
    if mapping not in ("stage_discrete_geometry", "stage_continuous_geometry"):
        fractions = np.array([row["gate_fraction"] for row in points])
        if not np.all(np.diff(delivered_v) > 0):
            raise RuntimeError("non-monotone charge transfer")
        floor_v, ceiling_v = float(delivered_v[0]), float(delivered_v[-1])
        for value in counts:
            requested_v = abs(value) * vpu
            if mapping == "stage_log":
                fraction = float(np.interp(np.log(max(requested_v, floor_v)), np.log(delivered_v), fractions))
            else:
                fraction = float(np.interp(requested_v, delivered_v, fractions))
            mapped.append((value, fraction, requested_v, 1.0, fraction, requested_v))
    ascending = sorted(mapped, key=lambda item: (item[0] > 0, abs(item[0])))
    shuffled = list(ascending)
    random.Random(140).shuffle(shuffled)
    sequences = {"forward": ascending, "reverse": list(reversed(ascending)), "shuffle": shuffled}
    if order_set != "all":
        sequences = {order_set: sequences[order_set]}
    if piecewise_first_range:
        for order, sequence in sequences.items():
            running = 0.0
            for item in sequence:
                running += item[0]
                if abs(running) > first_range_limit:
                    raise RuntimeError(f"{order} leaves the first piecewise range; use a state-aware map")
    event_width_ns = width_ns * event_width_scale
    event_period_ns = (float(event_period_override) if event_period_override
                       else width_ns + 10.0)
    if event_period_ns <= event_width_ns + 2.0:
        raise ValueError("event slot must exceed pulse width plus the 2ns gate fall edge")
    width_us = event_width_ns / 1000
    period_us = event_period_ns / 1000
    first_us = 3.0
    stop_us = first_us + (len(counts) - 1) * period_us + width_us + 0.5
    lines = [f"SKY130 {corner.upper()} {temperature_c}C first-touch full-float final-fusion weighted fan-in",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2 gmin=1e-12", f".temp {temperature_c}",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
             f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
             '.include "../../../asic/analog/modules.spice"',
             '.include "../../../asic/analog/sky130_ms_plif.spice"',
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    if mos_layout_state_cap:
        lines.append('.include "../layout/sky130_mos_gate_bank_100x10_nf10/mos_gate_bank_100x10_nf10.spice"')
    if per_synapse_devices:
        lines += ([".subckt diff_inject vp vn pp np pn nn en enb vdd vss params: geom=1 sw=1",
                  "Xp_pos vp_dev pp vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
                  "Xn_neg vn_dev nn vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
                  "Xp_neg vn_dev pn vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
                  "Xn_pos vp_dev np vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
                  "Xsw_p vp_dev vp en enb vdd vss transmission_gate_iso params: sw={sw}",
                  "Xsw_n vn_dev vn en enb vdd vss transmission_gate_iso params: sw={sw}",
                  ".ends diff_inject"] if isolate_inactive_synapses else [
                  ".subckt diff_inject vp vn pp np pn nn vdd vss params: geom=1",
                  "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
                  "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
                  "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
                  "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
                  ".ends diff_inject"])
        if isolate_inactive_synapses:
            lines += [".subckt transmission_gate_iso a b en enb vdd vss params: sw=1",
                      "Xn a en b vss sky130_fd_pr__nfet_01v8 w={sw} l=0.15",
                      "Xp a enb b vdd sky130_fd_pr__pfet_01v8 w={2*sw} l=0.15",
                      ".ends transmission_gate_iso"]
    else:
        lines.append(".subckt diff_inject vp vn " + " ".join(
            f"{pin}{i}" for i in range(len(GEOMETRIES)) for pin in ("pp", "np", "pn", "nn")) + " vdd vss")
        for i, geom_scale in enumerate(GEOMETRIES):
            lines += [f"Xp_pos{i} vp pp{i} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom_scale:g} l=10",
                      f"Xn_neg{i} vn nn{i} vss vss sky130_fd_pr__nfet_01v8 w={geom_scale:g} l=10",
                      f"Xp_neg{i} vn pn{i} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom_scale:g} l=10",
                      f"Xn_pos{i} vp np{i} vss vss sky130_fd_pr__nfet_01v8 w={geom_scale:g} l=10"]
        lines.append(".ends diff_inject")

    def wave(sequence: list[tuple[float, float, float, float, float, float]],
             sign: str, mos: str, geom_scale: float) -> str:
        off = 1.8 if mos == "p" else 0.0
        points = [(0.0, off)]
        ideal_state_v = 0.0
        for index, item in enumerate(sequence):
            value, fraction, requested_v, event_geom, drive_fraction, _ = item[:6]
            corrected_fraction = drive_fraction
            if measured_state_transfer_correction and event_geom in GEOMETRIES:
                state_for_curve = max(-0.031, min(0.031, ideal_state_v if value > 0 else -ideal_state_v))
                state_points = (-0.031, 0.0, 0.031)
                geom_index = GEOMETRIES.index(event_geom)
                state_curve = [np.interp(state_for_curve, state_points,
                                         [measured_state_maps[state][geom_index][bias_index]
                                          for state in state_points])
                               for bias_index in range(len(BIAS_FRACTIONS))]
                positive_indices = [i for i, transfer in enumerate(state_curve) if transfer > 0]
                if len(positive_indices) < 2:
                    raise RuntimeError(f"state transfer has fewer than two positive points at geometry {event_geom:g}")
                positive_curve = [state_curve[i] for i in positive_indices]
                positive_fractions = [BIAS_FRACTIONS[i] for i in positive_indices]
                if any(b <= a for a, b in zip(positive_curve, positive_curve[1:])):
                    raise RuntimeError(f"state transfer is non-monotone at geometry {event_geom:g}")
                bounded_target = min(max(requested_v, positive_curve[0]), positive_curve[-1])
                corrected_fraction = float(np.interp(np.log(bounded_target), np.log(positive_curve),
                                                     positive_fractions))
            if ideal_state_polarity_correction and ideal_state_v * value > 0:
                corrected_fraction += state_correction_slope * abs(ideal_state_v)
            ideal_state_v += (1 if value > 0 else -1) * requested_v
            if (value > 0) != (sign == "p") or event_geom != geom_scale:
                continue
            at = first_us + index * period_us
            active = 1.8 - corrected_fraction * 1.08 if mos == "p" else corrected_fraction * 0.6
            item_width_us = (item[6] if len(item) > 6 else event_width_ns) / 1000
            item_slew_us = (item[7] if len(item) > 7 else 2.0) / 1000
            points.extend(((at, off), (at + item_slew_us, active),
                           (at + item_width_us, active),
                           (at + item_width_us + item_slew_us, off)))
        points.append((stop_us, off))
        return "PWL(" + " ".join(f"{t:.12g}u {v:.12g}" for t, v in points) + ")"

    def event_envelope(sequence: list[tuple[float, float, float, float, float, float]],
                       sign: str, geom_scale: float, branch_name: str) -> str:
        points = [(0.0, 0.0)]
        if branch_name != "ref":
            for index, item in enumerate(sequence):
                value, _, _, event_geom, _, _ = item[:6]
                if (value > 0) != (sign == "p") or event_geom != geom_scale:
                    continue
                at = first_us + index * period_us
                item_width_us = (item[6] if len(item) > 6 else event_width_ns) / 1000
                item_slew_us = (item[7] if len(item) > 7 else 2.0) / 1000
                points.extend(((at, 0.0), (at + item_slew_us, 1.0),
                               (at + item_width_us, 1.0),
                               (at + item_width_us + item_slew_us, 0.0)))
        points.append((stop_us, 0.0))
        return "PWL(" + " ".join(f"{t:.12g}u {v:.12g}" for t, v in points) + ")"

    for name in ("ref", *sequences):
        sequence = sequences.get(name, [])
        if mos_layout_state_cap:
            lines += [f"Xmem_p_{name} vp_{name} vcm 0 mos_gate_bank_100x10_nf10",
                      f"Xmem_n_{name} vn_{name} vcm 0 mos_gate_bank_100x10_nf10"]
        elif mos_state_cap:
            lines += [f"Xmem_p_{name}_{finger} 0 vp_{name} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1"
                      for finger in range(10)]
            lines += [f"Xmem_n_{name}_{finger} 0 vn_{name} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1"
                      for finger in range(10)]
        else:
            lines += [f"Xmem_p_{name} vp_{name} vcm membrane_mim w_um=10 l_um=10",
                      f"Xmem_n_{name} vn_{name} vcm membrane_mim w_um=10 l_um=10"]
        lines += [f"Vcl_{name} cl_{name} 0 PWL(0 1.8 2.99u 1.8 2.991u 0 {stop_us:.12g}u 0)",
                  f"Vclb_{name} clb_{name} 0 PWL(0 0 2.99u 0 2.991u 1.8 {stop_us:.12g}u 1.8)",
                  f"Xcl_p_{name} vcm vp_{name} cl_{name} clb_{name} vdd 0 transmission_gate",
                  f"Xcl_n_{name} vcm vn_{name} cl_{name} clb_{name} vdd 0 transmission_gate"]
        if per_synapse_devices:
            for event_index, item in enumerate(sequence):
                value, _, _, geom_scale, drive_fraction, _ = item
                if geom_scale == 0:
                    continue
                at = first_us + event_index * period_us
                pins = []
                active_event = name != "ref" and value != 0
                for pin, sign, mos in (("pp", "p", "p"), ("np", "n", "n"),
                                       ("pn", "n", "p"), ("nn", "p", "n")):
                    node = f"{pin}e{event_index}_{name}"
                    off = 1.8 if mos == "p" else 0.0
                    if active_event and ((value > 0) == (sign == "p")):
                        active = 1.8 - drive_fraction * 1.08 if mos == "p" else drive_fraction * 0.6
                        signal = (f"PWL(0u {off:g} {at:.12g}u {off:g} "
                                  f"{at+0.002:.12g}u {active:.12g} "
                                  f"{at+width_us:.12g}u {active:.12g} "
                                  f"{at+width_us+0.002:.12g}u {off:g} {stop_us:.12g}u {off:g})")
                    else:
                        signal = f"{off:g}"
                    lines.append(f"V{node} {node} 0 {signal}")
                    pins.append(node)
                if isolate_inactive_synapses:
                    en = f"ene{event_index}_{name}"
                    enb = f"enbe{event_index}_{name}"
                    if active_event:
                        if isolation_precharge:
                            # Equalize the isolated drain to the live state before
                            # its MOS gate pulse; disconnect after the gate turns off.
                            en_signal = (f"PWL(0u 0 {at-0.004:.12g}u 0 {at-0.002:.12g}u 1.8 "
                                         f"{at+width_us+0.002:.12g}u 1.8 {at+width_us+0.004:.12g}u 0 {stop_us:.12g}u 0)")
                            enb_signal = (f"PWL(0u 1.8 {at-0.004:.12g}u 1.8 {at-0.002:.12g}u 0 "
                                          f"{at+width_us+0.002:.12g}u 0 {at+width_us+0.004:.12g}u 1.8 {stop_us:.12g}u 1.8)")
                        else:
                            en_signal = (f"PWL(0u 0 {at:.12g}u 0 {at+0.002:.12g}u 1.8 "
                                         f"{at+width_us:.12g}u 1.8 {at+width_us+0.002:.12g}u 0 {stop_us:.12g}u 0)")
                            enb_signal = (f"PWL(0u 1.8 {at:.12g}u 1.8 {at+0.002:.12g}u 0 "
                                          f"{at+width_us:.12g}u 0 {at+width_us+0.002:.12g}u 1.8 {stop_us:.12g}u 1.8)")
                    else:
                        en_signal, enb_signal = "0", "1.8"
                    lines += [f"V{en} {en} 0 {en_signal}", f"V{enb} {enb} 0 {enb_signal}"]
                    pins += [en, enb]
                instance_params = f"geom={geom_scale:g}"
                if isolate_inactive_synapses:
                    instance_params += f" sw={isolation_switch_scale:g}"
                lines.append(f"Xinj_{name}_{event_index} vp_{name} vn_{name} " +
                             " ".join(pins) + f" vdd 0 diff_inject params: {instance_params}")
        else:
            gate_nodes = []
            for geom_index, geom_scale in enumerate(GEOMETRIES):
                for pin, sign, mos in (("pp", "p", "p"), ("np", "n", "n"),
                                       ("pn", "n", "p"), ("nn", "p", "n")):
                    node = f"{pin}{geom_index}_{name}"
                    if physical_state_feedback:
                        base_node, env_node = f"{node}_base", f"{node}_env"
                        off = 1.8 if mos == "p" else 0.0
                        lines += [f"V{base_node} {base_node} 0 {wave(sequence, sign, mos, geom_scale)}",
                                  f"V{env_node} {env_node} 0 {event_envelope(sequence, sign, geom_scale, name)}"]
                        state_sign = "1" if sign == "p" else "-1"
                        state_term = (f"({state_sign})*(v(vp_{name})-v(vn_{name}))"
                                      if bidirectional_state_feedback else
                                      f"max(0,({state_sign})*(v(vp_{name})-v(vn_{name})))")
                        correction = f"{state_correction_slope:g}*{state_term}"
                        gate_expr = (f"v({base_node})-1.08*v({env_node})*({correction})" if mos == "p"
                                     else f"v({base_node})+0.6*v({env_node})*({correction})")
                        lines.append(f"B{node} {node} 0 V={{{gate_expr}}}")
                    else:
                        lines.append(f"V{node} {node} 0 {wave(sequence, sign, mos, geom_scale)}")
                    gate_nodes.append(node)
            lines.append(f"Xinj_{name} vp_{name} vn_{name} " + " ".join(gate_nodes) +
                         " vdd 0 diff_inject")
    saved_state_nodes = " ".join(
        signal for name in ("ref", *sequences)
        for signal in (f"v(vp_{name})", f"v(vn_{name})"))
    lines += [f".save {saved_state_nodes}", ".control", "set numdgt=15",
              f"tran {tran_max_step_ns:g}n {stop_us:.12g}u uic"]
    prefix_counts = ([*range(prefix_measure_step, len(counts) + 1, prefix_measure_step)]
                     if prefix_measure_step else [])
    if prefix_measure_step and (not prefix_counts or prefix_counts[-1] != len(counts)):
        prefix_counts.append(len(counts))
    for name in ("ref", *sequences):
        lines.append(f"let diff_{name}=v(vp_{name})-v(vn_{name})")
        for count in prefix_counts:
            at_us = first_us + (count - 1) * period_us + width_us + 0.005
            if at_us >= first_us + count * period_us and count < len(counts):
                raise RuntimeError("prefix measurement overlaps the next event")
            lines.append(f"meas tran prefix_{name}_{count} find diff_{name} at={at_us:.12g}u")
        lines.append(f"meas tran final_{name} find diff_{name} at={stop_us-0.1:.12g}u")
    lines += ["quit", ".endc", ".end"]
    stem = f"sky130_ms_first_touch_float_fanin_{corner}{temperature_c}"
    if map_corner != corner:
        stem += f"_map{map_corner}"
    if site != "max_fanin":
        stem += "_" + site
    if mapping != "short_linear":
        stem += "_" + mapping
    if abs(width_ns - stage_width_ns) > 0.001:
        stem += f"_mapw{width_ns:g}n".replace(".", "p")
    if banked_transfer_map:
        stem += "_bankedmap"
    if variable_pulse_floor:
        stem += "_durationfloor"
    if layout_bank_duration_map:
        stem += "_layoutduration"
    if piecewise_first_range:
        stem += "_piecewise1"
    if mos_state_cap:
        stem += "_mosstate"
    if mos_layout_state_cap:
        stem += "_layoutbank"
    if ideal_state_polarity_correction:
        stem += f"_statebiasideal_k{state_correction_slope:g}".replace(".", "p")
    if measured_state_transfer_correction:
        stem += "_statecal"
    if physical_state_feedback:
        stem += f"_statefb_k{state_correction_slope:g}".replace(".", "p")
    if bidirectional_state_feedback:
        stem += "_bidirectional"
    if prefix_measure_step:
        stem += f"_prefix{prefix_measure_step}"
    if per_synapse_devices:
        stem += "_per_synapse"
    if isolate_inactive_synapses:
        stem += "_isolated"
        if isolation_precharge:
            stem += "_precharge"
        if isolation_switch_scale != 1:
            stem += f"_sw{isolation_switch_scale:g}".replace(".", "p")
    if event_width_scale != 1:
        stem += f"_wscale{event_width_scale:g}".replace(".", "p")
    if abs(event_period_ns - (width_ns + 10.0)) > 0.001:
        stem += f"_slot{event_period_ns:g}n".replace(".", "p")
    if event_limit:
        stem += f"_n{event_limit}events"
    if order_set != "all":
        stem += f"_{order_set}only"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    chosen_current = (float(sum(counts)) if event_limit else
                      float(current.reshape(30, 16, 64, 64)[ni, oi, yy, xx]))
    ideal_table_sum = 0.0
    if mapping in ("stage_discrete_geometry", "stage_continuous_geometry"):
        if mapping == "stage_continuous_geometry":
            ideal_table_sum = float(sum((1 if item[0] > 0 else -1) * item[5]
                                        for item in mapped))
        else:
            ideal_table_sum = 0.0
    if mapping == "stage_discrete_geometry":
        for value, _, _, geom_scale, drive_fraction, _ in mapped:
            if geom_scale == 0 or value == 0:
                continue
            geom_index = GEOMETRIES.index(geom_scale)
            ideal_curve = np.asarray([ideal_curve_by_fraction[f][geom_index] for f in BIAS_FRACTIONS])
            if mapping == "stage_continuous_geometry":
                realized_uv = float(np.exp(np.interp(drive_fraction, BIAS_FRACTIONS,
                                                     np.log(ideal_curve))))
            else:
                realized_uv = float(np.interp(drive_fraction, BIAS_FRACTIONS, ideal_curve))
            ideal_table_sum += (1 if value > 0 else -1) * realized_uv * 1e-6
    elif mapping not in ("stage_discrete_geometry", "stage_continuous_geometry"):
        ideal_table_sum = float(sum((1 if item[0] > 0 else -1 if item[0] < 0 else 0) * item[5]
                                    for item in mapped))
    active_gate_fractions = [item[4] for item in mapped if item[3] > 0]
    metadata = {"test": "sky130_first_touch_full_float_fanin_deck",
                "checkpoint_sha256": expected, "qat_or_quantized_reference_used": False,
                "selected_flat_batch": int(ni), "selected_output_channel": int(oi),
                "selected_yx": [int(yy), int(xx)], "event_count": len(counts),
                "event_limit_applied": event_limit or None,
                "site_selection": site,
                "sum_folded_float_event_weights": float(sum(counts)),
                "mapped_discrete_event_sum_v": float(ideal_table_sum),
                "mapped_discrete_event_sum_error_v": float(
                    ideal_table_sum - sum(counts) * vpu),
                "mapped_discrete_event_count_below_floor": int(sum(item[3] == 0 for item in mapped)),
                "mapped_geometry_event_counts": {
                    str(geometry): int(sum(item[3] == geometry for item in mapped))
                    for geometry in GEOMETRIES if any(item[3] == geometry for item in mapped)
                },
                "mapped_positive_event_count": int(sum(item[0] > 0 for item in mapped)),
                "mapped_negative_event_count": int(sum(item[0] < 0 for item in mapped)),
                "mapped_event_commands": [
                    {"index": int(index), "weight_model_units": float(item[0]),
                     "requested_delta_v": float(item[2]), "geometry_factor": float(item[3]),
                     "target_gate_fraction": float(item[1]),
                     "zero_state_drive_gate_fraction": float(item[4]),
                     "zero_state_mapped_delta_v": float(item[5])}
                    for index, item in enumerate(mapped)
                ],
                "mapped_effective_gate_fraction_percentiles": {
                    str(percentile): (float(np.percentile(active_gate_fractions, percentile))
                                      if active_gate_fractions else None)
                    for percentile in (0, 10, 50, 90, 100)},
                "recorded_float_current_model_units": chosen_current,
                "volts_per_model_unit": vpu,
                "piecewise_first_range": piecewise_first_range,
                "piecewise_first_range_limit_model_units": first_range_limit,
                "ideal_state_polarity_correction": ideal_state_polarity_correction,
                "measured_state_transfer_correction": measured_state_transfer_correction,
                "physical_state_feedback": physical_state_feedback,
                "bidirectional_state_feedback": bidirectional_state_feedback,
                "state_correction_slope_per_volt": state_correction_slope if (ideal_state_polarity_correction or physical_state_feedback) else None,
                "prefix_measure_step": prefix_measure_step,
                "prefix_measure_counts": prefix_counts,
                "ideal_prefix_sums_v_by_order": {
                    name: {str(count): float(sum((1 if item[0] > 0 else -1) * item[2]
                                                  for item in sequence[:count]))
                           for count in prefix_counts}
                    for name, sequence in sequences.items()
                },
                "ideal_event_sum_v": float(sum(counts) * vpu),
                "ideal_recorded_current_v": chosen_current * vpu,
                "width_ns": event_width_ns, "transfer_map_width_ns": width_ns,
                "transient_max_step_ns": tran_max_step_ns,
                "stage_nominal_width_ns": stage_width_ns,
                "event_width_scale": event_width_scale, "period_ns": period_us * 1000,
                "banked_transfer_map": banked_transfer_map,
                "variable_pulse_floor": variable_pulse_floor,
                "layout_bank_duration_map": layout_bank_duration_map,
                "duration_encoded_event_count": sum(len(item) > 6 for item in mapped),
                "duration_encoded_min_width_ns": (min(item[6] for item in mapped if len(item) > 6)
                                                   if any(len(item) > 6 for item in mapped) else None),
                "duration_encoded_max_width_ns": (max(item[6] for item in mapped if len(item) > 6)
                                                   if any(len(item) > 6 for item in mapped) else None),
                "gate_mapping": mapping, "mos_corner": corner, "temperature_c": temperature_c,
                "device_architecture": ("one static MOS geometry per expanded event with an isolation transmission gate on each state connection" if isolate_inactive_synapses else "one static MOS geometry per expanded event, all event devices connected to the shared state pair" if per_synapse_devices else "shared 13-geometry bank connected to the shared state pair"),
                "state_cap_architecture": ("two replicated extracted-layout SKY130 ten-device NFET gate-cap banks sampled to VCM through physical TGs" if mos_layout_state_cap else "two banks of ten SKY130 10um/1um NFET gate capacitors sampled to VCM through physical TGs") if mos_state_cap else "two 10um x 10um MIM state capacitors sampled to VCM through physical TGs",
                "state_transfer_map_source": transfer_path.name if mos_state_cap else "SS/0C differential MIM injector transfer reports",
                "state_transfer_map_operating_point": ("0.9V common-mode, differential state corrected from -31/0/+31mV full-bank physical maps" if measured_state_transfer_correction else
                                                       "0.9V common-mode, zero differential initial state, full 13-geometry injector bank loaded" if mos_state_cap else
                                                       "0.9V MIM center with measured initial-state sweeps"),
                "state_feedback_mode": ("behavioral gate-bias sources read instantaneous simulated membrane differential" if physical_state_feedback else
                                        "offline ideal accumulated-state command" if ideal_state_polarity_correction else
                                        "none"),
                "isolation_precharge": isolation_precharge,
                "isolation_switch_scale": isolation_switch_scale if isolate_inactive_synapses else None,
                "gate_map_corner": map_corner,
                "event_orders": list(sequences),
                "requested_below_measured_floor_count": sum(item[3] == 0 for item in mapped),
                "requested_above_measured_ceiling_count": sum(item[2] > ceiling_v for item in mapped),
                "measured_floor_v_at_width": floor_v, "measured_ceiling_v_at_width": ceiling_v,
                "deck": deck.name,
                "scope": (f"One {site} final-fusion output from the original epoch58 float trace. Static folded weights and raw multiplicity expanded into events. The PDK {'extracted-layout replicated MOS gate state caps' if mos_layout_state_cap else 'MOS gate state caps' if mos_state_cap else 'MIM state caps'}, TG and MOS injector are simulated. " +
                ("The event geometry/bias map is measured on the MOS state banks with the full 13-geometry injector bank loaded at zero differential initial state; selected gate values and geometry interpolation are ideal controls, and no bias DAC is instantiated. "
                 if mos_state_cap else "12-bit R-2R event correction is represented by an effective ideal PWL gate command, not an instantiated ladder. ") +
                ("The requested voltage per model unit is the ideal eight-range piecewise map's first-segment slope, with an explicit trajectory guard; this is not a physical state encoder or an implementation of transitions to other segments. "
                 if piecewise_first_range else "") +
                ("An ideal event-by-event state estimate adds a measured one-geometry polarity gate-fraction correction 0.00193 per volt when an event pushes farther from VCM; no physical state sensor, feedback or calibration circuit is instantiated. "
                 if ideal_state_polarity_correction else "") +
                "Per-synapse mode allocates one device set per expanded event, so repeated weight multiplicities are not shared. No physical reference loop, noise, mismatch, beta/reset/adaptation, threshold/readout, full graph or extracted layout.")}
    (RES / f"{stem}_deck.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
