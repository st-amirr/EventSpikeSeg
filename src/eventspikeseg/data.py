"""Timestamp-aware DDD17 semantic data loading.

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
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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
