import numpy as np
import pytest

from eventscnn.model import EventBinningConfig
from eventscnn.data import (
    MEVDTFrameRecord,
    _load_mevdt_event_stream,
    chronological_mevdt_records,
    discover_mevdt_frames,
    load_event_npz,
    load_mevdt_boxes,
    load_mevdt_tracking_sequence,
    load_mevdt_window,
    remap_davis346_coordinate,
    split_mevdt_train_sequences,
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
    misses = _load_mevdt_event_stream.cache_info().misses
    load_mevdt_window(
        record,
        config=EventBinningConfig(bin_duration_us=1_000),
        window_steps=2,
    )
    assert _load_mevdt_event_stream.cache_info().misses == misses


def test_mevdt_rejects_xywh_misinterpretation(tmp_path) -> None:
    label = tmp_path / "bad.txt"
    label.write_text("1 200 10 50 30\n", encoding="utf-8")
    with pytest.raises(ValueError, match="x coordinates"):
        load_mevdt_boxes(label)


def test_mevdt_clips_only_floating_point_border_noise(tmp_path) -> None:
    label = tmp_path / "border.txt"
    label.write_text("1 200 10 240.00000000000003 30\n", encoding="utf-8")
    assert load_mevdt_boxes(label)[0].x_max == 240.0


def test_mevdt_validation_partition_is_sequence_disjoint_and_deterministic(tmp_path) -> None:
    records = []
    for scene in ("Scene_A", "Scene_B"):
        for sequence_index in range(5):
            sequence = str(sequence_index)
            for timestamp in (2, 1):
                path = tmp_path / f"{scene}-{sequence}-{timestamp}.txt"
                path.write_text("", encoding="utf-8")
                records.append(
                    MEVDTFrameRecord(
                        "train", scene, sequence, timestamp, tmp_path / "events.csv", path
                    )
                )
    training, validation = split_mevdt_train_sequences(records, seed=7)
    repeated = split_mevdt_train_sequences(records, seed=7)
    training_keys = {(record.scene, record.sequence) for record in training}
    validation_keys = {(record.scene, record.sequence) for record in validation}
    assert training_keys.isdisjoint(validation_keys)
    assert repeated == (training, validation)
    assert {record.scene for record in validation} == {"Scene_A", "Scene_B"}
    ordered = chronological_mevdt_records(list(reversed(validation)))
    assert ordered == sorted(
        validation, key=lambda record: (record.scene, record.sequence, record.timestamp_ns)
    )


def test_mevdt_tracking_coco_loads_timestamp_identity_and_xywh(tmp_path) -> None:
    path = (
        tmp_path
        / "labels"
        / "tracking_labels"
        / "test"
        / "Scene_A"
        / "123"
    )
    path.mkdir(parents=True)
    (path / "123-coco.json").write_text(
        '{"images":[{"id":7,"file_name":"456.png"}],'
        '"annotations":[{"image_id":7,"category_id":1,"track_id":"car-a",'
        '"bbox":[10,20,30,40]}]}',
        encoding="utf-8",
    )
    annotations = load_mevdt_tracking_sequence(
        tmp_path, split="test", scene="Scene_A", sequence="123"
    )
    item = annotations[456][0]
    assert item.track_id == "car-a"
    assert (item.box.x_min, item.box.y_min, item.box.x_max, item.box.y_max) == (
        10.0,
        20.0,
        40.0,
        60.0,
    )
