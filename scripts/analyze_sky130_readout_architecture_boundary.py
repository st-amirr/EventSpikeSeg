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
    bucket_base = "sky130_sc_integrator_many_events_n100_cp1_cm100_step0.3_ts20n_neutral_"
    bucket_cases = {name: result(bucket_base + name)
                    for name in ("p_train", "n_train", "mixed", "mixed_reverse")}
    bucket_bias = {offset: result(bucket_base + "mixed" + suffix)
                   for offset, suffix in ((0.1, "_nbias0p1mv"), (1.0, "_nbias1mv"))}
    bucket_startup = {
        "isolated_mixed": result(bucket_base + "mixed_init100u_fbstart1m"),
        "all_cases": result("sky130_sc_integrator_many_events_n100_cp1_cm100_step0.3_ts20n_neutral_init100u_fbstart1m"),
        "isolated_mixed_bias_0p1mv": result(bucket_base + "mixed_nbias0p1mv_init100u_fbstart1m"),
    }
    report["source_results"].extend(bucket_base + name for name in bucket_cases)
    report["source_results"].extend(bucket_base + "mixed" + suffix
                                    for suffix in ("_nbias0p1mv", "_nbias1mv"))
    report["source_results"].extend((bucket_base + "mixed_init100u_fbstart1m",
                                     "sky130_sc_integrator_many_events_n100_cp1_cm100_step0.3_ts20n_neutral_init100u_fbstart1m",
                                     bucket_base + "mixed_nbias0p1mv_init100u_fbstart1m"))
    report["continuous_ota_charge_bucket_neutral_reference_screen"] = {
        "positive_100_event_minus_neutral_mv": bucket_cases["p_train"]["read_state_difference_from_neutral_event_reference_mv"]["p_train"]["final"],
        "negative_100_event_minus_neutral_mv": bucket_cases["n_train"]["read_state_difference_from_neutral_event_reference_mv"]["n_train"]["final"],
        "balanced_100_event_minus_neutral_uv": {
            name: bucket_cases[name]["read_state_difference_from_neutral_event_reference_mv"][name]["final"] * 1000
            for name in ("mixed", "mixed_reverse")
        },
        "neutral_bias_offset_stress_uv": {
            str(offset): row["read_state_difference_from_neutral_event_reference_mv"]["mixed"]["final"] * 1000
            for offset, row in bucket_bias.items()
        },
        "physical_init_and_startup_feedback_mixed_minus_neutral_uv": {
            name: row["read_state_difference_from_neutral_event_reference_mv"]["mixed"]["final"] * 1000
            for name, row in bucket_startup.items()
        },
        "physical_init_and_startup_feedback_pre_event_mixed_offset_uv": {
            name: row["read_state_difference_from_neutral_event_reference_mv"]["mixed"]["pre"] * 1000
            for name, row in bucket_startup.items()
        },
        "startup_operating_point_qualified": False,
        "reference_matching_qualified": False,
        "state_storage_and_noise_qualified": False,
        "scope": "TT/27C 5ms nominal schematic, 100 fixed-amplitude events into continuously enabled single-ended OTAs and a separately switched zero-charge branch. A 100us physical VCM clamp plus switched 1Meg startup feedback does not make the mixed branch independent of deck composition. The branch bias offsets are deterministic voltage stresses, not statistical mismatch. No full-float weighted train, noise, state transfer, physical weight drive, beta/reset, extraction or population service."
    }
    weighted_latch = {}
    for label, tag in (("model_threshold", "0"), ("diagnostic_near_zero", "m4"),
                       ("diagnostic_positive", "m10")):
        stem = f"sky130_ms_weighted_threshold_latch_nearthr_shift{tag}uv"
        row = result(stem)
        if (not row["simulation_completed"] or row["event_count"] != 329 or
                row["qat_or_quantized_reference_used"] or
                not row["decision_matches_physical_preeval_state"]):
            raise RuntimeError(f"invalid weighted threshold latch result: {stem}")
        weighted_latch[label] = {
            "source_result": f"{stem}.json",
            "float_margin_uv": row["ideal_float_candidate_minus_threshold_uv"],
            "physical_preeval_margin_uv": row["preeval_state_minus_reference_uv"],
            "state_change_across_latch_window_uv_including_hold_drift": row["read_state_disturbance_uv"],
            "decision_matches_float": row["decision_matches_float"],
        }
        report["source_results"].append(stem)
    report["weighted_fanin_clocked_latch_screen"] = {
        "cases": weighted_latch,
        "independent_pair_kt_over_c_proxy_uv_rms_at_0c": row["independent_pair_kt_over_c_proxy_uv_rms_at_0c"],
        "physical_threshold_source_qualified": False,
        "readout_noise_qualified": False,
        "full_plif_feedback_qualified": False,
        "scope": "One 329-event original-float SS/0C shared-bank MOS/TG/10um-MIM sequence connected to a transistor latch. The model threshold is imposed by ideal differential startup levels. The near-zero and positive cases shift that threshold for sensitivity only, not model operation. Full-fanin analog gate levels emulate measured R-2R correction with ideal PWL; no physical ladder, thermal-noise transient, mismatch, beta/reset, full 5ms state evolution, extraction or layout."
    }
    def software_report(stem: str) -> dict:
        return json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
    range_boundary = software_report("sky130_float_dynamic_range_noise_boundary")
    if range_boundary["qat_or_quantized_reference_used"] or len(range_boundary["actors"]) != 25:
        raise RuntimeError("invalid float dynamic-range trace boundary")
    gain_cases = {}
    for record_index in (0, 1):
        noiseless_stem = (f"sky130_float_state_saturation_validation_{record_index}_"
                          "all_neurons_full_none_g32-64-100")
        noise_stems = (
            (f"sky130_float_state_saturation_validation_{record_index}_"
             f"all_neurons_full_reset_only_g{'1-4-10' if record_index == 0 else '1-4-10-32'}"),
            (f"sky130_float_state_saturation_validation_{record_index}_"
             f"all_neurons_full_reset_only_g{'32-64-100' if record_index == 0 else '64-100'}"),
        )
        noiseless = software_report(noiseless_stem)
        noisy = [software_report(stem) for stem in noise_stems]
        for row in (noiseless, *noisy):
            if (row["qat_or_quantized_reference_used"] or not row["full_frame"] or
                    row["record_index"] != record_index or row["scope"] != "all-neurons" or
                    row["checkpoint_sha256"] != range_boundary["checkpoint_sha256"]):
                raise RuntimeError("invalid full-float gain/noise replay")
        report["source_results"].extend((noiseless_stem, *noise_stems))
        gain_cases[str(record_index)] = {
            "baseline_present_class_mean_iou": noiseless["baseline_present_class_mean_iou"],
            "noiseless": {
                str(int(row["linear_gain_relative_to_max_fitting_range"])): {
                    "spike_mismatch": row["final_fuse_spike_mismatch"],
                    "pixel_agreement": row["segmentation_pixel_agreement_with_float"],
                    "present_class_mean_iou": row["present_class_mean_iou"],
                } for row in noiseless["trials"]
            },
            "independent_reset_noise": {
                str(gain): {
                    metric: sum(row[field] for row in rows) / len(rows)
                    for metric, field in (("mean_spike_mismatch", "final_fuse_spike_mismatch"),
                                          ("mean_pixel_agreement", "segmentation_pixel_agreement_with_float"),
                                          ("mean_present_class_mean_iou", "present_class_mean_iou"))
                }
                for gain in (1, 4, 10, 32, 64, 100)
                if (rows := [row for report_row in noisy for row in report_row["trials"]
                             if row["linear_gain_relative_to_max_fitting_range"] == gain])
            },
        }
    report["float_state_gain_noise_tradeoff"] = {
        "trace_boundary_source": "sky130_float_dynamic_range_noise_boundary.json",
        "final_fuse_trace_fraction_margin_below_10um_pair_noise_proxy": range_boundary["actors"]["final_fuse__standard"]["fraction_of_states_with_margin_below_independent_10um_pair_ktc_proxy"],
        "full_frame_cases": gain_cases,
        "simple_linear_gain_qualified": False,
        "physical_companded_or_split_range_store_qualified": False,
        "scope": "Two 440x640 full-float validation frames, 25 PLIF populations, original checkpoint, QAT disabled. Each actor's per-record maximum sets its ideal +/-0.9V baseline range. Candidate and post-reset membrane are clipped at higher linear gain. Three independent Gaussian 10um-pair reset-noise proxy seeds are added at initialization and after spikes. The per-record maxima make this an optimistic sensitivity screen, not a calibration recipe. Noise is not transistor transient noise; no physical nonlinear encoding, gain switching, local mismatch, measured injector scaling, timing or validation-set accuracy."
    }
    compander_cases = {}
    for record_index in (0, 1):
        prefix = (f"sky130_float_state_saturation_validation_{record_index}_"
                  "all_neurons_full_")
        stems = {
            "noiseless_100_to_1000": prefix + "none_g100-500-1000_asinh_ideal",
            "noiseless_5000_to_10000": prefix + "none_g5000-10000_asinh_ideal",
            "noise_100_to_1000": prefix + "reset_only_g100-500-1000_asinh_ideal",
            "noise_5000_to_10000": prefix + "reset_only_g5000-10000_asinh_ideal",
        }
        rows = {name: software_report(stem) for name, stem in stems.items()}
        for row in rows.values():
            if (row["encoding"] != "asinh-ideal" or row["record_index"] != record_index or
                    not row["full_frame"] or row["scope"] != "all-neurons" or
                    row["checkpoint_sha256"] != range_boundary["checkpoint_sha256"]):
                raise RuntimeError("invalid ideal companding replay")
        noiseless = rows["noiseless_100_to_1000"]["trials"] + rows["noiseless_5000_to_10000"]["trials"]
        if any(row["final_fuse_spike_mismatch"] != 0 or
               row["segmentation_pixel_agreement_with_float"] != 1 for row in noiseless):
            raise RuntimeError("ideal companding changed a zero-noise float result")
        noisy = rows["noise_100_to_1000"]["trials"] + rows["noise_5000_to_10000"]["trials"]
        compander_cases[str(record_index)] = {
            str(ratio): {
                "near_zero_voltage_gain_relative_to_linear": selected[0]["near_zero_voltage_gain_relative_to_linear"],
                "mean_spike_mismatch": statistics.mean(row["final_fuse_spike_mismatch"] for row in selected),
                "mean_pixel_agreement": statistics.mean(row["segmentation_pixel_agreement_with_float"] for row in selected),
                "mean_present_class_mean_iou": statistics.mean(row["present_class_mean_iou"] for row in selected),
            }
            for ratio in (100, 500, 1000, 5000, 10000)
            if (selected := [row for row in noisy
                            if row["linear_gain_relative_to_max_fitting_range"] == ratio])
        }
        report["source_results"].extend(stems.values())
    record0_asinh = software_report(
        "sky130_float_state_saturation_validation_0_all_neurons_full_none_g5000-10000_asinh_ideal")
    record0_max = record0_asinh["actor_max_absolute_candidate_model_units"]["final_fuse.standard"]
    asinh_scale = record0_max / 10000
    def illustrative_step(state: float) -> float:
        return (0.9 / math.asinh(10000) *
                (math.asinh((state + 1) / asinh_scale) - math.asinh(state / asinh_scale)))
    report["ideal_asinh_state_encoding_bound"] = {
        "full_frame_cases": compander_cases,
        "illustrative_final_fuse_record0_unit_event_at_ratio10000": {
            "state_model_units": (0, 1000),
            "delta_model_units": 1,
            "required_encoded_voltage_step_v": (illustrative_step(0), illustrative_step(1000)),
            "scope": "One illustrative +1 model-unit event; not an actual synaptic weight or measured circuit step."
        },
        "full_float_noise_qualified": False,
        "physical_encoding_and_update_implemented": False,
        "state_store_qualified": False,
        "scope": "Ideal per-record asinh state encoding V=0.9*asinh(m/(M/R))/asinh(R) with exact inverse and full-state range, across two full validation frames and 25 original-float PLIF actors. Independent Gaussian 10um-pair kT/C voltage noise is injected at initialization and after spikes, then exactly decoded; three seeds. This is an upper-bound software sensitivity, not a physical switched-capacitor, nonlinear injector, decoder, threshold, reset or state-store implementation. Per-record M is optimistic calibration; mismatch, transistor noise, current weight map, 5ms service and full validation are absent."
    }
    piecewise_cases = {}
    for record_index in (0, 1):
        prefix = (f"sky130_float_state_saturation_validation_{record_index}_"
                  "all_neurons_full_")
        control_stem = prefix + "none_g10000_piecewise8_ideal"
        noise_stem = prefix + "reset_only_g10000_piecewise8_ideal"
        control, noisy = software_report(control_stem), software_report(noise_stem)
        if (control["checkpoint_sha256"] != range_boundary["checkpoint_sha256"] or
                noisy["checkpoint_sha256"] != range_boundary["checkpoint_sha256"] or
                control["encoding"] != "piecewise-ideal" or
                noisy["encoding"] != "piecewise-ideal" or
                control["piecewise_segment_count"] != 8 or
                noisy["piecewise_segment_count"] != 8 or
                control["trials"][0]["final_fuse_spike_mismatch"] != 0 or
                control["trials"][0]["segmentation_pixel_agreement_with_float"] != 1 or
                len(noisy["trials"]) != 3):
            raise RuntimeError("invalid eight-range float replay")
        report["source_results"].extend((control_stem, noise_stem))
        piecewise_cases[str(record_index)] = {
            "near_zero_voltage_gain_relative_to_linear": noisy["trials"][0]["near_zero_voltage_gain_relative_to_linear"],
            "mean_spike_mismatch": statistics.mean(row["final_fuse_spike_mismatch"] for row in noisy["trials"]),
            "mean_pixel_agreement": statistics.mean(row["segmentation_pixel_agreement_with_float"] for row in noisy["trials"]),
            "mean_present_class_mean_iou": statistics.mean(row["present_class_mean_iou"] for row in noisy["trials"]),
        }
    piecewise_max = record0_asinh["actor_max_absolute_candidate_model_units"]["final_fuse.standard"]
    knots = [piecewise_max / 10000 * math.sinh(math.asinh(10000) * index / 8)
             for index in range(9)]
    slopes = [0.9 / 8 / (knots[index + 1] - knots[index]) for index in range(8)]
    required_last_cap_f = 207.6e-15 * slopes[0] / slopes[-1]
    required_last_cap_ff = required_last_cap_f * 1e15
    required_last_mim_side_um = (-0.76 + math.sqrt(0.76**2 + 8 * required_last_cap_ff)) / 4
    report["ideal_eight_range_state_encoding_bound"] = {
        "full_frame_cases": piecewise_cases,
        "illustrative_final_fuse_record0_positive_state_knots_model_units": knots,
        "illustrative_segment_slopes_v_per_model_unit": slopes,
        "first_to_last_segment_slope_ratio": slopes[0] / slopes[-1],
        "per_state_switched_capacitance_implementation_bound": {
            "fine_capacitance_per_side_f": 207.6e-15,
            "required_last_range_capacitance_per_side_f": required_last_cap_f,
            "required_last_range_square_mim_side_um_typical_model": required_last_mim_side_um,
            "all_30976000_states_bare_two_cap_area_m2":
                30976000 * 2 * required_last_mim_side_um**2 * 1e-12,
            "excludes_switches_routing_reference_and_peripherals": True,
            "full_range_per_state_capacitance_bank_selected": False,
            "interpretation": "If voltage slope is changed only by increasing local state capacitance while event charge per model unit stays fixed, the final range needs this capacitance. This is an architectural lower-bound scenario, not a measured layout. State-dependent event-charge scaling or shared active circuitry avoids this specific capacitor requirement but is unimplemented."
        },
        "physical_range_switching_and_charge_conservation_qualified": False,
        "scope": "Eight straight segments join equally spaced voltage samples of the ideal asinh curve at R10000. Exact encode/inverse and noiseless state-dependent updates are assumed; the same independent 10um-pair Gaussian voltage reset proxy uses three seeds on two full original-float frames. No physical gain-switch, carry, charge transfer, boundary-crossing signed event, beta/reset, mismatch, fixed calibration or 5ms service is implemented."
    }
    switch_cases = {}
    for name in ("matched_short", "vcm_short", "matched_5ms", "vcm_5ms",
                 "matched_crossing_short", "matched_crossing_5ms"):
        stem = f"sky130_piecewise_range_switch_{name}"
        row = result(stem)
        if row["long_hold"] != name.endswith("5ms"):
            raise RuntimeError(f"invalid range-switch duration: {stem}")
        switch_cases[name] = {
            "source_result": f"{stem}.json",
            "state_change_across_switch_window_uv": row["state_change_across_switch_measurement_window_uv"],
            "post_pulse_state_mv": row["measurements_v"]["after_pulse_event"] * 1000,
            "five_ms_event_difference_hold_loss_mv": row.get("event_difference_hold_change_mv_over_5ms"),
            "physical_final_minus_ideal_piecewise_mv": row.get("physical_final_minus_piecewise_ideal_mv"),
        }
        report["source_results"].append(stem)
    report["physical_piecewise_range_switch_screen"] = {
        "cases": switch_cases,
        "physical_matched_extension_precharge_implemented": False,
        "autonomous_range_detection_and_timing_implemented": False,
        "weighted_signed_event_across_both_directions_qualified": False,
        "five_ms_hold_qualified": False,
        "scope": "TT/27C two-branch SKY130 10um fine +13.3um extension differential MIM with physical TGs. A 100nA/50ns ideal current pulse is applied after range connection or while a manually timed range connection occurs 13ns into the pulse. Ideal voltage sources prepare the extension, so matched precharge is a best-case bound; VCM precharge is a charge-sharing negative control. The five-ms event-minus-no-event difference loses ~1.184mV. No physical precharge driver, range detector, reverse crossing, measured weighted MOS source, noise, mismatch, beta/reset, extracted layout or population service."
    }
    precharge_sensitivity = {}
    zero_crossing = result("sky130_piecewise_range_switch_matched_crossing_short")
    for label, tag in (("plus_0p1_mv", "0p1"), ("plus_1_mv", "1"),
                       ("minus_1_mv", "m1")):
        stem = f"sky130_piecewise_range_switch_matched_crossing_short_err{tag}mv"
        row = result(stem)
        precharge_sensitivity[label] = {
            "source_result": f"{stem}.json",
            "extension_differential_precharge_error_mv": row["extension_differential_precharge_error_mv"],
            "additional_final_state_error_mv_vs_zero_offset": (
                row["measurements_v"]["after_pulse_event"] -
                zero_crossing["measurements_v"]["after_pulse_event"]) * 1000,
        }
        report["source_results"].append(stem)
    report["physical_piecewise_range_switch_screen"]["boundary_reference_error_stress"] = precharge_sensitivity
    report["physical_piecewise_range_switch_screen"]["boundary_reference_is_fixed_per_segment_not_state_tracking"] = True
    actual_steps = json.loads((RES / "sky130_piecewise_actual_event_range_three_sites.json").read_text(encoding="utf-8"))
    if (actual_steps["checkpoint_sha256"] != range_boundary["checkpoint_sha256"] or
            actual_steps["qat_or_quantized_reference_used"] or
            actual_steps["piecewise_segment_count"] != 8 or
            actual_steps["piecewise_ratio"] != 10000 or
            set(actual_steps["sites"]) != {"near_threshold_scale", "high_cancellation", "max_fanin"}):
        raise RuntimeError("invalid actual-weight piecewise event demand")
    report["source_results"].append("sky130_piecewise_actual_event_range_three_sites")
    report["actual_float_weight_piecewise_event_demand"] = {
        name: {
            "event_count": site["event_count"],
            "orders": {order: {
                "largest_required_encoded_step_mv": row["required_absolute_encoded_step_mv_percentiles"]["100"],
                "events_above_measured_single_event_ceiling":
                    row["events_exceeding_measured_MOS_single_event_ceiling_count"],
                "events_below_measured_single_event_floor":
                    row["events_below_measured_MOS_single_event_floor_count"],
                "optimistic_equal_ceiling_extra_slots":
                    row["optimistic_minimum_equal_ceiling_extra_slots"],
                "optimistic_equal_ceiling_slot_time_us":
                    row["optimistic_minimum_equal_ceiling_slot_time_us"],
                "piecewise_range_or_zero_crossings": row["events_crossing_a_piecewise_range_or_zero_count"],
            } for order, row in site["orders"].items()},
        } for name, site in actual_steps["sites"].items()
    }
    report["actual_float_weight_piecewise_event_demand"]["scope"] = actual_steps["scope"]
    report["actual_float_weight_piecewise_event_demand"]["existing_MOS_bank_implements_encoded_update"] = False
    report["actual_float_weight_piecewise_event_demand"]["event_demand_qualified"] = False
    biased_step = result("sky130_ms_state_bias_step_ss0_geom4")
    if (biased_step["physical_case_count"] != 8 or
            biased_step["smaller_drive"]["physical_case_count"] != 4 or
            biased_step["repeated_smaller_drive"]["physical_case_count"] != 5 or
            biased_step["manual_polarity_gate_correction"]["physical_case_count"] != 6 or
            biased_step["mos_corner"] != "ss" or
            biased_step["temperature_c"] != 0):
        raise RuntimeError("invalid state-biased MOS event sweep")
    report["source_results"].append("sky130_ms_state_bias_step_ss0_geom4")
    report["physical_MOS_event_stored_state_sweep"] = {
        "minimum_absolute_step_mv": biased_step["minimum_absolute_step_mv"],
        "maximum_absolute_step_mv": biased_step["maximum_absolute_step_mv"],
        "max_to_min_absolute_step_ratio": biased_step["max_to_min_absolute_step_ratio"],
        "physical_case_count": biased_step["physical_case_count"],
        "smaller_drive_minimum_absolute_step_mv": biased_step["smaller_drive"]["minimum_absolute_step_mv"],
        "smaller_drive_maximum_absolute_step_mv": biased_step["smaller_drive"]["maximum_absolute_step_mv"],
        "smaller_drive_max_to_min_absolute_step_ratio":
            biased_step["smaller_drive"]["max_to_min_absolute_step_ratio"],
        "repeated_small_drive_bank_loaded_cases": [{
            "initial_differential_v": row["initial_differential_v"],
            "positive_negative_alternating_residual_mv":
                row["positive_negative_alternating_residual_mv"],
            "negative_positive_alternating_residual_mv":
                row["negative_positive_alternating_residual_mv"],
            "positive_negative_single_step_magnitude_difference_mv":
                row["positive_negative_single_step_magnitude_difference_mv"],
        } for row in biased_step["repeated_smaller_drive"]["cases"]],
        "manually_corrected_biased_state_max_alternating_residual_mv": {
            str(row["initial_differential_v"]): row["maximum_absolute_alternating_residual_after_mv"]
            for row in biased_step["manual_polarity_gate_correction"]["cases"]
            if row["strengthened_gate_fraction"] in (0.90058, 0.90116)
        },
        "physical_state_sensor_or_programmer_implemented": False,
        "state_dependent_companded_charge_control_implemented": False,
        "scope": biased_step["scope"],
    }
    first_range = json.loads((RES / "sky130_piecewise_first_range_physical_boundary.json").read_text(encoding="utf-8"))
    if (first_range["checkpoint_sha256"] != range_boundary["checkpoint_sha256"] or
            first_range["qat_or_quantized_reference_used"] or
            first_range["full_analog_architecture_ready"] or
            first_range["full_eight_range_physical_update_qualified"]):
        raise RuntimeError("invalid physical first-segment float fan-in evidence")
    report["source_results"].append("sky130_piecewise_first_range_physical_boundary")
    report["physical_piecewise_first_segment_float_fanin"] = {
        site: first_range[site] for site in
        ("near_threshold_scale", "high_cancellation",
         "high_cancellation_with_ideal_state_polarity_command")
    }
    report["physical_piecewise_first_segment_float_fanin"]["high_cancellation_50p253ns_slot_solver_failed"] = True
    report["physical_piecewise_first_segment_float_fanin"]["full_eight_range_update_qualified"] = False
    report["physical_piecewise_first_segment_float_fanin"]["scope"] = first_range["scope"]
    prefix = json.loads((RES / "sky130_piecewise_first_range_highcancel_prefix40.json").read_text(encoding="utf-8"))
    if (prefix["checkpoint_sha256"] != first_range["checkpoint_sha256"] or
            prefix["qat_or_quantized_reference_used"] or
            [row["event_count"] for row in prefix["rows"]] != [40, 80, 120, 160, 200, 240, 280, 320, 322]):
        raise RuntimeError("invalid physical high-cancellation prefix evidence")
    report["source_results"].append("sky130_piecewise_first_range_highcancel_prefix40")
    report["physical_piecewise_first_segment_float_fanin"]["high_cancellation_shuffle_prefix_errors_uv"] = {
        str(row["event_count"]): row["error_uv"] for row in prefix["rows"]
    }
    mos_store = json.loads((RES / "sky130_mos_state_cap_boundary.json").read_text(encoding="utf-8"))
    if (not mos_store["all_simulations_completed"] or
            mos_store["logical_state_count"] != 30_976_000 or
            [row["program_v"] for row in mos_store["results"]] != [0.6, 0.9, 1.2]):
        raise RuntimeError("invalid bounded MOS gate storage evidence")
    report["source_results"].append("sky130_mos_state_cap_boundary")
    report["physical_MOS_gate_state_cap_screen"] = {
        "results": mos_store["results"],
        "scope": mos_store["scope"],
        "dense_state_store_qualified": False,
        "five_ms_microvolt_hold_qualified": False,
        "noise_qualified": False,
    }
    refresh = json.loads((RES / "sky130_mos_refresh_service_boundary.json").read_text(encoding="utf-8"))
    decay = json.loads((RES / "sky130_mos_decay_prediction_boundary.json").read_text(encoding="utf-8"))
    if (refresh["logical_state_count"] != 30_976_000 or refresh["model_qualified"] or
            not decay["all_simulations_completed"] or
            [row["program_v"] for row in decay["rows"]] != [0.6, 0.75, 0.9, 1.05, 1.2]):
        raise RuntimeError("invalid MOS refresh/decay boundary evidence")
    report["source_results"].extend(("sky130_mos_refresh_service_boundary",
                                     "sky130_mos_decay_prediction_boundary"))
    report["physical_MOS_gate_state_cap_screen"]["conditional_refresh_service"] = {
        "rows": refresh["rows"], "scope": refresh["scope"]}
    report["physical_MOS_gate_state_cap_screen"]["nominal_decay_prediction"] = {
        "endpoint_fitted_tau_s": decay["endpoint_fitted_tau_s"],
        "intermediate_state_prediction_errors_uv": {
            str(row["program_v"]): row["two_endpoint_single_pole_prediction_errors_uv"]
            for row in decay["rows"] if row["program_v"] in (0.75, 1.05)},
        "scope": decay["scope"],
    }
    stack = json.loads((RES / "sky130_mos_stacked_isolation_boundary.json").read_text(encoding="utf-8"))
    switch_leak = json.loads((RES / "sky130_mos_switch_leakage_boundary.json").read_text(encoding="utf-8"))
    if (not stack["all_simulations_completed"] or not switch_leak["all_simulations_completed"] or
            [row["program_v"] for row in stack["results"]] != [0.6, 1.2] or
            [row["initial_state_v"] for row in switch_leak["results"]] != [0.6, 1.2]):
        raise RuntimeError("invalid MOS switch isolation evidence")
    report["source_results"].extend(("sky130_mos_stacked_isolation_boundary",
                                     "sky130_mos_switch_leakage_boundary"))
    report["physical_MOS_gate_state_cap_screen"]["stacked_switch_5ms"] = stack["results"]
    report["physical_MOS_gate_state_cap_screen"]["isolated_off_switch_5ms"] = switch_leak["results"]
    report["physical_MOS_gate_state_cap_screen"]["simple_stacked_TG_selected_for_layout"] = False
    hv_switch = json.loads((RES / "sky130_hv_switch_state_boundary.json").read_text(encoding="utf-8"))
    if (not hv_switch["all_simulations_completed"] or
            [row["program_v"] for row in hv_switch["results"]] != [0.6, 1.2]):
        raise RuntimeError("invalid public HV switch state evidence")
    report["source_results"].append("sky130_hv_switch_state_boundary")
    report["physical_MOS_gate_state_cap_screen"]["public_HV_switch_5ms"] = {
        "results": hv_switch["results"], "scope": hv_switch["scope"],
        "model_source": hv_switch["model_source"],
        "selected_for_layout": False,
    }
    fullrail = json.loads((RES / "sky130_mos_fullrail_hold_boundary.json").read_text(encoding="utf-8"))
    pvt_hold = json.loads((RES / "sky130_mos_pvt_hold_boundary.json").read_text(encoding="utf-8"))
    float_retention = json.loads((RES / "sky130_mos_retention_float_boundary.json").read_text(encoding="utf-8"))
    if (not fullrail["all_simulations_completed"] or
            not fullrail["measured_start_voltages_strictly_increasing"] or
            len(fullrail["rows"]) != 13 or
            not pvt_hold["all_simulations_completed"] or len(pvt_hold["results"]) != 9 or
            float_retention["checkpoint_sha256"] !=
            "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7" or
            float_retention["qat_or_quantized_reference_used"] or
            float_retention["analog_architecture_ready"] or
            len(float_retention["rows"]) != 2):
        raise RuntimeError("invalid full-rail MOS storage/float replay evidence")
    report["source_results"].extend(("sky130_mos_fullrail_hold_boundary",
                                     "sky130_mos_pvt_hold_boundary",
                                     "sky130_mos_retention_float_boundary"))
    report["physical_MOS_gate_state_cap_screen"]["fullrail_TT_5ms"] = {
        "rows": [{"program_v": row["program_v"],
                  "program_error_v": row["program_error_v"],
                  "hold_drift_v": row["hold_drift_v"]} for row in fullrail["rows"]],
        "scope": fullrail["scope"],
    }
    report["physical_MOS_gate_state_cap_screen"]["selected_PVT_5ms"] = pvt_hold["results"]
    report["physical_MOS_gate_state_cap_screen"]["original_float_replay"] = {
        "rows": float_retention["rows"], "scope": float_retention["scope"]}
    report["physical_MOS_gate_state_cap_screen"]["linear_state_cell_selected_for_layout"] = False
    report["physical_MOS_gate_state_cap_screen"]["piecewise_encoder_physically_qualified"] = False
    report["interpretation"] += " The fixed MOS gate event has a large selected-corner charge-transfer spread and needs physical compensation/calibration before full-float weight mapping."
    (RES / "sky130_readout_architecture_boundary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("nominal_clocked_sampler_all_signed_cases_correct", "held_direct_read_max_abs_state_disturbance_uv", "direct_read_cutoff_sweep", "post_cut_opposing_perturbation", "corrected_float_replay_reset_noise", "thermal_estimates_300k", "one_100um_mim_per_logical_state_geometry", "full_analog_architecture_ready")}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
