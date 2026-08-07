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
    archive_index: int | None = None


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


def _candidate_layout_roots(root: Path) -> list[Path]:
    """Return a bounded set of known Ev-SegNet wrapper roots without full-tree scans."""
    candidates = [root]
    if root.is_dir():
        with os.scandir(root) as entries:
            first_level = [Path(entry.path) for entry in entries if entry.is_dir(follow_symlinks=False)]
        candidates.extend(first_level)
        for directory in first_level:
            try:
                with os.scandir(directory) as entries:
                    candidates.extend(
                        Path(entry.path)
                        for entry in entries
                        if entry.is_dir(follow_symlinks=False)
                        and entry.name.lower() in {"our_codification", "ddd17", "dataset"}
                    )
            except OSError:
                continue
    return candidates


def _paired_directory_records(layout_root: Path, split: str) -> list[DDD17Record]:
    directory_pairs = (
        (layout_root / "events" / split, layout_root / "labels" / split),
        (layout_root / split / "events", layout_root / split / "labels"),
    )
    for events_dir, labels_dir in directory_pairs:
        event_files = _list_files(events_dir, ".npy")
        label_list = _list_files(labels_dir, ".png")
        if not event_files or not label_list:
            continue
        by_stem = {path.stem: path for path in label_list}
        exact = [
            DDD17Record(split, event_path, by_stem[event_path.stem])
            for event_path in event_files
            if event_path.stem in by_stem
        ]
        if len(exact) == len(event_files):
            return exact
        if len(event_files) == len(label_list):
            return [
                DDD17Record(split, event_path, label_path)
                for event_path, label_path in zip(event_files, label_list, strict=True)
            ]
    return []


def discover_ddd17_records(
    root: Path | str | None = None,
    split: str = "train",
) -> list[DDD17Record]:
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")
    root = resolve_ddd17_root(root)
    if not root.is_dir():
        raise FileNotFoundError(f"DDD17 root does not exist: {root}")

    for layout_root in _candidate_layout_roots(root):
        records = _paired_directory_records(layout_root, split)
        if records:
            return records

    archive = root / f"ddd17_{split}.npz"
    if archive.is_file():
        with np.load(archive, allow_pickle=False) as payload:
            if "events" not in payload or "labels" not in payload:
                raise ValueError(f"{archive} must contain events and labels arrays")
            count = min(len(payload["events"]), len(payload["labels"]))
        return [DDD17Record(split, archive, archive, index) for index in range(count)]
    return []


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
                    "Ev-SegNet six-channel representation detected: the expected primary input "
                    "contains two histograms, two timestamp means, and two timestamp standard deviations."
                )
            else:
                warnings.append(f"Unexpected event shape for first train sample: {shape}")
        except Exception as exc:
            warnings.append(f"Could not load first train sample: {exc}")

    return DDD17Inspection(str(root), counts, formats, tuple(warnings))


def _load_record_arrays(record: DDD17Record) -> tuple[np.ndarray, np.ndarray]:
    if record.archive_index is not None:
        with np.load(record.event_path, allow_pickle=False) as payload:
            return (
                np.asarray(payload["events"][record.archive_index]),
                np.asarray(payload["labels"][record.archive_index]),
            )
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
