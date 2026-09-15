#!/usr/bin/env python3
"""Generate one checkpoint-exact resident actor tile for physical design."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.generate_asic_top import (
        _mechanism_parameters,
        _packed_literal,
        _parameter_literal,
    )
except ModuleNotFoundError:  # Direct execution adds scripts/, not the repository root.
    from generate_asic_top import (  # type: ignore[no-redef]
        _mechanism_parameters,
        _packed_literal,
        _parameter_literal,
    )


def exact_tile_geometry(
    layer: dict[str, object],
    *,
    tile_width: int,
    tile_height: int,
    tile_column: int,
    tile_row: int,
) -> dict[str, int]:
    """Return the clipped global geometry for one nominal output tile."""
    if tile_width < 1 or tile_height < 1:
        raise ValueError("tile dimensions must be positive")
    if tile_column < 0 or tile_row < 0:
        raise ValueError("tile coordinates must be nonnegative")
    actor_input_height, actor_input_width = (
        int(value) for value in layer["input_hw"]  # type: ignore[index]
    )
    actor_output_height, actor_output_width = (
        int(value) for value in layer["output_hw"]  # type: ignore[index]
    )
    kernel_height, kernel_width = (
        int(value) for value in layer["kernel"]  # type: ignore[index]
    )
    stride_y, stride_x = (
        int(value) for value in layer["stride"]  # type: ignore[index]
    )
    padding_y, padding_x = (
        int(value) for value in layer.get("padding", [0, 0])  # type: ignore[union-attr]
    )
    dilation_y, dilation_x = (
        int(value) for value in layer["dilation"]  # type: ignore[index]
    )
    output_origin_x = tile_column * tile_width
    output_origin_y = tile_row * tile_height
    if output_origin_x >= actor_output_width or output_origin_y >= actor_output_height:
        raise ValueError("tile coordinates are outside the actor output")
    local_output_width = min(tile_width, actor_output_width - output_origin_x)
    local_output_height = min(tile_height, actor_output_height - output_origin_y)
    raw_input_min_x = output_origin_x * stride_x - padding_x
    raw_input_min_y = output_origin_y * stride_y - padding_y
    raw_input_max_x = (
        (output_origin_x + local_output_width - 1) * stride_x
        - padding_x
        + (kernel_width - 1) * dilation_x
    )
    raw_input_max_y = (
        (output_origin_y + local_output_height - 1) * stride_y
        - padding_y
        + (kernel_height - 1) * dilation_y
    )
    input_origin_x = max(0, raw_input_min_x)
    input_origin_y = max(0, raw_input_min_y)
    input_end_x = min(actor_input_width - 1, raw_input_max_x)
    input_end_y = min(actor_input_height - 1, raw_input_max_y)
    input_width = input_end_x - input_origin_x + 1
    input_height = input_end_y - input_origin_y + 1
    if input_width < 1 or input_height < 1:
        raise ValueError("tile has an empty input receptive halo")
    return {
        "actor_input_width": actor_input_width,
        "actor_input_height": actor_input_height,
        "actor_output_width": actor_output_width,
        "actor_output_height": actor_output_height,
        "output_origin_x": output_origin_x,
        "output_origin_y": output_origin_y,
        "output_width": local_output_width,
        "output_height": local_output_height,
        "input_origin_x": input_origin_x,
        "input_origin_y": input_origin_y,
        "input_width": input_width,
        "input_height": input_height,
        "input_offset_x": raw_input_min_x - input_origin_x,
        "input_offset_y": raw_input_min_y - input_origin_y,
    }


def exact_tile_variant_key(geometry: dict[str, int]) -> str:
    return (
        f"out_{geometry['output_height']}x{geometry['output_width']}__"
        f"halo_{geometry['input_height']}x{geometry['input_width']}__"
        f"offset_{geometry['input_offset_y']}_{geometry['input_offset_x']}"
    )


def generate_tile_top(
    model_spec_path: Path,
    output_path: Path,
    *,
    actor_name: str,
    tile_width: int = 8,
    tile_height: int = 8,
    tile_columns: int = 1,
    tile_rows: int = 1,
    tile_column: int | None = None,
    tile_row: int | None = None,
    module_name: str = "resident_actor_tile_pnr_top",
) -> None:
    if tile_width < 1 or tile_height < 1 or tile_columns < 1 or tile_rows < 1:
        raise ValueError("tile dimensions must be positive")
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    export = (model_spec_path.parent / str(spec.get("artifact_root", "."))).resolve()
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    if actor_name not in set(spec["graph"]["actor_topological_order"]):
        raise ValueError(f"{actor_name!r} is not a PLIF actor")
    layer = layers[actor_name]
    input_channels = int(layer["in_channels"])
    output_channels = int(layer["out_channels"])
    kernel_height, kernel_width = (int(value) for value in layer["kernel"])
    stride_y, stride_x = (int(value) for value in layer["stride"])
    dilation_y, dilation_x = (int(value) for value in layer["dilation"])
    padding_y, padding_x = (int(value) for value in layer.get("padding", [0, 0]))
    if (tile_column is None) != (tile_row is None):
        raise ValueError("tile_column and tile_row must be specified together")
    exact_tile = tile_column is not None
    if exact_tile and (tile_columns != 1 or tile_rows != 1):
        raise ValueError("an exact tile cannot also contain multiple child tiles")
    if exact_tile and (tile_column < 0 or tile_row < 0):
        raise ValueError("tile coordinates must be nonnegative")

    output_width = tile_width * tile_columns
    output_height = tile_height * tile_rows
    input_origin_x = 0
    input_origin_y = 0
    output_origin_x = 0
    output_origin_y = 0
    actor_output_width = output_width
    actor_output_height = output_height
    local_output_width = output_width
    local_output_height = output_height
    if exact_tile:
        geometry = exact_tile_geometry(
            layer,
            tile_width=tile_width,
            tile_height=tile_height,
            tile_column=tile_column,
            tile_row=tile_row,
        )
        actor_output_width = geometry["actor_output_width"]
        actor_output_height = geometry["actor_output_height"]
        output_origin_x = geometry["output_origin_x"]
        output_origin_y = geometry["output_origin_y"]
        local_output_width = geometry["output_width"]
        local_output_height = geometry["output_height"]
        input_origin_x = geometry["input_origin_x"]
        input_origin_y = geometry["input_origin_y"]
        input_width = geometry["input_width"]
        input_height = geometry["input_height"]
    # An interior output tile needs this exact local receptive-field halo. Using
    # PAD=0 translates global coordinates without changing cell structure.
    elif tile_columns == 1 and tile_rows == 1:
        input_width = (tile_width - 1) * stride_x + (kernel_width - 1) * dilation_x + 1
        input_height = (tile_height - 1) * stride_y + (kernel_height - 1) * dilation_y + 1
    else:
        # A small actor boundary keeps the real padding and stride so adjacent
        # child tiles exercise the production global-to-halo coordinate mapping.
        input_width = max(
            1,
            (output_width - 1) * stride_x - 2 * padding_x + (kernel_width - 1) * dilation_x + 1,
        )
        input_height = max(
            1,
            (output_height - 1) * stride_y - 2 * padding_y + (kernel_height - 1) * dilation_y + 1,
        )
    input_count = input_channels * input_width * input_height
    output_count = output_channels * local_output_width * local_output_height
    weights = _packed_literal(
        export / str(layer["weight_rom"]),
        word_bits=24,
        expected_words=int(layer["weight_count"]),
    )
    betas = _parameter_literal(export, layer, key="beta_q", rom_key="beta_rom", word_bits=24)
    thresholds = _parameter_literal(
        export, layer, key="threshold_q", rom_key="threshold_rom", word_bits=24
    )
    mechanism = _mechanism_parameters(export, layer)
    lines = [
        "`timescale 1ns/1ps",
        "// Generated from the checkpoint export; do not hand edit.",
        (
            f"// Source actor: {actor_name}; output: {local_output_height}x{local_output_width}; "
            f"child tile: {tile_height}x{tile_width}."
        ),
        f"module {module_name} (",
        "  input logic clk, input logic reset,",
        "  input logic presynaptic_valid_i, output logic presynaptic_ready_o,",
        f"  input logic [{input_count - 1}:0] presynaptic_spike_vector_i,",
        "  input logic completion_valid_i, output logic completion_ready_o,",
        "  input logic [23:0] completion_tag_i,",
        "  output logic result_valid_o, input logic result_ready_i,",
        f"  output logic [{output_count - 1}:0] spike_vector_o,",
        "  output logic [23:0] completion_tag_o, output logic error_o",
        ");",
        (
            "  resident_channelized_plif_actor #("
            if tile_columns == 1 and tile_rows == 1
            else "  tiled_resident_channelized_plif_actor #("
        ),
        f"    .INPUT_CHANNELS({input_channels}), .INPUT_WIDTH({input_width}),",
        f"    .INPUT_HEIGHT({input_height}), .OUTPUT_CHANNELS({output_channels}),",
        f"    .OUTPUT_WIDTH({actor_output_width}), .OUTPUT_HEIGHT({actor_output_height}),",
        *(
            [
                f"    .INPUT_TILE_X({input_origin_x}), .INPUT_TILE_Y({input_origin_y}),",
                f"    .OUTPUT_TILE_X({output_origin_x}), .OUTPUT_TILE_Y({output_origin_y}),",
                f"    .OUTPUT_TILE_WIDTH({local_output_width}),",
                f"    .OUTPUT_TILE_HEIGHT({local_output_height}),",
            ]
            if exact_tile
            else []
        ),
        *(
            [f"    .TILE_WIDTH({tile_width}), .TILE_HEIGHT({tile_height}),"]
            if tile_columns > 1 or tile_rows > 1
            else []
        ),
        f"    .GROUPS({int(layer['groups'])}), .KERNEL_WIDTH({kernel_width}),",
        (
            f"    .KERNEL_HEIGHT({kernel_height}), .STRIDE_X({stride_x}), "
            f".STRIDE_Y({stride_y}),"
            if exact_tile
            else f"    .KERNEL_HEIGHT({kernel_height}), .STRIDE_X(1), .STRIDE_Y(1),"
            if tile_columns == 1 and tile_rows == 1
            else (
                f"    .KERNEL_HEIGHT({kernel_height}), .STRIDE_X({stride_x}), "
                f".STRIDE_Y({stride_y}),"
            )
        ),
        f"    .DILATION_X({dilation_x}), .DILATION_Y({dilation_y}),",
        (
            f"    .PAD_X({padding_x}), .PAD_Y({padding_y}),"
            if exact_tile
            else "    .PAD_X(0), .PAD_Y(0),"
            if tile_columns == 1 and tile_rows == 1
            else f"    .PAD_X({padding_x}), .PAD_Y({padding_y}),"
        ),
        f"    .KERNEL_WEIGHTS({weights}),",
        f"    .CHANNEL_BETAS({betas}), .CHANNEL_THRESHOLDS({thresholds}),",
        f"    .ENABLE_INHIBITION({mechanism['inhibition_enabled']}),",
        f"    .ENABLE_ADAPTATION({mechanism['adaptation_enabled']}),",
        f"    .INHIBITION_STRENGTH(24'h{mechanism['inhibition_strength'] & 0xFFFFFF:06x}),",
        f"    .ADAPTATION_STRENGTH(19'h{mechanism['adaptation_strength'] & 0x7FFFF:05x}),",
        f"    .ADAPTATION_DURATION(21'h{mechanism['adaptation_duration'] & 0x1FFFFF:06x})",
        "  ) actor (.*);",
        "endmodule",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--actor", default="detail_stem")
    parser.add_argument("--tile-width", type=int, default=8)
    parser.add_argument("--tile-height", type=int, default=8)
    parser.add_argument("--tile-columns", type=int, default=1)
    parser.add_argument("--tile-rows", type=int, default=1)
    parser.add_argument("--tile-column", type=int)
    parser.add_argument("--tile-row", type=int)
    parser.add_argument("--module-name", default="resident_actor_tile_pnr_top")
    args = parser.parse_args()
    generate_tile_top(
        args.model_spec,
        args.output,
        actor_name=args.actor,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        tile_columns=args.tile_columns,
        tile_rows=args.tile_rows,
        tile_column=args.tile_column,
        tile_row=args.tile_row,
        module_name=args.module_name,
    )


if __name__ == "__main__":
    main()
