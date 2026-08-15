import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from eventspikeseg.data import (
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    DDD17TimestampEventDataset,
    TemporalMetadataError,
    deterministic_dataset_subset,
    discover_ddd17_records,
    inspect_ddd17,
    temporal_collate,
)


def _write_sequence(root: Path, split: str, sequence: str, count: int = 4) -> None:
    events_dir = root / "events" / split
    labels_dir = root / "labels" / split
    events_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "ddd17_temporal_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = {"schema_version": 1, "train": [], "test": []}
    for index in range(count):
        event_path = events_dir / f"{sequence}_{index:03d}.npy"
        label_path = labels_dir / f"{sequence}_{index:03d}.png"
        events = np.full((24, 32, 6), -1.0, dtype=np.float32)
        events[4:8, 5:9, 0] = 1.0
        events[4:8, 5:9, 2] = -0.5 + 0.25 * index
        events[4:8, 5:9, 3] = 0.1
        events[10:14, 12:16, 1] = 0.5
        events[10:14, 12:16, 4] = 0.5
        events[10:14, 12:16, 5] = 0.2
        np.save(event_path, events)
        labels = np.zeros((24, 32), dtype=np.uint8)
        labels[8:16, 8:16] = 5
        Image.fromarray(labels).save(label_path)
        manifest[split].append(
            {
                "event": str(event_path.relative_to(root)),
                "label": str(label_path.relative_to(root)),
                "sequence_id": sequence,
                "frame_index": index,
            }
        )
    manifest_path.write_text(json.dumps(manifest))


def test_default_root_is_embedded_desktop_path() -> None:
    assert Path(r"C:\Users\stamir\Desktop\Dataset\DDD17") == DEFAULT_DDD17_ROOT


def test_timestamp_dataset_decodes_one_interval(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "recA", count=2)
    dataset = DDD17TimestampEventDataset(
        tmp_path, split="train", output_size=(12, 16)
    )
    statistics, mask = dataset[0]
    assert statistics.shape == (6, 12, 16)
    assert mask.shape == (12, 16)
    assert statistics.min().item() >= 0.0
    assert statistics.max().item() <= 1.0
    assert statistics[0].count_nonzero() > 0
    assert statistics[1].count_nonzero() > 0
    inactive = statistics[:2].sum(0) == 0
    assert torch.count_nonzero(statistics[2:, inactive]) == 0
    assert DDD17_CLASS_NAMES[5] == "vehicle"


def test_collate_keeps_records_as_batch_not_time(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "recA", count=2)
    dataset = DDD17TimestampEventDataset(tmp_path, split="train")
    statistics, masks = temporal_collate([dataset[0], dataset[1]])
    assert statistics.shape == (2, 6, 24, 32)
    assert masks.shape == (2, 24, 32)


def test_contiguous_subset_preserves_order(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "recA", count=10)
    dataset = DDD17TimestampEventDataset(tmp_path, split="train")
    subset = deterministic_dataset_subset(dataset, maximum=4, seed=17)
    frames = [record.frame_index for record in subset.records]
    assert frames == list(range(frames[0], frames[0] + 4))
    assert subset.is_stream_start(0)


def test_stream_boundaries_detect_sequences_and_frame_gaps(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "recA", count=3)
    _write_sequence(tmp_path, "train", "recB", count=3)
    # Remove recB_001 from both disk and the authoritative manifest to introduce a chronology gap.
    (tmp_path / "events" / "train" / "recB_001.npy").unlink()
    (tmp_path / "labels" / "train" / "recB_001.png").unlink()
    manifest_path = tmp_path / "ddd17_temporal_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["train"] = [
        row for row in manifest["train"]
        if not (row["sequence_id"] == "recB" and row["frame_index"] == 1)
    ]
    manifest_path.write_text(json.dumps(manifest))
    dataset = DDD17TimestampEventDataset(tmp_path, split="train")
    assert [dataset.is_stream_start(index) for index in range(len(dataset))] == [
        True, False, False, True, True
    ]


def test_manifest_is_required(tmp_path: Path) -> None:
    events_dir = tmp_path / "events" / "train"
    labels_dir = tmp_path / "labels" / "train"
    events_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)
    np.save(events_dir / "000001.npy", np.zeros((24, 32, 6), dtype=np.float32))
    Image.fromarray(np.zeros((24, 32), dtype=np.uint8)).save(labels_dir / "000001.png")
    with pytest.raises(FileNotFoundError):
        discover_ddd17_records(tmp_path, "train")


def test_manifest_rejects_unresolved_sequence_id(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "recA", count=1)
    path = tmp_path / "ddd17_temporal_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["train"][0]["sequence_id"] = "REQUIRED_SEQUENCE_ID"
    path.write_text(json.dumps(manifest))
    with pytest.raises(TemporalMetadataError):
        discover_ddd17_records(tmp_path, "train")




def test_inspection_reports_sequence_counts(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "rec1487417411_export", count=2)
    _write_sequence(tmp_path, "train", "rec1487339175_export", count=2)
    inspection = inspect_ddd17(tmp_path)
    assert inspection.records["train"] == 4
    assert inspection.sequences["train"] == 2
    assert not inspection.warnings
