#!/usr/bin/env python3
"""Generate deterministic sparse full-DAG integer golden artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eventspikeseg.asic.dag_reference import SpikeEvent, write_golden_artifacts


def deterministic_ingress(
    *, height: int, width: int, bin_count: int, events_per_bin: int
) -> list[list[SpikeEvent]]:
    """Return reproducible event traffic spanning polarity and image quadrants."""

    if bin_count < 1 or events_per_bin < 0:
        raise ValueError("bin_count must be positive and events_per_bin non-negative")
    anchors = (
        (height // 4, width // 4),
        (height // 4, 3 * width // 4),
        (3 * height // 4, width // 4),
        (3 * height // 4, 3 * width // 4),
        (height // 2, width // 2),
    )
    bins: list[list[SpikeEvent]] = []
    for bin_index in range(bin_count):
        events: list[SpikeEvent] = []
        for event_index in range(events_per_bin):
            anchor_y, anchor_x = anchors[(event_index + bin_index) % len(anchors)]
            # Small deterministic motion avoids testing only one state address.
            y = min(max(anchor_y + ((bin_index + event_index) % 3) - 1, 0), height - 1)
            x = min(max(anchor_x + ((2 * bin_index + event_index) % 3) - 1, 0), width - 1)
            events.append(SpikeEvent((event_index + bin_index) & 1, y, x))
        bins.append(events)
    return bins


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--events-per-bin", type=int, default=128)
    parser.add_argument("--first-bin-tag", type=int, default=1)
    args = parser.parse_args()
    spec = json.loads(args.model_spec.read_text(encoding="utf-8"))
    height, width = (int(value) for value in spec["input_size"])
    bins = deterministic_ingress(
        height=height,
        width=width,
        bin_count=args.bins,
        events_per_bin=args.events_per_bin,
    )
    profile = write_golden_artifacts(
        args.model_spec,
        bins,
        args.output_dir,
        first_bin_tag=args.first_bin_tag,
    )
    print(json.dumps(profile, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
