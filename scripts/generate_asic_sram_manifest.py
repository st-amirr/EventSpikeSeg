#!/usr/bin/env python3
"""Emit exact logical SRAM-bank requirements for an exported ASIC DAG."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _address_width(depth: int) -> int:
    return max(1, (depth - 1).bit_length())


def _stream_geometries(spec: dict[str, Any]) -> dict[str, tuple[int, int, int]]:
    graph = spec["graph"]
    actors = set(graph["actor_topological_order"])
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph["edges"]:
        if str(edge["destination"]) != "prediction":
            incoming[str(edge["destination"])].append(edge)
    kinds = {str(node["name"]): str(node["kind"]) for node in graph["nodes"]}
    height, width = (int(value) for value in spec["input_size"])
    geometry = {"input": (height, width, int(spec["input_channels"]))}
    for raw_name in graph["node_topological_order"]:
        name = str(raw_name)
        if name == "input":
            continue
        if name in actors:
            layer = layers[name]
            out_h, out_w = (int(value) for value in layer["output_hw"])
            geometry[name] = (out_h, out_w, int(layer["out_channels"]))
            continue
        if name in {str(graph["current_readout"]), "prediction"}:
            continue
        inputs = [(geometry[str(edge["source"])], edge) for edge in incoming[name]]
        kind = kinds[name]
        if kind == "nearest_event_fanout_2x":
            in_h, in_w, channels = inputs[0][0]
            geometry[name] = (2 * in_h, 2 * in_w, channels)
        elif kind == "channel_concat":
            geometry[name] = (
                max(item[0][0] for item in inputs),
                max(item[0][1] for item in inputs),
                max(int(edge.get("channel_offset", 0)) + item[2]
                    for item, edge in inputs),
            )
        else:
            if kind == "binary_residual_or" and len({item for item, _ in inputs}) != 1:
                raise ValueError(f"residual join {name} has mismatched geometry")
            geometry[name] = tuple(max(item[index] for item, _ in inputs)
                                   for index in range(3))
    return geometry


def generate_manifest(model_spec_path: Path) -> dict[str, Any]:
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    export_dir = model_spec_path.parent
    graph = spec["graph"]
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    banks: list[dict[str, Any]] = []

    def add(owner: str, kind: str, width: int, depth: int, instances: int = 1) -> None:
        banks.append({
            "owner": owner, "kind": kind, "word_bits": width, "depth": depth,
            "instances": instances, "total_bits": width * depth * instances,
            "ports": "1RW", "simultaneous_read_write": False,
            "macro_required": True,
        })

    for name in graph["actor_topological_order"]:
        layer = layers[str(name)]
        channels = int(layer["out_channels"])
        out_h, out_w = (int(value) for value in layer["output_hw"])
        spatial = out_h * out_w
        destinations = channels * spatial
        parameters = json.loads(
            (export_dir / str(layer["parameter_file"])).read_text(encoding="utf-8")
        )
        mechanism = bool(parameters.get("inhibition_enabled")) or bool(
            parameters.get("threshold_adaptation_enabled")
        )
        if mechanism:
            add(str(name), "mechanism_channel_state", 65, spatial, channels)
            if bool(parameters.get("threshold_adaptation_enabled")):
                add(str(name), "adaptation_channel_state", 32, spatial, channels)
            add(str(name), "spatial_seen", 1, spatial)
            add(str(name), "spatial_touch_queue", _address_width(spatial), spatial)
        else:
            add(str(name), "simple_neuron_state", 66, destinations)
            add(str(name), "destination_touch_queue", _address_width(destinations), destinations)

    geometries = _stream_geometries(spec)
    kinds = {str(node["name"]): str(node["kind"]) for node in graph["nodes"]}
    for name, kind in kinds.items():
        if kind != "binary_residual_or":
            continue
        height, width, channels = geometries[name]
        addresses = height * width * channels
        add(name, "residual_seen", 1, addresses)
        add(name, "residual_address_queue", _address_width(addresses), addresses)

    readout = layers[str(graph["current_readout"])]
    out_h, out_w = (int(value) for value in readout["output_hw"])
    add(str(graph["current_readout"]), "temporal_score", 24 * int(readout["out_channels"]),
        out_h * out_w)

    totals: dict[str, int | float] = {
        "bank_entries": len(banks),
        "macro_instances": sum(int(bank["instances"]) for bank in banks),
        "total_bits": sum(int(bank["total_bits"]) for bank in banks),
    }
    totals["total_MiB"] = int(totals["total_bits"]) / 8 / 1024 / 1024
    return {
        "format": "eventspikeseg-sram-manifest-v1",
        "model_spec": model_spec_path.name,
        "assumptions": {
            "residual_queue_capacity": "full_logical_address_space",
            "actor_touch_queue_capacity": "full_logical_address_space",
            "physical_binding": "required_before_PPA",
        },
        "banks": banks,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = generate_manifest(args.model_spec.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
