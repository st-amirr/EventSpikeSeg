"""Summarize bounded SKY130 readout evidence without promoting unqualified screens."""
from __future__ import annotations
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"


def result(stem: str) -> dict:
    data = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
    if not data.get("simulation_completed"):
        raise RuntimeError(f"incomplete evidence: {stem}")
    return data


def by_delta(report: dict) -> dict[float, dict]:
    return {float(row.get("source_input_uv", row.get("input_differential_uv"))): row for row in report["measurements"]}


def replay(pattern: str) -> dict:
    paths = list(RES.glob(pattern))
    if len(paths) != 1:
        raise RuntimeError(f"expected one corrected float replay for {pattern}, got {len(paths)}")
    data = json.loads(paths[0].read_text(encoding="utf-8"))
    if not data.get("reset_noise_preserves_subtractive_state") or not data.get("full_frame"):
        raise RuntimeError(f"invalid replay semantics in {paths[0].name}")
    return data


def main() -> int:
    sampled = result("sky130_regenerative_comparator_clocked_eval100p0ns")
    held = result("sky130_regenerative_comparator_direct_mim_longinit")
    early = {delay: result(f"sky130_regenerative_comparator_direct_mim_{stem}") for delay, stem in ((-0.5, "isolated"), (0.5, "earlycut"), (1.0, "cut1ns"), (2.0, "cut2ns"), (3.0, "cut3ns"))}
    ac = result("sky130_regenerative_isolated_input_capacitance")
    cap = json.loads((RES / "sky130_cap_kTC_float_sensitivity.json").read_text(encoding="utf-8"))
    perturb = {current: result(f"sky130_regenerative_comparator_cut2ns_perturb{current if current != 40 else ''}") for current in (40, 80, 120, 160)}
    autozero_stem = "sky130_ms_diff_ota_autozero_th15p5_t500u_s2n_mostt_temp27_bn0p65_bp0p75_zero-pos06"
    autozero = {offset: result(autozero_stem + (f"_dinit{offset}uv".replace("-", "m") if offset else ""))
                for offset in (-20, 0, 20)}
    boundary_stem = autozero_stem.replace("zero-pos06", "zero-pos0601")
    autozero_boundary = {offset: result(boundary_stem + (f"_dinit{offset}uv".replace("-", "m") if offset else ""))
                         for offset in (-20, 0, 20)}
    replay_cases = {
        "zero_noise_record0": replay("*validation_0_reset_only_independent_pair_mim10um_full_all_neurons_n0uv_h0.9v_corrected_subtractive_reset.json"),
        "mim10um_record0": replay("*validation_0_reset_only_independent_pair_mim10um_full_all_neurons_n199.758uv_h0.9v_corrected_subtractive_reset.json"),
        "mim100um_record0": replay("*validation_0_reset_only_independent_pair_mim100um_full_all_neurons_n20.3132uv_h0.9v_corrected_subtractive_reset.json"),
        "mim100um_record1": replay("*validation_1_reset_only_independent_pair_mim100um_full_all_neurons_n20.3132uv_h0.9v_corrected_subtractive_reset.json"),
        "mim100um_init_only_record0": replay("*validation_0_init_only_independent_pair_mim100um_full_all_neurons_n20.3132uv_h0.9v_corrected_subtractive_reset.json"),
        "mim100um_init_only_record1": replay("*validation_1_init_only_independent_pair_mim100um_full_all_neurons_n20.3132uv_h0.9v_corrected_subtractive_reset.json"),
        "mim100um_first_event_record0": replay("*validation_0_first_event_independent_pair_mim100um_full_all_neurons_n20.3132uv_h0.9v_corrected_subtractive_reset.json"),
        "mim100um_first_event_record1": replay("*validation_1_first_event_independent_pair_mim100um_full_all_neurons_n20.3132uv_h0.9v_corrected_subtractive_reset.json"),
        "mim10um_first_event_record0": replay("*validation_0_first_event_independent_pair_mim10um_full_all_neurons_n199.758uv_h0.9v_corrected_subtractive_reset.json"),
        "mim10um_first_event_record1": replay("*validation_1_first_event_independent_pair_mim10um_full_all_neurons_n199.758uv_h0.9v_corrected_subtractive_reset.json"),
        "mim10um_first_event_record2": replay("*validation_2_first_event_independent_pair_mim10um_full_all_neurons_n199.758uv_h0.9v_corrected_subtractive_reset.json"),
        "mim10um_first_event_record3": replay("*validation_3_first_event_independent_pair_mim10um_full_all_neurons_n199.758uv_h0.9v_corrected_subtractive_reset.json"),
        "mim3um_first_event_record0": replay("*validation_0_first_event_independent_pair_mim3um_full_all_neurons_n639.121uv_h0.9v_corrected_subtractive_reset.json"),
        "mim3um_first_event_record1": replay("*validation_1_first_event_independent_pair_mim3um_full_all_neurons_n639.121uv_h0.9v_corrected_subtractive_reset.json"),
        "mim5um_first_event_record0": replay("*validation_0_first_event_independent_pair_mim5um_full_all_neurons_n392.397uv_h0.9v_corrected_subtractive_reset.json"),
        "mim5um_first_event_record1": replay("*validation_1_first_event_independent_pair_mim5um_full_all_neurons_n392.397uv_h0.9v_corrected_subtractive_reset.json"),
        "mim5um_single_cap_first_event_record0": replay("*validation_0_first_event_single_differential_cap_mim5um_full_all_neurons_n277.467uv_h0.9v_corrected_subtractive_reset.json"),
        "mim5um_single_cap_first_event_record1": replay("*validation_1_first_event_single_differential_cap_mim5um_full_all_neurons_n277.467uv_h0.9v_corrected_subtractive_reset.json"),
        "mim10um_single_cap_first_event_record0": replay("*validation_0_first_event_single_differential_cap_mim10um_full_all_neurons_n141.25uv_h0.9v_corrected_subtractive_reset.json"),
        "mim10um_single_cap_first_event_record1": replay("*validation_1_first_event_single_differential_cap_mim10um_full_all_neurons_n141.25uv_h0.9v_corrected_subtractive_reset.json"),
        "illustrative_3uv_record0": replay("*validation_0_reset_only_independent_pair_mim100um_full_all_neurons_n3uv_h0.9v_corrected_subtractive_reset.json"),
        "illustrative_3uv_record1": replay("*validation_1_reset_only_independent_pair_mim100um_full_all_neurons_n3uv_h0.9v_corrected_subtractive_reset.json"),
        "illustrative_1uv_record0": replay("*validation_0_reset_only_independent_pair_mim100um_full_all_neurons_n1uv_h0.9v_corrected_subtractive_reset.json"),
        "submicrovolt_record0": replay("*validation_0_reset_only_independent_pair_mim100um_full_all_neurons_n0.18uv_h0.9v_corrected_subtractive_reset.json"),
    }
    nonzero = [row for row in sampled["measurements"] if row["input_differential_uv"]]
    gate_f = min(ac["points"], key=lambda row: abs(row["frequency_hz"] - 1e6))["effective_capacitance_f"]
    state = next(row for row in cap["thermal_estimate"]["geometry_sweep"] if row["square_width_um"] == 100.0)
    count = cap["one_cap_per_PLIF_geometry_scenarios"]["logical_membrane_count"]
    c10 = cap["thermal_estimate"]["c10um_from_existing_report_f"]
    kt = 1.380649e-23 * 300
    records = []
    for delay, report in early.items():
        rows = report["measurements"]
        records.append({"read_switch_open_relative_to_eval_ns": delay, "all_nonzero_decisions_correct_nominal": all(row["decision_matches_preeval_state"] for row in rows if row["source_input_uv"]), "maximum_abs_state_disturbance_uv": max(abs(row["read_state_disturbance_uv"]) for row in rows), "state_disturbance_at_plus3uv_uv": by_delta(report)[3.0]["read_state_disturbance_uv"]})
    stress = []
    for current, report in perturb.items():
        r = by_delta(report)
        stress.append({"opposing_current_pulse_na": current, "observed_opposing_input_shift_mv_at_plus3uv": -r[3.0]["points"]["2602.3"]["latch_input_diff_uv"] / 1000, "plus_minus_3uv_decisions_correct": all(r[d]["decision_matches_preeval_state"] for d in (-3.0, 3.0)), "plus_minus_6uv_decisions_correct": all(r[d]["decision_matches_preeval_state"] for d in (-6.0, 6.0))})
    replay_summary = {}
    for name, case in replay_cases.items():
        replay_summary[name] = {"record_index": case["record_index"], "noise_sigma_uv": case["pair_kTC_sigma_uv"], "baseline_labeled_accuracy": case["baseline_labeled_pixel_accuracy"], "mean_labeled_accuracy": statistics.mean(trial["labeled_pixel_accuracy"] for trial in case["trials"]), "mean_pixel_agreement_with_float": statistics.mean(trial["segmentation_pixel_argmax_agreement"] for trial in case["trials"]), "mean_final_fuse_spike_mismatch": statistics.mean(trial["final_fuse_spike_mismatch"] for trial in case["trials"])}
        if "baseline_present_class_mean_iou" in case:
            replay_summary[name]["baseline_present_class_mean_iou"] = case["baseline_present_class_mean_iou"]
            replay_summary[name]["mean_present_class_mean_iou"] = statistics.mean(
                trial["present_class_mean_iou"] for trial in case["trials"])
        if case.get("noise_mode") == "first-event":
            replay_summary[name]["mean_first_event_touched_fraction"] = statistics.mean(
                trial["first_event_touched_fraction"] for trial in case["trials"])
    slowest_nominal_decision_ns = max(row["first_correct_decision_delay_ns"] for row in nonzero)
    five_ms_service_channels = math.ceil(count * slowest_nominal_decision_ns * 1e-9 / 0.005)
    report = {"test": "sky130_analog_readout_architecture_evidence_gate", "source_results": ["sky130_regenerative_comparator_clocked_eval100p0ns", "sky130_regenerative_comparator_direct_mim_longinit", "sky130_regenerative_comparator_direct_mim_isolated", "sky130_regenerative_comparator_direct_mim_earlycut", "sky130_regenerative_comparator_direct_mim_cut1ns", "sky130_regenerative_comparator_direct_mim_cut2ns", "sky130_regenerative_comparator_direct_mim_cut3ns", "sky130_regenerative_isolated_input_capacitance", "sky130_cap_kTC_float_sensitivity", "sky130_regenerative_comparator_cut2ns_perturb", "sky130_regenerative_comparator_cut2ns_perturb80", "sky130_regenerative_comparator_cut2ns_perturb120", "sky130_regenerative_comparator_cut2ns_perturb160"], "nominal_clocked_sampler_all_signed_cases_correct": all(row["latch_polarity_matches_preedge_inputs"] for row in nonzero), "nominal_clocked_sampler_preedge_outputs_equal_within_uv": max(abs(row["preedge_output_diff_uv"]) for row in sampled["measurements"]), "held_direct_read_max_abs_state_disturbance_uv": max(abs(row["read_state_disturbance_uv"]) for row in held["measurements"]), "direct_read_cutoff_sweep": records, "post_cut_opposing_perturbation": stress, "corrected_float_replay_reset_noise": replay_summary, "legacy_reset_noise_replays_invalid_reason": "The earlier reset-only implementation replaced the subtractively reset membrane with pure noise even at zero sigma; corrected replays add noise to the original post-reset membrane and pass a full-frame zero-noise control.", "thermal_estimates_300k": {"10um_sample_cap_f": c10, "10um_sample_single_kTC_uv": math.sqrt(kt / c10) * 1e6, "10um_independent_pair_kTC_uv": math.sqrt(2 * kt / c10) * 1e6, "isolated_latch_input_cap_f_at_1mhz": gate_f, "isolated_input_single_kTC_uv_if_fully_sampled": math.sqrt(kt / gate_f) * 1e6, "isolated_input_independent_pair_kTC_uv_if_fully_sampled": math.sqrt(2 * kt / gate_f) * 1e6, "100um_state_cap_f": state["capacitance_f_area_scaled"], "100um_state_single_kTC_uv": state["single_cap_kTC_sigma_uv"], "100um_state_independent_pair_kTC_uv": state["independent_differential_pair_sigma_uv"]}, "one_100um_mim_per_logical_state_geometry": {"logical_state_count": count, "bare_mim_area_mm2": state["aggregate_area_mm2"], "excludes_routing_and_helpers": True}, "readout_noise_qualified": False, "state_storage_qualified": False, "full_analog_architecture_ready": False, "interpretation": "Clock gating and early read isolation fix the nominal latch timing/state-kick screens. A 10um sample pair and the isolated input node have much larger estimated kT/C than a 3uV example decision. Corrected full-float reset-noise replay loses substantial task accuracy at 10um and 100um on the sampled validation records. The 100um per-state MIM geometry is enormous across the 140k inventory. Post-cut perturbation is deterministic, not a noise yield. Retain the analog readout only as an exploration until credible switched noise, state storage, throughput, PVT/mismatch and dataset-level full-float replay close."}
    report["interpretation"] += " An ideal first-touch clamp substantially improves two-frame mean IoU at the 100um-pair noise proxy, but physical release must precede the weighted event, and first-touch noise/readout/throughput are unqualified."
    report["optimistic_shared_latch_service_bound"] = {
        "logical_state_count": count,
        "bin_seconds": 0.005,
        "nominal_slowest_signed_decision_ns": slowest_nominal_decision_ns,
        "minimum_parallel_channels_if_decision_time_were_entire_service": five_ms_service_channels,
        "illustrative_total_service_time_scenarios": [
            {"total_service_ns": service_ns,
             "minimum_parallel_channels": math.ceil(count * service_ns * 1e-9 / 0.005)}
            for service_ns in (10, 100, 1000, 10000)
        ],
        "excludes": ["sampling", "precharge", "state_restore", "reset_beta_adaptation", "graph_dependencies", "routing", "noise_and_mismatch_margin"],
        "qualified_throughput": False,
    }
    independent_pair_sigma_uv = state["independent_differential_pair_sigma_uv"]
    report["illustrative_reset_noise_correlation_requirement"] = {
        "state_cap_square_width_um": 100,
        "independent_pair_sigma_uv": independent_pair_sigma_uv,
        "bare_two_cap_per_state_area_mm2": 2 * state["aggregate_area_mm2"],
        "equal_single_cap_variances_assumed": True,
        "formula": "pair_sigma(rho) = independent_pair_sigma * sqrt(1-rho)",
        "target_examples_not_acceptance_limits": [
            {"illustrative_pair_sigma_uv": target_uv,
             "required_correlation_rho": 1 - (target_uv / independent_pair_sigma_uv) ** 2}
            for target_uv in (3.0, 1.0)
        ],
        "physical_correlation_measured": False,
        "interpretation": "Geometric matching does not correlate thermal reset noise. Any correlated-reset scheme must demonstrate the necessary covariance through its physical switching sequence; the target examples are not model-derived acceptance limits.",
    }
    report["correlated_state_geometry_tradeoff"] = [
        {
            "mim_square_width_um": row["square_width_um"],
            "independent_pair_sigma_uv": row["independent_differential_pair_sigma_uv"],
            "bare_two_cap_full_inventory_area_mm2": 2 * row["aggregate_area_mm2"],
            "illustrative_required_rho_for_3uv": max(0.0, 1 - (3.0 / row["independent_differential_pair_sigma_uv"]) ** 2),
            "illustrative_required_rho_for_1uv": max(0.0, 1 - (1.0 / row["independent_differential_pair_sigma_uv"]) ** 2),
        }
        for row in cap["thermal_estimate"]["geometry_sweep"]
    ]
    autozero_rows = []
    for offset, case in autozero.items():
        cases = {row["case"]: row for row in case["cases"]}
        zero = cases["zero"]
        event = cases["pos06"]
        autozero_rows.append({
            "applied_initial_differential_uv": offset,
            "measured_pre_event_state_differential_uv": zero["pre_diff_v"] * 1e6,
            "post_no_event_output_minus_held_mv": zero["post_sense_v"] * 1e3,
            "post_event_minus_no_event_state_uv": event["post_diff_relative_to_zero_v"] * 1e6,
            "post_event_minus_no_event_output_mv": event["post_sense_relative_to_zero_v"] * 1e3,
            "post_comparator_output_v": event["post_comp_v"],
            "at_400us_no_event_output_minus_held_mv": zero["end_sense_v"] * 1e3,
            "at_400us_event_minus_no_event_output_mv": event["end_sense_relative_to_zero_v"] * 1e3,
            "at_400us_event_comparator_output_v": event["end_comp_v"],
        })
    report["physical_autozero_initial_offset_screen"] = {
        "scope": "TT physical 20um MIM pair, per-case OTA and output-sample MIM, ideal bias/clock/threshold, one positive MOS event; deterministic initial offsets only, no noise or mismatch",
        "cases": autozero_rows,
        "no_event_output_span_mv": max(row["post_no_event_output_minus_held_mv"] for row in autozero_rows) - min(row["post_no_event_output_minus_held_mv"] for row in autozero_rows),
        "initial_offset_cancellation_qualified": False,
    }
    boundary_rows = []
    for offset, case in autozero_boundary.items():
        event = next(row for row in case["cases"] if row["case"] == "pos0601")
        boundary_rows.append({
            "applied_initial_differential_uv": offset,
            "event_minus_no_event_state_uv": event["post_diff_relative_to_zero_v"] * 1e6,
            "event_minus_no_event_output_at_400us_mv": event["end_sense_relative_to_zero_v"] * 1e3,
            "comparator_output_at_400us_v": event["end_comp_v"],
            "comparator_low_below_0p9v": event["end_comp_v"] < 0.9,
        })
    report["physical_autozero_near_threshold_initial_offset_screen"] = {
        "gate_fraction": 0.601,
        "ideal_second_ota_threshold_offset_mv": 15.5,
        "cases": boundary_rows,
        "all_initial_offsets_same_decision": len({row["comparator_low_below_0p9v"] for row in boundary_rows}) == 1,
        "scope": "Nominal TT deterministic offset sweep with physical 20um MIM/TGs and per-case OTA/output sample; no thermal noise, mismatch, calibrated threshold or extraction",
    }
    first_touch = result("sky130_ms_first_event_clamp_tt")
    report["physical_first_event_clamp_timing_screen"] = {
        "source_result": "sky130_ms_first_event_clamp_tt",
        "cases": first_touch["cases"],
        "first_touch_reference_noise_qualified": False,
        "first_touch_population_timing_qualified": False,
        "interpretation": "The deterministic 10um MIM/TG/MOS screen preserves the reference event charge when the clamp opens 0.2-10ns before the event; release at or after its beginning creates large erroneous retained charge. The replay assumes ideal first-touch gating and thermal noise not simulated by this circuit screen."
    }
    corner_reports = {name: result(f"sky130_ms_first_event_clamp_{name}") for name in
                      ("ff_temp0", "ff_temp85", "ss_temp0", "ss_temp85")}
    corner_rows = []
    for name, corner_report in corner_reports.items():
        by_case = {row["case"]: row for row in corner_report["cases"]}
        corner_rows.append({"case": name,
                            "reference_event_step_uv": by_case["reference"]["post_event_minus_no_event_uv"],
                            "early_release_0p2ns_step_uv": by_case["before_0p2ns"]["post_event_minus_no_event_uv"],
                            "at_event_step_uv": by_case["at_event"]["post_event_minus_no_event_uv"],
                            "late_release_1ns_step_uv": by_case["after_1ns"]["post_event_minus_no_event_uv"]})
    steps = [row["early_release_0p2ns_step_uv"] for row in corner_rows]
    report["physical_first_event_pvt_gate_transfer_screen"] = {
        "cases": corner_rows,
        "min_to_max_fixed_gate_step_ratio": max(steps) / min(steps),
        "same_weight_transfer_across_pvt_qualified": False,
        "scope": "Selected MOS SS/FF and 0/85C, typical passive MIM/R/C models; deterministic single event with fixed ideal gate amplitudes, no supply sweep, mismatch, thermal noise or calibration."
    }
    tuned_rows = []
    for stem in ("ss_temp0_g0p68", "ss_temp0_g0p687", "ss_temp0_g0p7",
                 "ff_temp85_g0p449", "ff_temp85_g0p45", "ff_temp85_g0p5"):
        tuned = result(f"sky130_ms_first_event_clamp_{stem}")
        early = next(row for row in tuned["cases"] if row["case"] == "before_0p2ns")
        tuned_rows.append({"case": stem, "gate_fraction": tuned["gate_fraction"],
                           "event_step_uv": early["post_event_minus_no_event_uv"]})
    report["physical_first_event_selected_gate_tuning_probe"] = {
        "cases": tuned_rows,
        "target_nominal_tt_event_step_uv": next(row for row in first_touch["cases"]
                                                 if row["case"] == "before_0p2ns")["post_event_minus_no_event_uv"],
        "physical_calibration_implemented": False,
        "interpretation": "Ideal corner-specific gate amplitudes can bring two extremes near the TT event step. This does not establish per-weight linearity, feasible on-chip sensing/trim, power, or accuracy under local mismatch."
    }
    tight_rows = []
    for label, zero_stem, low_stem in (
        ("tt_27c", "tt_tight", "tt_g0p4_tight"),
        ("ss_0c", "ss_temp0_tight", "ss_temp0_g0p4_tight"),
        ("ff_85c", "ff_temp85_tight", "ff_temp85_g0p4_tight"),
    ):
        high = result(f"sky130_ms_first_event_clamp_{zero_stem}")
        low = result(f"sky130_ms_first_event_clamp_{low_stem}")
        high_step = next(row for row in high["cases"] if row["case"] == "before_0p2ns")["post_event_minus_no_event_uv"]
        low_step = next(row for row in low["cases"] if row["case"] == "before_0p2ns")["post_event_minus_no_event_uv"]
        tight_rows.append({"corner_temperature": label, "gate_fraction_0p4_step_uv": low_step,
                           "gate_fraction_0p6_step_uv": high_step,
                           "low_to_high_step_ratio": low_step / high_step})
    report["physical_injector_two_point_tight_pvt_shape"] = {
        "cases": tight_rows,
        "normalized_shape_ratio_max_to_min": max(row["low_to_high_step_ratio"] for row in tight_rows) / min(row["low_to_high_step_ratio"] for row in tight_rows),
        "low_point_timestep_check_tt_uv": [next(row for row in result(f"sky130_ms_first_event_clamp_tt_g0p4_tight_{stem}")["cases"] if row["case"] == "before_0p2ns")["post_event_minus_no_event_uv"] for stem in ("s0p1n", "s0p05n")],
        "low_point_timestep_check_ss_uv": [next(row for row in result(f"sky130_ms_first_event_clamp_ss_temp0_g0p4_tight_{stem}")["cases"] if row["case"] == "before_0p2ns")["post_event_minus_no_event_uv"] for stem in ("s0p1n", "s0p05n")],
        "single_gain_trim_sufficient_for_curve": False,
        "scope": "Two selected gate fractions with stricter ngspice reltol/abstol/vntol, physical TG/MIM and ideal gate drivers. Timestep convergence checked at the low point for TT and SS. No complete weight curve, calibration circuit, mismatch, supply sweep or extraction."
    }
    report["first_touch_mim_area_noise_tradeoff"] = {
        "logical_state_count": count,
        "bare_two_cap_area_mm2_by_square_width_um": [
            {"square_width_um": width_um, "bare_area_mm2": 2 * count * width_um ** 2 / 1e6}
            for width_um in (3.0, 5.0, 10.0, 100.0)
        ],
        "layout_minimum_legal_width_checked": False,
        "interpretation": "First-touch replay improves initialization sensitivity, but shrinking the pair to 3um raises the kT/C proxy to 639uV and lowers mean IoU on both selected frames. Bare MIM area excludes switches and routing."
    }
    report["first_touch_ideal_single_cap_shared_reference_probe"] = {
        "bare_one_cap_all_state_area_mm2": [
            {"square_width_um": width_um, "bare_area_mm2": count * width_um ** 2 / 1e6}
            for width_um in (5.0, 10.0)
        ],
        "shared_reference_noise_and_distribution_measured": False,
        "physical_single_ended_readout_qualified": False,
        "interpretation": "The single-cap software proxy improves two-frame replay against independent pairs at the same width, but its ideal shared reference and huge bare area prevent architecture acceptance."
    }
    occupancy_rows = []
    for index in (0, 1):
        occupancy = json.loads((RES / f"sky130_float_membrane_occupancy_validation_{index}.json").read_text(encoding="utf-8"))
        if occupancy["checkpoint_sha256"] != "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7" or occupancy["logical_membrane_count"] != count:
            raise RuntimeError("invalid float occupancy reference")
        occupancy_rows.append({"record_index": index,
                               "nonzero_fraction_after_first_update": occupancy["per_update"][0]["nonzero_membrane_fraction"],
                               "nonzero_fraction_after_tenth_update": occupancy["per_update"][-1]["nonzero_membrane_fraction"],
                               "peak_nonzero_membranes": max(row["nonzero_membranes"] for row in occupancy["per_update"])})
    report["full_float_exact_nonzero_state_occupancy"] = {
        "source_results": ["sky130_float_membrane_occupancy_validation_0", "sky130_float_membrane_occupancy_validation_1"],
        "records": occupancy_rows,
        "sparse_analog_storage_qualified": False,
        "interpretation": "Exact-zero sparsity is too limited on these two full records to make a simple dynamically allocated analog store a clear area solution; adaptation state, addresses and routing are excluded."
    }
    pvt_curve = result("sky130_ms_first_event_pvt_transfer_curve_tight")
    weight_coverage = json.loads((RES / "sky130_ms_pvt_float_weight_charge_coverage.json").read_text(encoding="utf-8"))
    if weight_coverage["checkpoint_sha256"] != "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7":
        raise RuntimeError("unexpected float weight coverage checkpoint")
    static_weights = weight_coverage["stages"]
    total_plif_weights = sum(row["weight_count"] for row in static_weights)
    report["physical_injector_tight_curve_and_float_coverage"] = {
        "source_curve": "sky130_ms_first_event_pvt_transfer_curve_tight",
        "source_float_coverage": "sky130_ms_pvt_float_weight_charge_coverage",
        "tested_gate_fractions": [row["gate_fraction"] for row in pvt_curve["conditions"][0]["points"]],
        "common_charge_ranges_uv": weight_coverage["common_charge_ranges"],
        "plif_folded_float_static_weight_count": total_plif_weights,
        "fraction_all_plif_static_weights_in_common_0p1_to_0p95_range_at_fixed_10p5ns": sum(
            row["weight_count"] * row["range_coverage"][1]["inside_common_range_fraction"]
            for row in static_weights) / total_plif_weights,
        "illustrative_max_per_stage_width_ns_to_cover_static_max_at_ss": max(
            row["illustrative_worst_corner_width_ns_to_cover_max_weight"] for row in static_weights),
        "illustrative_largest_sampled_p99_serial_pulse_service_us": max(
            row["optimistic_serial_pulse_service_us_p99_max"][0] for row in static_weights),
        "illustrative_static_weights_below_scaled_low_floor_fraction": sum(
            row["weight_count"] * row["illustrative_static_weights_below_that_floor_fraction"]
            for row in static_weights) / total_plif_weights,
        "full_float_weight_encoding_qualified": False,
    }
    width_rows = []
    for width_ns in (10.5, 50, 100, 150, 300, 450):
        suffix = "" if width_ns == 10.5 else f"_w{width_ns:g}n"
        source = result(f"sky130_ms_first_event_clamp_ss_temp0_g0p95_tight_s0p1n{suffix}_onlyreference-before_0p2ns")
        early = next(row for row in source["cases"] if row["case"] == "before_0p2ns")
        width_rows.append({"width_ns": width_ns, "event_step_uv": early["post_event_minus_no_event_uv"]})
    baseline_width = width_rows[0]["event_step_uv"]
    for row in width_rows:
        row["relative_error_from_10p5ns_linear_extrapolation"] = row["event_step_uv"] / (
            baseline_width * row["width_ns"] / 10.5) - 1
    state_rows = []
    for state_v in (-0.9, -0.6, -0.3, 0.3, 0.6, 0.9):
        value_tag = f"{state_v:g}".replace("-", "m").replace(".", "p")
        source = result(f"sky130_ms_first_event_clamp_ss_temp0_g0p95_tight_s0p1n_w450n_d{value_tag}v_onlyreference-before_0p2ns")
        early = next(row for row in source["cases"] if row["case"] == "before_0p2ns")
        state_rows.append({"commanded_initial_differential_v": state_v,
                           "actual_no_event_differential_at_post_v": early["post_no_event_diff_uv"] * 1e-6,
                           "event_minus_no_event_step_uv": early["post_event_minus_no_event_uv"]})
    report["physical_long_pulse_state_dependence_screen"] = {
        "corner": "ss", "temperature_c": 0, "gate_fraction": 0.95,
        "pulse_width_sweep": width_rows,
        "initial_state_sweep_at_450ns": state_rows,
        "state_step_span_fraction_of_zero_state_step": (max(row["event_minus_no_event_step_uv"] for row in state_rows) - min(row["event_minus_no_event_step_uv"] for row in state_rows)) / width_rows[-1]["event_step_uv"],
        "scope": "Nominal schematic MIM/TG/MOS deterministic controls, tight solver. Positive event, one event per case; prepared nonzero states use physical TG and show their own initialization feedthrough. Event effect is simulator-subtracted from a matched no-event case. Negative polarity is separately checked in the sequence bench. No on-chip correction, actual weighted fan-in, noise or mismatch."
    }
    long_sequence = result("sky130_ms_first_touch_long_event_sequence_ss0")
    short_sequence = result("sky130_ms_first_touch_long_event_sequence_ss0_n10_w40n_p100n")
    final_trace = next(row for row in json.loads((ROOT / "artifacts/analog_asic/model_reference/float_patch_trace_all.json").read_text(encoding="utf-8"))["sampled_stages"] if row["name"] == "final_fuse.standard")
    final_scale = next(row for row in static_weights if row["stage"] == "final_fuse.standard")["volts_per_model_unit_at_0p9v_headroom"]
    final_min_threshold_uv = final_trace["effective_threshold"]["min"] * final_scale * 1e6
    report["physical_first_touch_repeated_signed_event_screen"] = {
        "long_450ns": {"source_result": "sky130_ms_first_touch_long_event_sequence_ss0",
                       "event_step_and_sequences": long_sequence["final_differential_change_from_no_event_mv"],
                       "same_sign_relative_error": long_sequence["same_sign_relative_error_vs_ten_isolated_events"],
                       "alternating_residual_mv": long_sequence["alternating_residual_mv"]},
        "short_40ns": {"source_result": "sky130_ms_first_touch_long_event_sequence_ss0_n10_w40n_p100n",
                      "event_step_and_sequences": short_sequence["final_differential_change_from_no_event_mv"],
                      "same_sign_relative_error": short_sequence["same_sign_relative_error_vs_ten_isolated_events"],
                      "alternating_residual_mv": short_sequence["alternating_residual_mv"]},
        "illustrative_final_fuse_min_threshold_uv_at_0p9v_headroom": final_min_threshold_uv,
        "scope": "Physical first-touch TG/MIM and positive/negative MOS branches at selected SS/0C; ten equal-magnitude events, ideal gate drivers, simulator no-event subtraction. Does not model actual float weight mixtures, adaptation, network task response, noise, mismatch or calibration."
    }
    fanin_stem = "sky130_ms_first_touch_float_fanin_ss0"
    fanin_cases = []
    for label, suffix in (("short_linear_max_fanin", ""),
                          ("stage_linear_max_fanin", "_stage_linear"),
                          ("stage_log_max_fanin", "_stage_log"),
                          ("stage_log_high_cancellation", "_high_cancellation_stage_log"),
                          ("stage_log_near_threshold_scale", "_near_threshold_scale_stage_log")):
        source = json.loads((RES / f"{fanin_stem}{suffix}.json").read_text(encoding="utf-8"))
        if not source["simulation_completed"] or source["checkpoint_sha256"] != "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7":
            raise RuntimeError("invalid physical full-float fan-in result")
        fanin_cases.append({"case": label, "source_result": f"{fanin_stem}{suffix}.json",
                            "event_count": source["event_count"],
                            "ideal_sum_v": source["ideal_event_sum_v"],
                            "physical_sum_v_by_order": source["physical_final_minus_reference_v"],
                            "relative_error_by_order": source["relative_error_by_order"],
                            "order_spread_v": source["max_order_spread_v"],
                            "below_measured_floor_count": source["requested_below_measured_floor_count"]})
    report["physical_first_touch_actual_float_fanin_screen"] = {
        "cases": fanin_cases, "corner": "ss", "temperature_c": 0,
        "fixed_final_fuse_pulse_width_ns": fanin_cases and source["width_ns"],
        "weight_mapping_qualified": False, "closed_loop_neuron_qualified": False,
        "scope": "Three selected final-fusion sites from the epoch58 full-float trace, physical 10um MIM/TG/MOS, ideal per-weight gate levels and first-touch clamp, deterministic ngspice. The maximum-fanin site also compares 10.5ns width scaling and linear versus log charge interpolation. No DAC resolution/calibration, switched noise, mismatch, retention, beta/reset/adaptation, threshold/readout, full graph or extraction."
    }
    pvt_cases = []
    for label, stem in (("ss_map_ss", "sky130_ms_first_touch_float_fanin_ss0_stage_log"),
                        ("tt_map_tt", "sky130_ms_first_touch_float_fanin_tt27_stage_log"),
                        ("ff_map_ff", "sky130_ms_first_touch_float_fanin_ff85_stage_log"),
                        ("tt_map_ss_forward", "sky130_ms_first_touch_float_fanin_tt27_mapss_stage_log_forwardonly"),
                        ("tt_map_ss_reverse", "sky130_ms_first_touch_float_fanin_tt27_mapss_stage_log_reverseonly"),
                        ("ff_map_ss", "sky130_ms_first_touch_float_fanin_ff85_mapss_stage_log")):
        row = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
        if not row["simulation_completed"] or row["event_count"] != 370:
            raise RuntimeError("invalid physical corner-map fan-in result")
        pvt_cases.append({"case": label, "source_result": f"{stem}.json",
                          "physical_sum_v_by_order": row["physical_final_minus_reference_v"],
                          "relative_error_by_order": row["relative_error_by_order"],
                          "order_spread_v": row["max_order_spread_v"]})
    report["physical_first_touch_weight_map_corner_screen"] = {
        "ideal_370_event_sum_v": pvt_cases and row["ideal_event_sum_v"],
        "cases": pvt_cases, "corner_specific_ideal_gate_maps_implemented_on_chip": False,
        "tt_map_ss_combined_run_completed": False,
        "tt_map_ss_combined_run_failure": "ngspice timestep collapse in shuffled circuit at 13.85us; separate forward and reverse decks completed",
        "scope": "Same 370 actual float events and fixed 40.253ns pulse at SS/0C, TT/27C and FF/85C. Each corner-specific curve is externally measured and ideal gate levels are supplied. Fixed SS gate settings on TT and FF show uncalibrated drift; FF sequence can saturate/switch sign. No physical calibration, local mismatch, noise, supply spread or extraction."
    }
    gate_hold = json.loads((RES / "sky130_ms_weight_gate_storage_boundary.json").read_text(encoding="utf-8"))
    if not gate_hold["simulation_completed"] or gate_hold["checkpoint_float_plif_weight_count"] != 143728:
        raise RuntimeError("invalid analog weight gate storage screen")
    report["physical_analog_weight_gate_storage_screen"] = {
        "source_result": "sky130_ms_weight_gate_storage_boundary.json",
        "direct_gate_mux": gate_hold["direct_gate_mux"],
        "steered_drain": gate_hold["steered_drain"],
        "physical_weight_store_qualified": False,
        "scope": gate_hold["scope"]
    }
    buffer_dc = json.loads((RES / "sky130_ms_weight_gate_unity_buffer_ss0.json").read_text(encoding="utf-8"))
    buffer_step = json.loads((RES / "sky130_ms_weight_gate_ota_buffer_settle_ss0_f0p8.json").read_text(encoding="utf-8"))
    if not buffer_dc["simulation_completed"] or not buffer_step["simulation_completed"]:
        raise RuntimeError("incomplete physical weight gate buffer screen")
    report["physical_analog_weight_gate_buffer_screen"] = {
        "dc_source_result": "sky130_ms_weight_gate_unity_buffer_ss0.json",
        "loaded_step_source_result": "sky130_ms_weight_gate_ota_buffer_settle_ss0_f0p8.json",
        "dc_follow_errors_mv": buffer_dc["rows"],
        "loaded_step_samples": buffer_step["rows"],
        "loaded_step_two_ota_supply_current_a_with_mos_drain_loads": buffer_step["supply_current_a"],
        "shared_buffer_service_and_calibration_qualified": False,
        "scope": "Existing transistor OTA at SS/0C with ideal biases. DC follower range and off-rail-to-weight transient under injector MOS gate loading. No sampled weight input, mux, event charge, thermal noise, mismatch, local calibration, extracted parasitics or full population throughput."
    }
    report["interpretation"] += " The fixed MOS gate event has a large selected-corner charge-transfer spread and needs physical compensation/calibration before full-float weight mapping."
    (RES / "sky130_readout_architecture_boundary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("nominal_clocked_sampler_all_signed_cases_correct", "held_direct_read_max_abs_state_disturbance_uv", "direct_read_cutoff_sweep", "post_cut_opposing_perturbation", "corrected_float_replay_reset_noise", "thermal_estimates_300k", "one_100um_mim_per_logical_state_geometry", "full_analog_architecture_ready")}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
