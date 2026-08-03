"""Dataset adapters for tiny fixtures and native MEVDT event streams."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from torch import Tensor

from .config import EventBinningConfig
from .events import Event, bin_events

MEVDT_TIMESTAMP_UNITS_PER_US = 1_000


@dataclass(frozen=True)
class MEVDTBox:
    """One MEVDT detection in native ``x_min,y_min,x_max,y_max`` coordinates."""

    class_id: int
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def __post_init__(self) -> None:
        tolerance = 1e-6
        if -tolerance <= self.x_min < 0.0:
            object.__setattr__(self, "x_min", 0.0)
        if 240.0 < self.x_max <= 240.0 + tolerance:
            object.__setattr__(self, "x_max", 240.0)
        if -tolerance <= self.y_min < 0.0:
            object.__setattr__(self, "y_min", 0.0)
        if 180.0 < self.y_max <= 180.0 + tolerance:
            object.__setattr__(self, "y_max", 180.0)
        if self.class_id < 0:
            raise ValueError("MEVDT class_id cannot be negative")
        if not (0.0 <= self.x_min < self.x_max <= 240.0):
            raise ValueError("MEVDT x coordinates are invalid")
        if not (0.0 <= self.y_min < self.y_max <= 180.0):
            raise ValueError("MEVDT y coordinates are invalid")

    @property
    def area(self) -> float:
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)


@dataclass(frozen=True)
class MEVDTFrameRecord:
    """Paths and synchronization metadata for one annotated MEVDT frame."""

    split: str
    scene: str
    sequence: str
    timestamp_ns: int
    event_csv_path: Path
    label_path: Path


@dataclass(frozen=True)
class MEVDTSample:
    """A fixed-duration event tensor and the boxes at its end timestamp."""

    events: Tensor
    boxes: tuple[MEVDTBox, ...]
    record: MEVDTFrameRecord


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


def discover_mevdt_frames(
    root: Path,
    *,
    split: str,
    sample_duration: str = "org_rate",
) -> list[MEVDTFrameRecord]:
    """Index frames from MEVDT's authoritative object-detection split CSV."""

    if split not in {"train", "test"}:
        raise ValueError("MEVDT split must be 'train' or 'test'")
    root = root.expanduser().resolve()
    sequences = root / "sequences" / split
    labels = root / "labels" / "detection_labels" / split
    if not sequences.is_dir() or not labels.is_dir():
        raise FileNotFoundError(f"invalid MEVDT root or incomplete {split} split: {root}")

    split_index = root / "data_splits" / f"MEVDT_{sample_duration}_{split}.csv"
    if not split_index.is_file():
        raise FileNotFoundError(f"missing official MEVDT split index: {split_index}")

    records: list[MEVDTFrameRecord] = []
    with split_index.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = ["events_file_path", "image_path", "labels_file_path"]
        if reader.fieldnames != expected:
            raise ValueError(f"unexpected MEVDT split header: {split_index}")
        label_paths = [root / row["labels_file_path"] for row in reader]
    for label_path in label_paths:
        try:
            label_path.resolve().relative_to(root)
        except ValueError as error:
            raise ValueError(f"MEVDT split path escapes dataset root: {label_path}") from error
        if not label_path.is_file():
            raise FileNotFoundError(f"missing indexed MEVDT label: {label_path}")
        scene = label_path.parent.parent.name
        sequence = label_path.parent.name
        event_csv = sequences / scene / sequence / f"{sequence}_events.csv"
        if not event_csv.is_file():
            raise FileNotFoundError(f"missing sequence event stream: {event_csv}")
        try:
            timestamp_ns = int(label_path.stem)
        except ValueError as error:
            raise ValueError(f"non-numeric MEVDT label timestamp: {label_path}") from error
        records.append(
            MEVDTFrameRecord(
                split=split,
                scene=scene,
                sequence=sequence,
                timestamp_ns=timestamp_ns,
                event_csv_path=event_csv,
                label_path=label_path,
            )
        )
    if not records:
        raise ValueError(f"no MEVDT frames found in {split_index}")
    return records


def load_mevdt_boxes(path: Path) -> tuple[MEVDTBox, ...]:
    """Load MEVDT detection rows: ``class x_min y_min x_max y_max``."""

    boxes: list[MEVDTBox] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.split()
            if not fields:
                continue
            if len(fields) != 5:
                raise ValueError(f"invalid MEVDT label row at {path}:{line_number}")
            try:
                class_id = int(fields[0])
                x_min, y_min, x_max, y_max = (float(value) for value in fields[1:])
            except ValueError as error:
                raise ValueError(
                    f"non-numeric MEVDT label row at {path}:{line_number}"
                ) from error
            try:
                boxes.append(MEVDTBox(class_id, x_min, y_min, x_max, y_max))
            except ValueError as error:
                raise ValueError(f"{error} at {path}:{line_number}") from error
    return tuple(boxes)


def load_mevdt_window(
    record: MEVDTFrameRecord,
    *,
    config: Optional[EventBinningConfig] = None,
    window_steps: int = 20,
) -> MEVDTSample:
    """Load the event window ending at an annotation and bin it to TNCHW.

    MEVDT CSV timestamps are integer nanoseconds. Filtering is performed in nanoseconds
    before conversion to relative microseconds so the annotation boundary remains exact.
    """

    config = config or EventBinningConfig()
    if config.width != 240 or config.height != 180:
        raise ValueError("MEVDT native event windows require 240x180 configuration")
    if window_steps <= 0:
        raise ValueError("window_steps must be positive")
    end_ns = record.timestamp_ns
    start_ns = end_ns - window_steps * config.bin_duration_us * MEVDT_TIMESTAMP_UNITS_PER_US
    events: list[Event] = []
    with record.event_csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["ts", "x", "y", "p"]:
            raise ValueError(
                f"MEVDT event CSV must have header ts,x,y,p: {record.event_csv_path}"
            )
        for row in reader:
            timestamp_ns = int(row["ts"])
            if timestamp_ns < start_ns:
                continue
            if timestamp_ns >= end_ns:
                break
            polarity = int(row["p"])
            if polarity not in {0, 1}:
                raise ValueError(f"invalid MEVDT polarity {polarity}")
            events.append(
                Event(
                    timestamp_us=(timestamp_ns - start_ns) // MEVDT_TIMESTAMP_UNITS_PER_US,
                    x=int(row["x"]),
                    y=int(row["y"]),
                    polarity=bool(polarity),
                )
            )
    tensor = bin_events(events, config, num_bins=window_steps, start_us=0)
    return MEVDTSample(tensor, load_mevdt_boxes(record.label_path), record)
