"""Ev-SegNet DDD17 loader.

Known layout on this machine::

    C:/Users/stamir/Desktop/Dataset/DDD17/
      events/{train,test}/*.npy   # six-channel event statistics
      labels/{train,test}/*.png   # class-index masks (ignore = 255)

``test`` is the official held-out set. Preview folders such as ``events_images``
and ``labels/test_colored`` are ignored.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

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

DEFAULT_DDD17_ROOT = Path(r"C:\Users\stamir\Desktop\Dataset\DDD17")


def resolve_ddd17_root(root: Path | str | None = None) -> Path:
    if root is None:
        return DEFAULT_DDD17_ROOT.expanduser().resolve()
    return Path(root).expanduser().resolve()


@dataclass(frozen=True)
class DDD17Record:
    split: str
    event_path: Path
    label_path: Path


@dataclass(frozen=True)
class DDD17Inspection:
    root: str
    records: dict[str, int]
    formats: dict[str, int]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "records": self.records,
            "formats": self.formats,
            "warnings": list(self.warnings),
        }


def _list_files(directory: Path, suffix: str) -> list[Path]:
    if not directory.is_dir():
        return []
    matched: list[Path] = []
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_file(follow_symlinks=False) and entry.name.lower().endswith(suffix):
                matched.append(Path(entry.path))
    return sorted(matched)


def discover_ddd17_records(
    root: Path | str | None = None,
    split: str = "train",
) -> list[DDD17Record]:
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")
    root = resolve_ddd17_root(root)
    if not root.is_dir():
        raise FileNotFoundError(f"DDD17 root does not exist: {root}")

    events_dir = root / "events" / split
    labels_dir = root / "labels" / split
    event_files = _list_files(events_dir, ".npy")
    label_files = {path.stem: path for path in _list_files(labels_dir, ".png")}

    records: list[DDD17Record] = []
    for event_path in event_files:
        label_path = label_files.get(event_path.stem)
        if label_path is not None:
            records.append(DDD17Record(split, event_path, label_path))
    return records


def inspect_ddd17(root: Path | str | None = None) -> DDD17Inspection:
    root = resolve_ddd17_root(root)
    counts: dict[str, int] = {}
    formats: dict[str, int] = {}
    warnings: list[str] = []
    train_records: list[DDD17Record] = []

    for split in SPLITS:
        try:
            records = discover_ddd17_records(root, split)
        except FileNotFoundError:
            records = []
        if split == "train":
            train_records = records
        counts[split] = len(records)
        for record in records[:64]:
            suffix = record.event_path.suffix.lower()
            formats[suffix] = formats.get(suffix, 0) + 1

    if counts["train"] == 0:
        if (root / "events" / "train").is_dir() and not (root / "labels" / "train").is_dir():
            warnings.append("events/train exists but labels/train is missing.")
        else:
            warnings.append("No train records found under events/train + labels/train.")
    if counts["test"] == 0:
        warnings.append("No test records found under events/test + labels/test.")
    else:
        warnings.append("Held-out evaluation uses the official Ev-SegNet test split.")

    if train_records:
        try:
            events, _ = _load_record_arrays(train_records[0])
            shape = tuple(events.shape)
            if events.ndim == 3 and (shape[0] == 6 or shape[-1] == 6):
                warnings.append(
                    "Ev-SegNet six-channel representation detected: two histograms, "
                    "two timestamp means, and two timestamp standard deviations."
                )
            else:
                warnings.append(f"Unexpected event shape for first train sample: {shape}")
        except Exception as exc:
            warnings.append(f"Could not load first train sample: {exc}")

    return DDD17Inspection(str(root), counts, formats, tuple(warnings))


def _load_record_arrays(record: DDD17Record) -> tuple[np.ndarray, np.ndarray]:
    events = np.asarray(np.load(record.event_path, allow_pickle=False))
    labels = np.asarray(Image.open(record.label_path))
    return events, labels


def _canonical_events(array: np.ndarray) -> Tensor:
    """Return one Ev-SegNet sample as ``[1, 6, H, W]``."""

    tensor = torch.as_tensor(array).float().squeeze()
    if tensor.ndim != 3:
        raise ValueError(f"expected a 3-D Ev-SegNet event image, got {tuple(tensor.shape)}")
    if tensor.shape[0] == 6:
        channels_first = tensor
    elif tensor.shape[-1] == 6:
        channels_first = tensor.permute(2, 0, 1)
    else:
        raise ValueError(
            "Ev-SegNet samples must contain six channels "
            f"(histogram/mean/std for two polarities); got {tuple(tensor.shape)}"
        )
    return torch.nan_to_num(channels_first, nan=0.0, posinf=0.0, neginf=0.0).unsqueeze(0)


def _canonical_mask(array: np.ndarray) -> Tensor:
    mask = torch.as_tensor(np.array(array, copy=True)).squeeze().long()
    if mask.ndim != 2:
        raise ValueError(f"unsupported semantic mask shape: {tuple(mask.shape)}")
    mask[(mask < 0) | (mask >= DDD17_CLASS_COUNT)] = IGNORE_INDEX
    return mask


class DDD17Dataset(Dataset[tuple[Tensor, Tensor]]):
    def __init__(
        self,
        root: Path | str | None = None,
        *,
        split: str,
        output_size: tuple[int, int] = (64, 64),
        records: list[DDD17Record] | None = None,
    ) -> None:
        self.root = resolve_ddd17_root(root)
        self.records = records if records is not None else discover_ddd17_records(self.root, split)
        if not self.records:
            raise FileNotFoundError(f"no DDD17 {split} records under {self.root}")
        self.output_size = output_size

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        events_array, mask_array = _load_record_arrays(self.records[index])
        events = _canonical_events(events_array)
        mask = _canonical_mask(mask_array)
        t, c, _, _ = events.shape
        events = F.interpolate(
            events.view(t * c, 1, *events.shape[-2:]),
            size=self.output_size,
            mode="area",
        ).view(t, c, *self.output_size)
        mask = F.interpolate(
            mask[None, None].float(), size=self.output_size, mode="nearest"
        )[0, 0].long()
        return events, mask


def deterministic_record_subset(
    records: list[DDD17Record], *, maximum: int, seed: int
) -> list[DDD17Record]:
    if maximum <= 0 or maximum >= len(records):
        return list(records)
    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(len(records), generator=generator)[:maximum].tolist()
    return [records[index] for index in indices]


def write_inspection(root: Path | str | None, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(inspect_ddd17(root).to_dict(), indent=2), encoding="utf-8")
