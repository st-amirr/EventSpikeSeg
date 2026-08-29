#!/usr/bin/env python3
"""Build a reduced-geometry RTL replay package from a trained ASIC export.

Weights, channel counts, mechanisms, topology, and arithmetic remain unchanged.
Only spatial dimensions are reduced so behavioral RTL arrays can be simulated;
the package is never a physical-capacity or PPA result.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from generate_asic_golden import deterministic_ingress
from generate_asic_top import generate_top

from eventspikeseg.asic.dag_reference import write_golden_artifacts


def prepare_replay(
    source: Path,
    destination: Path,
    *,
    height: int = 8,
    width: int = 8,
    bins: int = 10,
    events_per_bin: int = 128,
) -> dict[str, int]:
    if height < 8 or width < 8 or height % 8 or width % 8:
        raise ValueError("replay height and width must be multiples of eight and at least eight")
    source_spec_path = source / "model_spec.yaml"
    spec = json.loads(source_spec_path.read_text(encoding="utf-8"))
    if spec.get("model") != "EventSpikeSeg140k" or spec.get("class_count") != 6:
        raise ValueError("RTL replay requires the active six-class EventSpikeSeg140k export")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "weights", destination / "weights", dirs_exist_ok=True)
    shutil.copytree(source / "parameters", destination / "parameters", dirs_exist_ok=True)
    for name in ("quantized_weights.npz", "class_mapping.json", "layer_graph.json"):
        shutil.copy2(source / name, destination / name)

    shapes = {
        "native": [height, width],
        "half": [height // 2, width // 2],
        "quarter": [height // 4, width // 4],
        "eighth": [height // 8, width // 8],
    }
    old_shape_tiers = {
        tuple(int(value) for value in shape): tier
        for tier, shape in spec["spatial_shapes"].items()
    }
    logical_states = 0
    for layer in spec["layers"]:
        input_tier = old_shape_tiers[tuple(int(value) for value in layer["input_hw"])]
        output_tier = old_shape_tiers[tuple(int(value) for value in layer["output_hw"])]
        layer["input_hw"] = shapes[input_tier]
        layer["output_hw"] = shapes[output_tier]
        if int(layer.get("logical_membrane_states", 0)):
            layer["logical_membrane_states"] = (
                int(layer["out_channels"])
                * int(layer["output_hw"][0])
                * int(layer["output_hw"][1])
            )
            logical_states += int(layer["logical_membrane_states"])
    spec["input_size"] = shapes["native"]
    spec["spatial_shapes"] = shapes
    spec["logical_membrane_states"] = logical_states
    spec["verification_fixture"] = {
        "kind": "reduced_spatial_real_checkpoint_RTL_replay",
        "source_export": str(source),
        "weights_parameters_channels_and_topology_unchanged": True,
        "physical_capacity_or_PPA_evidence": False,
        "native_geometry": [height, width],
    }
    replay_spec = destination / "model_spec.yaml"
    replay_spec.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    generate_top(replay_spec, destination / "eventspikeseg140k_replay_top.sv")
    ingress = deterministic_ingress(
        height=height,
        width=width,
        bin_count=bins,
        events_per_bin=events_per_bin,
    )
    profile = write_golden_artifacts(replay_spec, ingress, destination)
    profile["logical_membrane_states"] = logical_states
    (destination / "replay_profile.json").write_text(
        json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--height", type=int, default=8)
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--events-per-bin", type=int, default=128)
    args = parser.parse_args()
    profile = prepare_replay(
        args.source,
        args.destination,
        height=args.height,
        width=args.width,
        bins=args.bins,
        events_per_bin=args.events_per_bin,
    )
    print(json.dumps(profile, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
