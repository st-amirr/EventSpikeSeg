"""Compare measured SKY130 pulse swing and width to full-float model ranges.

This is a scale-sensitivity and service-time screen, not a selected voltage
encoding or a transistor-level accuracy simulation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RESULTS = ROOT / "artifacts/analog_asic/results"
PARAMS = REF / "eventspikeseg140k_float_parameters.npz"
TRACE = REF / "float_patch_trace.json"
PULSE = RESULTS / "sky130_ms_pulse_width_operating_range.json"
SC = RESULTS / "sky130_sc_small_cap_geometry.json"
OUT = RESULTS / "sky130_float_pulse_mapping_screen.json"


def main() -> int:
    pulse = json.loads(PULSE.read_text(encoding="utf-8"))
    sc = json.loads(SC.read_text(encoding="utf-8"))
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    params = np.load(PARAMS)
    trace_archive = np.load(REF / trace["trace_archive"])
    vpos = abs(float(pulse["transfer_by_initial_state"]["0.9"]["positive"]["points"][-1]["signed_delta_v"]))
    vneg = abs(float(pulse["transfer_by_initial_state"]["0.9"]["negative"]["points"][-1]["signed_delta_v"]))
    minpos = abs(float(pulse["transfer_by_initial_state"]["0.9"]["positive"]["points"][0]["signed_delta_v"]))
    minneg = abs(float(pulse["transfer_by_initial_state"]["0.9"]["negative"]["points"][0]["signed_delta_v"]))
    max_logical_us = float(pulse["transfer_by_initial_state"]["0.9"]["positive"]["points"][-1]["logical_width_us"])
    pos_duration_multiplier = float(pulse["positive_duration_scale"])
    layers = []
    state_cap_mapping = []
    threshold_sensitivity = []
    cap_floor_replay = []
    trace_rows = {row["name"]: row for row in trace["sampled_stages"]}
    # Use same-phase no-event-subtracted transfer values, not the raw output
    # drift in the original packet bench.
    pos_case = next(case for case in sc["cases"] if float(case["packet_size_um"]) == 10.0 and case["polarity"] == "positive")
    neg_case = next(case for case in sc["cases"] if float(case["packet_size_um"]) == 10.0 and case["polarity"] == "negative")
    pos_per_area = abs(float(pos_case["state_change_v"])) / 100.0
    neg_per_area = abs(float(neg_case["state_change_v"])) / 100.0
    cap_delta_per_area_mean = (pos_per_area + neg_per_area) / 2.0
    cap_curve = {}
    for polarity in ("positive", "negative"):
        areas = []
        deltas = []
        for width_um in (1.0, 3.0, 10.0):
            points = [case for case in sc["cases"] if float(case["packet_size_um"]) == width_um and case["polarity"] == polarity]
            areas.append(width_um * width_um)
            deltas.append(float(np.mean([abs(float(case["state_change_v"])) for case in points])))
        slope, intercept = np.polyfit(areas, deltas, 1)
        cap_curve[polarity] = {"slope_v_per_um2": float(slope), "intercept_v": float(intercept),
                               "minimum_tested_packet_v": float(min(deltas)),
                               "measured_area_um2": areas, "measured_abs_packet_v": deltas}
    for key in params.files:
        if not key.startswith("weight__"):
            continue
        name = key.removeprefix("weight__")
        # The float-reference exporter stores the effective convolution
        # coefficient (raw conv weight already multiplied by ChannelAffine).
        # Do not fold affine_gain__* a second time here.
        w_tensor = torch.from_numpy(params[key].copy()).float()
        w = w_tensor.numpy().astype(np.float64).ravel()
        a = np.abs(w)
        max_abs = float(a.max())
        median_abs = float(np.median(a))
        p99_abs = float(np.percentile(a, 99))
        scale_max_fit = min(vpos, vneg) / max_abs
        pulse_floor_weights = np.where(w >= 0, minpos / scale_max_fit, minneg / scale_max_fit)
        threshold_key = "threshold__" + name
        threshold_median = float(np.median(params[threshold_key])) if threshold_key in params.files else None
        trace_key = "presynaptic_input__" + name.replace(".", "__")
        service = None
        trace_name = name.replace("__", ".")
        trace_name = trace_name.replace("final_fuse.standard", "final_fuse.standard")
        if trace_name in trace_rows and name in ("stem", "enc1__standard", "final_fuse__standard"):
            trace_row = trace_rows[trace_name]
            candidate = trace_row["candidate_before_threshold_and_reset"]
            candidate_max = max(abs(float(candidate["min"])), abs(float(candidate["max"])))
            margin = trace_row["candidate_minus_threshold_margin_model_units"]["abs_percentiles_0p1_1_10_50_90"]
            eff_abs = np.abs(w)
            weight_q = np.percentile(eff_abs, [0.1, 1, 50, 99, 100])
            threshold_med = float(np.median(params[threshold_key])) if threshold_key in params.files else None
            headroom_rows = []
            for swing in (0.15, 0.30, 0.60):
                v_per_unit = swing / candidate_max
                required_delta = weight_q * v_per_unit
                cap_width = np.sqrt(required_delta / cap_delta_per_area_mean)
                all_cap_width = np.sqrt(eff_abs * v_per_unit / cap_delta_per_area_mean)
                headroom_rows.append({
                    "observed_candidate_max_model_units": candidate_max,
                    "candidate_headroom_v": swing,
                    "volts_per_model_unit": v_per_unit,
                    "median_learned_threshold_voltage_v": threshold_med * v_per_unit if threshold_med is not None else None,
                    "abs_threshold_margin_q0p1_q1_model_units": [float(margin[0]), float(margin[1])],
                    "abs_threshold_margin_q0p1_q1_voltage": [float(margin[0] * v_per_unit), float(margin[1] * v_per_unit)],
                    "effective_abs_weight_quantiles_p0p1_p1_p50_p99_max": [float(v) for v in weight_q],
                    "required_square_mim_packet_width_um_p0p1_p1_p50_p99_max": [float(v) for v in cap_width],
                    "tested_min_packet_width_um": 1.0,
                    "required_square_mim_packet_width_um_p0p1_p1_p50_p99_max_by_sign": {
                        "positive_packet_input": [float(v) for v in np.sqrt(required_delta / pos_per_area)],
                        "negative_packet_input": [float(v) for v in np.sqrt(required_delta / neg_per_area)],
                    },
                    "fraction_of_static_coefficients_requiring_packet_width_below_3um": float(np.mean(all_cap_width < 3.0)),
                    "fraction_requiring_packet_width_below_1um": float(np.mean(all_cap_width < 1.0)),
                })
            state_cap_mapping.append({
                "layer": trace_name,
                "weight_count": int(w.size),
                "pdk_mim_output_delta_per_cap_area_at_0p3v_v_per_um2": {"positive_packet_input": pos_per_area, "negative_packet_input": neg_per_area, "mean_for_area_sizing": cap_delta_per_area_mean},
                "candidate_headroom_sensitivity": headroom_rows,
                "scope": "linear area extrapolation from 10um-square virtual-summing-node screen; per-layer candidate max from one bounded float trace; physical cap minimum, routing, parasitics, area sharing and matching not qualified",
            })
            candidate_arr = torch.from_numpy(trace_archive["candidate__" + name].copy()).float()
            threshold_arr = torch.from_numpy(trace_archive["threshold__" + name].copy()).float()
            reference_spikes = torch.from_numpy(trace_archive["spikes__" + name].copy()).bool()
            offset_rows = []
            for swing in (0.15, 0.30, 0.60):
                scale = swing / candidate_max
                for offset_uv in (0.1, 1.0, 10.0, 100.0):
                    offset_units = (offset_uv * 1e-6) / scale
                    positive_mismatch = float(((candidate_arr >= threshold_arr + offset_units) != reference_spikes).float().mean())
                    negative_mismatch = float(((candidate_arr >= threshold_arr - offset_units) != reference_spikes).float().mean())
                    offset_rows.append({
                        "candidate_headroom_v": swing,
                        "mapped_median_threshold_uv": threshold_med * scale * 1e6 if threshold_med is not None else None,
                        "uniform_threshold_offset_uv": offset_uv,
                        "threshold_shift_model_units": offset_units,
                        "spike_bit_mismatch_fraction_threshold_shift_positive_negative": [positive_mismatch, negative_mismatch],
                    })
            threshold_sensitivity.append({
                "layer": trace_name,
                "spike_bit_count": int(reference_spikes.numel()),
                "sensitivity": offset_rows,
                "scope": "software threshold perturbation on the recorded float candidate tensors; static uniform offset only, not OTA noise or mismatch simulation",
            })
        if trace_key in trace_archive.files:
            x = torch.from_numpy(trace_archive[trace_key].copy()).float().abs()
            shape = params[key].shape
            effective = torch.from_numpy(params[key].copy()).float()
            # Report a deliberately optimistic lane lower bound: all incoming
            # tap contributions for one destination neuron are serialized, but
            # independent output neurons operate in parallel. No setup time.
            max_coeff = float(effective.abs().max())
            logical_width = effective.abs() * (max_logical_us / max_coeff)
            physical_width = torch.where(effective >= 0, logical_width * pos_duration_multiplier, logical_width)
            total_us = F.conv2d(x, physical_width, padding=(shape[2] // 2, shape[3] // 2))
            active = total_us[total_us > 0].flatten().numpy()
            event_count_kernel = torch.ones_like(effective)
            incoming_count = F.conv2d(x, event_count_kernel, padding=(shape[2] // 2, shape[3] // 2))
            active_counts = incoming_count[incoming_count > 0].flatten().numpy()
            sc_cycle_us = 2.5  # bench action window from first initialization to packet disconnect
            service = {
                "trace_input_shape": list(x.shape),
                "active_destination_count": int(active.size),
                "serialized_input_pulse_service_us_p50_p90_p99_max": [float(v) for v in np.percentile(active, [50, 90, 99, 100])] if active.size else [0.0] * 4,
                "fraction_active_destinations_over_5ms": float(np.mean(active > 5000.0)) if active.size else 0.0,
                "p50_active_destinations_per_5ms_bin_at_this_single_lane_bound": float(5000.0 / np.median(active)) if active.size else None,
                "active_synaptic_contribution_count_p50_p90_p99_max": [float(v) for v in np.percentile(active_counts, [50, 90, 99, 100])] if active_counts.size else [0.0] * 4,
                "sc_integrator_optimistic_serial_service_us_p50_p90_p99_max": [float(v * sc_cycle_us) for v in np.percentile(active_counts, [50, 90, 99, 100])] if active_counts.size else [0.0] * 4,
                "sc_integrator_fraction_over_5ms_at_2p5us_per_contribution": float(np.mean(active_counts * sc_cycle_us > 5000.0)) if active_counts.size else 0.0,
                "sc_integrator_assumed_event_cycle_us": sc_cycle_us,
                "coverage": "30 patch-timesteps from three sampled 64x64 positions in one training frame; sum of absolute per-tap pulse durations for each active output destination, assuming output-neuron parallelism and serialized fan-in",
            }
            if name == "final_fuse__standard":
                candidate = trace_rows["final_fuse.standard"]["candidate_before_threshold_and_reset"]
                candidate_max = max(abs(float(candidate["min"])), abs(float(candidate["max"])))
                pulse_positive = pulse["transfer_by_initial_state"]["0.9"]["positive"]
                pulse_negative = pulse["transfer_by_initial_state"]["0.9"]["negative"]
                pulse_slope_pos = float(pulse_positive["gain_v_per_logical_us"][-1])
                pulse_slope_neg = float(pulse_negative["gain_v_per_logical_us"][-1])
                pulse_floor_pos = abs(float(pulse_positive["points"][0]["signed_delta_v"]))
                pulse_floor_neg = abs(float(pulse_negative["points"][0]["signed_delta_v"]))
                hybrid_rows = []
                for swing in (0.15, 0.30, 0.60):
                    vpu = swing / candidate_max
                    use_neg_packet = effective > 0
                    # Positive weights use negative-going packet input; negative weights use positive-going packet input.
                    floor_by_weight = torch.where(use_neg_packet,
                                                  float(cap_curve["negative"]["minimum_tested_packet_v"]),
                                                  float(cap_curve["positive"]["minimum_tested_packet_v"]))
                    below_floor = effective.abs() * vpu < floor_by_weight
                    desired_packet_v = effective.abs() * vpu
                    pulse_slope = torch.where(effective >= 0, pulse_slope_pos, pulse_slope_neg)
                    pulse_floor = torch.where(effective >= 0, pulse_floor_pos, pulse_floor_neg)
                    pulse_width_logical = desired_packet_v / pulse_slope
                    pulse_widths = torch.where(effective >= 0,
                                               pulse_width_logical * pos_duration_multiplier,
                                               pulse_width_logical)
                    pulse_fine_deliverable = desired_packet_v >= pulse_floor
                    pulse_fine_assigned = below_floor & pulse_fine_deliverable
                    fine_unrepresented = below_floor & ~pulse_fine_deliverable
                    tiny_pulse_width = torch.where(pulse_fine_assigned, pulse_widths, torch.zeros_like(pulse_widths))
                    small_pulse_us = F.conv2d(x, tiny_pulse_width, padding=(shape[2] // 2, shape[3] // 2))
                    large_event_count = F.conv2d(x, (~below_floor).float(), padding=(shape[2] // 2, shape[3] // 2))
                    hybrid_service = (small_pulse_us + large_event_count * sc_cycle_us).flatten()
                    active_hybrid = hybrid_service[hybrid_service > 0].numpy()
                    hybrid_rows.append({
                        "candidate_headroom_v": swing,
                        "fraction_static_coefficients_below_SC_floor": float(below_floor.float().mean()),
                        "fraction_static_coefficients_assigned_to_pulse_fine_path": float(pulse_fine_assigned.float().mean()),
                        "fraction_static_coefficients_still_unrepresented_below_both_floors": float(fine_unrepresented.float().mean()),
                        "hybrid_service_p50_p90_p99_max_us": [float(v) for v in np.percentile(active_hybrid, [50, 90, 99, 100])],
                        "fraction_active_destinations_over_5ms": float(np.mean(active_hybrid > 5000.0)),
                    })
                service["optimistic_SC_coarse_plus_pulse_fine_hybrid_screen"] = {
                    "cases": hybrid_rows,
                    "assumptions": "each above-floor contribution costs 2.5us; pulse fine path maps the same candidate-headroom voltage-per-model-unit as the SC mapping using measured sign-specific pulse slopes/minimum deltas; sub-floor coefficients below both pulse and capacitor floors remain unrepresented; output neurons parallel; no shared packet cap, arbitration, switching overhead, restore/ADC, settle or cross-path summing error",
                }
            if name == "final_fuse__standard":
                candidate_arr = torch.from_numpy(trace_archive["candidate__" + name].copy()).float()
                threshold_arr = torch.from_numpy(trace_archive["threshold__" + name].copy()).float()
                reference_spikes = torch.from_numpy(trace_archive["spikes__" + name].copy()).bool()
                reference_membrane = torch.from_numpy(trace_archive["membrane__" + name].copy()).float()
                beta = torch.from_numpy(params["beta__" + name].copy()).float().view(1, -1, 1, 1)
                x_seq = x.reshape(candidate_arr.shape[0], candidate_arr.shape[1], *x.shape[1:])
                replay_rows = []
                for swing in (0.15, 0.30, 0.60):
                    v_per_unit = swing / candidate_max
                    abs_eff = effective.abs()
                    required_v = abs_eff * v_per_unit
                    # Positive model weight must raise membrane voltage; this
                    # inverting charge amp therefore uses the negative packet input.
                    packet_polarity = torch.where(effective >= 0, 1.0, 0.0)
                    area_pos = (required_v - cap_curve["negative"]["intercept_v"]) / cap_curve["negative"]["slope_v_per_um2"]
                    area_neg = (required_v - cap_curve["positive"]["intercept_v"]) / cap_curve["positive"]["slope_v_per_um2"]
                    area = torch.where(packet_polarity > 0, area_pos, area_neg)
                    minimum_packet = torch.where(packet_polarity > 0,
                                                 cap_curve["negative"]["minimum_tested_packet_v"],
                                                 cap_curve["positive"]["minimum_tested_packet_v"])
                    representable = required_v >= minimum_packet
                    realized_v = torch.where(representable,
                                             torch.where(packet_polarity > 0,
                                                         cap_curve["negative"]["intercept_v"] + cap_curve["negative"]["slope_v_per_um2"] * area.clamp_min(1.0),
                                                         cap_curve["positive"]["intercept_v"] + cap_curve["positive"]["slope_v_per_um2"] * area.clamp_min(1.0)),
                                             0.0)
                    mapped_weight = torch.sign(effective) * (realized_v / v_per_unit)
                    mapped_current = F.conv2d(x, mapped_weight, padding=(shape[2] // 2, shape[3] // 2))
                    mapped_current = mapped_current.reshape_as(candidate_arr)
                    state = torch.zeros_like(reference_membrane[0])
                    mapped_spikes = []
                    mapped_states = []
                    for timestep in range(candidate_arr.shape[0]):
                        mapped_candidate = beta * state + mapped_current[timestep]
                        spikes_now = mapped_candidate >= threshold_arr[timestep]
                        state = mapped_candidate - spikes_now.to(mapped_candidate.dtype) * threshold_arr[timestep]
                        mapped_spikes.append(spikes_now)
                        mapped_states.append(state)
                    mapped_spike_array = torch.stack(mapped_spikes)
                    mapped_state_array = torch.stack(mapped_states)
                    current_error = mapped_current - torch.from_numpy(trace_archive["current__" + name].copy()).float()
                    state_error = mapped_state_array - reference_membrane
                    cap_width = torch.sqrt(area.clamp_min(0.0))
                    replay_rows.append({
                        "candidate_headroom_v": swing,
                        "volts_per_model_unit": v_per_unit,
                        "median_threshold_uv": float(torch.median(threshold_arr) * v_per_unit * 1e6),
                        "static_coefficients_zeroed_below_one_um_tested_cap": float((~representable).float().mean()),
                        "required_cap_width_um_median_and_max_among_retained": [float(torch.median(cap_width[representable])), float(cap_width[representable].max())],
                        "mapped_current_abs_error_model_units_p50_p90_p99": [float(v) for v in torch.quantile(current_error.abs().flatten(), torch.tensor([0.5, 0.9, 0.99]))],
                        "mapped_membrane_abs_error_model_units_p50_p90_p99_max": [float(v) for v in [torch.quantile(state_error.abs().flatten(), 0.5), torch.quantile(state_error.abs().flatten(), 0.9), torch.quantile(state_error.abs().flatten(), 0.99), state_error.abs().max()]],
                        "spike_bit_mismatch_fraction_vs_float_trace": float((mapped_spike_array != reference_spikes).float().mean()),
                        "reference_mapped_spike_rate": [float(reference_spikes.float().mean()), float(mapped_spike_array.float().mean())],
                    })
                cap_floor_replay.append({
                    "layer": trace_name,
                    "cap_area_curve": cap_curve,
                    "candidate_headroom_replay": replay_rows,
                    "scope": "final-fusion current/spike replay for three real 64x64 DSEC patches using measured 1/3/10um cap-area fit; coefficients needing less than the measured 1um packet are explicitly dropped; no training, task metric, mismatch/noise, physical layout or QAT",
                })
        layers.append({
            "layer": name,
            "weight_count": int(w.size),
            "abs_weight_p50_p99_max_model_units": [median_abs, p99_abs, max_abs],
            "linear_slope_voltage_per_logical_us_v": [vpos / max_logical_us, vneg / max_logical_us],
            "max_weight_fit_scale_v_per_model_unit": scale_max_fit,
            "threshold_median_model_units": threshold_median,
            "threshold_median_voltage_at_max_weight_fit_v": scale_max_fit * threshold_median if threshold_median is not None else None,
            "min_measured_pulse_equivalent_model_units_at_max_weight_fit": min(minpos, minneg) / scale_max_fit,
            "fraction_static_coefficients_below_measured_minimum_pulse_by_sign": {
                "all": float(np.mean(a < pulse_floor_weights)),
                "positive_weights": float(np.mean((w >= 0) & (a < pulse_floor_weights))),
                "negative_weights": float(np.mean((w < 0) & (a < pulse_floor_weights))),
            },
            "linear_logical_width_us_for_abs_weight_p50_p99_max": [median_abs / max_abs * max_logical_us, p99_abs / max_abs * max_logical_us, max_logical_us],
            "sampled_trace_service_screen": service,
            "physical_duration_us_max_weight_positive_negative": [max_logical_us * pos_duration_multiplier, max_logical_us],
            "serial_p50_contributions_per_5ms_bin_before_setup": [
                5000.0 / (median_abs / max_abs * max_logical_us * pos_duration_multiplier),
                5000.0 / (median_abs / max_abs * max_logical_us),
            ],
            "warning": "per-layer scale fits the largest static weight to the tested maximum pulse; linearized from four TT points and ignores pulse setup, fanout contention, state dependence, beta/reset, affine offset, and extracted variation",
        })
    out = {
        "test": "sky130_full_float_weight_to_pulse_range_scale_sensitivity",
        "checkpoint_sha256": trace["checkpoint_sha256"],
        "float_path": True,
        "qat_or_quantized_reference_used": False,
        "measured_tt_pulse": {
            "initial_membrane_v": 0.9,
            "minimum_positive_negative_delta_v": [minpos, minneg],
            "maximum_positive_negative_delta_v": [vpos, vneg],
            "maximum_logical_width_us": max_logical_us,
            "maximum_physical_positive_width_us": max_logical_us * pos_duration_multiplier,
            "update_bin_budget_us": float(pulse["update_bin_budget_us"]),
        },
        "trace_current_abs_p99_model_units": {row["name"]: row["current"]["abs_p50_p90_p99_p999"][2] for row in trace["sampled_stages"]},
        "per_layer_sensitivity": layers,
        "switched_capacitor_float_weight_mapping_sensitivity": state_cap_mapping,
        "float_spike_sensitivity_to_analog_threshold_offset": threshold_sensitivity,
        "measured_mim_cap_floor_float_trace_replay": cap_floor_replay,
        "scope": "full-float weights with exported ChannelAffine gains folded, plus three sampled real-DSEC patch traces for stem, enc1.standard and final_fuse.standard. Pulse response is locally linearized from four 0.9V TT points and each layer scale fits its largest coefficient at the longest tested pulse. Service assumes parallel output neurons, serial fan-in and no setup; it is optimistic, does not replay PLIF voltage/spikes or assert an acceptable error/selected scale.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT), "layer_count": len(layers), "max_event_duration_us": out["measured_tt_pulse"]["maximum_physical_positive_width_us"], "per_layer": [{"layer": x["layer"], "scale": x["max_weight_fit_scale_v_per_model_unit"], "threshold_v": x["threshold_median_voltage_at_max_weight_fit_v"], "median_positive_event_us": x["linear_logical_width_us_for_abs_weight_p50_p99_max"][0] * pos_duration_multiplier} for x in layers]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
