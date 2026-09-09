#!/usr/bin/env python3
"""Prove multiprocessing preserves the serial integer-DAG result."""

from __future__ import annotations

import argparse
from pathlib import Path

from eventspikeseg.asic.dag_reference import IntegerDAGReference, SpikeEvent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    events = [
        SpikeEvent(index % 2, (index * 17) % 440, (index * 29) % 640)
        for index in range(32)
    ]
    serial = IntegerDAGReference(args.model_spec, capture_trace=False)
    parallel = IntegerDAGReference(
        args.model_spec,
        capture_trace=False,
        workers=args.workers,
        parallel_min_work=0,
    )
    serial_prediction = serial.process_bin(events, bin_tag=1)
    parallel_prediction = parallel.process_bin(events, bin_tag=1)
    assert serial_prediction is None and parallel_prediction is None
    assert parallel.last_actor_activity == serial.last_actor_activity
    assert parallel.last_route_event_counts == serial.last_route_event_counts
    assert parallel.states == serial.states
    print(
        f"Parallel integer DAG matches serial for {len(events)} events, "
        f"{len(serial.actors)} actors, and {args.workers} workers."
    )


if __name__ == "__main__":
    main()
