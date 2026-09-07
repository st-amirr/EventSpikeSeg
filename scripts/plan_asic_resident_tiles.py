#!/usr/bin/env python3
"""Plan exact spatial tiles for the register-resident PLIF ASIC."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def plan_tiles(
    model_spec_path: Path,
    *,
    tile_width: int = 8,
    tile_height: int = 8,
    current_width: int = 32,
    adaptation_age_width: int = 6,
    adaptation_amplitude_width: int = 19,
) -> dict[str, Any]:
    if tile_width < 1 or tile_height < 1:
        raise ValueError("tile dimensions must be positive")
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    export = (model_spec_path.parent / str(spec.get("artifact_root", "."))).resolve()
    actors = set(spec["graph"]["actor_topological_order"])
    layers = [layer for layer in spec["layers"] if layer["name"] in actors]
    state_bits_per_plif = current_width
    adaptation_bits_per_plif = adaptation_age_width + adaptation_amplitude_width
    actor_plans: list[dict[str, Any]] = []

    for layer in layers:
        height, width = (int(value) for value in layer["output_hw"])
        input_height, input_width = (int(value) for value in layer["input_hw"])
        channels = int(layer["out_channels"])
        input_channels = int(layer["in_channels"])
        kernel_height, kernel_width = (int(value) for value in layer["kernel"])
        stride_y, stride_x = (int(value) for value in layer["stride"])
        padding_y, padding_x = (int(value) for value in layer["padding"])
        dilation_y, dilation_x = (int(value) for value in layer["dilation"])
        parameter_path = export / str(layer["parameter_file"])
        parameters = json.loads(parameter_path.read_text(encoding="utf-8"))
        adaptation_enabled = bool(parameters.get("threshold_adaptation_enabled", False))
        tile_shape_counts: dict[str, int] = {}
        tile_plifs = 0
        tile_state_bits = 0
        receptive_halo_input_bits = 0
        receptive_halo_shapes: dict[str, int] = {}
        for y in range(0, height, tile_height):
            for x in range(0, width, tile_width):
                local_width = min(tile_width, width - x)
                local_height = min(tile_height, height - y)
                neurons = channels * local_width * local_height
                state_bits = neurons * (
                    state_bits_per_plif
                    + (adaptation_bits_per_plif if adaptation_enabled else 0)
                )
                shape = f"{local_height}x{local_width}"
                tile_shape_counts[shape] = tile_shape_counts.get(shape, 0) + 1
                tile_plifs += neurons
                tile_state_bits += state_bits
                input_min_x = max(0, x * stride_x - padding_x)
                input_min_y = max(0, y * stride_y - padding_y)
                input_max_x = min(
                    input_width - 1,
                    (x + local_width - 1) * stride_x
                    - padding_x
                    + (kernel_width - 1) * dilation_x,
                )
                input_max_y = min(
                    input_height - 1,
                    (y + local_height - 1) * stride_y
                    - padding_y
                    + (kernel_height - 1) * dilation_y,
                )
                halo_width = input_max_x - input_min_x + 1
                halo_height = input_max_y - input_min_y + 1
                if halo_width < 1 or halo_height < 1:
                    raise RuntimeError(f"{layer['name']} tile has an empty input halo")
                halo_shape = f"{halo_height}x{halo_width}"
                receptive_halo_shapes[halo_shape] = (
                    receptive_halo_shapes.get(halo_shape, 0) + 1
                )
                receptive_halo_input_bits += input_channels * halo_height * halo_width
        logical_plifs = channels * height * width
        if tile_plifs != logical_plifs:
            raise RuntimeError(f"{layer['name']} tile plan does not conserve PLIFs")
        actor_plans.append(
            {
                "name": layer["name"],
                "channels": channels,
                "output_hw": [height, width],
                "tile_grid": [math.ceil(height / tile_height), math.ceil(width / tile_width)],
                "tile_count": sum(tile_shape_counts.values()),
                "tile_shape_counts": tile_shape_counts,
                "logical_plifs": logical_plifs,
                "adaptation_enabled": adaptation_enabled,
                "resident_state_bits": tile_state_bits,
                "static_weight_bits": int(layer["weight_count"]) * 24,
                "receptive_halo_shape_counts": receptive_halo_shapes,
                "receptive_halo_input_bits": receptive_halo_input_bits,
                "full_bitmap_broadcast_input_bits": (
                    input_channels * input_height * input_width
                    * sum(tile_shape_counts.values())
                ),
            }
        )

    total_plifs = sum(actor["logical_plifs"] for actor in actor_plans)
    total_state_bits = sum(actor["resident_state_bits"] for actor in actor_plans)
    total_halo_input_bits = sum(
        actor["receptive_halo_input_bits"] for actor in actor_plans
    )
    total_broadcast_input_bits = sum(
        actor["full_bitmap_broadcast_input_bits"] for actor in actor_plans
    )
    return {
        "schema_version": 1,
        "architecture": "spatially_tiled_register_resident_plif",
        "model_spec": str(model_spec_path),
        "model_spec_sha256": _sha256(model_spec_path),
        "checkpoint_metadata": spec.get("checkpoint", {}),
        "tile_nominal_hw": [tile_height, tile_width],
        "state_widths": {
            "combined_accumulator": current_width,
            "adaptation_age": adaptation_age_width,
            "adaptation_amplitude": adaptation_amplitude_width,
        },
        "actors": actor_plans,
        "totals": {
            "actor_count": len(actor_plans),
            "tile_count": sum(actor["tile_count"] for actor in actor_plans),
            "logical_plifs": total_plifs,
            "resident_state_bits": total_state_bits,
            "resident_state_bytes_equivalent": math.ceil(total_state_bits / 8),
            "static_weight_bits": sum(actor["static_weight_bits"] for actor in actor_plans),
            "receptive_halo_input_bits": total_halo_input_bits,
            "full_bitmap_broadcast_input_bits": total_broadcast_input_bits,
            "input_wiring_reduction_fraction": (
                1.0 - total_halo_input_bits / total_broadcast_input_bits
            ),
        },
        "invariant": (
            "Tiling changes hierarchy only: every PLIF combined accumulator/adaptation value "
            "remains a dedicated local state element; no addressed runtime state memory is added."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tile-width", type=int, default=8)
    parser.add_argument("--tile-height", type=int, default=8)
    args = parser.parse_args()
    result = plan_tiles(
        args.model_spec, tile_width=args.tile_width, tile_height=args.tile_height
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2))


if __name__ == "__main__":
    main()
