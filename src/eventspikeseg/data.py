"""Sequence-aware DDD17 semantic data loading.

The project supports two *temporal* input representations made directly from
the installed Ev-SegNet NumPy tensors:

``event-bins``
    A chronological window of consecutive Ev-SegNet intervals using only the
    two ON/OFF histogram channels. The stored ``[-1, 1]`` histogram encoding is
    mapped to nonnegative ``[0, 1]`` activity. Each item is ``[T, 2, H, W]``.

``sequential-6ch``
    A chronological window of consecutive Ev-SegNet six-channel pseudo-frames.
    Each dataset item is ``[T, 6, H, W]`` and the target is the semantic mask of
    the final pseudo-frame.

The old repeated-static direct-encoding path is intentionally unsupported.
Sequence metadata is required so windows never cross recording/interval
boundaries and so validation can hold out complete temporal groups.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, replace
from functools import cache, lru_cache
from pathlib import Path
from typing import Any

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
INPUT_MODES = ("event-bins", "sequential-6ch")
TEMPORAL_PROTOCOL_VERSION = "ddd17-temporal-v2"
DEFAULT_MANIFEST_NAME = "ddd17_temporal_manifest.json"
DEFAULT_DDD17_ROOT = Path(r"C:\Users\stamir\Desktop\Dataset\DDD17")

# Exact Ev-Seg subset intervals from Alonso & Murillo (CVPRW 2019), Table 1.
# Values are original DDD17 50 ms frame indices [start, stop).
EVSEG_SOURCE_INTERVALS: dict[str, tuple[tuple[int, int], ...]] = {
    "1487339175": ((0, 4150), (5200, 6600)),
    "1487842276": ((1310, 1400), (1900, 2000), (2600, 3550)),
    "1487593224": ((870, 2190),),
    "1487846842": ((380, 500), (1800, 2150), (2575, 2730), (3530, 3900)),
    "1487779465": (
        (1800, 3400),
        (4000, 4700),
        (8400, 8630),
        (8800, 9160),
        (9920, 10175),
        (18500, 22300),
    ),
    "1487417411": ((100, 1500), (2150, 3100), (3200, 4430), (4840, 5150)),
}

class TemporalMetadataError(ValueError):
    """Raised when chronological grouping cannot be established safely."""


@dataclass(frozen=True)
class DDD17Record:
    split: str
    event_path: Path
    label_path: Path
    sequence_id: str
    frame_index: int
    timestamp_us: int | None = None
    raw_event_path: Path | None = None
    raw_event_key: str | None = None
    raw_event_columns: tuple[str, str, str, str] = ("t", "x", "y", "p")
    archive_index: int | None = None

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
            "timestamp_us": self.timestamp_us,
            "raw_event": path_value(self.raw_event_path),
            "raw_event_key": self.raw_event_key,
            "raw_event_columns": list(self.raw_event_columns),
            "archive_index": self.archive_index,
        }


@dataclass(frozen=True)
class DDD17Window:
    records: tuple[DDD17Record, ...]

    @property
    def target_record(self) -> DDD17Record:
        return self.records[-1]

    @property
    def sequence_id(self) -> str:
        return self.target_record.sequence_id

    @property
    def frame_index(self) -> int:
        return self.target_record.frame_index


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
    time_steps: int
    input_channels: int
    sequence_stride: int
    validation_fraction: float
    manifest_digest: str
    training_sequences: tuple[str, ...]
    validation_sequences: tuple[str, ...]
    training_record_ids: tuple[tuple[str, int], ...]
    validation_record_ids: tuple[tuple[str, int], ...]
    validation_record_digest: str

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
        archive_index=(None if item.get("archive_index") is None else int(item["archive_index"])),
    )


def _evseg_recording_id(sequence_id: str) -> str:
    if not sequence_id.startswith("rec") or not sequence_id.endswith("_export"):
        raise TemporalMetadataError(
            f"raw DDD17 preparation requires sequence_id='rec<ID>_export', got {sequence_id!r}"
        )
    recording_id = sequence_id[3:-7]
    if recording_id not in EVSEG_SOURCE_INTERVALS:
        raise TemporalMetadataError(
            f"sequence {sequence_id!r} is not one of the six published Ev-Seg DDD17 recordings"
        )
    return recording_id


@cache
def _evseg_source_frames(recording_id: str) -> tuple[int, ...]:
    """Return source APS frame indices for the published Ev-Seg intervals.

    The intervals are half-open.  Some distributed Ev-Seg archives contain one
    additional sample at the final interval boundary; that exact terminal frame
    is supported separately by :func:`_evseg_source_frame`.
    """
    return tuple(
        frame
        for start, stop in EVSEG_SOURCE_INTERVALS[recording_id]
        for frame in range(start, stop)
    )


def _evseg_source_frame(recording_id: str, export_frame_index: int) -> int:
    """Map a local Ev-Seg export index to its original DDD17 APS frame index.

    The normal mapping follows the published half-open intervals exactly.  The
    local Ev-Seg test archive used by this project contains one extra terminal
    sample (index 3890 for rec1487417411_export).  We accept only this exact
    terminal-boundary variant: export index == canonical sample count maps to the
    final interval stop.  Larger indices remain invalid.
    """
    if export_frame_index < 0:
        raise TemporalMetadataError("frame_index must be non-negative")
    source_frames = _evseg_source_frames(recording_id)
    if export_frame_index < len(source_frames):
        return source_frames[export_frame_index]
    if export_frame_index == len(source_frames):
        return EVSEG_SOURCE_INTERVALS[recording_id][-1][1]
    raise TemporalMetadataError(
        f"Ev-Seg export frame {export_frame_index} is invalid for rec{recording_id}; "
        f"supported local indices are 0..{len(source_frames)} (the last index is "
        "the optional terminal-boundary sample)"
    )


_FRAME_TIMESTAMP_DATASET_NAMES = (
    "frame_ts",
    "frame_timestamps",
    "image_raw_ts",
    "image_ts",
    "aps_ts",
)


def _timestamp_to_us(value: Any) -> int:
    """Normalize DDD-style timestamps to integer microseconds.

    DDD exports conventionally store floating timestamps in seconds while some
    derived files store integer microseconds.  The dtype, not the magnitude,
    selects the unit so there is no data-dependent guessing.
    """
    scalar = np.asarray(value).reshape(-1)[0]
    if np.issubdtype(np.asarray(scalar).dtype, np.floating):
        return int(round(float(scalar) * 1_000_000.0))
    return int(scalar)


def _find_dataset_by_exact_name(
    group: h5py.Group, names: Sequence[str]
) -> h5py.Dataset | None:
    wanted = {name.lower() for name in names}
    for key, value in group.items():
        if isinstance(value, h5py.Dataset) and key.lower() in wanted:
            return value
    for value in group.values():
        if isinstance(value, h5py.Group):
            found = _find_dataset_by_exact_name(value, names)
            if found is not None:
                return found
    return None


def _find_images_group(group: h5py.Group) -> h5py.Group | None:
    for key, value in group.items():
        if isinstance(value, h5py.Group) and key.lower() == "images":
            return value
    for value in group.values():
        if isinstance(value, h5py.Group):
            found = _find_images_group(value)
            if found is not None:
                return found
    return None


def _image_group_timestamps(group: h5py.Group) -> tuple[int, ...] | None:
    """Read v2e/DDD-style image datasets carrying a timestamp attribute."""
    entries: list[tuple[str, int]] = []
    for key, value in group.items():
        if isinstance(value, h5py.Dataset) and "timestamp" in value.attrs:
            entries.append((key, _timestamp_to_us(value.attrs["timestamp"])))
    if not entries:
        return None

    def sort_key(item: tuple[str, int]) -> tuple[int, str]:
        name = item[0]
        digits = "".join(ch for ch in name if ch.isdigit())
        return (int(digits) if digits else 0, name)

    entries.sort(key=sort_key)
    return tuple(timestamp for _, timestamp in entries)


@lru_cache(maxsize=16)
def _h5_frame_timestamps_cached(path_text: str) -> tuple[int, ...]:
    """Read actual APS frame timestamps from one DDD recording once per process."""
    path = Path(path_text)
    with h5py.File(path, "r") as handle:
        dataset = _find_dataset_by_exact_name(handle, _FRAME_TIMESTAMP_DATASET_NAMES)
        if dataset is not None:
            values = np.asarray(dataset).reshape(-1)
            timestamps = tuple(_timestamp_to_us(value) for value in values)
        else:
            images = _find_images_group(handle)
            timestamps = _image_group_timestamps(images) if images is not None else None
            if timestamps is None:
                top_level = ", ".join(sorted(handle.keys()))
                raise TemporalMetadataError(
                    f"raw DDD17 recording {path} has no supported APS timestamp source; "
                    "expected frame_ts/frame_timestamps/image_raw_ts/image_ts/aps_ts, "
                    "or an images group whose datasets carry a timestamp attribute. "
                    f"Top-level HDF5 keys: [{top_level}]"
                )

    if not timestamps:
        raise TemporalMetadataError(f"raw DDD17 recording has no APS timestamps: {path}")
    if any(b <= a for a, b in zip(timestamps, timestamps[1:])):
        raise TemporalMetadataError(f"APS timestamps are not strictly increasing in {path}")
    return timestamps


def _raw_recording_path(root: Path, recording_id: str) -> Path:
    path = root / "raw" / f"rec{recording_id}.hdf5"
    if not path.is_file():
        raise FileNotFoundError(
            "raw-events requires the original DDD17 recording at the canonical path; "
            f"missing {path}"
        )
    return path


def _resolve_raw_alignment(
    root: Path, records: Sequence[DDD17Record]
) -> list[DDD17Record]:
    """Resolve semantic rows to original raw DDD17 timestamps in memory.

    Manifest raw paths/timestamps are deliberately ignored.  Sequence identity and
    export frame index come from the manifest; the original recording and exact APS
    timestamp come from ``raw/rec<ID>.hdf5``.  The manifest is never rewritten.
    """
    resolved: list[DDD17Record] = []
    cache: dict[str, tuple[Path, tuple[int, ...]]] = {}
    for record in records:
        recording_id = _evseg_recording_id(record.sequence_id)
        if recording_id not in cache:
            raw_path = _raw_recording_path(root, recording_id)
            cache[recording_id] = (
                raw_path,
                _h5_frame_timestamps_cached(str(raw_path)),
            )
        raw_path, frame_timestamps = cache[recording_id]
        source_frame = _evseg_source_frame(recording_id, record.frame_index)
        if source_frame >= len(frame_timestamps):
            raise TemporalMetadataError(
                f"{record.sequence_id}:{record.frame_index} maps to raw APS frame "
                f"{source_frame}, but {raw_path.name} only contains "
                f"{len(frame_timestamps)} APS timestamps"
            )
        resolved.append(
            replace(
                record,
                timestamp_us=frame_timestamps[source_frame],
                raw_event_path=raw_path,
                raw_event_key=None,
                raw_event_columns=("t", "x", "y", "p"),
            )
        )
    return resolved


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
    if record.archive_index is not None:
        with np.load(record.event_path, allow_pickle=False) as payload:
            return np.asarray(payload["events"][record.archive_index])
    return np.asarray(np.load(record.event_path, allow_pickle=False))


def _load_record_mask(record: DDD17Record) -> np.ndarray:
    if record.archive_index is not None:
        with np.load(record.event_path, allow_pickle=False) as payload:
            return np.asarray(payload["labels"][record.archive_index])
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


def _canonical_event_histograms(array: np.ndarray) -> Tensor:
    """Extract nonnegative ON/OFF activity from one Ev-SegNet interval.

    Channels 0 and 1 are the two polarity histograms. The distributed tensors
    store them in ``[-1, 1]``; ``-1`` is the zero-event background. Timestamp
    mean/std channels are deliberately excluded because they are statistics,
    not additional timesteps.
    """
    statistics = _canonical_events(array)
    return ((statistics[:2] + 1.0) * 0.5).clamp_(0.0, 1.0)


def _canonical_mask(array: np.ndarray) -> Tensor:
    mask = torch.as_tensor(np.array(array, copy=True)).squeeze().long()
    if mask.ndim != 2:
        raise ValueError(f"unsupported semantic mask shape: {tuple(mask.shape)}")
    mask[(mask < 0) | (mask >= DDD17_CLASS_COUNT)] = IGNORE_INDEX
    return mask


def _resize_sequence_and_mask(
    events: Tensor,
    mask: Tensor,
    output_size: tuple[int, int] | None,
    *,
    preserve_event_count: bool = False,
) -> tuple[Tensor, Tensor]:
    if output_size is None:
        return events, mask
    t, c, input_h, input_w = events.shape
    events = F.interpolate(events, size=output_size, mode="area")
    if preserve_event_count:
        events = events * ((input_h * input_w) / float(output_size[0] * output_size[1]))
    mask = _resize_mask(mask, output_size)
    if events.shape != (t, c, *output_size):
        raise RuntimeError("unexpected resized temporal tensor shape")
    return events, mask


def _resize_mask(mask: Tensor, output_size: tuple[int, int] | None) -> Tensor:
    if output_size is None:
        return mask
    return F.interpolate(
        mask[None, None].float(), size=output_size, mode="nearest"
    )[0, 0].long()


def build_consecutive_windows(
    records: Sequence[DDD17Record],
    *,
    time_steps: int,
    stride: int = 1,
) -> list[DDD17Window]:
    if time_steps < 1:
        raise ValueError("time_steps must be >= 1")
    if stride < 1:
        raise ValueError("stride must be >= 1")
    grouped: dict[str, list[DDD17Record]] = {}
    for record in records:
        grouped.setdefault(record.sequence_id, []).append(record)
    windows: list[DDD17Window] = []
    for sequence_id in sorted(grouped):
        sequence = sorted(grouped[sequence_id], key=lambda record: record.frame_index)
        for start in range(0, max(0, len(sequence) - time_steps + 1), stride):
            candidate = sequence[start : start + time_steps]
            expected = list(range(candidate[0].frame_index, candidate[0].frame_index + time_steps))
            if [record.frame_index for record in candidate] != expected:
                continue
            windows.append(DDD17Window(tuple(candidate)))
    return windows


def split_records_by_sequence(
    records: Sequence[DDD17Record],
    *,
    validation_fraction: float,
    seed: int,
    guard_records: int = 0,
) -> tuple[list[DDD17Record], list[DDD17Record]]:
    """Create a deterministic temporal train/validation split.

    Multiple sequence IDs are held out as whole groups. If the manifest contains
    only one sequence, use one contiguous validation block instead of failing or
    randomly mixing individual frames. ``guard_records`` removes a buffer around
    that block so chronological T-frame windows from train/validation do not touch.
    """
    if not (0.0 < validation_fraction < 0.5):
        raise ValueError("validation_fraction must satisfy 0 < value < 0.5")
    if guard_records < 0:
        raise ValueError("guard_records must be >= 0")
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
        minimum_training = max(1, guard_records + 1)
        if len(ordered) < target + minimum_training:
            raise TemporalMetadataError(
                "single-sequence validation does not leave enough training records; "
                "reduce validation_fraction or time_steps"
            )
        available_starts = len(ordered) - target + 1
        generator = torch.Generator().manual_seed(seed + 1)
        start = int(torch.randint(0, available_starts, (1,), generator=generator).item())
        stop = start + target
        validation = ordered[start:stop]
        guard_start = max(0, start - guard_records)
        guard_stop = min(len(ordered), stop + guard_records)
        training = ordered[:guard_start] + ordered[guard_stop:]
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


class DDD17SequentialDataset(Dataset[tuple[Tensor, Tensor]]):
    """Chronological Ev-SegNet windows, never repeated-static pseudo-time."""

    input_channels = 6
    input_mode = "sequential-6ch"

    def __init__(
        self,
        root: Path | str | None = None,
        *,
        split: str,
        time_steps: int,
        output_size: tuple[int, int] | None = None,
        records: Sequence[DDD17Record] | None = None,
        windows: Sequence[DDD17Window] | None = None,
        sequence_stride: int = 1,
        manifest: Path | str | None = None,
    ) -> None:
        self.root = resolve_ddd17_root(root)
        self.split = split
        self.time_steps = time_steps
        self.output_size = output_size
        self.sequence_stride = sequence_stride
        self.records = list(records) if records is not None else discover_ddd17_records(
            self.root, split, manifest=manifest
        )
        self.windows = list(windows) if windows is not None else build_consecutive_windows(
            self.records, time_steps=time_steps, stride=sequence_stride
        )
        if not self.windows:
            raise TemporalMetadataError(
                f"no {time_steps}-frame consecutive windows available in DDD17 {split}"
            )

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        window = self.windows[index]
        frames: list[Tensor] = []
        for record in window.records:
            frames.append(_canonical_events(_load_record_events(record)))
        target = _canonical_mask(_load_record_mask(window.target_record))
        events = torch.stack(frames, dim=0)
        return _resize_sequence_and_mask(events, target, self.output_size)

    def target_mask(self, index: int) -> Tensor:
        target = _canonical_mask(_load_record_mask(self.windows[index].target_record))
        return _resize_mask(target, self.output_size)

    def subset(self, indices: Sequence[int]) -> DDD17SequentialDataset:
        return DDD17SequentialDataset(
            self.root,
            split=self.split,
            time_steps=self.time_steps,
            output_size=self.output_size,
            records=self.records,
            windows=[self.windows[index] for index in indices],
            sequence_stride=self.sequence_stride,
        )


class DDD17EventBinDataset(DDD17SequentialDataset):
    """Chronological two-polarity event-histogram bins from installed NumPy data."""

    input_channels = 2
    input_mode = "event-bins"

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        window = self.windows[index]
        bins = [
            _canonical_event_histograms(_load_record_events(record))
            for record in window.records
        ]
        target = _canonical_mask(_load_record_mask(window.target_record))
        events = torch.stack(bins, dim=0)
        return _resize_sequence_and_mask(events, target, self.output_size)

    def subset(self, indices: Sequence[int]) -> DDD17EventBinDataset:
        return DDD17EventBinDataset(
            self.root,
            split=self.split,
            time_steps=self.time_steps,
            output_size=self.output_size,
            records=self.records,
            windows=[self.windows[index] for index in indices],
            sequence_stride=self.sequence_stride,
        )


_TIMESTAMP_NAMES = ("t", "ts", "timestamp", "timestamps", "time", "time_us")
_X_NAMES = ("x", "xs", "xpos", "x_addr")
_Y_NAMES = ("y", "ys", "ypos", "y_addr")
_P_NAMES = ("p", "pol", "polarity", "polarities")


def _first_named(container: h5py.Group, names: Iterable[str]) -> h5py.Dataset | None:
    lower = {key.lower(): key for key in container}
    for name in names:
        key = lower.get(name.lower())
        if key is not None and isinstance(container[key], h5py.Dataset):
            return container[key]
    return None


def _find_event_group(group: h5py.Group) -> h5py.Group | None:
    if (
        _first_named(group, _TIMESTAMP_NAMES) is not None
        and _first_named(group, _X_NAMES) is not None
        and _first_named(group, _Y_NAMES) is not None
        and _first_named(group, _P_NAMES) is not None
    ):
        return group
    for value in group.values():
        if isinstance(value, h5py.Group):
            found = _find_event_group(value)
            if found is not None:
                return found
    return None


def _binary_search_dataset(dataset: Any, value: int | float, *, side: str) -> int:
    lo, hi = 0, len(dataset)
    while lo < hi:
        mid = (lo + hi) // 2
        current = dataset[mid]
        if current < value or (side == "right" and current == value):
            lo = mid + 1
        else:
            hi = mid
    return lo


def _timestamp_search_value(dtype: np.dtype[Any], timestamp_us: int) -> int | float:
    """Convert a microsecond query to the units defined by a timestamp dtype."""
    if np.issubdtype(dtype, np.floating):
        return timestamp_us / 1_000_000.0
    return timestamp_us


def _timestamps_to_us(values: np.ndarray) -> np.ndarray:
    """Normalize timestamp arrays using the same explicit dtype convention."""
    array = np.asarray(values)
    if np.issubdtype(array.dtype, np.floating):
        return np.rint(array.astype(np.float64) * 1_000_000.0).astype(np.int64)
    return array.astype(np.int64, copy=False)


def _structured_field(dtype_names: Sequence[str], candidates: Iterable[str]) -> str | None:
    lookup = {name.lower(): name for name in dtype_names}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _find_compound_event_dataset(group: h5py.Group) -> h5py.Dataset | None:
    for value in group.values():
        if isinstance(value, h5py.Dataset) and value.dtype.names:
            names = value.dtype.names
            if (
                _structured_field(names, _TIMESTAMP_NAMES)
                and _structured_field(names, _X_NAMES)
                and _structured_field(names, _Y_NAMES)
                and _structured_field(names, _P_NAMES)
            ):
                return value
        if isinstance(value, h5py.Group):
            found = _find_compound_event_dataset(value)
            if found is not None:
                return found
    return None


def _find_numeric_event_dataset(group: h5py.Group) -> h5py.Dataset | None:
    """Locate an explicit normalized ``event``/``events`` Nx4 dataset.

    Numeric matrices have no field names, so only canonical event dataset names
    are accepted and the column contract is fixed to ``[t, x, y, p]``.  This
    avoids heuristically treating unrelated Nx4 telemetry as events.
    """
    for key, value in group.items():
        if (
            isinstance(value, h5py.Dataset)
            and key.lower() in {"event", "events"}
            and not value.dtype.names
            and value.ndim == 2
            and value.shape[1] >= 4
        ):
            return value
    for value in group.values():
        if isinstance(value, h5py.Group):
            found = _find_numeric_event_dataset(value)
            if found is not None:
                return found
    return None


def _slice_raw_h5(
    path: Path,
    *,
    start_us: int,
    stop_us: int,
    key: str | None,
    columns: tuple[str, str, str, str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with h5py.File(path, "r") as handle:
        if key is not None:
            node = handle[key]
            if isinstance(node, h5py.Group):
                group = node
            elif isinstance(node, h5py.Dataset):
                dataset = node
                group = None
            else:
                raise ValueError(f"unsupported HDF5 node at {key!r}")
        else:
            group = _find_event_group(handle)
            dataset = None
            if group is None:
                dataset = _find_compound_event_dataset(handle)
            if group is None and dataset is None:
                dataset = _find_numeric_event_dataset(handle)

        if group is not None:
            t_ds = _first_named(group, _TIMESTAMP_NAMES)
            x_ds = _first_named(group, _X_NAMES)
            y_ds = _first_named(group, _Y_NAMES)
            p_ds = _first_named(group, _P_NAMES)
            if any(value is None for value in (t_ds, x_ds, y_ds, p_ds)):
                raise ValueError(f"HDF5 event group in {path} lacks t/x/y/p datasets")
            lo = _binary_search_dataset(
                t_ds, _timestamp_search_value(t_ds.dtype, start_us), side="left"
            )
            hi = _binary_search_dataset(
                t_ds, _timestamp_search_value(t_ds.dtype, stop_us), side="left"
            )
            return (
                _timestamps_to_us(np.asarray(t_ds[lo:hi])),
                np.asarray(x_ds[lo:hi]),
                np.asarray(y_ds[lo:hi]),
                np.asarray(p_ds[lo:hi]),
            )

        if dataset is None:
            raise ValueError(
                f"could not locate raw t/x/y/p events in {path}; expected a group with "
                "named t/x/y/p arrays, a compound event dataset, or an event/events Nx4 matrix"
            )
        names = dataset.dtype.names
        if not names:
            if dataset.ndim != 2 or dataset.shape[1] < 4:
                raise ValueError(
                    "raw event dataset must be a group, compound dataset, or Nx4+ numeric dataset"
                )
            default_indices = {"t": 0, "x": 1, "y": 2, "p": 3}
            indices: list[int] = []
            for name in columns:
                if str(name).lstrip("+-").isdigit():
                    index = int(name)
                elif name.lower() in default_indices:
                    index = default_indices[name.lower()]
                else:
                    raise ValueError(
                        f"numeric HDF5 raw_event_columns must be indices or t/x/y/p, got {columns}"
                    )
                if not (0 <= index < dataset.shape[1]):
                    raise ValueError(
                        f"raw event column {index} is outside dataset width "
                        f"{dataset.shape[1]}"
                    )
                indices.append(index)

            class _MatrixTimeView:
                def __len__(self) -> int:
                    return len(dataset)

                def __getitem__(self, item: int) -> Any:
                    return dataset[item, indices[0]]

            view = _MatrixTimeView()
            lo = _binary_search_dataset(
                view, _timestamp_search_value(dataset.dtype, start_us), side="left"
            )
            hi = _binary_search_dataset(
                view, _timestamp_search_value(dataset.dtype, stop_us), side="left"
            )
            rows = np.asarray(dataset[lo:hi])
            result = [np.asarray(rows[:, index]) for index in indices]
            result[0] = _timestamps_to_us(result[0])
            return tuple(result)  # type: ignore[return-value]
        t_name = _structured_field(names, _TIMESTAMP_NAMES)
        x_name = _structured_field(names, _X_NAMES)
        y_name = _structured_field(names, _Y_NAMES)
        p_name = _structured_field(names, _P_NAMES)
        if None in (t_name, x_name, y_name, p_name):
            raise ValueError(f"compound event dataset in {path} lacks t/x/y/p fields")

        # HDF5 compound columns are sorted by timestamp in DDD-style recordings.
        class _FieldView:
            def __len__(self) -> int:
                return len(dataset)

            def __getitem__(self, item: int) -> Any:
                return dataset[item][t_name]

        field_view = _FieldView()
        time_dtype = dataset.dtype.fields[t_name][0]
        lo = _binary_search_dataset(
            field_view, _timestamp_search_value(time_dtype, start_us), side="left"
        )
        hi = _binary_search_dataset(
            field_view, _timestamp_search_value(time_dtype, stop_us), side="left"
        )
        rows = dataset[lo:hi]
        return (
            _timestamps_to_us(np.asarray(rows[t_name])),
            np.asarray(rows[x_name]),
            np.asarray(rows[y_name]),
            np.asarray(rows[p_name]),
        )


def _slice_raw_numpy(
    path: Path,
    *,
    start_us: int,
    stop_us: int,
    columns: tuple[str, str, str, str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    payload = np.load(path, allow_pickle=False)
    if isinstance(payload, np.lib.npyio.NpzFile):
        try:
            t = np.asarray(payload[columns[0]])
            x = np.asarray(payload[columns[1]])
            y = np.asarray(payload[columns[2]])
            p = np.asarray(payload[columns[3]])
        finally:
            payload.close()
    else:
        array = np.asarray(payload)
        if array.dtype.names:
            t, x, y, p = (np.asarray(array[name]) for name in columns)
        elif array.ndim == 2 and array.shape[1] >= 4:
            # Explicit default for simple fixtures/exported raw event files: t,x,y,p.
            t, x, y, p = (array[:, index] for index in range(4))
        else:
            raise ValueError(f"unsupported raw numpy event format: {path}")
    lo = int(np.searchsorted(t, _timestamp_search_value(t.dtype, start_us), side="left"))
    hi = int(np.searchsorted(t, _timestamp_search_value(t.dtype, stop_us), side="left"))
    return _timestamps_to_us(t[lo:hi]), x[lo:hi], y[lo:hi], p[lo:hi]


def slice_raw_events(
    record: DDD17Record,
    *,
    start_us: int,
    stop_us: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    path = record.raw_event_path
    if path is None:
        raise TemporalMetadataError(
            f"record {record.sequence_id}:{record.frame_index} has no resolved raw recording"
        )
    suffix = path.suffix.lower()
    if suffix in {".h5", ".hdf5"}:
        return _slice_raw_h5(
            path,
            start_us=start_us,
            stop_us=stop_us,
            key=record.raw_event_key,
            columns=record.raw_event_columns,
        )
    if suffix in {".npz", ".npy"}:
        return _slice_raw_numpy(
            path,
            start_us=start_us,
            stop_us=stop_us,
            columns=record.raw_event_columns,
        )
    raise ValueError(f"unsupported raw event file extension {suffix!r}: {path}")


def bin_raw_events(
    t: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    p: np.ndarray,
    *,
    start_us: int,
    stop_us: int,
    time_steps: int,
    height: int,
    width: int,
) -> Tensor:
    if time_steps < 1 or stop_us <= start_us:
        raise ValueError("invalid raw event bin interval")
    result = torch.zeros((time_steps, 2, height, width), dtype=torch.float32)
    if len(t) == 0:
        return result
    t = np.asarray(t, dtype=np.int64)
    x = np.asarray(x, dtype=np.int64)
    y = np.asarray(y, dtype=np.int64)
    p = np.asarray(p)
    valid = (t >= start_us) & (t < stop_us) & (x >= 0) & (x < width) & (y >= 0) & (y < height)
    if not np.any(valid):
        return result
    t, x, y, p = t[valid], x[valid], y[valid], p[valid]
    duration = stop_us - start_us
    bins = np.minimum(((t - start_us) * time_steps // duration), time_steps - 1).astype(np.int64)
    # channel 0 = ON/positive, channel 1 = OFF/non-positive.
    polarity = np.where(p > 0, 0, 1).astype(np.int64)
    flat = (((bins * 2 + polarity) * height + y) * width + x)
    counts = np.bincount(flat, minlength=time_steps * 2 * height * width).astype(np.float32)
    return torch.from_numpy(counts.reshape(time_steps, 2, height, width))


class DDD17RawEventDataset(Dataset[tuple[Tensor, Tensor]]):
    """Raw DDD17 ON/OFF count bins aligned to semantic frame timestamps."""

    input_channels = 2
    input_mode = "raw-events"

    def __init__(
        self,
        root: Path | str | None = None,
        *,
        split: str,
        time_steps: int,
        raw_window_us: int,
        output_size: tuple[int, int] | None = None,
        records: Sequence[DDD17Record] | None = None,
        manifest: Path | str | None = None,
    ) -> None:
        self.root = resolve_ddd17_root(root)
        self.split = split
        self.time_steps = time_steps
        self.raw_window_us = raw_window_us
        self.output_size = output_size
        semantic_records = list(records) if records is not None else discover_ddd17_records(
            self.root, split, manifest=manifest
        )
        if raw_window_us <= 0:
            raise ValueError("raw_window_us must be positive")
        if not semantic_records:
            raise FileNotFoundError(f"no DDD17 {split} records")
        if all(
            record.timestamp_us is not None and record.raw_event_path is not None
            for record in semantic_records
        ):
            # Internal fast path used by ``subset``: these records were already
            # resolved by this dataset instance, never loaded from manifest fields.
            self.records = semantic_records
        else:
            self.records = _resolve_raw_alignment(self.root, semantic_records)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        record = self.records[index]
        mask = _canonical_mask(_load_record_mask(record))
        # Use the semantic-label raster as the raw-event ROI. Ev-SegNet crops the
        # bottom 60 rows of native DDD17, so events outside the stored mask height
        # are intentionally excluded before optional resizing.
        height, width = mask.shape
        stop_us = int(record.timestamp_us or 0)
        start_us = stop_us - self.raw_window_us
        t, x, y, p = slice_raw_events(record, start_us=start_us, stop_us=stop_us)
        events = bin_raw_events(
            t,
            x,
            y,
            p,
            start_us=start_us,
            stop_us=stop_us,
            time_steps=self.time_steps,
            height=height,
            width=width,
        )
        return _resize_sequence_and_mask(
            events, mask, self.output_size, preserve_event_count=True
        )

    def target_mask(self, index: int) -> Tensor:
        mask = _canonical_mask(_load_record_mask(self.records[index]))
        return _resize_mask(mask, self.output_size)

    def subset(self, indices: Sequence[int]) -> DDD17RawEventDataset:
        return DDD17RawEventDataset(
            self.root,
            split=self.split,
            time_steps=self.time_steps,
            raw_window_us=self.raw_window_us,
            output_size=self.output_size,
            records=[self.records[index] for index in indices],
        )


TemporalDataset = DDD17EventBinDataset | DDD17SequentialDataset
DDD17Dataset = DDD17EventBinDataset


def build_temporal_dataset(
    root: Path | str | None,
    *,
    split: str,
    input_mode: str,
    time_steps: int,
    output_size: tuple[int, int] | None,
    records: Sequence[DDD17Record] | None = None,
    sequence_stride: int = 1,
    manifest: Path | str | None = None,
) -> TemporalDataset:
    if input_mode == "event-bins":
        return DDD17EventBinDataset(
            root,
            split=split,
            time_steps=time_steps,
            output_size=output_size,
            records=records,
            sequence_stride=sequence_stride,
            manifest=manifest,
        )
    if input_mode == "sequential-6ch":
        return DDD17SequentialDataset(
            root,
            split=split,
            time_steps=time_steps,
            output_size=output_size,
            records=records,
            sequence_stride=sequence_stride,
            manifest=manifest,
        )
    raise ValueError(f"input_mode must be one of {INPUT_MODES}, got {input_mode!r}")


def deterministic_dataset_subset(
    dataset: TemporalDataset, *, maximum: int, seed: int
) -> TemporalDataset:
    if maximum <= 0 or maximum >= len(dataset):
        return dataset
    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(len(dataset), generator=generator)[:maximum].tolist()
    return dataset.subset(indices)


def deterministic_record_subset(
    records: Sequence[DDD17Record], *, maximum: int, seed: int
) -> list[DDD17Record]:
    if maximum <= 0 or maximum >= len(records):
        return list(records)
    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(len(records), generator=generator)[:maximum].tolist()
    return [records[index] for index in indices]


def temporal_collate(batch: list[tuple[Tensor, Tensor]]) -> tuple[Tensor, Tensor]:
    """Collate exact temporal samples; padding/repetition is forbidden."""
    if not batch:
        raise ValueError("cannot collate an empty batch")
    shapes = {tuple(events.shape) for events, _ in batch}
    if len(shapes) != 1:
        raise ValueError(f"temporal batch contains inconsistent event shapes: {sorted(shapes)}")
    sequence = torch.stack([events for events, _ in batch], dim=1)  # T,N,C,H,W
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
    time_steps: int,
    sequence_stride: int,
    validation_fraction: float,
    training_records: Sequence[DDD17Record],
    validation_records: Sequence[DDD17Record],
    manifest: Path | str | None = None,
) -> TemporalProtocol:
    return TemporalProtocol(
        version=TEMPORAL_PROTOCOL_VERSION,
        input_mode=input_mode,
        time_steps=time_steps,
        input_channels=6 if input_mode == "sequential-6ch" else 2,
        sequence_stride=sequence_stride,
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
