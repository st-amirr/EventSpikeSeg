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


def generate_tile_top(
    model_spec_path: Path,
    output_path: Path,
    *,
    actor_name: str,
    tile_width: int = 8,
    tile_height: int = 8,
    tile_columns: int = 1,
    tile_rows: int = 1,
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
    output_width = tile_width * tile_columns
    output_height = tile_height * tile_rows
    # An interior output tile needs this exact local receptive-field halo. Using
    # PAD=0 translates global coordinates without changing cell structure.
    if tile_columns == 1 and tile_rows == 1:
        input_width = (tile_width - 1) * stride_x + (kernel_width - 1) * dilation_x + 1
        input_height = (tile_height - 1) * stride_y + (kernel_height - 1) * dilation_y + 1
    else:
        # A small actor boundary keeps the real padding and stride so adjacent
        # child tiles exercise the production global-to-halo coordinate mapping.
        input_width = max(
            1,
            (output_width - 1) * stride_x
            - 2 * padding_x
            + (kernel_width - 1) * dilation_x
            + 1,
        )
        input_height = max(
            1,
            (output_height - 1) * stride_y
            - 2 * padding_y
            + (kernel_height - 1) * dilation_y
            + 1,
        )
    input_count = input_channels * input_width * input_height
    output_count = output_channels * output_width * output_height
    weights = _packed_literal(
        export / str(layer["weight_rom"]),
        word_bits=8,
        expected_words=int(layer["weight_count"]),
    )
    betas = _parameter_literal(
        export, layer, key="beta_q", rom_key="beta_rom", word_bits=16
    )
    thresholds = _parameter_literal(
        export, layer, key="threshold_q", rom_key="threshold_rom", word_bits=16
    )
    mechanism = _mechanism_parameters(export, layer)
    lines = [
        "`timescale 1ns/1ps",
        "// Generated from the checkpoint export; do not hand edit.",
        (
            f"// Source actor: {actor_name}; output: {output_height}x{output_width}; "
            f"child tile: {tile_height}x{tile_width}."
        ),
        f"module {module_name} (",
        "  input logic clk, input logic reset,",
        "  input logic presynaptic_valid_i, output logic presynaptic_ready_o,",
        f"  input logic [{input_count-1}:0] presynaptic_spike_vector_i,",
        "  input logic completion_valid_i, output logic completion_ready_o,",
        "  input logic [23:0] completion_tag_i,",
        "  output logic result_valid_o, input logic result_ready_i,",
        f"  output logic [{output_count-1}:0] spike_vector_o,",
        "  output logic [23:0] completion_tag_o, output logic error_o",
        ");",
        (
            "  resident_channelized_plif_actor #(" if tile_columns == 1 and tile_rows == 1
            else "  tiled_resident_channelized_plif_actor #("
        ),
        f"    .INPUT_CHANNELS({input_channels}), .INPUT_WIDTH({input_width}),",
        f"    .INPUT_HEIGHT({input_height}), .OUTPUT_CHANNELS({output_channels}),",
        f"    .OUTPUT_WIDTH({output_width}), .OUTPUT_HEIGHT({output_height}),",
        *(
            [f"    .TILE_WIDTH({tile_width}), .TILE_HEIGHT({tile_height}),"]
            if tile_columns > 1 or tile_rows > 1
            else []
        ),
        f"    .GROUPS({int(layer['groups'])}), .KERNEL_WIDTH({kernel_width}),",
        (
            f"    .KERNEL_HEIGHT({kernel_height}), .STRIDE_X(1), .STRIDE_Y(1),"
            if tile_columns == 1 and tile_rows == 1
            else f"    .KERNEL_HEIGHT({kernel_height}), .STRIDE_X({stride_x}), .STRIDE_Y({stride_y}),"
        ),
        f"    .DILATION_X({dilation_x}), .DILATION_Y({dilation_y}),",
        (
            "    .PAD_X(0), .PAD_Y(0),"
            if tile_columns == 1 and tile_rows == 1
            else f"    .PAD_X({padding_x}), .PAD_Y({padding_y}),"
        ),
        f"    .KERNEL_WEIGHTS({weights}),",
        f"    .CHANNEL_BETAS({betas}), .CHANNEL_THRESHOLDS({thresholds}),",
        f"    .ENABLE_INHIBITION({mechanism['inhibition_enabled']}),",
        f"    .ENABLE_ADAPTATION({mechanism['adaptation_enabled']}),",
        f"    .INHIBITION_STRENGTH(16'h{mechanism['inhibition_strength'] & 0xFFFF:04x}),",
        f"    .ADAPTATION_STRENGTH(16'h{mechanism['adaptation_strength'] & 0xFFFF:04x}),",
        f"    .ADAPTATION_DURATION(16'h{mechanism['adaptation_duration'] & 0xFFFF:04x})",
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
    args = parser.parse_args()
    generate_tile_top(
        args.model_spec,
        args.output,
        actor_name=args.actor,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        tile_columns=args.tile_columns,
        tile_rows=args.tile_rows,
    )


if __name__ == "__main__":
    main()
