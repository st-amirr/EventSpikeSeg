#!/usr/bin/env python3
"""Prepare exact XL hard-macro declarations, view bindings, and instance map."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def _actor_physical_partition(layer: dict[str, Any]) -> dict[str, int | str]:
    """Select a conservative exact leaf size from static actor complexity."""
    input_channels = int(layer["in_channels"])
    output_channels = int(layer["out_channels"])
    groups = int(layer["groups"])
    kernel_h, kernel_w = (int(value) for value in layer["kernel"])
    terms = output_channels * (input_channels // groups) * kernel_h * kernel_w
    depthwise = groups == input_channels == output_channels
    if depthwise and output_channels <= 32:
        leaf = 4
        resource_class = "light_depthwise_4x4"
    elif depthwise or terms <= 1024:
        leaf = 2
        resource_class = "moderate_2x2"
    else:
        leaf = 1
        resource_class = "dense_1x1"
    return {
        "resource_class": resource_class,
        "physical_tile_height": leaf,
        "physical_tile_width": leaf,
        "synaptic_terms_per_output_location": terms,
    }


def _actor_tiles(
    layer: dict[str, Any],
    logical_tile_h: int,
    logical_tile_w: int,
    physical_tile_h: int,
    physical_tile_w: int,
) -> list[dict[str, int | str]]:
    output_h, output_w = (int(value) for value in layer["output_hw"])
    input_h, input_w = (int(value) for value in layer["input_hw"])
    kernel_h, kernel_w = (int(value) for value in layer["kernel"])
    stride_y, stride_x = (int(value) for value in layer["stride"])
    pad_y, pad_x = (int(value) for value in layer["padding"])
    dilation_y, dilation_x = (int(value) for value in layer["dilation"])
    result: list[dict[str, int | str]] = []
    for output_y in range(0, output_h, physical_tile_h):
        for output_x in range(0, output_w, physical_tile_w):
            local_h = min(physical_tile_h, output_h - output_y)
            local_w = min(physical_tile_w, output_w - output_x)
            raw_min_y = output_y * stride_y - pad_y
            raw_min_x = output_x * stride_x - pad_x
            input_y = max(0, raw_min_y)
            input_x = max(0, raw_min_x)
            input_end_y = min(
                input_h - 1,
                (output_y + local_h - 1) * stride_y
                - pad_y
                + (kernel_h - 1) * dilation_y,
            )
            input_end_x = min(
                input_w - 1,
                (output_x + local_w - 1) * stride_x
                - pad_x
                + (kernel_w - 1) * dilation_x,
            )
            halo_h = input_end_y - input_y + 1
            halo_w = input_end_x - input_x + 1
            offset_y = raw_min_y - input_y
            offset_x = raw_min_x - input_x
            variant = (
                f"out_{local_h}x{local_w}__halo_{halo_h}x{halo_w}__"
                f"offset_{offset_y}_{offset_x}"
            )
            result.append(
                {
                    "tile_row": output_y // logical_tile_h,
                    "tile_column": output_x // logical_tile_w,
                    "physical_subtile_row": (output_y % logical_tile_h) // physical_tile_h,
                    "physical_subtile_column": (output_x % logical_tile_w) // physical_tile_w,
                    "physical_tile_row": output_y // physical_tile_h,
                    "physical_tile_column": output_x // physical_tile_w,
                    "output_y": output_y,
                    "output_x": output_x,
                    "output_height": local_h,
                    "output_width": local_w,
                    "input_y": input_y,
                    "input_x": input_x,
                    "input_height": halo_h,
                    "input_width": halo_w,
                    "variant": variant,
                }
            )
    return result


def _actor_blackbox(master: dict[str, Any]) -> str:
    input_bits = int(master["input_bits"])
    output_bits = int(master["output_bits"])
    return "\n".join(
        [
            "(* blackbox *)",
            f"module {master['module']} (",
            "  input logic clk, input logic reset,",
            "  input logic presynaptic_valid_i, output logic presynaptic_ready_o,",
            f"  input logic [{input_bits - 1}:0] presynaptic_spike_vector_i,",
            "  input logic completion_valid_i, output logic completion_ready_o,",
            "  input logic [23:0] completion_tag_i,",
            "  output logic result_valid_o, input logic result_ready_i,",
            f"  output logic [{output_bits - 1}:0] spike_vector_o,",
            "  output logic [23:0] completion_tag_o, output logic error_o",
            ");",
            "endmodule",
        ]
    )


def _readout_blackbox(master: dict[str, Any]) -> str:
    x_width = max(1, (int(master["output_width"]) - 1).bit_length())
    y_width = max(1, (int(master["output_height"]) - 1).bit_length())
    return "\n".join(
        [
            "(* blackbox *)",
            f"module {master['module']} (",
            "  input logic clk, input logic reset,",
            "  input logic in_valid_i, output logic in_ready_o,",
            f"  input logic [{int(master['input_bits']) - 1}:0] in_spike_vector_i,",
            "  input logic in_completion_i, input logic [23:0] in_tag_i,",
            "  output logic prediction_valid_o, input logic prediction_ready_i,",
            f"  output logic [{x_width - 1}:0] prediction_x_o,",
            f"  output logic [{y_width - 1}:0] prediction_y_o,",
            "  output logic [3:0] prediction_class_o,",
            "  output logic frame_done_valid_o, input logic frame_done_ready_i,",
            "  output logic [23:0] frame_tag_o",
            ");",
            "endmodule",
        ]
    )


def prepare(model_spec: Path, tile_plan: Path, output_dir: Path) -> dict[str, Any]:
    spec = json.loads(model_spec.read_text(encoding="utf-8"))
    plan = json.loads(tile_plan.read_text(encoding="utf-8"))
    tile_h, tile_w = (int(value) for value in plan["tile_nominal_hw"])
    actors = [str(name) for name in spec["graph"]["actor_topological_order"]]
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    plan_actors = {str(actor["name"]): actor for actor in plan["actors"]}
    if set(actors) != set(plan_actors):
        raise ValueError("tile plan actor set does not match the model graph")

    output_dir.mkdir(parents=True, exist_ok=True)
    view_root = output_dir / "views"
    masters: dict[str, dict[str, Any]] = {}
    instance_rows: list[dict[str, Any]] = []
    actor_counts: Counter[str] = Counter()
    actor_partitions: dict[str, dict[str, int | str]] = {}
    for actor in actors:
        layer = layers[actor]
        input_channels = int(layer["in_channels"])
        output_channels = int(layer["out_channels"])
        partition = _actor_physical_partition(layer)
        actor_partitions[actor] = partition
        actor_macro_h = int(partition["physical_tile_height"])
        actor_macro_w = int(partition["physical_tile_width"])
        tiles = _actor_tiles(layer, tile_h, tile_w, actor_macro_h, actor_macro_w)
        for tile in tiles:
            variant = str(tile["variant"])
            module = "xl_hm_actor__" + _identifier(actor) + "__" + _identifier(variant)
            view_dir = view_root / module
            master = masters.setdefault(
                module,
                {
                    "kind": "actor_tile",
                    "module": module,
                    "actor": actor,
                    "variant": variant,
                    **partition,
                    "input_bits": input_channels
                    * int(tile["input_height"])
                    * int(tile["input_width"]),
                    "output_bits": output_channels
                    * int(tile["output_height"])
                    * int(tile["output_width"]),
                    "representative_tile_row": int(tile["physical_tile_row"]),
                    "representative_tile_column": int(tile["physical_tile_column"]),
                    "views": {
                        "lef": (view_dir / f"{module}.lef").as_posix(),
                        "gds": (view_dir / f"{module}.gds").as_posix(),
                        "lib": (view_dir / f"{module}.lib").as_posix(),
                    },
                    "instances": 0,
                },
            )
            master["instances"] += 1
            actor_counts[actor] += 1
            instance_rows.append(
                {
                    "kind": "actor_tile",
                    "actor": actor,
                    "master": module,
                    **partition,
                    **tile,
                }
            )

    readout = layers[str(spec["graph"]["current_readout"])]
    readout_h, readout_w = (int(value) for value in readout["output_hw"])
    readout_macro_h = 2
    readout_macro_w = 2
    readout_module = "xl_hm_readout__out_2x2"
    readout_physical_count = 0
    for y in range(0, readout_h, readout_macro_h):
        for x in range(0, readout_w, readout_macro_w):
            local_h = min(readout_macro_h, readout_h - y)
            local_w = min(readout_macro_w, readout_w - x)
            if (local_h, local_w) != (readout_macro_h, readout_macro_w):
                raise ValueError("native readout requires an unplanned boundary master")
            instance_rows.append(
                {
                    "kind": "readout_tile",
                    "actor": str(readout["name"]),
                    "master": readout_module,
                    "tile_row": y // tile_h,
                    "tile_column": x // tile_w,
                    "physical_subtile_row": (y % tile_h) // readout_macro_h,
                    "physical_subtile_column": (x % tile_w) // readout_macro_w,
                    "output_y": y,
                    "output_x": x,
                    "output_height": local_h,
                    "output_width": local_w,
                    "input_y": y,
                    "input_x": x,
                    "input_height": local_h,
                    "input_width": local_w,
                    "variant": "out_2x2",
                }
            )
            readout_physical_count += 1
    readout_logical_count = (readout_h // tile_h) * (readout_w // tile_w)
    view_dir = view_root / readout_module
    masters[readout_module] = {
        "kind": "readout_tile",
        "module": readout_module,
        "actor": str(readout["name"]),
        "variant": "out_2x2",
        "input_bits": int(readout["in_channels"]) * readout_macro_h * readout_macro_w,
        "output_bits": 0,
        "output_height": readout_macro_h,
        "output_width": readout_macro_w,
        "representative_tile_row": 0,
        "representative_tile_column": 0,
        "views": {
            "lef": (view_dir / f"{readout_module}.lef").as_posix(),
            "gds": (view_dir / f"{readout_module}.gds").as_posix(),
            "lib": (view_dir / f"{readout_module}.lib").as_posix(),
        },
        "instances": readout_physical_count,
    }

    expected_actor_tiles = int(plan["totals"]["tile_count"])
    actor_physical_count = sum(actor_counts.values())
    actor_logical_plifs = sum(
        int(master["output_bits"]) * int(master["instances"])
        for master in masters.values()
        if master["kind"] == "actor_tile"
    )
    if actor_logical_plifs != int(plan["totals"]["logical_plifs"]):
        raise ValueError("hard hierarchy does not conserve actor PLIF identities")
    synthesis_evidence = model_spec.parent / "partitioned_synthesis_1x1" / "summary.tsv"
    if (
        readout_logical_count != 4400
        or readout_physical_count != 70400
        or readout_h * readout_w != 281600
        or (readout_h, readout_w) != (440, 640)
    ):
        raise ValueError("hard hierarchy does not conserve the native XL readout")

    catalog = {
        "schema_version": "1.0.0",
        "scope": "exact_native_xl_hard_hierarchy",
        "model_spec_sha256": _sha256(model_spec),
        "tile_plan_sha256": _sha256(tile_plan),
        "native_dimensions_hw": [440, 640],
        "actor_count": len(actors),
        "actor_tile_instances": expected_actor_tiles,
        "logical_actor_tiles_8x8": expected_actor_tiles,
        "actor_physical_partition_policy": {
            "name": "conservative_exact_actor_leaves_v1",
            "rule": (
                "4x4 only for depthwise actors with at most 32 channels; 2x2 for other "
                "depthwise actors or at most 1024 synaptic terms per output location; "
                "1x1 for denser actors. Boundary leaves are clipped exactly."
            ),
            "baseline_1x1_synthesis_evidence": synthesis_evidence.as_posix(),
            "baseline_1x1_synthesis_evidence_sha256": (
                _sha256(synthesis_evidence) if synthesis_evidence.is_file() else None
            ),
            "actors": actor_partitions,
        },
        "actor_physical_macro_instances": actor_physical_count,
        "actor_physical_macro_instances_by_hw": dict(sorted(Counter(
            f"{partition['physical_tile_height']}x{partition['physical_tile_width']}"
            for actor, partition in actor_partitions.items()
            for _ in range(actor_counts[actor])
        ).items())),
        "actor_count_by_resource_class": dict(sorted(Counter(
            str(partition["resource_class"]) for partition in actor_partitions.values()
        ).items())),
        "actor_logical_plifs": actor_logical_plifs,
        "readout_tile_instances": readout_logical_count,
        "logical_readout_tiles_8x8": readout_logical_count,
        "readout_physical_macro_instances_2x2": readout_physical_count,
        "readout_physical_macros_per_logical_tile": 16,
        "nominal_tile_instances": expected_actor_tiles + readout_logical_count,
        "total_hard_macro_instances": actor_physical_count + readout_physical_count,
        "native_readout_pixels": readout_h * readout_w,
        "unique_hard_macro_masters": len(masters),
        "masters": list(masters.values()),
        "assembly": {
            "instance_map": (output_dir / "hard_macro_instances.tsv").as_posix(),
            "master_generation": (output_dir / "hard_macro_master_generation.tsv").as_posix(),
            "blackboxes": (output_dir / "hard_macro_blackboxes.sv").as_posix(),
            "orfs_view_bindings": (output_dir / "hard_macro_views.mk").as_posix(),
            "view_readiness": (output_dir / "hard_macro_view_readiness.json").as_posix(),
            "macroized_top": (output_dir / "generated_eventspikesegxl_macroized_top.sv").as_posix(),
            "macro_wrappers": (output_dir / "generated_xl_macro_wrappers.sv").as_posix(),
            "assembly_preflight": (output_dir / "macroized_assembly_preflight.json").as_posix(),
            "rule": (
                "Replace only each exact tiled actor/readout leaf with its named hard master; "
                "retain generated eventspikesegxl_dag_top routing, joins, completion tokens, "
                "global dimensions, and one dedicated resident state per logical PLIF."
            ),
        },
    }
    (output_dir / "hard_macro_catalog.json").write_text(
        json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
    )

    with (output_dir / "hard_macro_instances.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        fields = list(instance_rows[0])
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(instance_rows)

    generation_rows: list[dict[str, Any]] = []
    for master in masters.values():
        source = output_dir / "masters" / str(master["module"]) / f"{master['module']}.sv"
        source_text = source.as_posix()
        if master["kind"] == "actor_tile":
            command = (
                "python scripts/generate_resident_tile_pnr_top.py "
                f"artifacts/ASIC_XL/model_spec.yaml {source_text} "
                f"--actor {master['actor']} --tile-width {master['physical_tile_width']} "
                f"--tile-height {master['physical_tile_height']} "
                f"--tile-column {master['representative_tile_column']} "
                f"--tile-row {master['representative_tile_row']} "
                f"--module-name {master['module']}"
            )
        else:
            command = (
                "python scripts/generate_resident_readout_tile_pnr_top.py "
                f"artifacts/ASIC_XL/model_spec.yaml {source_text} "
                f"--tile-width {master['output_width']} "
                f"--tile-height {master['output_height']} "
                f"--module-name {master['module']}"
            )
        generation_rows.append(
            {
                "module": master["module"],
                "kind": master["kind"],
                "actor": master["actor"],
                "variant": master["variant"],
                "instances": master["instances"],
                "implementation_rtl": source_text,
                "generation_command": command,
            }
        )
    with (output_dir / "hard_macro_master_generation.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(generation_rows[0]), delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(generation_rows)

    declarations = ["`timescale 1ns/1ps", "// Generated exact hard-macro logical views."]
    declarations.extend(
        _actor_blackbox(master)
        if master["kind"] == "actor_tile"
        else _readout_blackbox(master)
        for master in masters.values()
    )
    (output_dir / "hard_macro_blackboxes.sv").write_text(
        "\n\n".join(declarations) + "\n", encoding="utf-8"
    )

    make_lines = [
        "# Generated explicit ORFS bindings for every exact XL hard-macro master.",
        "XL_HARD_MACRO_ROOT := $(PROJECT_DIR)/artifacts/ASIC_XL/hard_hierarchy/views",
    ]
    for variable, suffix in (
        ("ADDITIONAL_LEFS", "lef"),
        ("ADDITIONAL_GDS", "gds"),
        ("ADDITIONAL_LIBS", "lib"),
    ):
        make_lines.append(f"export {variable} += \\")
        paths = [f"  $(XL_HARD_MACRO_ROOT)/{name}/{name}.{suffix}" for name in masters]
        make_lines.extend(
            path + (" \\" if index + 1 < len(paths) else "")
            for index, path in enumerate(paths)
        )
    (output_dir / "hard_macro_views.mk").write_text(
        "\n".join(make_lines) + "\n", encoding="utf-8"
    )
    required_views = [
        Path(path)
        for master in masters.values()
        for path in master["views"].values()
    ]
    missing_views = [path.as_posix() for path in required_views if not path.is_file()]
    readiness = {
        "schema_version": "1.0.0",
        "ready": not missing_views,
        "required_master_count": len(masters),
        "required_view_file_count": len(required_views),
        "present_view_file_count": len(required_views) - len(missing_views),
        "missing_view_file_count": len(missing_views),
        "missing_views": missing_views,
        "gate": (
            "Do not start native hard-hierarchy ORFS until every explicit LEF, GDS, "
            "and Liberty view exists and its logical module matches the blackbox declaration."
        ),
    }
    (output_dir / "hard_macro_view_readiness.json").write_text(
        json.dumps(readiness, indent=2) + "\n", encoding="utf-8"
    )
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-spec", type=Path, required=True)
    parser.add_argument("--tile-plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    catalog = prepare(args.model_spec, args.tile_plan, args.output_dir)
    print(json.dumps({key: catalog[key] for key in (
        "actor_count", "actor_tile_instances", "logical_actor_tiles_8x8",
        "actor_physical_macro_instances", "actor_logical_plifs", "readout_tile_instances",
        "logical_readout_tiles_8x8", "readout_physical_macro_instances_2x2",
        "nominal_tile_instances", "total_hard_macro_instances",
        "native_readout_pixels", "unique_hard_macro_masters",
    )}, indent=2))


if __name__ == "__main__":
    main()
