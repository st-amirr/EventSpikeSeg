import numpy as np
import pytest

from eventscnn.config import EventBinningConfig
from eventscnn.datasets import (
    discover_mevdt_frames,
    load_event_npz,
    load_mevdt_boxes,
    load_mevdt_window,
    remap_davis346_coordinate,
)


def test_frozen_davis346_coordinate_mapping() -> None:
    assert remap_davis346_coordinate(0, 0) == (0, 0)
    assert remap_davis346_coordinate(345, 259) == (239, 179)
    with pytest.raises(ValueError):
        remap_davis346_coordinate(346, 0)


def test_tiny_npz_fixture_loads_without_dataset_download(tmp_path) -> None:
    path = tmp_path / "events.npz"
    np.savez(path, t=[0, 999], x=[0, 345], y=[0, 259], p=[0, 1])
    events = load_event_npz(path, remap_davis346=True)
    assert [(event.x, event.y, event.polarity) for event in events] == [
        (0, 0, False),
        (239, 179, True),
    ]


def test_fixture_schema_rejects_missing_arrays(tmp_path) -> None:
    path = tmp_path / "bad.npz"
    np.savez(path, t=[0], x=[0])
    with pytest.raises(ValueError, match="requires arrays"):
        load_event_npz(path)


def _write_mevdt_fixture(tmp_path):
    root = tmp_path / "MEVDT"
    sequence = "1000000000"
    event_dir = root / "sequences" / "train" / "Scene_A" / sequence
    label_dir = root / "labels" / "detection_labels" / "train" / "Scene_A" / sequence
    split_dir = root / "data_splits"
    event_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    split_dir.mkdir(parents=True)
    (event_dir / f"{sequence}_events.csv").write_text(
        "ts,x,y,p\n"
        "1000000500,1,2,0\n"
        "1000000999,1,2,1\n"
        "1001000000,3,4,1\n"
        "1001999999,3,4,1\n"
        "1002000000,5,6,1\n",
        encoding="utf-8",
    )
    (label_dir / "1002000000.txt").write_text(
        "1 10.5 20.0 30.5 40.0\n", encoding="utf-8"
    )
    (split_dir / "MEVDT_org_rate_train.csv").write_text(
        "events_file_path,image_path,labels_file_path\n"
        "unused.aedat,unused.png,"
        "labels/detection_labels/train/Scene_A/1000000000/1002000000.txt\n",
        encoding="utf-8",
    )
    return root


def test_mevdt_discovers_frames_and_parses_xyxy_labels(tmp_path) -> None:
    root = _write_mevdt_fixture(tmp_path)
    records = discover_mevdt_frames(root, split="train")
    assert len(records) == 1
    assert records[0].timestamp_ns == 1_002_000_000
    boxes = load_mevdt_boxes(records[0].label_path)
    assert boxes[0].class_id == 1
    assert boxes[0].area == 400.0


def test_mevdt_nanosecond_window_is_half_open_and_preserves_counts(tmp_path) -> None:
    root = _write_mevdt_fixture(tmp_path)
    record = discover_mevdt_frames(root, split="train")[0]
    sample = load_mevdt_window(
        record,
        config=EventBinningConfig(bin_duration_us=1_000),
        window_steps=2,
    )
    assert sample.events.shape == (2, 1, 2, 180, 240)
    assert sample.events[0, 0, 0, 2, 1] == 1
    assert sample.events[0, 0, 1, 2, 1] == 1
    assert sample.events[1, 0, 1, 4, 3] == 2
    assert sample.events[:, 0, 1, 6, 5].sum() == 0


def test_mevdt_rejects_xywh_misinterpretation(tmp_path) -> None:
    label = tmp_path / "bad.txt"
    label.write_text("1 200 10 50 30\n", encoding="utf-8")
    with pytest.raises(ValueError, match="x coordinates"):
        load_mevdt_boxes(label)


def test_mevdt_clips_only_floating_point_border_noise(tmp_path) -> None:
    label = tmp_path / "border.txt"
    label.write_text("1 200 10 240.00000000000003 30\n", encoding="utf-8")
    assert load_mevdt_boxes(label)[0].x_max == 240.0
