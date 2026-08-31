"""Temporal semantic data loading for DDD17 and raw-event DSEC.

The active representation is made directly from one installed Ev-SegNet NumPy
tensor and its aligned semantic mask:

``timestamp-events``
    One 50 ms six-channel Ev-SegNet interval. Histogram channels provide ON/OFF
    synaptic strength, normalized timestamp means schedule arrival, and timestamp
    standard deviations describe temporal spread. Each item is ``[6, H, W]``;
    the model's input adapter converts it into timestamp-ordered synaptic events.

The loader never synthesizes a multi-file time axis. Consecutive records remain
ordered so the model can carry PLIF state across the stream. Sequence metadata is
required both for leakage-safe partitioning and for state reset boundaries.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

try:  # Registers the Blosc compression filters used by official DSEC event files.
    import hdf5plugin  # noqa: F401
except ImportError:  # pragma: no cover - exercised only by an incomplete installation
    hdf5plugin = None

import h5py
import numpy as np
import torch
from PIL import Image
from torch import Tensor
from torch.nn import functional as F
from torch.utils.data import Dataset

DDD17_CLASS_NAMES = ("flat", "construction+sky", "object", "nature", "human", "vehicle")
DDD17_CLASS_COUNT = len(DDD17_CLASS_NAMES)
IGNORE_INDEX = 255
SPLITS = ("train", "test")
INPUT_MODES = ("timestamp-events",)
TEMPORAL_PROTOCOL_VERSION = "ddd17-timestamp-v3"
EVSEG_INTEGRATION_WINDOW_US = 50_000
DEFAULT_INTERNAL_UPDATES = 10
DEFAULT_MANIFEST_NAME = "ddd17_temporal_manifest.json"
DEFAULT_DDD17_ROOT = Path(r"C:\Users\stamir\Desktop\Dataset\DDD17")

class TemporalMetadataError(ValueError):
    """Raised when chronological grouping cannot be established safely."""


@dataclass(frozen=True)
class DDD17Record:
    split: str
    event_path: Path
    label_path: Path
    sequence_id: str
    frame_index: int

    def identity(self, root: Path | None = None) -> dict[str, object]:
        def path_value(path: Path | None) -> str | None:
            if path is None:
                return None
            if root is not None:
                try:
                    return str(path.resolve().relative_to(root.resolve()))
                except ValueError:
                    pass
            return str(path)

        return {
            "split": self.split,
            "event": path_value(self.event_path),
            "label": path_value(self.label_path),
            "sequence_id": self.sequence_id,
            "frame_index": self.frame_index,
        }


@dataclass(frozen=True)
class DDD17Inspection:
    root: str
    records: dict[str, int]
    sequences: dict[str, int]
    formats: dict[str, int]
    manifest: str | None
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TemporalProtocol:
    version: str
    input_mode: str
    input_channels: int
    integration_window_us: int
    internal_updates: int
    event_clock_us: int
    stateful_stream: bool
    validation_fraction: float
    manifest_digest: str
    training_sequences: tuple[str, ...]
    validation_sequences: tuple[str, ...]
    training_record_ids: tuple[tuple[str, int], ...]
    validation_record_ids: tuple[tuple[str, int], ...]
    validation_record_digest: str
    timing_mode: str = "fixed-step"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["training_sequences"] = list(self.training_sequences)
        payload["validation_sequences"] = list(self.validation_sequences)
        payload["training_record_ids"] = [list(value) for value in self.training_record_ids]
        payload["validation_record_ids"] = [
            list(value) for value in self.validation_record_ids
        ]
        return payload

    @property
    def fingerprint(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def resolve_ddd17_root(root: Path | str | None = None) -> Path:
    return (DEFAULT_DDD17_ROOT if root is None else Path(root)).expanduser().resolve()


def resolve_manifest_path(root: Path, manifest: Path | str | None = None) -> Path:
    if manifest is None:
        return root / DEFAULT_MANIFEST_NAME
    path = Path(manifest).expanduser()
    if path.is_absolute():
        return path.resolve()
    # Accept either a path relative to the dataset root or an explicitly supplied
    # path relative to the current working directory.
    if path.exists():
        return path.resolve()
    return (root / path).resolve()


def _manifest_record(root: Path, split: str, item: dict[str, Any]) -> DDD17Record:
    required = {"event", "label", "sequence_id", "frame_index"}
    missing = sorted(required.difference(item))
    if missing:
        raise TemporalMetadataError(f"manifest {split} entry missing {missing}")

    def local_path(value: str | None) -> Path | None:
        if value is None:
            return None
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    sequence_id = str(item["sequence_id"]).strip()
    if not sequence_id or sequence_id == "REQUIRED_SEQUENCE_ID":
        raise TemporalMetadataError(
            f"manifest {split} entry has unresolved sequence_id at frame {item['frame_index']}"
        )

    return DDD17Record(
        split=split,
        event_path=local_path(str(item["event"])) or root,
        label_path=local_path(str(item["label"])) or root,
        sequence_id=sequence_id,
        frame_index=int(item["frame_index"]),
    )


def load_temporal_manifest(root: Path, manifest: Path | str | None = None) -> dict[str, Any]:
    path = resolve_manifest_path(root, manifest)
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TemporalMetadataError("temporal manifest must be a JSON object")
    if payload.get("schema_version") != 1:
        version = payload.get("schema_version")
        raise TemporalMetadataError(
            f"unsupported temporal manifest schema_version={version!r}; expected 1"
        )
    for split in SPLITS:
        if split not in payload or not isinstance(payload[split], list):
            raise TemporalMetadataError(f"temporal manifest must contain a {split!r} list")
    return payload


def discover_ddd17_records(
    root: Path | str | None = None,
    split: str = "train",
    *,
    manifest: Path | str | None = None,
) -> list[DDD17Record]:
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")
    root = resolve_ddd17_root(root)
    if not root.is_dir():
        raise FileNotFoundError(f"DDD17 root does not exist: {root}")

    manifest_path = resolve_manifest_path(root, manifest)
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"required DDD17 temporal manifest not found: {manifest_path}"
        )
    payload = load_temporal_manifest(root, manifest_path)
    items = payload.get(split, [])
    records = [_manifest_record(root, split, item) for item in items]
    return sorted(records, key=lambda r: (r.sequence_id, r.frame_index))


def manifest_digest(
    root: Path | str | None = None,
    *,
    manifest: Path | str | None = None,
) -> str:
    root = resolve_ddd17_root(root)
    path = resolve_manifest_path(root, manifest)
    if not path.is_file():
        raise FileNotFoundError(f"required DDD17 temporal manifest not found: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _load_record_events(record: DDD17Record) -> np.ndarray:
    return np.asarray(np.load(record.event_path, allow_pickle=False))


def _load_record_mask(record: DDD17Record) -> np.ndarray:
    with Image.open(record.label_path) as image:
        return np.asarray(image)


def _canonical_events(array: np.ndarray) -> Tensor:
    tensor = torch.as_tensor(array).float().squeeze()
    if tensor.ndim != 3:
        raise ValueError(f"expected a 3-D Ev-SegNet event image, got {tuple(tensor.shape)}")
    if tensor.shape[0] == 6:
        channels_first = tensor
    elif tensor.shape[-1] == 6:
        channels_first = tensor.permute(2, 0, 1)
    else:
        raise ValueError(f"Ev-SegNet samples must contain six channels, got {tuple(tensor.shape)}")
    return torch.nan_to_num(channels_first, nan=0.0, posinf=0.0, neginf=0.0)


def _canonical_timestamp_statistics(array: np.ndarray) -> Tensor:
    """Decode one Ev-SegNet interval for timestamp-driven input synapses.

    The distributed tensors store two histograms first, followed by
    ``mean_0, std_0, mean_1, std_1``. Histogram background is ``-1``;
    timestamp means are normalized to ``[-1, 1]`` within the 50 ms interval;
    standard deviations are nonnegative. Return the explicit model contract
    ``[activity_0, activity_1, mean_0, mean_1, std_0, std_1]`` in ``[0, 1]``.
    Empty pixels are masked so their placeholder timestamp values cannot create
    input events.
    """
    statistics = _canonical_events(array)
    activity = ((statistics[:2] + 1.0) * 0.5).clamp(0.0, 1.0)
    active = activity > 0.0
    means = torch.stack((statistics[2], statistics[4]))
    means = ((means + 1.0) * 0.5).clamp(0.0, 1.0)
    deviations = torch.stack((statistics[3], statistics[5])).clamp(0.0, 1.0)
    means = torch.where(active, means, torch.zeros_like(means))
    deviations = torch.where(active, deviations, torch.zeros_like(deviations))
    return torch.cat((activity, means, deviations), dim=0)


def _resize_timestamp_statistics(
    statistics: Tensor, mask: Tensor, output_size: tuple[int, int] | None
) -> tuple[Tensor, Tensor]:
    """Resize moment maps without averaging timestamps into empty background."""
    if output_size is None:
        return statistics, mask
    activity = F.interpolate(statistics[None, :2], size=output_size, mode="area")[0]
    means = statistics[2:4]
    deviations = statistics[4:6]
    weighted_mean = F.interpolate(
        (statistics[:2] * means)[None], size=output_size, mode="area"
    )[0]
    weighted_second = F.interpolate(
        (statistics[:2] * (deviations.square() + means.square()))[None],
        size=output_size,
        mode="area",
    )[0]
    denominator = activity.clamp_min(torch.finfo(activity.dtype).eps)
    resized_mean = weighted_mean / denominator
    variance = (weighted_second / denominator - resized_mean.square()).clamp_min(0.0)
    resized_std = variance.sqrt()
    active = activity > 0.0
    resized_mean = torch.where(active, resized_mean, torch.zeros_like(resized_mean))
    resized_std = torch.where(active, resized_std, torch.zeros_like(resized_std))
    result = torch.cat((activity.clamp(0.0, 1.0), resized_mean, resized_std), dim=0)
    return result, _resize_mask(mask, output_size)


def _canonical_mask(array: np.ndarray) -> Tensor:
    mask = torch.as_tensor(np.array(array, copy=True)).squeeze().long()
    if mask.ndim != 2:
        raise ValueError(f"unsupported semantic mask shape: {tuple(mask.shape)}")
    mask[(mask < 0) | (mask >= DDD17_CLASS_COUNT)] = IGNORE_INDEX
    return mask


def _resize_mask(mask: Tensor, output_size: tuple[int, int] | None) -> Tensor:
    if output_size is None:
        return mask
    return F.interpolate(
        mask[None, None].float(), size=output_size, mode="nearest"
    )[0, 0].long()


def split_records_by_sequence(
    records: Sequence[DDD17Record],
    *,
    validation_fraction: float,
    seed: int,
) -> tuple[list[DDD17Record], list[DDD17Record]]:
    """Create a deterministic temporal train/validation split.

    Multiple sequence IDs are held out as whole groups. If the manifest contains
    only one sequence, use one contiguous validation block instead of failing or
    randomly mixing individual frames. Removing a validation block creates a
    detectable frame gap, so the streaming model resets before the next record.
    """
    if not (0.0 < validation_fraction < 0.5):
        raise ValueError("validation_fraction must satisfy 0 < value < 0.5")
    if not records:
        raise TemporalMetadataError("cannot split an empty DDD17 record set")

    grouped: dict[str, list[DDD17Record]] = {}
    for record in records:
        grouped.setdefault(record.sequence_id, []).append(record)
    for sequence_records in grouped.values():
        sequence_records.sort(key=lambda record: record.frame_index)
    sequence_ids = sorted(grouped)

    if len(sequence_ids) == 1:
        ordered = grouped[sequence_ids[0]]
        target = max(1, int(round(len(ordered) * validation_fraction)))
        if len(ordered) < target + 1:
            raise TemporalMetadataError(
                "single-sequence validation does not leave enough training records; "
                "reduce validation_fraction"
            )
        available_starts = len(ordered) - target + 1
        generator = torch.Generator().manual_seed(seed + 1)
        start = int(torch.randint(0, available_starts, (1,), generator=generator).item())
        stop = start + target
        validation = ordered[start:stop]
        training = ordered[:start] + ordered[stop:]
        if not training or not validation:
            raise TemporalMetadataError(
                "single-sequence temporal split produced an empty partition"
            )
        return training, validation

    generator = torch.Generator().manual_seed(seed + 1)
    order = torch.randperm(len(sequence_ids), generator=generator).tolist()
    shuffled = [sequence_ids[index] for index in order]
    target = max(1, int(round(len(records) * validation_fraction)))
    validation_ids: list[str] = []
    count = 0
    for sequence_id in shuffled:
        if len(validation_ids) >= len(sequence_ids) - 1:
            break
        validation_ids.append(sequence_id)
        count += len(grouped[sequence_id])
        if count >= target:
            break
    validation_set = set(validation_ids)
    training = [record for record in records if record.sequence_id not in validation_set]
    validation = [record for record in records if record.sequence_id in validation_set]
    if not training or not validation:
        raise TemporalMetadataError("sequence-level split produced an empty partition")
    return training, validation


class DDD17TimestampEventDataset(Dataset[tuple[Tensor, Tensor]]):
    """One timestamp-statistic interval and its directly aligned semantic mask."""

    input_channels = 6
    input_mode = "timestamp-events"
    class_count = DDD17_CLASS_COUNT
    class_names = DDD17_CLASS_NAMES
    protocol_version = TEMPORAL_PROTOCOL_VERSION
    streaming = True

    def __init__(
        self,
        root: Path | str | None = None,
        *,
        split: str,
        output_size: tuple[int, int] | None = None,
        records: Sequence[DDD17Record] | None = None,
        manifest: Path | str | None = None,
    ) -> None:
        self.root = resolve_ddd17_root(root)
        self.split = split
        self.output_size = output_size
        self.records = list(records) if records is not None else discover_ddd17_records(
            self.root, split, manifest=manifest
        )
        if not self.records:
            raise TemporalMetadataError(f"no timestamp-event records available in DDD17 {split}")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        record = self.records[index]
        statistics = _canonical_timestamp_statistics(_load_record_events(record))
        target = _canonical_mask(_load_record_mask(record))
        return _resize_timestamp_statistics(statistics, target, self.output_size)

    def target_mask(self, index: int) -> Tensor:
        target = _canonical_mask(_load_record_mask(self.records[index]))
        return _resize_mask(target, self.output_size)

    def is_stream_start(self, index: int) -> bool:
        if index == 0:
            return True
        previous = self.records[index - 1]
        current = self.records[index]
        return (
            current.sequence_id != previous.sequence_id
            or current.frame_index != previous.frame_index + 1
        )

    def subset(self, indices: Sequence[int]) -> DDD17TimestampEventDataset:
        return DDD17TimestampEventDataset(
            self.root,
            split=self.split,
            output_size=self.output_size,
            records=[self.records[index] for index in indices],
        )


TemporalDataset = DDD17TimestampEventDataset
DDD17Dataset = DDD17TimestampEventDataset


def build_temporal_dataset(
    root: Path | str | None,
    *,
    split: str,
    input_mode: str,
    output_size: tuple[int, int] | None,
    records: Sequence[DDD17Record] | None = None,
    manifest: Path | str | None = None,
) -> TemporalDataset:
    if input_mode == "timestamp-events":
        return DDD17TimestampEventDataset(
            root,
            split=split,
            output_size=output_size,
            records=records,
            manifest=manifest,
        )
    raise ValueError(f"input_mode must be one of {INPUT_MODES}, got {input_mode!r}")


def deterministic_dataset_subset(
    dataset: TemporalDataset, *, maximum: int, seed: int
) -> TemporalDataset:
    if maximum <= 0 or maximum >= len(dataset):
        return dataset
    generator = torch.Generator().manual_seed(seed)
    start = int(
        torch.randint(0, len(dataset) - maximum + 1, (1,), generator=generator).item()
    )
    return dataset.subset(list(range(start, start + maximum)))


def deterministic_record_subset(
    records: Sequence[DDD17Record], *, maximum: int, seed: int
) -> list[DDD17Record]:
    if maximum <= 0 or maximum >= len(records):
        return list(records)
    generator = torch.Generator().manual_seed(seed)
    start = int(
        torch.randint(0, len(records) - maximum + 1, (1,), generator=generator).item()
    )
    return list(records[start : start + maximum])


def temporal_collate(batch: list[tuple[Tensor, Tensor]]) -> tuple[Tensor, Tensor]:
    """Collate one timestamp-statistic interval per stream item."""
    if not batch:
        raise ValueError("cannot collate an empty batch")
    shapes = {tuple(events.shape) for events, _ in batch}
    if len(shapes) != 1:
        raise ValueError(f"temporal batch contains inconsistent event shapes: {sorted(shapes)}")
    if batch[0][0].ndim != 3:
        raise ValueError(f"timestamp-event samples must be [C,H,W], got {shapes.pop()}")
    sequence = torch.stack([events for events, _ in batch])  # N,C,H,W
    masks = torch.stack([mask for _, mask in batch])
    return sequence, masks


def _record_identity_digest(records: Sequence[DDD17Record], root: Path) -> str:
    payload = [record.identity(root) for record in records]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def make_temporal_protocol(
    root: Path | str | None,
    *,
    input_mode: str,
    validation_fraction: float,
    training_records: Sequence[DDD17Record],
    validation_records: Sequence[DDD17Record],
    internal_updates: int = DEFAULT_INTERNAL_UPDATES,
    stateful_stream: bool = True,
    manifest: Path | str | None = None,
) -> TemporalProtocol:
    if internal_updates < 1:
        raise ValueError("internal_updates must be positive")
    if EVSEG_INTEGRATION_WINDOW_US % internal_updates != 0:
        raise ValueError(
            "internal_updates must divide the 50,000 us integration interval exactly"
        )
    return TemporalProtocol(
        version=TEMPORAL_PROTOCOL_VERSION,
        input_mode=input_mode,
        input_channels=6,
        integration_window_us=EVSEG_INTEGRATION_WINDOW_US,
        internal_updates=internal_updates,
        event_clock_us=EVSEG_INTEGRATION_WINDOW_US // internal_updates,
        stateful_stream=stateful_stream,
        validation_fraction=validation_fraction,
        manifest_digest=manifest_digest(root, manifest=manifest),
        training_sequences=tuple(sorted({record.sequence_id for record in training_records})),
        validation_sequences=tuple(sorted({record.sequence_id for record in validation_records})),
        training_record_ids=tuple(
            (record.sequence_id, record.frame_index) for record in training_records
        ),
        validation_record_ids=tuple(
            (record.sequence_id, record.frame_index) for record in validation_records
        ),
        validation_record_digest=_record_identity_digest(
            validation_records, resolve_ddd17_root(root)
        ),
    )


def inspect_ddd17(
    root: Path | str | None = None,
    *,
    manifest: Path | str | None = None,
) -> DDD17Inspection:
    root = resolve_ddd17_root(root)
    counts: dict[str, int] = {}
    sequences: dict[str, int] = {}
    formats: dict[str, int] = {}
    warnings: list[str] = []
    manifest_path = resolve_manifest_path(root, manifest)
    for split in SPLITS:
        try:
            records = discover_ddd17_records(root, split, manifest=manifest)
        except (FileNotFoundError, TemporalMetadataError) as exc:
            records = []
            warnings.append(f"{split}: {exc}")
        counts[split] = len(records)
        sequences[split] = len({record.sequence_id for record in records})
        for record in records[:64]:
            suffix = record.event_path.suffix.lower()
            formats[suffix] = formats.get(suffix, 0) + 1
        event_dir = root / "events" / split
        label_dir = root / "labels" / split
        available_events = (
            sum(entry.name.lower().endswith(".npy") for entry in os.scandir(event_dir))
            if event_dir.is_dir()
            else 0
        )
        available_labels = (
            sum(entry.name.lower().endswith(".png") for entry in os.scandir(label_dir))
            if label_dir.is_dir()
            else 0
        )
        if available_events != available_labels:
            warnings.append(
                f"{split}: event/label file count mismatch: "
                f"{available_events} NumPy events vs {available_labels} PNG labels"
            )
        if records and len(records) != available_events:
            warnings.append(
                f"{split}: manifest references {len(records)} records but "
                f"{available_events} event files are installed"
            )
    return DDD17Inspection(
        root=str(root),
        records=counts,
        sequences=sequences,
        formats=formats,
        manifest=str(manifest_path) if manifest_path.is_file() else None,
        warnings=tuple(warnings),
    )


def write_inspection(
    root: Path | str | None,
    destination: Path,
    *,
    manifest: Path | str | None = None,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(inspect_ddd17(root, manifest=manifest).to_dict(), indent=2), encoding="utf-8"
    )


DSEC_CLASS_NAMES = (
    "sky",
    "building",
    "fence",
    "person",
    "pole",
    "road",
    "sidewalk",
    "vegetation",
    "vehicle",
    "wall",
    "traffic-sign",
)
DSEC_CLASS_COUNT = len(DSEC_CLASS_NAMES)
DSEC_6_CLASS_NAMES = DDD17_CLASS_NAMES
DSEC_6_CLASS_COUNT = len(DSEC_6_CLASS_NAMES)
# DSEC 11-class index -> broad six-class semantic index:
# flat, construction+sky, object, nature, human, vehicle.
DSEC_11_TO_6 = (1, 1, 1, 4, 2, 0, 0, 3, 5, 1, 2)
DSEC_INPUT_MODE = "raw-events"
DSEC_PROTOCOL_VERSION = "dsec-fixed-time-counts-async-fpga-v4"
DSEC_6_PROTOCOL_VERSION = "dsec-six-class-fixed-time-counts-async-v1"
DSEC_EVENT_VALUE_ENCODING = "linear-event-multiplicity"
DSEC_SENSOR_HEIGHT = 480
DSEC_SENSOR_WIDTH = 640
DSEC_LABEL_HEIGHT = 440
DSEC_LABEL_WIDTH = 640
DEFAULT_DSEC_ROOT = Path(r"C:\Users\stamir\Desktop\Dataset\DSEC")
DSEC_SPLIT_SEED = 17
DSEC_VALIDATION_SEQUENCE_COUNT = 2
DSEC_HORIZONTAL_FLIP_PROBABILITY = 0.4
DSEC_MAX_TRANSLATION_PIXELS = 6
DSEC_MAX_EVENT_DROPOUT = 0.05


@dataclass(frozen=True)
class DSECRecord:
    split: str
    sequence_id: str
    frame_index: int
    timestamp_us: int
    event_path: Path
    rectify_path: Path
    label_path: Path

    def identity(self, root: Path | None = None) -> dict[str, object]:
        def relative(path: Path) -> str:
            if root is not None:
                try:
                    return str(path.resolve().relative_to(root.resolve()))
                except ValueError:
                    pass
            return str(path)

        return {
            "split": self.split,
            "sequence_id": self.sequence_id,
            "frame_index": self.frame_index,
            "timestamp_us": self.timestamp_us,
            "event": relative(self.event_path),
            "rectify": relative(self.rectify_path),
            "label": relative(self.label_path),
        }


@dataclass(frozen=True)
class DSECInspection:
    root: str
    records: dict[str, int]
    sequences: dict[str, int]
    label_interval_us: dict[str, tuple[int, int]]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def split_dsec_records_by_sequence(
    records: Sequence[DSECRecord],
    *,
    validation_fraction: float,
    train_samples: float = 0.0,
    split_seed: int = DSEC_SPLIT_SEED,
    validation_sequence_count: int | None = None,
) -> tuple[list[DSECRecord], list[DSECRecord]]:
    """Hold out complete sequences scaled to the active training fraction."""
    if not (0.0 < validation_fraction < 0.5):
        raise ValueError("validation_fraction must satisfy 0 < value < 0.5")
    if not records:
        raise TemporalMetadataError("cannot split an empty DSEC record set")
    grouped: dict[str, list[DSECRecord]] = {}
    for record in records:
        grouped.setdefault(record.sequence_id, []).append(record)
    for sequence_records in grouped.values():
        sequence_records.sort(key=lambda record: record.frame_index)
    sequence_ids = sorted(grouped)
    if train_samples <= 0:
        active_fraction = 1.0
    elif train_samples <= 1:
        active_fraction = train_samples
    else:
        active_fraction = min(1.0, train_samples / len(records))
    if validation_sequence_count is None:
        validation_sequence_count = (
            1 if active_fraction <= 0.5 else DSEC_VALIDATION_SEQUENCE_COUNT
        )
    if not (1 <= validation_sequence_count < len(sequence_ids)):
        raise TemporalMetadataError(
            "DSEC validation_sequence_count must leave at least one training sequence"
        )

    candidates = list(combinations(sequence_ids, validation_sequence_count))
    generator = torch.Generator().manual_seed(split_seed)
    tie_order = torch.randperm(len(candidates), generator=generator).tolist()
    candidates = [candidates[index] for index in tie_order]
    target = len(records) * validation_fraction * active_fraction
    validation_ids = min(
        candidates,
        key=lambda candidate: abs(
            sum(len(grouped[sequence_id]) for sequence_id in candidate) - target
        ),
    )
    validation_set = set(validation_ids)
    training = [record for record in records if record.sequence_id not in validation_set]
    validation = [record for record in records if record.sequence_id in validation_set]
    return training, validation


def resolve_dsec_root(root: Path | str | None = None) -> Path:
    return (DEFAULT_DSEC_ROOT if root is None else Path(root)).expanduser().resolve()


def _first_existing(sequence: Path, candidates: Sequence[str]) -> Path | None:
    for candidate in candidates:
        path = sequence / candidate
        if path.is_file():
            return path
    return None


def _label_directory(sequence: Path) -> Path | None:
    candidates = (
        sequence / "11classes",
        sequence / "semantic" / "11classes" / "data",
        sequence / "semantic" / "left" / "11classes" / "data",
    )
    return next((path for path in candidates if path.is_dir()), None)


def _sequence_layout(sequence: Path) -> tuple[Path, Path, Path, Path]:
    event_path = _first_existing(
        sequence, ("events.h5", "events/left/events.h5")
    )
    rectify_path = _first_existing(
        sequence, ("rectify_map.h5", "events/left/rectify_map.h5")
    )
    timestamp_path = _first_existing(
        sequence,
        (
            f"{sequence.name}_semantic_timestamps.txt",
            "semantic/timestamps.txt",
            "semantic/left/timestamps.txt",
        ),
    )
    label_dir = _label_directory(sequence)
    missing = [
        name
        for name, path in (
            ("events.h5", event_path),
            ("rectify_map.h5", rectify_path),
            ("semantic timestamps", timestamp_path),
            ("11classes labels", label_dir),
        )
        if path is None
    ]
    if missing:
        raise TemporalMetadataError(
            f"DSEC sequence {sequence.name} is missing {', '.join(missing)}"
        )
    assert event_path is not None
    assert rectify_path is not None
    assert timestamp_path is not None
    assert label_dir is not None
    return event_path, rectify_path, timestamp_path, label_dir


def _event_time_offset(event_path: Path) -> int:
    with h5py.File(event_path, "r") as handle:
        if "t_offset" not in handle:
            raise TemporalMetadataError(f"DSEC event file lacks t_offset: {event_path}")
        return int(handle["t_offset"][()])


def discover_dsec_records(
    root: Path | str | None = None, split: str = "train"
) -> list[DSECRecord]:
    root = resolve_dsec_root(root)
    split_root = root / split
    if split not in ("train", "test"):
        raise ValueError("DSEC split must be 'train' or 'test'")
    if not split_root.is_dir():
        raise FileNotFoundError(f"DSEC split directory does not exist: {split_root}")

    records: list[DSECRecord] = []
    for sequence in sorted(path for path in split_root.iterdir() if path.is_dir()):
        event_path, rectify_path, timestamp_path, label_dir = _sequence_layout(sequence)
        timestamps = np.atleast_1d(np.loadtxt(timestamp_path, dtype=np.int64))
        labels = sorted(label_dir.glob("*.png"))
        if len(labels) != int(timestamps.size):
            raise TemporalMetadataError(
                f"DSEC {sequence.name} has {len(labels)} labels but "
                f"{timestamps.size} timestamps"
            )
        offset = _event_time_offset(event_path)
        for frame_index, (timestamp, label_path) in enumerate(zip(timestamps, labels)):
            timestamp_us = int(timestamp)
            # The first published label is commonly only hundreds of microseconds
            # after the HDF5 origin and therefore has no complete preceding window.
            if timestamp_us - EVSEG_INTEGRATION_WINDOW_US < offset:
                continue
            records.append(
                DSECRecord(
                    split=split,
                    sequence_id=sequence.name,
                    frame_index=frame_index,
                    timestamp_us=timestamp_us,
                    event_path=event_path,
                    rectify_path=rectify_path,
                    label_path=label_path,
                )
            )
    if not records:
        raise TemporalMetadataError(f"no usable DSEC raw-event records found in {split_root}")
    return records


def _canonical_dsec_mask(
    path: Path,
    output_size: tuple[int, int] | None,
    class_count: int = DSEC_CLASS_COUNT,
) -> Tensor:
    with Image.open(path) as image:
        mask = torch.as_tensor(np.array(image, copy=True)).long().squeeze()
    if mask.ndim != 2:
        raise ValueError(f"unsupported DSEC semantic mask shape: {tuple(mask.shape)}")
    mask[(mask < 0) | (mask >= DSEC_CLASS_COUNT)] = IGNORE_INDEX
    if class_count == DSEC_6_CLASS_COUNT:
        valid = mask != IGNORE_INDEX
        mapping = torch.tensor(DSEC_11_TO_6, dtype=torch.long)
        mask[valid] = mapping[mask[valid]]
    elif class_count != DSEC_CLASS_COUNT:
        raise ValueError("DSEC class_count must be 6 or 11")
    if output_size is not None:
        mask = F.interpolate(
            mask[None, None].float(), size=output_size, mode="nearest"
        )[0, 0].long()
    return mask


def _translate_dsec_mask(mask: Tensor, dx: int, dy: int) -> Tensor:
    """Translate a semantic mask without wrapping, filling exposed pixels as ignore."""
    if dx == 0 and dy == 0:
        return mask
    height, width = mask.shape
    translated = torch.full_like(mask, IGNORE_INDEX)
    source_x0 = max(0, -dx)
    source_x1 = min(width, width - dx)
    source_y0 = max(0, -dy)
    source_y1 = min(height, height - dy)
    if source_x0 < source_x1 and source_y0 < source_y1:
        translated[
            source_y0 + dy : source_y1 + dy,
            source_x0 + dx : source_x1 + dx,
        ] = mask[source_y0:source_y1, source_x0:source_x1]
    return translated


class DSECRawEventDataset(Dataset[tuple[Tensor, Tensor, Tensor]]):
    """One fixed-time 50 ms event stream and its aligned mask.

    Every source event contributes one unit of input mass to exactly one physical-time
    division. Event count never changes the number or duration of model updates.
    """

    input_channels = 2
    input_mode = DSEC_INPUT_MODE
    class_count = DSEC_CLASS_COUNT
    class_names = DSEC_CLASS_NAMES
    protocol_version = DSEC_PROTOCOL_VERSION
    streaming = True

    def __init__(
        self,
        root: Path | str | None = None,
        *,
        split: str,
        output_size: tuple[int, int] | None = None,
        internal_updates: int = DEFAULT_INTERNAL_UPDATES,
        class_count: int = DSEC_CLASS_COUNT,
        records: Sequence[DSECRecord] | None = None,
        augmentation_seed: int | None = None,
        augmentation_epoch: int = 1,
    ) -> None:
        if internal_updates < 1 or EVSEG_INTEGRATION_WINDOW_US % internal_updates != 0:
            raise ValueError("internal_updates must divide the 50,000 us DSEC interval")
        self.root = resolve_dsec_root(root)
        self.split = split
        self.output_size = output_size
        self.internal_updates = internal_updates
        self.augmentation_seed = augmentation_seed
        self.augmentation_epoch = augmentation_epoch
        if class_count not in (DSEC_6_CLASS_COUNT, DSEC_CLASS_COUNT):
            raise ValueError("DSEC class_count must be 6 or 11")
        self.class_count = class_count
        self.class_names = (
            DSEC_6_CLASS_NAMES if class_count == DSEC_6_CLASS_COUNT else DSEC_CLASS_NAMES
        )
        self.protocol_version = (
            DSEC_6_PROTOCOL_VERSION
            if class_count == DSEC_6_CLASS_COUNT
            else DSEC_PROTOCOL_VERSION
        )
        self.records = list(records) if records is not None else discover_dsec_records(
            self.root, split
        )
        if not self.records:
            raise TemporalMetadataError(f"no DSEC records available for split {split}")
        self._event_handles: dict[Path, h5py.File] = {}
        self._rectify_maps: dict[Path, np.ndarray] = {}

    def _augmentation_rng(self, record: DSECRecord, scope: str) -> np.random.Generator:
        epoch = self.augmentation_epoch if scope == "dropout" else 0
        payload = (
            f"{self.augmentation_seed}:{record.sequence_id}:"
            f"{record.frame_index if scope == 'dropout' else 0}:{epoch}:{scope}"
        ).encode()
        seed = int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")
        return np.random.default_rng(seed)

    def _spatial_augmentation(self, record: DSECRecord) -> tuple[bool, int, int]:
        """Return one run-stable transform for an entire recording sequence."""
        if self.augmentation_seed is None:
            return False, 0, 0
        generator = self._augmentation_rng(record, "spatial")
        flip = bool(generator.random() < DSEC_HORIZONTAL_FLIP_PROBABILITY)
        maximum = DSEC_MAX_TRANSLATION_PIXELS
        dx = int(generator.integers(-maximum, maximum + 1))
        dy = int(generator.integers(-maximum, maximum + 1))
        return flip, dx, dy

    def set_augmentation_epoch(self, epoch: int) -> None:
        """Select reproducible per-record dropout while preserving spatial continuity."""
        self.augmentation_epoch = epoch

    def __len__(self) -> int:
        return len(self.records)

    def _event_handle(self, path: Path) -> h5py.File:
        if hdf5plugin is None:
            raise RuntimeError(
                "DSEC event files use Blosc compression, but hdf5plugin is not "
                "installed in this runtime. Rebuild the Docker image with "
                "`docker compose build` before training."
            )
        handle = self._event_handles.get(path)
        if handle is None:
            handle = h5py.File(path, "r")
            self._event_handles[path] = handle
        return handle

    def _rectify_map(self, path: Path) -> np.ndarray:
        rectify = self._rectify_maps.get(path)
        if rectify is None:
            with h5py.File(path, "r") as handle:
                rectify = np.asarray(handle["rectify_map"][()], dtype=np.float32)
            if rectify.ndim != 3 or rectify.shape[2] != 2:
                raise ValueError(f"invalid DSEC rectify map shape: {rectify.shape}")
            self._rectify_maps[path] = rectify
        return rectify

    @staticmethod
    def _coarse_event_indices(
        handle: h5py.File, start_relative_us: int, end_relative_us: int
    ) -> tuple[int, int]:
        ms_to_idx = handle["ms_to_idx"]
        maximum = len(handle["events/t"])
        start_ms = max(0, start_relative_us // 1_000)
        end_ms = max(0, (end_relative_us + 999) // 1_000)
        start_index = int(ms_to_idx[min(start_ms, len(ms_to_idx) - 1)])
        end_index = (
            int(ms_to_idx[end_ms])
            if end_ms < len(ms_to_idx)
            else maximum
        )
        return max(0, start_index), min(maximum, max(start_index, end_index))

    def _read_interval(self, record: DSECRecord) -> tuple[np.ndarray, ...]:
        handle = self._event_handle(record.event_path)
        offset = int(handle["t_offset"][()])
        start_relative = record.timestamp_us - EVSEG_INTEGRATION_WINDOW_US - offset
        end_relative = record.timestamp_us - offset
        coarse_start, coarse_end = self._coarse_event_indices(
            handle, start_relative, end_relative
        )
        try:  # noqa: SIM105 - contextlib globals may be cleared during shutdown
            timestamps = np.asarray(handle["events/t"][coarse_start:coarse_end])
            x = np.asarray(handle["events/x"][coarse_start:coarse_end])
            y = np.asarray(handle["events/y"][coarse_start:coarse_end])
            polarity = np.asarray(handle["events/p"][coarse_start:coarse_end])
        except OSError as exc:
            if hdf5plugin is None:
                raise RuntimeError(
                    "compressed DSEC events require the hdf5plugin package"
                ) from exc
            raise
        valid = (timestamps >= start_relative) & (timestamps < end_relative)
        return x[valid], y[valid], timestamps[valid], polarity[valid]

    def _schedule_events(self, record: DSECRecord) -> tuple[Tensor, Tensor]:
        x, y, timestamps, polarity = self._read_interval(record)
        output_height, output_width = self.output_size or (
            DSEC_LABEL_HEIGHT,
            DSEC_LABEL_WIDTH,
        )
        step_us = EVSEG_INTEGRATION_WINDOW_US // self.internal_updates
        scheduled = np.zeros(
            (self.internal_updates, 2, output_height, output_width), dtype=np.float32
        )
        deltas = torch.full((self.internal_updates,), float(step_us))
        if timestamps.size == 0:
            return torch.from_numpy(scheduled), deltas

        rectify = self._rectify_map(record.rectify_path)
        xy_rect = rectify[y.astype(np.int64), x.astype(np.int64)]
        x_rect = xy_rect[:, 0]
        y_rect = xy_rect[:, 1]
        valid = (
            np.isfinite(x_rect)
            & np.isfinite(y_rect)
            & (x_rect >= 0.0)
            & (x_rect < DSEC_LABEL_WIDTH)
            & (y_rect >= 0.0)
            & (y_rect < DSEC_LABEL_HEIGHT)
            & ((polarity == 0) | (polarity == 1))
        )
        if not np.any(valid):
            return torch.from_numpy(scheduled), deltas

        x_out = np.floor(x_rect[valid] * output_width / DSEC_LABEL_WIDTH).astype(np.int64)
        y_out = np.floor(y_rect[valid] * output_height / DSEC_LABEL_HEIGHT).astype(np.int64)
        p_out = polarity[valid].astype(np.int64)
        absolute_t = timestamps[valid].astype(np.int64) + int(
            self._event_handle(record.event_path)["t_offset"][()]
        )
        relative_t = absolute_t - (record.timestamp_us - EVSEG_INTEGRATION_WINDOW_US)
        clock = np.floor_divide(relative_t, step_us).clip(0, self.internal_updates - 1)
        flip, dx, dy = self._spatial_augmentation(record)
        if flip:
            x_out = (output_width - 1) - x_out
        x_out = x_out + dx
        y_out = y_out + dy
        in_bounds = (
            (x_out >= 0)
            & (x_out < output_width)
            & (y_out >= 0)
            & (y_out < output_height)
        )
        if self.augmentation_seed is not None and np.any(in_bounds):
            dropout_rng = self._augmentation_rng(record, "dropout")
            dropout_rate = dropout_rng.uniform(0.0, DSEC_MAX_EVENT_DROPOUT)
            in_bounds &= dropout_rng.random(len(in_bounds)) >= dropout_rate
        x_out = x_out[in_bounds]
        y_out = y_out[in_bounds]
        p_out = p_out[in_bounds]
        clock = clock[in_bounds]
        np.add.at(scheduled, (clock, p_out, y_out, x_out), 1.0)
        return torch.from_numpy(scheduled), deltas

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor, Tensor]:
        record = self.records[index]
        events, deltas_us = self._schedule_events(record)
        mask = _canonical_dsec_mask(record.label_path, self.output_size, self.class_count)
        flip, dx, dy = self._spatial_augmentation(record)
        if flip:
            mask = torch.flip(mask, dims=(1,))
        mask = _translate_dsec_mask(mask, dx, dy)
        return (
            events,
            mask,
            deltas_us,
        )

    def target_mask(self, index: int) -> Tensor:
        return _canonical_dsec_mask(
            self.records[index].label_path, self.output_size, self.class_count
        )

    def is_stream_start(self, index: int) -> bool:
        if index == 0:
            return True
        previous = self.records[index - 1]
        current = self.records[index]
        return (
            current.sequence_id != previous.sequence_id
            or current.frame_index != previous.frame_index + 1
        )

    def subset(self, indices: Sequence[int]) -> DSECRawEventDataset:
        return DSECRawEventDataset(
            self.root,
            split=self.split,
            output_size=self.output_size,
            internal_updates=self.internal_updates,
            class_count=self.class_count,
            records=[self.records[index] for index in indices],
            augmentation_seed=self.augmentation_seed,
            augmentation_epoch=self.augmentation_epoch,
        )

    def close(self) -> None:
        for handle in self._event_handles.values():
            handle.close()
        self._event_handles.clear()

    def __del__(self) -> None:  # pragma: no cover - interpreter shutdown is nondeterministic
        active_handles = getattr(self, "_event_handles", None)
        if sys is not None and not sys.is_finalizing() and active_handles:
            self.close()


def dsec_temporal_collate(
    batch: list[tuple[Tensor, Tensor, Tensor]],
) -> tuple[Tensor, Tensor, Tensor]:
    if not batch:
        raise ValueError("cannot collate an empty DSEC batch")
    if len(batch) != 1:
        raise ValueError("stateful DSEC streams require batch size 1")
    events, mask, deltas_us = batch[0]
    if events.ndim != 4 or deltas_us.shape != (events.shape[0],):
        raise ValueError("DSEC samples must contain [T,2,H,W] and one delta per packet")
    # T,C,H,W becomes T,N,C,H,W; N remains one for stateful training.
    return events.unsqueeze(1), mask.unsqueeze(0), deltas_us


def _record_digest(records: Sequence[DSECRecord], root: Path) -> str:
    payload = [record.identity(root) for record in records]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def make_dsec_protocol(
    root: Path | str | None,
    *,
    validation_fraction: float,
    training_records: Sequence[DSECRecord],
    validation_records: Sequence[DSECRecord],
    internal_updates: int,
    stateful_stream: bool,
    class_count: int = DSEC_CLASS_COUNT,
) -> TemporalProtocol:
    root = resolve_dsec_root(root)
    if internal_updates < 1 or EVSEG_INTEGRATION_WINDOW_US % internal_updates != 0:
        raise ValueError("internal_updates must divide the 50,000 us DSEC interval")
    all_records = [*training_records, *validation_records]
    if class_count not in (DSEC_6_CLASS_COUNT, DSEC_CLASS_COUNT):
        raise ValueError("DSEC class_count must be 6 or 11")
    return TemporalProtocol(
        version=(
            DSEC_6_PROTOCOL_VERSION
            if class_count == DSEC_6_CLASS_COUNT
            else DSEC_PROTOCOL_VERSION
        ),
        input_mode=DSEC_INPUT_MODE,
        input_channels=2,
        integration_window_us=EVSEG_INTEGRATION_WINDOW_US,
        internal_updates=internal_updates,
        event_clock_us=EVSEG_INTEGRATION_WINDOW_US // internal_updates,
        stateful_stream=stateful_stream,
        validation_fraction=validation_fraction,
        manifest_digest=_record_digest(all_records, root),
        training_sequences=tuple(sorted({r.sequence_id for r in training_records})),
        validation_sequences=tuple(sorted({r.sequence_id for r in validation_records})),
        training_record_ids=tuple((r.sequence_id, r.frame_index) for r in training_records),
        validation_record_ids=tuple((r.sequence_id, r.frame_index) for r in validation_records),
        validation_record_digest=_record_digest(validation_records, root),
        timing_mode="fixed-physical-time-counts-training-plus-direct-event-fpga",
    )


def inspect_dsec(root: Path | str | None = None) -> DSECInspection:
    root = resolve_dsec_root(root)
    record_counts: dict[str, int] = {}
    sequence_counts: dict[str, int] = {}
    intervals: dict[str, tuple[int, int]] = {}
    warnings: list[str] = []
    for split in ("train", "test"):
        try:
            records = discover_dsec_records(root, split)
            record_counts[split] = len(records)
            sequence_counts[split] = len({record.sequence_id for record in records})
            deltas = [
                current.timestamp_us - previous.timestamp_us
                for previous, current in zip(records, records[1:])
                if previous.sequence_id == current.sequence_id
            ]
            intervals[split] = (min(deltas), max(deltas)) if deltas else (0, 0)
        except (FileNotFoundError, TemporalMetadataError, OSError) as exc:
            record_counts[split] = 0
            sequence_counts[split] = 0
            intervals[split] = (0, 0)
            warnings.append(f"{split}: {exc}")
    return DSECInspection(
        root=str(root),
        records=record_counts,
        sequences=sequence_counts,
        label_interval_us=intervals,
        warnings=tuple(warnings),
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--root", type=Path, default=DEFAULT_DDD17_ROOT)
    inspect_parser.add_argument("--manifest", type=Path, default=None)

    args = parser.parse_args()
    if args.command == "inspect":
        print(json.dumps(inspect_ddd17(args.root, manifest=args.manifest).to_dict(), indent=2))
    else:
        raise RuntimeError(f"unsupported command {args.command!r}")


if __name__ == "__main__":
    main()
