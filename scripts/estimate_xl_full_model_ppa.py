#!/usr/bin/env python3
"""Build an exact-inventory, representative-block XL PPA estimate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(root: Path, path: str) -> dict[str, Any]:
    return json.loads((root / path).read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("asic/xl_representative_ppa.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/ASIC_XL/full_model_estimate"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = root / args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sources = config["sources"]
    model = load_json(root, sources["model_spec"])
    catalog = load_json(root, sources["catalog"])
    preflight = load_json(root, sources["assembly_preflight"])
    profile = load_json(root, sources["activity_profile"])
    actor_route = load_json(root, sources["actor_route_report"])
    readout_route = load_json(root, sources["readout_route_report"])
    trace = load_json(root, sources["actor_trace"])

    if not preflight.get("structural_generation_complete"):
        raise ValueError("macroized structural generation is incomplete")
    if int(preflight["actor_count"]) != 44 or int(preflight["native_readout_pixels"]) != 281600:
        raise ValueError("input inventory is not the exact native XL model")
    if profile.get("bins_profiled") != 10 or not profile.get("prediction_emitted"):
        raise ValueError("the selected full-model activity profile is incomplete")

    layers = {str(layer["name"]): layer for layer in model["layers"] if layer.get("name") != "head.synapse"}
    partitions = catalog["actor_physical_partition_policy"]["actors"]
    per_actor_preflight = preflight["per_actor"]
    activity_in = profile["actor_input_events"]
    activity_out = profile["actor_output_spikes"]
    contributions = profile["actor_synaptic_contributions"]

    reference = config["calibration"]
    reference_actor = str(reference["actor"])
    reference_layer = layers[reference_actor]
    reference_terms = int(partitions[reference_actor]["synaptic_terms_per_output_location"])
    reference_plifs = int(reference_layer["out_channels"])
    reference_cycles = int(reference["measured_trace_cycles"])
    clock_hz = float(config["clock_hz"])
    sample_duration = float(config["sample_duration_s"])
    syn_fraction = float(reference["dynamic_energy_allocation"]["synaptic_contributions"])
    commit_fraction = float(reference["dynamic_energy_allocation"]["plif_commits"])
    area_syn_weight = float(reference["complexity_area_weight"]["synaptic_terms"])
    area_state_weight = float(reference["complexity_area_weight"]["resident_plifs"])
    representative_routes = {
        str(item["actor"]): {
            **item,
            "data": load_json(root, str(item["report"])),
        }
        for item in config.get("representative_actor_routes", [])
    }

    ref_internal = 1.405026997e-3
    ref_switching = 1.645694370e-3
    ref_dynamic = ref_internal + ref_switching
    ref_leakage = float(actor_route["finish__power__leakage__total"])
    ref_area_um2 = float(actor_route["finish__design__instance__area"])
    ref_trace_contributions = int(trace["selected_input_spikes"])
    ref_trace_commits = reference_cycles * reference_plifs
    ref_dynamic_energy_j = ref_dynamic * reference_cycles / clock_hz
    energy_per_contribution_j = ref_dynamic_energy_j * syn_fraction / ref_trace_contributions
    energy_per_plif_commit_j = ref_dynamic_energy_j * commit_fraction / ref_trace_commits

    rows: list[dict[str, Any]] = []
    actor_area_um2 = 0.0
    actor_leakage_w = 0.0
    actor_dynamic_energy_j = 0.0
    for actor in model["graph"]["actor_topological_order"]:
        layer = layers[actor]
        partition = partitions[actor]
        physical_instances = int(per_actor_preflight[actor]["physical_instances"])
        output_h, output_w = (int(value) for value in layer["output_hw"])
        spatial_positions = output_h * output_w
        terms = int(partition["synaptic_terms_per_output_location"])
        out_channels = int(layer["out_channels"])
        complexity = area_syn_weight * terms / reference_terms + area_state_weight * out_channels / reference_plifs
        equivalent_reference_instances = spatial_positions * complexity
        route = representative_routes.get(actor)
        if route:
            tile_pixels = int(route["tile_pixels"])
            area_um2 = spatial_positions / tile_pixels * float(route["data"]["finish__design__instance__area"])
            leakage_w = spatial_positions / tile_pixels * float(route["data"]["finish__power__leakage__total"])
            physical_basis = "routed_representative"
        else:
            area_um2 = equivalent_reference_instances * ref_area_um2
            leakage_w = equivalent_reference_instances * ref_leakage
            physical_basis = "enc1_complexity_scaled_proxy"
        commits = int(layer["logical_membrane_states"]) * int(profile["bins_profiled"])
        dynamic_energy_j = int(contributions[actor]) * energy_per_contribution_j + commits * energy_per_plif_commit_j
        actor_area_um2 += area_um2
        actor_leakage_w += leakage_w
        actor_dynamic_energy_j += dynamic_energy_j
        rows.append({
            "actor": actor,
            "resource_class": partition["resource_class"],
            "physical_tile_hw": f"{partition['physical_tile_height']}x{partition['physical_tile_width']}",
            "physical_macro_instances": physical_instances,
            "logical_plifs": int(layer["logical_membrane_states"]),
            "synaptic_terms_per_output_location": terms,
            "input_events_50ms": int(activity_in[actor]),
            "output_spikes_50ms": int(activity_out[actor]),
            "synaptic_contributions_50ms": int(contributions[actor]),
            "estimated_area_mm2": area_um2 / 1e6,
            "estimated_leakage_w": leakage_w,
            "estimated_dynamic_energy_mj_per_50ms": dynamic_energy_j * 1e3,
            "physical_basis": physical_basis,
        })

    readout_instances = int(catalog["readout_physical_macro_instances_2x2"])
    readout_area_um2 = readout_instances * float(readout_route["finish__design__instance__area"])
    readout_leakage_w = readout_instances * float(readout_route["finish__power__leakage__total"])
    # Vectorless readout power is retained only as a stress scenario; it is not mixed into activity power.
    readout_vectorless_w = readout_instances * float(readout_route["finish__power__total"])
    central_area_mm2 = (actor_area_um2 + readout_area_um2) / 1e6
    central_power_w = actor_leakage_w + readout_leakage_w + actor_dynamic_energy_j / sample_duration
    low_factor, high_factor = (float(value) for value in reference["estimate_multiplier_range"])
    required_physical_views = 3 * len(catalog["masters"])
    present_physical_views = sum(
        1
        for master in catalog["masters"]
        for path in master["views"].values()
        if (root / str(path)).is_file()
    )

    edges = model["graph"]["edges"]
    edge_transforms = Counter(str(edge["transform"]) for edge in edges)
    fanout = Counter(str(edge["source"]) for edge in edges)
    interconnect = {
        "graph_edges": len(edges),
        "edge_transform_counts": dict(sorted(edge_transforms.items())),
        "fanout_source_count": sum(1 for value in fanout.values() if value > 1),
        "maximum_graph_fanout": max(fanout.values()),
        "ordered_completion_token_bits_per_edge": 24,
        "actor_physical_receptive_halo_input_bits": int(preflight["actor_physical_receptive_halo_input_bits"]),
        "actor_logical_8x8_receptive_halo_input_bits": int(preflight["actor_logical_8x8_receptive_halo_input_bits"]),
        "actor_output_vector_bits": int(preflight["actor_logical_plifs"]),
        "soft_instance_inventory": preflight["soft_instance_inventory"],
        "activity_packets_50ms": {
            "input_events": int(profile["input_events"]),
            "actor_input_events": sum(int(value) for value in activity_in.values()),
            "actor_output_spikes": sum(int(value) for value in activity_out.values()),
            "synaptic_contributions": sum(int(value) for value in contributions.values()),
        },
        "wirelength_status": "requires top-level floorplan and placement; no wirelength is inferred from graph edges",
    }

    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "actor_inventory_estimate.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    write_json(output_dir / "interconnect_inventory.json", interconnect)
    estimate = {
        "schema_version": "1.0.0",
        "scope": "exact_native_xl_inventory_with_representative_block_scaling",
        "exact_inventory": {
            "actors": 44,
            "logical_plifs": int(preflight["actor_logical_plifs"]),
            "resident_state_bits": 2916390400,
            "actor_physical_macro_instances": int(catalog["actor_physical_macro_instances"]),
            "readout_physical_macro_instances": readout_instances,
            "total_hard_macro_instances": int(catalog["total_hard_macro_instances"]),
            "unique_hard_macro_masters": int(catalog["unique_hard_macro_masters"]),
            "native_output_pixels": 281600,
        },
        "calibration": {
            "actor": reference_actor,
            "measured_area_um2": ref_area_um2,
            "measured_activity_power_w": ref_dynamic + ref_leakage,
            "measured_leakage_w": ref_leakage,
            "trace_contributions": ref_trace_contributions,
            "trace_plif_commits": ref_trace_commits,
            "derived_energy_per_synaptic_contribution_fj": energy_per_contribution_j * 1e15,
            "derived_energy_per_plif_commit_fj": energy_per_plif_commit_j * 1e15,
        },
        "provisional_estimate": {
            "central_standard_cell_area_mm2": central_area_mm2,
            "range_standard_cell_area_mm2": [central_area_mm2 * low_factor, central_area_mm2 * high_factor],
            "actor_dynamic_energy_mj_per_50ms": actor_dynamic_energy_j * 1e3,
            "central_average_power_w_at_20_fps": central_power_w,
            "range_average_power_w_at_20_fps": [central_power_w * low_factor, central_power_w * high_factor],
            "central_energy_mj_per_50ms": central_power_w * sample_duration * 1e3,
            "central_frames_per_joule": 1.0 / (central_power_w * sample_duration),
            "central_input_events_per_joule": int(profile["input_events"]) / (central_power_w * sample_duration),
            "readout_vectorless_stress_power_w_excluded_from_central": readout_vectorless_w,
        },
        "layout_readiness": {
            "structural_generation_complete": bool(preflight["structural_generation_complete"]),
            "physical_implementation_ready": bool(preflight["physical_implementation_ready"]),
            "present_physical_views": present_physical_views,
            "required_physical_views": required_physical_views,
            "completed_layout_blocks": [
                "enc1.depthwise 1x1 representative with activity power",
                "detail2.vertical 1x1 hard master",
                "detail2.horizontal 1x1 hard master",
                "detail1.depthwise 1x1 hard master",
                "down2.depthwise 1x1 hard master",
                "readout 2x2 hard master",
            ],
            "routed_actor_population_coverage": f"{len(representative_routes)}/44",
            "top_level_floorplan_place_route_complete": False,
        },
        "limitations": [
            "Only enc1.depthwise has representative-event routed power; other actors are complexity-scaled proxies.",
            "Readout activity power and top-level clock, routing, buffering, IO, and interconnect power are absent.",
            "The 0.5x to 3.0x range is a sensitivity band, not a statistical confidence interval.",
            "The activity trace is one unrectified 50 ms sample from epoch 11 while physical calibration uses the provisional epoch-1 export.",
            "Full-chip signoff requires all hard-macro views and top-level placement, routing, extraction, timing, DRC, and activity power.",
        ],
        "digests": {name: sha256(root / path) for name, path in sources.items()},
        "representative_route_digests": {
            actor: sha256(root / str(route["report"]))
            for actor, route in representative_routes.items()
        },
        "config_sha256": sha256(config_path),
    }
    write_json(output_dir / "full_model_ppa_estimate.json", estimate)
    print(json.dumps({"inventory": estimate["exact_inventory"], "estimate": estimate["provisional_estimate"], "layout": estimate["layout_readiness"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
