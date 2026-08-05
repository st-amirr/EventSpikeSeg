"""Dataset adapters for tiny fixtures and native MEVDT event streams."""

import csv
import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
from torch import Tensor

from .config import EventBinningConfig
from .events import Event, bin_events

MEVDT_TIMESTAMP_UNITS_PER_US = 1_000
MEVDT_VALIDATION_PARTITION_SEED = 20260804


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


@dataclass(frozen=True)
class MEVDTTrackAnnotation:
    """One timestamped COCO tracking box with a persistent sequence-local identity."""

    timestamp_ns: int
    track_id: str
    box: MEVDTBox


def split_mevdt_train_sequences(
    records: list[MEVDTFrameRecord],
    *,
    validation_fraction: float = 0.2,
    seed: int = MEVDT_VALIDATION_PARTITION_SEED,
) -> tuple[list[MEVDTFrameRecord], list[MEVDTFrameRecord]]:
    """Create deterministic, scene-stratified train/validation sequence partitions."""

    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between zero and one")
    by_scene: dict[str, list[str]] = {}
    for record in records:
        if record.split != "train":
            raise ValueError("only official training records may be partitioned")
        by_scene.setdefault(record.scene, []).append(record.sequence)
    generator = random.Random(seed)
    validation_keys: set[tuple[str, str]] = set()
    for scene, scene_sequences in sorted(by_scene.items()):
        sequences = sorted(set(scene_sequences))
        if len(sequences) < 2:
            raise ValueError(f"scene {scene} needs at least two sequences for validation")
        generator.shuffle(sequences)
        validation_count = max(
            1,
            min(len(sequences) - 1, round(len(sequences) * validation_fraction)),
        )
        validation_keys.update((scene, sequence) for sequence in sequences[:validation_count])
    training = [
        record for record in records if (record.scene, record.sequence) not in validation_keys
    ]
    validation = [
        record for record in records if (record.scene, record.sequence) in validation_keys
    ]
    if not training or not validation:
        raise ValueError("MEVDT train/validation partition is empty")
    return training, validation


def chronological_mevdt_records(
    records: list[MEVDTFrameRecord],
) -> list[MEVDTFrameRecord]:
    """Sort records by scene, sequence, and exact annotation timestamp."""

    return sorted(records, key=lambda record: (record.scene, record.sequence, record.timestamp_ns))


def remap_davis346_coordinate(x: int, y: int) -> tuple[int, int]:
    """Apply the frozen generic DAVIS346-to-240x180 floor transform."""

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


@lru_cache(maxsize=128)
def _load_mevdt_tracking_coco(path: Path) -> dict[int, tuple[MEVDTTrackAnnotation, ...]]:
    """Load one sequence's COCO tracking annotations keyed by exact timestamp."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    image_timestamps: dict[int, int] = {}
    for image in payload.get("images", []):
        try:
            image_timestamps[int(image["id"])] = int(Path(image["file_name"]).stem)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid MEVDT tracking image row: {path}") from error
    grouped: dict[int, list[MEVDTTrackAnnotation]] = {}
    for annotation in payload.get("annotations", []):
        try:
            timestamp_ns = image_timestamps[int(annotation["image_id"])]
            x, y, width, height = (float(value) for value in annotation["bbox"])
            box = MEVDTBox(
                int(annotation["category_id"]), x, y, x + width, y + height
            )
            track_id = str(annotation["track_id"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid MEVDT tracking annotation: {path}") from error
        grouped.setdefault(timestamp_ns, []).append(
            MEVDTTrackAnnotation(timestamp_ns, track_id, box)
        )
    return {
        timestamp: tuple(sorted(items, key=lambda item: item.track_id))
        for timestamp, items in grouped.items()
    }


def load_mevdt_tracking_sequence(
    root: Path,
    *,
    split: str,
    scene: str,
    sequence: str,
) -> dict[int, tuple[MEVDTTrackAnnotation, ...]]:
    """Load official MEVDT tracking identities for one train or test sequence."""

    if split not in {"train", "test"}:
        raise ValueError("MEVDT tracking split must be 'train' or 'test'")
    path = (
        root.expanduser().resolve()
        / "labels"
        / "tracking_labels"
        / split
        / scene
        / sequence
        / f"{sequence}-coco.json"
    )
    if not path.is_file():
        raise FileNotFoundError(f"missing MEVDT tracking annotations: {path}")
    return _load_mevdt_tracking_coco(path)


@lru_cache(maxsize=64)
def _load_mevdt_event_stream(path: Path) -> tuple[np.ndarray, ...]:
    """Parse one sequence CSV once and cache compact, sorted event columns."""

    timestamps: list[int] = []
    xs: list[int] = []
    ys: list[int] = []
    polarities: list[int] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["ts", "x", "y", "p"]:
            raise ValueError(f"MEVDT event CSV must have header ts,x,y,p: {path}")
        previous_timestamp = -1
        for row in reader:
            timestamp = int(row["ts"])
            polarity = int(row["p"])
            if timestamp < previous_timestamp:
                raise ValueError(f"MEVDT event timestamps are not sorted: {path}")
            if polarity not in {0, 1}:
                raise ValueError(f"invalid MEVDT polarity {polarity}")
            previous_timestamp = timestamp
            timestamps.append(timestamp)
            xs.append(int(row["x"]))
            ys.append(int(row["y"]))
            polarities.append(polarity)
    return (
        np.asarray(timestamps, dtype=np.int64),
        np.asarray(xs, dtype=np.int16),
        np.asarray(ys, dtype=np.int16),
        np.asarray(polarities, dtype=np.bool_),
    )


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
    timestamps, xs, ys, polarities = _load_mevdt_event_stream(record.event_csv_path)
    first = int(np.searchsorted(timestamps, start_ns, side="left"))
    last = int(np.searchsorted(timestamps, end_ns, side="left"))
    events = [
        Event(
            timestamp_us=int((timestamps[index] - start_ns) // MEVDT_TIMESTAMP_UNITS_PER_US),
            x=int(xs[index]),
            y=int(ys[index]),
            polarity=bool(polarities[index]),
        )
        for index in range(first, last)
    ]
    tensor = bin_events(events, config, num_bins=window_steps, start_us=0)
    return MEVDTSample(tensor, load_mevdt_boxes(record.label_path), record)
