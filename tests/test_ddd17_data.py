import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import eventspikeseg.data as data_module
from eventspikeseg.data import (
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    DDD17EventBinDataset,
    DDD17RawEventDataset,
    DDD17SequentialDataset,
    TemporalMetadataError,
    bin_raw_events,
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
        events = np.zeros((24, 32, 6), dtype=np.float32)
        events[..., 0] = index + 1
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


def test_sequential_dataset_uses_real_consecutive_frames(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "recA", count=4)
    dataset = DDD17SequentialDataset(
        tmp_path, split="train", time_steps=3, output_size=(32, 32)
    )
    events, mask = dataset[0]
    assert events.shape == (3, 6, 32, 32)
    assert mask.shape == (32, 32)
    assert float(events[0, 0].mean()) < float(events[1, 0].mean()) < float(events[2, 0].mean())
    sequence, masks = temporal_collate([(events, mask)])
    assert sequence.shape == (3, 1, 6, 32, 32)
    assert masks.shape == (1, 32, 32)
    assert DDD17_CLASS_NAMES[5] == "vehicle"


def test_event_bin_dataset_uses_consecutive_polarity_histograms(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "recA", count=4)
    for index, path in enumerate(sorted((tmp_path / "events" / "train").glob("*.npy"))):
        statistics = np.load(path)
        statistics[..., 0] = -1.0 + 2.0 * index / 3.0
        statistics[..., 1] = -1.0
        statistics[..., 2:] = 0.75  # Statistics must not leak into event-bin input.
        np.save(path, statistics)

    dataset = DDD17EventBinDataset(tmp_path, split="train", time_steps=3)
    bins, mask = dataset[0]
    assert bins.shape == (3, 2, 24, 32)
    assert mask.shape == (24, 32)
    assert bins.min().item() == 0.0
    assert bins.max().item() <= 1.0
    assert [float(bins[t, 0].mean()) for t in range(3)] == pytest.approx(
        [0.0, 1.0 / 3.0, 2.0 / 3.0]
    )
    assert bins[:, 1].count_nonzero().item() == 0


def test_sequential_dataset_reads_only_the_final_target_mask(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_sequence(tmp_path, "train", "recA", count=4)
    dataset = DDD17SequentialDataset(tmp_path, split="train", time_steps=3)
    loaded_paths: list[Path] = []
    original = data_module._load_record_mask

    def tracked_load(record):
        loaded_paths.append(record.label_path)
        return original(record)

    monkeypatch.setattr(data_module, "_load_record_mask", tracked_load)
    dataset[0]
    assert loaded_paths == [dataset.windows[0].target_record.label_path]


def test_windows_never_cross_sequence_or_frame_gap(tmp_path: Path) -> None:
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
    dataset = DDD17SequentialDataset(tmp_path, split="train", time_steps=2)
    assert all(window.sequence_id == "recA" for window in dataset.windows)


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


def test_raw_event_binning_preserves_time_and_polarity() -> None:
    t = np.array([100, 110, 125, 149], dtype=np.int64)
    x = np.array([1, 1, 2, 2])
    y = np.array([1, 1, 2, 2])
    p = np.array([1, 0, 1, -1])
    bins = bin_raw_events(
        t, x, y, p, start_us=100, stop_us=150, time_steps=5, height=4, width=4
    )
    assert bins.shape == (5, 2, 4, 4)
    assert bins.sum().item() == 4
    assert bins[0, 0, 1, 1] == 1
    assert bins[1, 1, 1, 1] == 1
    assert bins[2, 0, 2, 2] == 1
    assert bins[4, 1, 2, 2] == 1


def _write_raw_ddd_recording(
    root: Path, recording_id: str, frame_count: int, *, float_seconds: bool = False
) -> Path:
    import h5py

    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"rec{recording_id}.hdf5"
    frame_us = np.arange(frame_count, dtype=np.int64) * 50_000
    event_us = np.array([4_960_000, 4_980_000, 5_000_000], dtype=np.int64)
    frame_ts = frame_us.astype(np.float64) / 1_000_000.0 if float_seconds else frame_us
    event_t = event_us.astype(np.float64) / 1_000_000.0 if float_seconds else event_us
    with h5py.File(raw_path, "w") as handle:
        handle.create_dataset("frame_ts", data=frame_ts)
        events = handle.create_group("events")
        events.create_dataset("t", data=event_t)
        events.create_dataset("x", data=np.array([2, 3, 4], dtype=np.int16))
        events.create_dataset("y", data=np.array([2, 3, 4], dtype=np.int16))
        events.create_dataset("p", data=np.array([1, 0, 1], dtype=np.int8))
    return raw_path


def test_raw_event_dataset_resolves_alignment_from_raw_hdf5(tmp_path: Path) -> None:
    sequence = "rec1487417411_export"
    _write_sequence(tmp_path, "train", sequence, count=1)
    _write_raw_ddd_recording(tmp_path, "1487417411", frame_count=5152)

    dataset = DDD17RawEventDataset(
        tmp_path, split="train", time_steps=5, raw_window_us=50_000
    )
    record = dataset.records[0]
    assert record.raw_event_path == tmp_path / "raw" / "rec1487417411.hdf5"
    assert record.timestamp_us == 100 * 50_000
    events, mask = dataset[0]
    assert events.shape == (5, 2, 24, 32)
    assert events.sum().item() == 2  # [4.95s, 5.0s) excludes the endpoint event
    assert mask.shape == (24, 32)


def test_raw_event_dataset_does_not_load_precomputed_six_channel_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sequence = "rec1487417411_export"
    _write_sequence(tmp_path, "train", sequence, count=1)
    _write_raw_ddd_recording(tmp_path, "1487417411", frame_count=5152)
    dataset = DDD17RawEventDataset(
        tmp_path, split="train", time_steps=5, raw_window_us=50_000
    )

    def unexpected_load(_record):
        raise AssertionError("raw-events must not load Ev-SegNet six-channel input")

    monkeypatch.setattr(data_module, "_load_record_events", unexpected_load)
    events, _ = dataset[0]
    assert events.shape == (5, 2, 24, 32)


def test_raw_event_dataset_normalizes_float_second_timestamps(tmp_path: Path) -> None:
    sequence = "rec1487417411_export"
    _write_sequence(tmp_path, "train", sequence, count=1)
    _write_raw_ddd_recording(
        tmp_path, "1487417411", frame_count=5152, float_seconds=True
    )

    dataset = DDD17RawEventDataset(
        tmp_path, split="train", time_steps=5, raw_window_us=50_000
    )
    assert dataset.records[0].timestamp_us == 5_000_000
    events, _ = dataset[0]
    assert events.sum().item() == 2


def test_raw_alignment_accepts_exact_terminal_boundary_sample(tmp_path: Path) -> None:
    sequence = "rec1487417411_export"
    _write_sequence(tmp_path, "test", sequence, count=1)
    manifest_path = tmp_path / "ddd17_temporal_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["test"][0]["frame_index"] = 3890
    manifest_path.write_text(json.dumps(manifest))
    _write_raw_ddd_recording(tmp_path, "1487417411", frame_count=5152)

    dataset = DDD17RawEventDataset(
        tmp_path, split="test", time_steps=5, raw_window_us=50_000
    )
    assert dataset.records[0].timestamp_us == 5150 * 50_000


def test_raw_alignment_rejects_beyond_terminal_boundary(tmp_path: Path) -> None:
    sequence = "rec1487417411_export"
    _write_sequence(tmp_path, "test", sequence, count=1)
    manifest_path = tmp_path / "ddd17_temporal_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["test"][0]["frame_index"] = 3891
    manifest_path.write_text(json.dumps(manifest))
    _write_raw_ddd_recording(tmp_path, "1487417411", frame_count=5152)

    with pytest.raises(TemporalMetadataError, match="supported local indices"):
        DDD17RawEventDataset(
            tmp_path, split="test", time_steps=5, raw_window_us=50_000
        )


def test_inspection_reports_sequence_counts_without_hdf5_requirement(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "train", "rec1487417411_export", count=2)
    _write_sequence(tmp_path, "train", "rec1487339175_export", count=2)
    inspection = inspect_ddd17(tmp_path)
    assert inspection.records["train"] == 4
    assert inspection.sequences["train"] == 2
    assert not inspection.warnings


def test_raw_hdf5_numeric_matrix_support(tmp_path: Path) -> None:
    import h5py

    from eventspikeseg.data import DDD17Record, slice_raw_events

    raw = tmp_path / "raw.h5"
    rows = np.array(
        [
            [900, 1, 2, 1],
            [950, 2, 3, 0],
            [990, 3, 4, 1],
            [1010, 4, 5, 0],
        ],
        dtype=np.int64,
    )
    with h5py.File(raw, "w") as handle:
        handle.create_dataset("events", data=rows)
    record = DDD17Record(
        "train", tmp_path / "dummy.npy", tmp_path / "dummy.png", "recA", 0,
        timestamp_us=1000, raw_event_path=raw
    )
    t, x, y, p = slice_raw_events(record, start_us=940, stop_us=1000)
    assert t.tolist() == [950, 990]
    assert x.tolist() == [2, 3]
    assert y.tolist() == [3, 4]
    assert p.tolist() == [0, 1]
