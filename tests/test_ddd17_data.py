from pathlib import Path

import numpy as np
from PIL import Image

from eventscnn.data import (
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    DDD17Dataset,
    discover_ddd17_records,
    inspect_ddd17,
)
from eventscnn.train import temporal_collate


def _write_split(root: Path, split: str, count: int = 3) -> None:
    events_dir = root / "events" / split
    labels_dir = root / "labels" / split
    events_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)
    for index in range(count):
        events = np.zeros((24, 32, 6), dtype=np.float32)
        events[4:12, 4:12, 0] = index + 1
        np.save(events_dir / f"sample_{index:03d}.npy", events)
        labels = np.zeros((24, 32), dtype=np.uint8)
        labels[8:16, 8:16] = 5
        Image.fromarray(labels).save(labels_dir / f"sample_{index:03d}.png")


def test_default_root_is_embedded_desktop_path() -> None:
    assert Path(r"C:\Users\stamir\Desktop\Dataset\DDD17") == DEFAULT_DDD17_ROOT


def test_modality_layout_loads_six_channel_samples(tmp_path: Path) -> None:
    _write_split(tmp_path, "train", count=2)
    (tmp_path / "events_images").mkdir()
    Image.fromarray(np.zeros((24, 32), dtype=np.uint8)).save(
        tmp_path / "events_images" / "preview.png"
    )

    records = discover_ddd17_records(tmp_path, "train")
    assert len(records) == 2
    assert all(record.event_path.parent.name == "train" for record in records)
    assert all("events_images" not in record.event_path.parts for record in records)

    dataset = DDD17Dataset(tmp_path, split="train", output_size=(32, 32))
    events, mask = dataset[0]
    assert events.shape == (1, 6, 32, 32)
    assert mask.shape == (32, 32)
    assert int(mask.max()) == 5
    assert DDD17_CLASS_NAMES[5] == "vehicle"


def test_direct_encoding_repeats_one_event_image_over_internal_time(tmp_path: Path) -> None:
    _write_split(tmp_path, "train")
    sample = DDD17Dataset(tmp_path, split="train", output_size=(32, 32))[0]
    sequence, mask = temporal_collate([sample], time_steps=4)
    assert sequence.shape == (4, 1, 6, 32, 32)
    assert mask.shape == (1, 32, 32)
    assert np.allclose(sequence[0].numpy(), sequence[-1].numpy())
    inspection = inspect_ddd17(tmp_path)
    assert any("six-channel" in warning for warning in inspection.warnings)


def test_stem_mismatch_is_skipped(tmp_path: Path) -> None:
    _write_split(tmp_path, "train", count=1)
    Image.fromarray(np.zeros((24, 32), dtype=np.uint8)).save(
        tmp_path / "labels" / "train" / "unmatched.png"
    )
    assert len(discover_ddd17_records(tmp_path, "train")) == 1


def test_missing_labels_train_is_reported(tmp_path: Path) -> None:
    (tmp_path / "events" / "train").mkdir(parents=True)
    (tmp_path / "labels" / "test").mkdir(parents=True)
    np.save(
        tmp_path / "events" / "train" / "sample.npy",
        np.zeros((24, 32, 6), dtype=np.float32),
    )
    inspection = inspect_ddd17(tmp_path)
    assert inspection.records["train"] == 0
    assert any("labels/train is missing" in warning for warning in inspection.warnings)
