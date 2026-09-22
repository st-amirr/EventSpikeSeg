#!/usr/bin/env python3
"""Build the checkpoint-exact 140k primitive inventory and scaling report."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASIC = ROOT / "artifacts" / "ASIC"
OUT = ASIC / "primitive_characterization" / "base_140k_inventory"
ADAPTATION_MANIFEST = ROOT / "asic" / "primitive_140k_down2_adaptation_decomposition.yaml"

EXPECTED_ADAPTATION_COUNTS = {
    "adaptation_lane_instances": 10_982_400,
    "spatial_groups_64_channels": 92_400,
    "spatial_groups_128_channels": 39_600,
    "penalty_reduce64_direct_instances": 92_400,
    "penalty_reduce64_lower_instances": 79_200,
    "penalty_reduce64_upper_instances": 39_600,
    "energy_reduce64_instances": 92_400,
    "energy_reduce128_instances": 39_600,
}

EXPECTED_ADAPTATION_COMPOSITION = {
    64: [
        ("channel_penalties", "primitive_140k_down2_adaptation_penalty_lane_pnr_top", None, 64),
        ("shared_penalty", "primitive_140k_down2_adaptation_penalty_reduce64_pnr_top", "direct", 1),
        ("adjusted_squares", "primitive_140k_down2_adaptation_square_lane_pnr_top", None, 64),
        ("shared_energy", "primitive_140k_down2_adaptation_energy_reduce64_pnr_top", None, 1),
        ("channel_commits", "primitive_140k_down2_adaptation_commit_lane_pnr_top", None, 64),
    ],
    128: [
        ("channel_penalties", "primitive_140k_down2_adaptation_penalty_lane_pnr_top", None, 128),
        ("shared_penalty_lower", "primitive_140k_down2_adaptation_penalty_reduce64_pnr_top", "lower", 2),
        ("shared_penalty_upper", "primitive_140k_down2_adaptation_penalty_reduce64_pnr_top", "upper_two_values_plus_62_zeros", 1),
        ("adjusted_squares", "primitive_140k_down2_adaptation_square_lane_pnr_top", None, 128),
        ("shared_energy", "primitive_140k_adaptation_energy_reduce128_pnr_top", None, 1),
        ("channel_commits", "primitive_140k_down2_adaptation_commit_lane_pnr_top", None, 128),
    ],
}


def read_json(path: Path) -> dict:
    require_file(path)
    return json.loads(path.read_text(encoding="utf-8"))


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Required characterization artifact is absent: {path}")
    return path


def read_adaptation_manifest(path: Path) -> dict:
    """Read the small schema-v2 YAML contract without adding a YAML dependency."""
    require_file(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    schema_version = None
    monolithic_policy = None
    inventory: dict[str, int] = {}
    composition: dict[int, list[dict[str, object]]] = {}
    section = None
    width = None
    item = None

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0:
            section = stripped.removesuffix(":")
            width = None
            item = None
            if stripped.startswith("schema_version:"):
                schema_version = int(stripped.split(":", 1)[1].strip())
            elif stripped.startswith("monolithic_physical_characterization:"):
                monolithic_policy = stripped.split(":", 1)[1].strip()
            continue
        if section == "full_model_inventory" and indent == 2:
            key, value = stripped.split(":", 1)
            inventory[key] = int(value.strip())
        elif section == "composition_by_channel_width":
            if indent == 2 and stripped.endswith(":"):
                width = int(stripped[:-1])
                composition[width] = []
                item = None
            elif indent == 4 and stripped.startswith("- "):
                if width is None:
                    raise ValueError(f"Malformed composition in {path}: item precedes width")
                key, value = stripped[2:].split(":", 1)
                item = {key: value.strip()}
                composition[width].append(item)
            elif indent == 6 and item is not None:
                key, value = stripped.split(":", 1)
                value = value.strip()
                item[key] = int(value) if key == "instances_per_spatial_group" else value

    if schema_version != 2:
        raise ValueError(f"Expected adaptation manifest schema_version 2 in {path}; got {schema_version!r}")
    if monolithic_policy != "forbidden":
        raise ValueError(
            "The schema-v2 adaptation contract must forbid monolithic physical "
            f"characterization; got {monolithic_policy!r} in {path}"
        )
    missing = sorted(set(EXPECTED_ADAPTATION_COUNTS) - set(inventory))
    if missing:
        raise ValueError(f"Adaptation manifest is missing full_model_inventory keys: {missing}")
    mismatched = {
        key: (inventory[key], expected)
        for key, expected in EXPECTED_ADAPTATION_COUNTS.items()
        if inventory[key] != expected
    }
    if mismatched:
        raise ValueError(f"Adaptation manifest population counts do not match the exact 140k inventory: {mismatched}")

    normalized = {
        channel_width: [
            (entry.get("stage"), entry.get("design"), entry.get("role"), entry.get("instances_per_spatial_group"))
            for entry in entries
        ]
        for channel_width, entries in composition.items()
    }
    if normalized != EXPECTED_ADAPTATION_COMPOSITION:
        raise ValueError(
            "Adaptation manifest composition_by_channel_width does not match the exact "
            f"64/128-channel hierarchy: {normalized}"
        )
    return {
        "schema_version": schema_version,
        "full_model_inventory": inventory,
        "composition_by_channel_width": composition,
    }


def route_metrics(path: Path, stage: str = "finish") -> dict:
    data = read_json(path)
    return {
        "stage": stage,
        "die_area_um2": data[f"{stage}__design__die__area"],
        "core_area_um2": data[f"{stage}__design__core__area"],
        "cell_area_um2": data[f"{stage}__design__instance__area"],
        "fmax_hz": data[f"{stage}__timing__fmax"],
        "setup_tns_ns": data[f"{stage}__timing__setup__tns"],
        "hold_tns_ns": data[f"{stage}__timing__hold__tns"],
        "flow_errors": data[f"{stage}__flow__errors__count"],
    }


def activity_power(path: Path) -> dict:
    require_file(path)
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^Total\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)",
        text,
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError(f"No total power row in {path}")
    internal, switching, leakage, total = map(float, match.groups())
    return {
        "internal_w": internal,
        "switching_w": switching,
        "dynamic_w": internal + switching,
        "leakage_w": leakage,
        "total_w": total,
    }


def checked_route(path: Path, stage: str, maturity: str) -> dict:
    route = route_metrics(path, stage)
    if route["flow_errors"] != 0 or route["setup_tns_ns"] != 0 or route["hold_tns_ns"] != 0:
        raise RuntimeError(
            f"Required {maturity} checkpoint is not timing-clean: {path} "
            f"(flow_errors={route['flow_errors']}, setup_tns={route['setup_tns_ns']}, "
            f"hold_tns={route['hold_tns_ns']})"
        )
    route["maturity"] = maturity
    route["report"] = str(path.relative_to(ROOT))
    return route


def adaptation_characterization(
    *,
    name: str,
    design: str,
    activity_directory: str,
    expected_activity_block: str,
    instance_count: int,
    allow_global_route_fallback: bool = False,
) -> dict:
    report_dir = ROOT / "artifacts" / "OpenROAD" / "logs" / "asap7" / design / "checkpoint_exact"
    power_dir = ASIC / "primitive_characterization" / activity_directory
    detailed_route = report_dir / "6_report.json"
    detailed_power = power_dir / "activity_power.rpt"
    global_route = report_dir / "5_1_grt.json"
    global_power = power_dir / "activity_power_global_route.rpt"

    if detailed_route.is_file() and detailed_power.is_file():
        route = checked_route(detailed_route, "finish", "detailed_route")
        power_path = detailed_power
    elif allow_global_route_fallback and global_route.is_file() and global_power.is_file():
        route = checked_route(
            global_route,
            "globalroute",
            "timing_closed_global_route_with_estimated_parasitics",
        )
        power_path = global_power
    else:
        required = [detailed_route, detailed_power]
        if allow_global_route_fallback:
            required.extend([global_route, global_power])
        available = [str(path.relative_to(ROOT)) for path in required if path.is_file()]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        raise FileNotFoundError(
            f"No complete routed/power artifact pair for adaptation role {name!r}. "
            f"Present candidates: {available or 'none'}; absent candidates: {missing}"
        )

    power = activity_power(power_path)
    activity_manifest_path = power_dir / "activity_manifest.json"
    activity_manifest = read_json(activity_manifest_path)
    if activity_manifest.get("decomposition_block") != expected_activity_block:
        raise ValueError(
            f"Activity manifest {activity_manifest_path} identifies "
            f"{activity_manifest.get('decomposition_block')!r}, expected {expected_activity_block!r}"
        )
    period_ns = float(activity_manifest["clock_period_ns"])
    if period_ns <= 0:
        raise ValueError(f"Invalid clock_period_ns in {activity_manifest_path}: {period_ns}")
    energy_j = power["dynamic_w"] * period_ns * 1e-9
    return {
        "design": design,
        "activity_role": expected_activity_block,
        "instance_count": instance_count,
        "route": route,
        "activity_power": power,
        "power_report": str(power_path.relative_to(ROOT)),
        "activity_manifest": str(activity_manifest_path.relative_to(ROOT)),
        "dynamic_energy_j_per_evaluation": energy_j,
        "scaled_dynamic_energy_j_per_bin": instance_count * energy_j,
        "scaled_dynamic_power_w_at_200_bins_per_second": instance_count * energy_j * 200,
        "scaled_leakage_w": instance_count * power["leakage_w"],
        "scaled_die_area_mm2": instance_count * route["die_area_um2"] / 1_000_000,
        "scaled_cell_area_mm2": instance_count * route["cell_area_um2"] / 1_000_000,
    }


def main() -> None:
    spec = read_json(ASIC / "model_spec.yaml")
    adaptation_manifest = read_adaptation_manifest(ADAPTATION_MANIFEST)
    actor_rows = []
    classes = {"ordinary": 0, "adaptation": 0, "inhibition": 0, "adaptation_and_inhibition": 0}
    leaves = {key: 0 for key in classes}
    actor_terms = 0

    for layer in spec["layers"]:
        states = int(layer["logical_membrane_states"])
        h, w = map(int, layer["output_hw"])
        spatial = h * w
        weights = int(layer["weight_count"])
        terms = spatial * weights
        if states == 0:
            continue
        params = read_json(ASIC / layer["parameter_file"])
        adaptation = bool(params["threshold_adaptation_enabled"])
        inhibition = bool(params["inhibition_enabled"])
        if adaptation and inhibition:
            kind = "adaptation_and_inhibition"
        elif adaptation:
            kind = "adaptation"
        elif inhibition:
            kind = "inhibition"
        else:
            kind = "ordinary"
        classes[kind] += states
        leaves[kind] += spatial
        actor_terms += terms
        actor_rows.append(
            {
                "name": layer["name"],
                "class": kind,
                "output_hw": [h, w],
                "channels": int(layer["out_channels"]),
                "logical_plifs": states,
                "spatial_actor_leaves_1x1": spatial,
                "weight_count": weights,
                "dense_synapse_term_evaluations_per_bin": terms,
            }
        )

    head = next(layer for layer in spec["layers"] if layer["name"] == "head.synapse")
    readout_spatial = math.prod(head["output_hw"])
    readout_terms = readout_spatial * int(head["weight_count"])
    readout_accumulators = readout_spatial * int(spec["class_count"])

    plif_route = route_metrics(
        ROOT / "artifacts/OpenROAD/logs/asap7/primitive_140k_plif_1_pnr_top/checkpoint_exact/6_report.json"
    )
    conv_route = route_metrics(
        ROOT / "artifacts/OpenROAD/logs/asap7/primitive_140k_conv9_pnr_top/checkpoint_exact/6_report.json"
    )
    readout_route = route_metrics(
        ROOT / "artifacts/OpenROAD/logs/asap7/primitive_140k_readout_1x1_pnr_top/checkpoint_exact/6_report.json"
    )
    inhibition_route = route_metrics(
        ROOT / "artifacts/OpenROAD/logs/asap7/primitive_140k_stem_inhibition_32_pnr_top/checkpoint_exact/5_1_grt.json",
        "globalroute",
    )
    plif_power = activity_power(
        ASIC / "primitive_characterization/ordinary_plif_1_checkpoint_exact/activity_power.rpt"
    )
    conv_power = activity_power(
        ASIC / "primitive_characterization/detail_stem_conv9_checkpoint_exact/activity_power.rpt"
    )
    readout_power = activity_power(
        ASIC / "primitive_characterization/readout_1x1_checkpoint_exact/activity_power.rpt"
    )
    inhibition_power = activity_power(
        ASIC / "primitive_characterization/stem_inhibition_32_checkpoint_exact/activity_power_global_route.rpt"
    )
    readout_manifest = read_json(
        ASIC / "primitive_characterization/readout_1x1_checkpoint_exact/activity_manifest.json"
    )

    adaptation_counts = adaptation_manifest["full_model_inventory"]
    if classes["adaptation"] != adaptation_counts["adaptation_lane_instances"]:
        raise ValueError(
            "Model inventory and adaptation decomposition disagree on lane count: "
            f"model={classes['adaptation']}, manifest={adaptation_counts['adaptation_lane_instances']}"
        )
    adaptation_blocks = {
        "penalty_lane": adaptation_characterization(
            name="penalty_lane",
            design="primitive_140k_down2_adaptation_penalty_lane_pnr_top",
            activity_directory="down2_adaptation_penalty_lane_checkpoint_exact",
            expected_activity_block="penalty_lane",
            instance_count=adaptation_counts["adaptation_lane_instances"],
        ),
        "penalty_reduce64_direct": adaptation_characterization(
            name="penalty_reduce64_direct",
            design="primitive_140k_down2_adaptation_penalty_reduce64_pnr_top",
            activity_directory="down2_adaptation_penalty_reduce64_checkpoint_exact",
            expected_activity_block="penalty_reduce64_direct",
            instance_count=adaptation_counts["penalty_reduce64_direct_instances"],
        ),
        "penalty_reduce64_lower": adaptation_characterization(
            name="penalty_reduce64_lower",
            design="primitive_140k_down2_adaptation_penalty_reduce64_pnr_top",
            activity_directory="adaptation_penalty_reduce64_lower_checkpoint_exact",
            expected_activity_block="penalty_reduce64_lower",
            instance_count=adaptation_counts["penalty_reduce64_lower_instances"],
        ),
        "penalty_reduce64_upper": adaptation_characterization(
            name="penalty_reduce64_upper",
            design="primitive_140k_down2_adaptation_penalty_reduce64_pnr_top",
            activity_directory="adaptation_penalty_reduce64_upper_checkpoint_exact",
            expected_activity_block="penalty_reduce64_upper",
            instance_count=adaptation_counts["penalty_reduce64_upper_instances"],
        ),
        "square_lane": adaptation_characterization(
            name="square_lane",
            design="primitive_140k_down2_adaptation_square_lane_pnr_top",
            activity_directory="down2_adaptation_square_lane_checkpoint_exact",
            expected_activity_block="square_lane",
            instance_count=adaptation_counts["adaptation_lane_instances"],
        ),
        "energy_reduce64": adaptation_characterization(
            name="energy_reduce64",
            design="primitive_140k_down2_adaptation_energy_reduce64_pnr_top",
            activity_directory="down2_adaptation_energy_reduce64_checkpoint_exact",
            expected_activity_block="energy_reduce64",
            instance_count=adaptation_counts["energy_reduce64_instances"],
            allow_global_route_fallback=True,
        ),
        "energy_reduce128": adaptation_characterization(
            name="energy_reduce128",
            design="primitive_140k_adaptation_energy_reduce128_pnr_top",
            activity_directory="adaptation_energy_reduce128_checkpoint_exact",
            expected_activity_block="energy_reduce128",
            instance_count=adaptation_counts["energy_reduce128_instances"],
            allow_global_route_fallback=True,
        ),
        "commit_lane": adaptation_characterization(
            name="commit_lane",
            design="primitive_140k_down2_adaptation_commit_lane_pnr_top",
            activity_directory="down2_adaptation_commit_lane_checkpoint_exact",
            expected_activity_block="commit_lane",
            instance_count=adaptation_counts["adaptation_lane_instances"],
        ),
    }

    plif_bins = 10
    plif_trace_s = 325e-9
    plif_energy_j_per_bin = plif_power["dynamic_w"] * plif_trace_s / plif_bins
    conv_period_s = 5e-9
    conv_terms_per_sample = 9
    conv_energy_j_per_term = conv_power["dynamic_w"] * conv_period_s / conv_terms_per_sample
    readout_trace_s = int(readout_manifest["cycles"]) * 5e-9
    readout_energy_j_per_prediction = readout_power["dynamic_w"] * readout_trace_s
    inhibition_energy_j_per_group_evaluation = inhibition_power["dynamic_w"] * 5e-9
    inhibition_groups = leaves["inhibition"]
    inhibition_energy_j_per_bin = (
        inhibition_energy_j_per_group_evaluation * inhibition_groups
    )
    adaptation_energy_j_per_bin = sum(
        block["scaled_dynamic_energy_j_per_bin"] for block in adaptation_blocks.values()
    )
    adaptation_leakage_w = sum(block["scaled_leakage_w"] for block in adaptation_blocks.values())
    adaptation_die_area_mm2 = sum(block["scaled_die_area_mm2"] for block in adaptation_blocks.values())
    adaptation_cell_area_mm2 = sum(block["scaled_cell_area_mm2"] for block in adaptation_blocks.values())
    bins_per_second = 20 * 10

    ordinary_plif_energy_j_per_bin = classes["ordinary"] * plif_energy_j_per_bin
    actor_synapse_energy_j_per_bin = actor_terms * conv_energy_j_per_term
    readout_energy_j_per_frame = readout_spatial * readout_energy_j_per_prediction
    dense_characterized_power_w = (
        (ordinary_plif_energy_j_per_bin + actor_synapse_energy_j_per_bin
         + inhibition_energy_j_per_bin + adaptation_energy_j_per_bin) * bins_per_second
        + readout_energy_j_per_frame * 20
    )

    budgets = {}
    for mm2 in (100, 400, 800):
        usable_um2 = mm2 * 1_000_000 * 0.70
        budgets[str(mm2)] = {
            "usable_area_mm2_at_70_percent": mm2 * 0.70,
            "checkpoint_exact_plif_instances": math.floor(usable_um2 / plif_route["die_area_um2"]),
            "checkpoint_exact_conv9_blocks": math.floor(usable_um2 / conv_route["die_area_um2"]),
            "checkpoint_exact_conv_terms": math.floor(usable_um2 / (conv_route["die_area_um2"] / 9)),
            "checkpoint_exact_readout_1x1_blocks": math.floor(usable_um2 / readout_route["die_area_um2"]),
            "checkpoint_exact_inhibition_32_groups": math.floor(usable_um2 / inhibition_route["die_area_um2"]),
        }

    report = {
        "schema_version": 2,
        "scope": "EventSpikeSeg140k_v8_epoch80_seed17",
        "checkpoint": spec["checkpoint"],
        "model": {
            "actor_count": len(actor_rows),
            "graph_edge_count": len(spec["graph"]["edges"]),
            "logical_plifs": sum(classes.values()),
            "plif_classes": classes,
            "spatial_actor_leaves_1x1": sum(leaves.values()),
            "spatial_leaf_classes": leaves,
            "actor_dense_synapse_term_evaluations_per_bin": actor_terms,
            "readout_dense_synapse_term_evaluations_per_bin": readout_terms,
            "readout_class_accumulators": readout_accumulators,
            "executed_convolution_weights": spec["executed_convolution_weights"],
            "executed_inference_parameters": spec["executed_inference_parameters"],
            "resident_state_bits": spec["state_capacity"]["dense_exact_state_bytes"] * 8,
        },
        "actors": actor_rows,
        "characterized_primitives": {
            "ordinary_plif": {
                "route": plif_route,
                "activity_power": plif_power,
                "dynamic_energy_j_per_logical_bin": plif_energy_j_per_bin,
                "stimulus": "ten checkpoint-format bins using epoch-80 beta/threshold and real base-weight contributions",
            },
            "detail_stem_conv9": {
                "route": conv_route,
                "activity_power": conv_power,
                "dynamic_energy_j_per_term_evaluation": conv_energy_j_per_term,
                "stimulus": "128 vectors through one exact epoch-80 detail_stem 3x3 kernel",
            },
            "readout_1x1": {
                "route": readout_route,
                "activity_power": readout_power,
                "dynamic_energy_j_per_ten_bin_prediction": readout_energy_j_per_prediction,
                "stimulus": "ten bins of deterministic 16-channel spikes plus prediction and frame-done handshakes",
            },
            "stem_inhibition_32": {
                "route": inhibition_route,
                "route_maturity": "timing_closed_congestion_free_global_route; detailed route exceeded 12 GiB",
                "activity_power": inhibition_power,
                "spatial_group_count": inhibition_groups,
                "dynamic_energy_j_per_group_evaluation": inhibition_energy_j_per_group_evaluation,
                "stimulus": "128 checkpoint-derived 32-channel vectors with 1035 spikes",
            },
            "adaptation_decomposition": {
                "manifest": str(ADAPTATION_MANIFEST.relative_to(ROOT)),
                "manifest_schema_version": adaptation_manifest["schema_version"],
                "exact_instance_counts": adaptation_counts,
                "blocks": adaptation_blocks,
                "scaled_dynamic_energy_j_per_bin": adaptation_energy_j_per_bin,
                "scaled_dynamic_power_w_at_200_bins_per_second": adaptation_energy_j_per_bin * bins_per_second,
                "scaled_leakage_w": adaptation_leakage_w,
                "scaled_die_area_mm2": adaptation_die_area_mm2,
                "scaled_cell_area_mm2": adaptation_cell_area_mm2,
            },
        },
        "dense_scaling": {
            "bins_per_second_at_20_fps_10_bins": bins_per_second,
            "ordinary_plif_dynamic_energy_j_per_bin": ordinary_plif_energy_j_per_bin,
            "actor_synapse_dynamic_energy_j_per_bin": actor_synapse_energy_j_per_bin,
            "readout_dynamic_energy_j_per_frame": readout_energy_j_per_frame,
            "inhibition_dynamic_energy_j_per_bin": inhibition_energy_j_per_bin,
            "inhibition_dynamic_power_w": inhibition_energy_j_per_bin * bins_per_second,
            "adaptation_dynamic_energy_j_per_bin": adaptation_energy_j_per_bin,
            "adaptation_dynamic_power_w": adaptation_energy_j_per_bin * bins_per_second,
            "adaptation_scaled_leakage_w": adaptation_leakage_w,
            "adaptation_scaled_die_area_mm2": adaptation_die_area_mm2,
            "adaptation_scaled_cell_area_mm2": adaptation_cell_area_mm2,
            "characterized_dynamic_power_w": dense_characterized_power_w,
            "coverage": "ordinary PLIF updates, dense actor synapse terms, exact one-pixel readout blocks, exact 32-channel stem inhibition groups, and the exact schema-v2 adaptation hierarchy",
            "excluded": [
                "remaining direct-state mechanism registers and static weight-distribution overhead",
                "event routing, completion-token joins, clock tree, and top-level interconnect",
                "actual checkpoint activation sparsity",
            ],
            "interpretation": "A dense-operation extrapolation, not a signed-off full-chip power result.",
        },
        "direct_resident_area_scaling": {
            "all_logical_plifs_times_isolated_plif_die_area_mm2": sum(classes.values()) * plif_route["die_area_um2"] / 1_000_000,
            "all_logical_plifs_times_isolated_plif_cell_area_mm2": sum(classes.values()) * plif_route["cell_area_um2"] / 1_000_000,
            "ordinary_plifs_times_isolated_plif_die_area_mm2": classes["ordinary"] * plif_route["die_area_um2"] / 1_000_000,
            "interpretation": "Capacity bound for the required direct register/latch-resident state. Mechanism variants and shared hierarchy will change the final area.",
        },
        "die_capacity": budgets,
        "layout_status": {
            "primitive_routes_complete": 10,
            "full_model_floorplan_complete": False,
            "full_model_place_route_complete": False,
            "blocking_requirement": "complete the direct-state hard hierarchy, top-level floorplan, and interconnect implementation",
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inventory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    dense = report["dense_scaling"]
    adaptation_labels = {
        "penalty_lane": "Adaptation penalty lane",
        "penalty_reduce64_direct": "Adaptation penalty reduce64, direct role",
        "penalty_reduce64_lower": "Adaptation penalty reduce64, lower role",
        "penalty_reduce64_upper": "Adaptation penalty reduce64, upper role",
        "square_lane": "Adaptation square lane",
        "energy_reduce64": "Adaptation energy reduce64",
        "energy_reduce128": "Adaptation energy reduce128",
        "commit_lane": "Adaptation commit lane",
    }
    adaptation_rows = ""
    for name, block in adaptation_blocks.items():
        route = block["route"]
        power = block["activity_power"]
        maturity = " GR" if route["stage"] == "globalroute" else ""
        adaptation_rows += (
            f"| {adaptation_labels[name]}{maturity} | {route['die_area_um2']:.3f} | "
            f"{route['fmax_hz']/1e6:.3f} | {power['dynamic_w']*1e3:.6f} mW | "
            f"{power['leakage_w']*1e6:.6f} uW | "
            f"{block['dynamic_energy_j_per_evaluation']*1e12:.6f} pJ/evaluation |\n"
        )
    md = f"""# EventSpikeSeg140k checkpoint-exact primitive inventory

This report applies to EventSpikeSeg140k v8, epoch 80, seed 17 at 440x640 with six classes.

## Exact model inventory

- Dedicated PLIF actors: {len(actor_rows)}
- Logical PLIF states: {sum(classes.values()):,}
- Ordinary PLIF states: {classes['ordinary']:,}
- Adaptation PLIF states: {classes['adaptation']:,}
- Inhibition PLIF states: {classes['inhibition']:,}
- Adaptation-and-inhibition PLIF states: {classes['adaptation_and_inhibition']:,}
- Spatial 1x1 actor leaves under the current capacity policy: {sum(leaves.values()):,}
- Dense actor synapse-term evaluations per 5 ms bin: {actor_terms:,}
- Dense readout synapse-term evaluations per 5 ms bin: {readout_terms:,}
- Readout class accumulators: {readout_accumulators:,}
- Static graph edges: {len(spec['graph']['edges'])}

## Routed checkpoint-exact primitives

| Primitive | Die area (um^2) | Fmax (MHz) | Dynamic power in trace | Leakage | Derived energy |
|---|---:|---:|---:|---:|---:|
| Ordinary PLIF | {plif_route['die_area_um2']:.3f} | {plif_route['fmax_hz']/1e6:.3f} | {plif_power['dynamic_w']*1e3:.6f} mW | {plif_power['leakage_w']*1e6:.6f} uW | {plif_energy_j_per_bin*1e12:.6f} pJ/bin |
| detail_stem 3x3 convolution | {conv_route['die_area_um2']:.3f} | {conv_route['fmax_hz']/1e6:.3f} | {conv_power['dynamic_w']*1e3:.6f} mW | {conv_power['leakage_w']*1e9:.6f} nW | {conv_energy_j_per_term*1e12:.6f} pJ/term |
| Six-class readout, one pixel | {readout_route['die_area_um2']:.3f} | {readout_route['fmax_hz']/1e6:.3f} | {readout_power['dynamic_w']*1e3:.6f} mW | {readout_power['leakage_w']*1e6:.6f} uW | {readout_energy_j_per_prediction*1e12:.6f} pJ/prediction |
| Stem inhibition, 32 channels | {inhibition_route['die_area_um2']:.3f} | {inhibition_route['fmax_hz']/1e6:.3f} | {inhibition_power['dynamic_w']*1e3:.6f} mW | {inhibition_power['leakage_w']*1e6:.6f} uW | {inhibition_energy_j_per_group_evaluation*1e12:.6f} pJ/group evaluation |
{adaptation_rows}

All ten unique physical designs have zero flow errors and zero setup/hold TNS at the selected checkpoint. A `GR` suffix marks an energy reducer using the timing-closed global-route fallback and estimated global-route parasitics. The three penalty-reducer rows use one detailed-routed macro with separate direct, lower, and upper pooled activity reports. Inhibition remains timing-closed and congestion-free at global route because detailed routing exceeded the bounded 12 GiB limit.

The schema-v2 adaptation composition scales 10,982,400 instances of each lane macro, 92,400 direct reduce64 instances, 79,200 lower reduce64 instances, 39,600 upper reduce64 instances, 92,400 energy64 instances, and 39,600 energy128 instances. Its isolated-macro totals are {adaptation_die_area_mm2:,.3f} mm^2 die area, {adaptation_cell_area_mm2:,.3f} mm^2 cell area, {adaptation_leakage_w:.6f} W leakage, and {adaptation_energy_j_per_bin:.9f} J per bin.

## Multiplication result

At 20 frames/s and ten 5 ms bins per frame, the measured ordinary-PLIF update cost, dense actor-synapse term cost, exact one-pixel readout cost, 70,400 exact stem-inhibition groups, and exact adaptation decomposition give **{dense['characterized_dynamic_power_w']:.6f} W**. The adaptation contribution is **{dense['adaptation_dynamic_power_w']:.6f} W**. This is a per-block multiplication result, not full-chip signoff. It excludes graph interconnect, completion-token control, clock distribution, static weight-distribution overhead, and measured network spike sparsity.

The required direct register/latch-resident implementation contains 30,976,000 physical state identities. Multiplying the isolated ordinary-PLIF footprint across every logical PLIF gives {sum(classes.values()) * plif_route['die_area_um2'] / 1_000_000:,.3f} mm^2 of isolated die footprint ({sum(classes.values()) * plif_route['cell_area_um2'] / 1_000_000:,.3f} mm^2 of standard cells), before the larger adaptation/inhibition variants, synapses, hierarchy, clock, power, and routing. This is a capacity bound rather than a completed floorplan.

## Die capacity at 70% usable area

| Die | PLIF instances | conv9 blocks | equivalent convolution terms | readout 1x1 blocks | inhibition groups |
|---:|---:|---:|---:|---:|---:|
"""
    for mm2, values in budgets.items():
        md += f"| {mm2} mm^2 | {values['checkpoint_exact_plif_instances']:,} | {values['checkpoint_exact_conv9_blocks']:,} | {values['checkpoint_exact_conv_terms']:,} | {values['checkpoint_exact_readout_1x1_blocks']:,} | {values['checkpoint_exact_inhibition_32_groups']:,} |\n"
    md += "\nThese capacities are isolated-macro packing bounds. They do not include hierarchy wiring, power delivery, clock distribution, or top-level routing.\n"
    (OUT / "README.md").write_text(md, encoding="utf-8")
    print(json.dumps({"output": str(OUT), "model": report["model"], "dense_scaling": dense}, indent=2))


if __name__ == "__main__":
    main()
