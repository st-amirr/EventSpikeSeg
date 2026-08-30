#!/usr/bin/env python3
"""Profile actor first-touch queue occupancy from integer golden currents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def profile_touch_occupancy(model_spec: Path, currents_npz: Path) -> dict:
    spec = json.loads(model_spec.read_text(encoding="utf-8"))
    export_dir = model_spec.parent
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    trace = np.load(currents_npz, allow_pickle=False)
    columns = {str(name): index for index, name in enumerate(trace["columns"].tolist())}
    rows = trace["currents"]
    actor_names = [str(name) for name in trace["actor_names"].tolist()]
    required = {"bin_tag", "actor_id", "channel", "y", "x"}
    if required - columns.keys():
        raise ValueError("current trace is missing occupancy columns")
    actors = []
    for actor_id, name in enumerate(actor_names):
        layer = layers[name]
        parameters = json.loads(
            (export_dir / str(layer["parameter_file"])).read_text(encoding="utf-8")
        )
        mechanism = bool(parameters.get("inhibition_enabled")) or bool(
            parameters.get("threshold_adaptation_enabled")
        )
        actor_rows = rows[rows[:, columns["actor_id"]] == actor_id]
        per_bin: dict[int, set[tuple[int, ...]]] = {}
        for row in actor_rows:
            tag = int(row[columns["bin_tag"]])
            coordinate = (int(row[columns["y"]]), int(row[columns["x"]]))
            if not mechanism:
                coordinate = (int(row[columns["channel"]]), *coordinate)
            per_bin.setdefault(tag, set()).add(coordinate)
        out_h, out_w = (int(value) for value in layer["output_hw"])
        capacity = out_h * out_w * (1 if mechanism else int(layer["out_channels"]))
        maximum = max((len(items) for items in per_bin.values()), default=0)
        actors.append(
            {
                "actor": name,
                "queue_addressing": "spatial" if mechanism else "destination",
                "logical_capacity": capacity,
                "observed_max_per_bin": maximum,
                "observed_fraction": maximum / capacity,
                "bins_observed": len(per_bin),
            }
        )
    return {
        "format": "eventspikeseg-touch-occupancy-v1",
        "source": currents_npz.name,
        "scope": "observed_fixture_only_not_a_safe_native_capacity_bound",
        "actors": actors,
        "global_max_observed": max(item["observed_max_per_bin"] for item in actors),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("currents", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = profile_touch_occupancy(args.model_spec.resolve(), args.currents.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
