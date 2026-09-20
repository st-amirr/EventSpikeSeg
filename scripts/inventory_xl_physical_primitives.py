#!/usr/bin/env python3
"""Write exact XL primitive counts and simple die-capacity scenarios."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_power_total(path: str) -> tuple[float, float, float, float]:
    text = (ROOT / path).read_text(encoding="utf-8")
    match = re.search(
        r"(?m)^Total\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+"
        r"([0-9.eE+-]+)\s+([0-9.eE+-]+)", text
    )
    if match is None:
        raise ValueError(f"no total power row in {path}")
    return tuple(float(value) for value in match.groups())


def main() -> int:
    model = read("artifacts/ASIC_XL/model_spec.yaml")
    catalog = read("artifacts/ASIC_XL/hard_hierarchy/hard_macro_catalog.json")
    preflight = read("artifacts/ASIC_XL/hard_hierarchy/macroized_assembly_preflight.json")
    estimate = read("artifacts/ASIC_XL/full_model_estimate/full_model_ppa_estimate.json")
    layers = [layer for layer in model["layers"] if layer.get("name") != "head.synapse"]

    ordinary_plifs = 0
    mechanism_plifs = 0
    adaptation_plifs = 0
    inhibition_plifs = 0
    ordinary_population_blocks = 0
    mechanism_population_blocks = 0
    synapse_term_lanes = 0
    per_actor = []
    for layer in layers:
        name = str(layer["name"])
        parameter_path = ROOT / "artifacts/ASIC_XL" / str(layer["parameter_file"])
        parameters = json.loads(parameter_path.read_text(encoding="utf-8"))
        adaptation = bool(parameters.get("threshold_adaptation_enabled", False))
        inhibition = bool(parameters.get("inhibition_enabled", False))
        mechanism = adaptation or inhibition
        height, width = (int(value) for value in layer["output_hw"])
        spatial = height * width
        plifs = int(layer["logical_membrane_states"])
        partition = catalog["actor_physical_partition_policy"]["actors"][name]
        terms = int(partition["synaptic_terms_per_output_location"])
        if mechanism:
            mechanism_plifs += plifs
            mechanism_population_blocks += spatial
        else:
            ordinary_plifs += plifs
            ordinary_population_blocks += spatial
        if adaptation:
            adaptation_plifs += plifs
        if inhibition:
            inhibition_plifs += plifs
        synapse_term_lanes += spatial * terms
        per_actor.append({
            "actor": name,
            "spatial_actor_macros": spatial,
            "plif_cells": plifs,
            "synapse_term_lanes": spatial * terms,
            "mechanism": mechanism,
            "adaptation": adaptation,
            "inhibition": inhibition,
        })

    measured = {}
    for item in json.loads((ROOT / "asic/xl_representative_ppa.yaml").read_text())["representative_actor_routes"]:
        report = read(str(item["report"]))
        measured[str(item["actor"])] = float(report["finish__design__instance__area"])
    readout_report = read(
        "artifacts/OpenROAD/logs/asap7/xl_hm_readout__out_2x2/hard_macro_exact/6_report.json"
    )
    measured["readout_2x2"] = float(readout_report["finish__design__instance__area"])
    plif_report = read(
        "artifacts/OpenROAD/logs/asap7/xl_primitive_plif_1_pnr_top/primitive_plif_1/6_report.json"
    )
    plif_manifest = read(
        "artifacts/ASIC_XL/primitive_characterization/ordinary_plif_1/activity_manifest.json"
    )
    plif_internal, plif_switching, plif_leakage, plif_total = read_power_total(
        "artifacts/ASIC_XL/primitive_characterization/ordinary_plif_1/activity_power.rpt"
    )
    plif_duration_s = float(plif_manifest["trace_duration_ns"]) * 1e-9
    plif_bins = int(plif_manifest["bins"])
    plif_dynamic_j_per_update = (
        (plif_internal + plif_switching) * plif_duration_s / plif_bins
    )
    plif_update_rate_hz = 10 * 20
    plif_area = float(plif_report["finish__design__instance__area"])
    measured["ordinary_plif_cell"] = plif_area
    ordinary_plif_characterization = {
        "route": "DRC-clean extracted ASAP7 layout",
        "standard_cell_area_um2": plif_area,
        "fmax_hz": float(plif_report["finish__timing__fmax"]),
        "setup_wns_ps": float(plif_report["finish__timing__setup__ws"]),
        "hold_wns_ps": float(plif_report["finish__timing__hold__ws"]),
        "activity_trace_bins": plif_bins,
        "activity_trace_cycles": int(plif_manifest["cycles"]),
        "activity_trace_duration_ns": float(plif_manifest["trace_duration_ns"]),
        "activity_power_w": plif_total,
        "dynamic_power_w_during_trace": plif_internal + plif_switching,
        "leakage_power_w": plif_leakage,
        "dynamic_energy_j_per_bin_update": plif_dynamic_j_per_update,
        "assumed_bin_update_rate_hz": plif_update_rate_hz,
        "full_ordinary_plif_dynamic_power_w": (
            plif_dynamic_j_per_update * plif_update_rate_hz * ordinary_plifs
        ),
        "full_ordinary_plif_leakage_power_w": plif_leakage * ordinary_plifs,
        "full_ordinary_plif_standard_cell_area_mm2": plif_area * ordinary_plifs / 1e6,
        "claim_limit": plif_manifest["claim_limit"],
    }
    conv_report = read(
        "artifacts/OpenROAD/logs/asap7/xl_primitive_conv9_pnr_top/primitive_conv9/6_report.json"
    )
    conv_manifest = read(
        "artifacts/ASIC_XL/primitive_characterization/convolution_synapse_9term/activity_manifest.json"
    )
    conv_internal, conv_switching, conv_leakage, conv_total = read_power_total(
        "artifacts/ASIC_XL/primitive_characterization/convolution_synapse_9term/activity_power.rpt"
    )
    conv_terms = int(conv_manifest["term_count"])
    conv_area = float(conv_report["finish__design__instance__area"])
    conv_sample_period_s = 5e-9
    conv_dynamic_j_per_term_evaluation = (
        (conv_internal + conv_switching) * conv_sample_period_s / conv_terms
    )
    measured["convolution_synapse_9term"] = conv_area
    convolution_characterization = {
        "route": "DRC-clean extracted ASAP7 layout",
        "term_count": conv_terms,
        "standard_cell_area_um2": conv_area,
        "standard_cell_area_um2_per_term": conv_area / conv_terms,
        "activity_samples": int(conv_manifest["samples"]),
        "activity_sample_period_ns": conv_sample_period_s * 1e9,
        "activity_power_w": conv_total,
        "dynamic_power_w_during_trace": conv_internal + conv_switching,
        "leakage_power_w": conv_leakage,
        "dynamic_energy_j_per_term_evaluation": conv_dynamic_j_per_term_evaluation,
        "leakage_power_w_per_term": conv_leakage / conv_terms,
        "assumed_bin_evaluation_rate_hz": plif_update_rate_hz,
        "full_synapse_term_dynamic_power_w": (
            conv_dynamic_j_per_term_evaluation * plif_update_rate_hz * synapse_term_lanes
        ),
        "full_synapse_term_leakage_power_w": (
            conv_leakage / conv_terms * synapse_term_lanes
        ),
        "full_synapse_term_standard_cell_area_mm2": (
            conv_area / conv_terms * synapse_term_lanes / 1e6
        ),
        "claim_limit": conv_manifest["claim_limit"],
    }

    utilization = 0.70
    die_areas = [100, 400, 800]
    capacity = {
        name: {
            str(die): math.floor(die * 1_000_000 * utilization / area)
            for die in die_areas
        }
        for name, area in measured.items()
    }
    central_area = float(estimate["provisional_estimate"]["central_standard_cell_area_mm2"])
    model_fit = {
        str(die): {
            "usable_area_mm2": die * utilization,
            "model_fraction": die * utilization / central_area,
            "equivalent_die_count": math.ceil(central_area / (die * utilization)),
        }
        for die in die_areas
    }

    result = {
        "schema_version": "1.0.0",
        "scope": "exact_native_xl_primitive_inventory_and_pre_floorplan_capacity",
        "exact_counts": {
            "actor_macro_instances_1x1": int(catalog["actor_physical_macro_instances"]),
            "resident_convolution_synapses_blocks": int(catalog["actor_physical_macro_instances"]),
            "resident_plif_population_blocks": ordinary_population_blocks,
            "resident_retinotopic_plif_population_blocks": mechanism_population_blocks,
            "retinotopic_mechanism_update_blocks": mechanism_population_blocks,
            "ordinary_plif_cells": ordinary_plifs,
            "mechanism_plif_cells": mechanism_plifs,
            "total_plif_cells": ordinary_plifs + mechanism_plifs,
            "adaptation_enabled_plif_cells": adaptation_plifs,
            "inhibition_enabled_plif_cells": inhibition_plifs,
            "hardwired_synapse_term_lanes": synapse_term_lanes,
            "readout_2x2_macros": int(catalog["readout_physical_macro_instances_2x2"]),
            "readout_class_accumulators": 281600 * 11,
            "soft_graph_module_instances": preflight["soft_instance_inventory"],
        },
        "measured_standard_cell_area_um2": measured,
        "isolated_primitive_characterization": {
            "ordinary_resident_plif_cell": ordinary_plif_characterization,
            "convolution_synapse_nine_term_block": convolution_characterization,
        },
        "capacity_at_70_percent_utilization": {
            "module_instances_per_die": capacity,
            "full_model_scenarios": model_fit,
            "die_area_mm2_options": die_areas,
        },
        "per_actor": per_actor,
        "power_characterization": {
            "activity_power_complete": ["enc1.depthwise integrated 1x1 actor"],
            "isolated_primitive_activity_power_complete": [
                "ordinary one-cell resident PLIF",
                "nine-term hardwired convolution synapse block",
            ],
            "isolated_primitive_in_progress": "adaptive/retinotopic PLIF mechanism",
            "remaining_classes": [
                "adaptive/retinotopic PLIF",
                "fork/join/union/offset/upsample routing",
                "attention gate",
                "temporal readout accumulator",
            ],
        },
        "claim_boundary": (
            "Counts are exact. Capacity uses measured block standard-cell area or the current "
            "hierarchical proxy and excludes top-level wires, clock tree, power grid, pads, "
            "routing congestion, and floorplan whitespace beyond the stated utilization."
        ),
    }
    output = ROOT / "artifacts/ASIC_XL/full_model_estimate/primitive_inventory_and_capacity.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exact_counts": result["exact_counts"], "full_model_scenarios": model_fit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
