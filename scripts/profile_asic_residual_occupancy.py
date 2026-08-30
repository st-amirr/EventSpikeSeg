#!/usr/bin/env python3
"""Replay golden ingress and profile exact residual-union output occupancy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eventspikeseg.asic.dag_reference import IntegerDAGReference, SpikeEvent


def profile_residual_occupancy(model_spec: Path, golden_input: Path) -> dict:
    reference = IntegerDAGReference(model_spec)
    archive = np.load(golden_input, allow_pickle=False)
    columns = {str(name): index for index, name in enumerate(archive["columns"].tolist())}
    rows = archive["events"]
    by_bin: dict[int, list[SpikeEvent]] = {}
    for row in rows:
        tag = int(row[columns["bin_tag"]])
        by_bin.setdefault(tag, []).append(
            SpikeEvent(
                int(row[columns["channel"]]),
                int(row[columns["y"]]),
                int(row[columns["x"]]),
            )
        )
    maxima = {
        str(node["name"]): 0
        for node in reference.graph["nodes"]
        if str(node["kind"]) == "binary_residual_or"
    }
    observed_bins = {name: 0 for name in maxima}
    for tag, events in by_bin.items():
        reference.process_bin(events, bin_tag=tag)
        for name, count in reference.last_route_counts.items():
            maxima[name] = max(maxima[name], count)
            observed_bins[name] += 1
    return {
        "format": "eventspikeseg-residual-occupancy-v1",
        "source": golden_input.name,
        "scope": "observed_fixture_only_not_a_safe_native_capacity_bound",
        "joins": [
            {"join": name, "observed_max_per_bin": maximum,
             "bins_observed": observed_bins[name]}
            for name, maximum in maxima.items()
        ],
        "global_max_observed": max(maxima.values(), default=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("golden_input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = profile_residual_occupancy(args.model_spec.resolve(), args.golden_input.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
