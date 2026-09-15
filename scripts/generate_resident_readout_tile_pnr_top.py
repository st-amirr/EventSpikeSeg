#!/usr/bin/env python3
"""Generate one exact resident temporal-readout tile for physical design."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.generate_asic_top import _packed_literal
except ModuleNotFoundError:
    from generate_asic_top import _packed_literal  # type: ignore[no-redef]


def generate(
    model_spec: Path,
    output: Path,
    *,
    tile_width: int,
    tile_height: int,
    module_name: str = "resident_readout_tile_pnr_top",
) -> None:
    spec = json.loads(model_spec.read_text(encoding="utf-8"))
    export = (model_spec.parent / str(spec.get("artifact_root", "."))).resolve()
    readout_name = str(spec["graph"]["current_readout"])
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    readout = layers[readout_name]
    weights = _packed_literal(
        export / str(readout["weight_rom"]),
        word_bits=24,
        expected_words=int(readout["weight_count"]),
    )
    inputs = int(readout["in_channels"])
    classes = int(readout["out_channels"])
    spatial = tile_width * tile_height
    class_width = max(1, (classes - 1).bit_length())
    x_width = max(1, (tile_width - 1).bit_length())
    y_width = max(1, (tile_height - 1).bit_length())
    prediction_bins = int(spec["timing_contract"]["prediction_bins_default"])
    lines = [
        "`timescale 1ns/1ps",
        (
            "// Checkpoint-exact "
            f"{tile_width}x{tile_height} resident readout hard-macro master."
        ),
        f"module {module_name} (",
        "  input logic clk, input logic reset,",
        "  input logic in_valid_i, output logic in_ready_o,",
        f"  input logic [{inputs * spatial - 1}:0] in_spike_vector_i,",
        "  input logic in_completion_i, input logic [23:0] in_tag_i,",
        "  output logic prediction_valid_o, input logic prediction_ready_i,",
        f"  output logic [{x_width - 1}:0] prediction_x_o,",
        f"  output logic [{y_width - 1}:0] prediction_y_o,",
        f"  output logic [{class_width - 1}:0] prediction_class_o,",
        "  output logic frame_done_valid_o, input logic frame_done_ready_i,",
        "  output logic [23:0] frame_tag_o",
        ");",
        "  resident_temporal_class_readout #(",
        f"    .INPUT_CHANNELS({inputs}), .CLASS_COUNT({classes}),",
        f"    .OUTPUT_WIDTH({tile_width}), .OUTPUT_HEIGHT({tile_height}),",
        f"    .PREDICTION_BINS({prediction_bins}), .TAG_WIDTH(24),",
        f"    .READOUT_WEIGHTS({weights})",
        "  ) readout (.*);",
        "endmodule",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tile-width", type=int, default=8)
    parser.add_argument("--tile-height", type=int, default=8)
    parser.add_argument("--module-name", default="resident_readout_tile_pnr_top")
    args = parser.parse_args()
    generate(
        args.model_spec,
        args.output,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        module_name=args.module_name,
    )


if __name__ == "__main__":
    main()
