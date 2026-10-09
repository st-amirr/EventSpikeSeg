"""Map one actual float-weight fan-in through an ideal piecewise analog state curve."""
from __future__ import annotations

import bisect
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "artifacts/analog_asic/model_reference"
RES = ROOT / "artifacts/analog_asic/results"
SOURCES = {
    "near_threshold_scale": ("sky130_ms_first_touch_float_fanin_ss0_near_threshold_scale_stage_"
                             "continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly"),
    "high_cancellation": ("sky130_ms_first_touch_float_fanin_ss0_high_cancellation_stage_"
                          "continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n_shuffleonly"),
    "max_fanin": ("sky130_ms_first_touch_float_fanin_ss0_stage_"
                  "continuous_geometry_mapw42p2657n_bankedmap_durationfloor_slot50p253n"),
}


def main() -> int:
    meta = json.loads((REF / "float_patch_trace_all.json").read_text(encoding="utf-8"))
    frame = json.loads((RES / "sky130_float_state_saturation_validation_0_all_neurons_full_"
                        "none_g5000-10000_asinh_ideal.json").read_text(encoding="utf-8"))
    if (meta["qat_or_quantized_reference_used"] or
            meta["checkpoint_sha256"] != frame["checkpoint_sha256"]):
        raise RuntimeError("full-float trace, source deck and range reference differ")
    archive = np.load(REF / "float_patch_trace_all.npz")
    params = np.load(REF / "eventspikeseg140k_float_parameters.npz")
    inputs = archive["presynaptic_input__final_fuse__standard"]
    weights = params["weight__final_fuse__standard"]
    maximum = frame["actor_max_absolute_candidate_model_units"]["final_fuse.standard"]
    ratio = float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--range-gain=')), '10000'))
    segments = int(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--segments=')), '8'))
    if ratio < 1 or segments < 2 or segments > 32:
        raise ValueError('range gain must be >=1 and segment count must be 2..32')
    knots_m = [maximum / ratio * math.sinh(math.asinh(ratio) * i / segments)
               for i in range(segments + 1)]
    knots_v = [0.9 * i / segments for i in range(segments + 1)]
    def voltage(state: float) -> float:
        magnitude = min(abs(state), maximum)
        segment = min(bisect.bisect_right(knots_m, magnitude) - 1, segments - 1)
        interpolated = (knots_v[segment] +
                        (magnitude - knots_m[segment]) *
                        (knots_v[segment + 1] - knots_v[segment]) /
                        (knots_m[segment + 1] - knots_m[segment]))
        return math.copysign(interpolated, state)
    def inverse_voltage(encoded: float) -> float:
        magnitude = min(abs(encoded), 0.9)
        segment = min(bisect.bisect_right(knots_v, magnitude) - 1, segments - 1)
        interpolated = (knots_m[segment] +
                        (magnitude - knots_v[segment]) *
                        (knots_m[segment + 1] - knots_m[segment]) /
                        (knots_v[segment + 1] - knots_v[segment]))
        return math.copysign(interpolated, encoded)
    sites = {}
    for site_name, source_stem in SOURCES.items():
        source = json.loads((RES / f"{source_stem}_deck.json").read_text(encoding="utf-8"))
        if (source["qat_or_quantized_reference_used"] or
                source["checkpoint_sha256"] != meta["checkpoint_sha256"] or
                source["site_selection"] != site_name):
            raise RuntimeError(f"invalid full-float source: {site_name}")
        batch = source["selected_flat_batch"]
        output = source["selected_output_channel"]
        y, x = source["selected_yx"]
        events = []
        for input_channel in range(weights.shape[1]):
            for ky in range(weights.shape[2]):
                for kx in range(weights.shape[3]):
                    iy, ix = y + ky - 1, x + kx - 1
                    if 0 <= iy < inputs.shape[-2] and 0 <= ix < inputs.shape[-1]:
                        events.extend([float(weights[output, input_channel, ky, kx])] *
                                      int(inputs[batch, input_channel, iy, ix]))
        if (len(events) != source["event_count"] or
                abs(sum(events) - source["sum_folded_float_event_weights"]) > 1e-4):
            raise RuntimeError(f"could not reproduce physical deck float events: {site_name}")
        orders = {}
        ascending = sorted(events, key=lambda value: (value > 0, abs(value)))
        shuffled = list(ascending)
        random.Random(140).shuffle(shuffled)
        ceiling = float(source["measured_ceiling_v_at_width"])
        floor = float(source["measured_floor_v_at_width"])
        for name, sequence in (("forward", ascending), ("reverse", list(reversed(ascending))),
                               ("shuffle", shuffled)):
            state = 0.0
            magnitudes = []
            local_gain_errors = []
            above = []
            crossing_count = 0
            range_boundary_crossings = 0
            zero_crossings = 0
            local_gain_range_crossings = 0
            local_gain_zero_crossings = 0
            local_encoded_state = 0.0
            maximum_local_gain_error = 0.0
            maximum_state = 0.0
            for event_index, weight in enumerate(sequence):
                next_state = state + weight
                delta_v = voltage(next_state) - voltage(state)
                magnitudes.append(abs(delta_v))
                if abs(delta_v) > ceiling:
                    above.append({"event_index": event_index, "float_weight": weight,
                                  "state_before_model_units": state,
                                  "requested_encoded_step_v": delta_v})
                before_segment = min(bisect.bisect_right(knots_m, abs(state)) - 1, segments - 1)
                after_segment = min(bisect.bisect_right(knots_m, abs(next_state)) - 1, segments - 1)
                range_boundary_crossings += before_segment != after_segment
                zero_crossings += state * next_state < 0
                crossing_count += before_segment != after_segment or state * next_state < 0
                local_voltage_segment = min(bisect.bisect_right(knots_v, abs(local_encoded_state)) - 1,
                                            segments - 1)
                local_slope = ((knots_v[local_voltage_segment + 1] - knots_v[local_voltage_segment]) /
                               (knots_m[local_voltage_segment + 1] - knots_m[local_voltage_segment]))
                local_next_voltage = math.copysign(min(abs(local_encoded_state + local_slope * weight), 0.9),
                                                   local_encoded_state + local_slope * weight)
                local_next_model = inverse_voltage(local_next_voltage)
                local_model_segment = min(bisect.bisect_right(knots_m, abs(local_next_model)) - 1,
                                          segments - 1)
                local_gain_range_crossings += local_model_segment != local_voltage_segment
                local_gain_zero_crossings += local_encoded_state * local_next_voltage < 0
                local_error = local_next_voltage - voltage(next_state)
                local_gain_errors.append(local_error)
                maximum_local_gain_error = max(maximum_local_gain_error, abs(local_error))
                local_encoded_state = local_next_voltage
                state = next_state
                maximum_state = max(maximum_state, abs(state))
            orders[name] = {
            "event_count": len(sequence),
            "final_float_state_model_units": state,
            "final_encoded_voltage_mv": voltage(state) * 1e3,
            "maximum_absolute_intermediate_state_model_units": maximum_state,
            "required_absolute_encoded_step_mv_percentiles": {
                str(percentile): float(np.percentile(magnitudes, percentile) * 1e3)
                for percentile in (50, 90, 99, 100)
            },
            "events_exceeding_measured_MOS_single_event_ceiling_count": len(above),
            "events_exceeding_measured_MOS_single_event_ceiling_fraction": len(above) / len(sequence),
            "events_below_measured_MOS_single_event_floor_count":
                sum(step < floor for step in magnitudes),
            "optimistic_minimum_equal_ceiling_subpulse_count":
                sum(max(1, math.ceil(step / ceiling)) for step in magnitudes),
            "optimistic_minimum_equal_ceiling_extra_slots":
                sum(max(1, math.ceil(step / ceiling)) - 1 for step in magnitudes),
            "optimistic_minimum_equal_ceiling_slot_time_us":
                sum(max(1, math.ceil(step / ceiling)) for step in magnitudes) *
                float(source["period_ns"]) / 1000,
            "events_crossing_a_piecewise_range_or_zero_count": crossing_count,
            "events_crossing_a_piecewise_range_boundary_count": range_boundary_crossings,
            "events_crossing_zero_count": zero_crossings,
            "events_crossing_a_piecewise_range_with_one_pre_event_gain_count": local_gain_range_crossings,
            "events_crossing_zero_with_one_pre_event_gain_count": local_gain_zero_crossings,
            "one_gain_per_event_final_encoded_error_v": local_encoded_state - voltage(state),
            "one_gain_per_event_maximum_absolute_prefix_error_v": maximum_local_gain_error,
            "one_gain_per_event_prefix_error_v_percentiles": {
                str(percentile): float(np.percentile(np.abs(local_gain_errors), percentile))
                for percentile in (50, 90, 99, 100)
            },
            "largest_above_ceiling_events": sorted(above, key=lambda row: abs(row["requested_encoded_step_v"]),
                                                    reverse=True)[:5],
            }
        sites[site_name] = {"site": [0, batch, output, y, x], "source_deck": source["deck"],
                            "event_count": len(events), "sum_folded_float_event_weights": sum(events),
                            "measured_shared_bank_single_event_voltage_floor_v": floor,
                            "measured_shared_bank_single_event_voltage_ceiling_v": ceiling,
                            "orders": orders}
    report = {
        "test": "sky130_actual_float_events_ideal_piecewise_range_demand",
        "checkpoint_sha256": meta["checkpoint_sha256"],
        "qat_or_quantized_reference_used": False,
        "sites": sites,
        "piecewise_segment_count": segments,
        "piecewise_ratio": ratio,
        "final_fuse_per_record_maximum_model_units": maximum,
        "scope": "Actual signed float weights/multiplicities for three final-fuse sites. Alongside the exact ideal piecewise encoded update, a fixed-cap event-gain screen applies one pre-event segment slope for the whole weight pulse, reselecting the slope between events; voltage is decoded/re-encoded through the ideal piecewise map. Model state starts at zero and sums only current-bin weights; prior membrane, beta and threshold are absent. The floor and ceiling are measured SS/0C bank-loaded one-event voltage steps on a 10um MIM pair, not hard electrical impossibilities. Equal-ceiling subpulse count is only an arithmetic lower bound. No physical range detector, state-dependent driver, timing, noise, mismatch, hold, feedback or layout is included."
    }
    path = RES / ("sky130_piecewise_actual_event_range_three_sites.json" if ratio == 10000 and segments == 8 else
                  f"sky130_piecewise_actual_event_range_gain{ratio:g}_segments{segments}.json")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({site: {order: {key: value for key, value in row.items()
                                     if key != "largest_above_ceiling_events"}
                              for order, row in site_row["orders"].items()}
                      for site, site_row in sites.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
