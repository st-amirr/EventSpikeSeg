"""Tiny-fixture dataset adapters; no large dataset download is performed."""

from pathlib import Path

import numpy as np

from .events import Event


def remap_davis346_coordinate(x: int, y: int) -> tuple[int, int]:
    """Apply the frozen FE108 DAVIS346→240×180 floor transform."""

    if not (0 <= x < 346 and 0 <= y < 260):
        raise ValueError("DAVIS346 coordinate out of bounds")
    return x * 240 // 346, y * 180 // 260


def load_event_npz(path: Path, *, remap_davis346: bool = False) -> list[Event]:
    """Load a tiny fixture containing equal-length ``t,x,y,p[,batch]`` arrays."""

    with np.load(path, allow_pickle=False) as data:
        required = {"t", "x", "y", "p"}
        if not required.issubset(data.files):
            raise ValueError(f"event fixture requires arrays: {sorted(required)}")
        arrays = [data[name] for name in ("t", "x", "y", "p")]
        if len({len(array) for array in arrays}) != 1:
            raise ValueError("event fixture arrays must have equal lengths")
        batches = data["batch"] if "batch" in data.files else np.zeros(len(arrays[0]), dtype=int)
        if len(batches) != len(arrays[0]):
            raise ValueError("batch array length differs from events")
        events = []
        for timestamp, x_value, y_value, polarity, batch in zip(*arrays, batches):
            x, y = int(x_value), int(y_value)
            if remap_davis346:
                x, y = remap_davis346_coordinate(x, y)
            events.append(Event(int(timestamp), x, y, bool(polarity), int(batch)))
        return events
