from pathlib import Path

import h5py
import numpy as np
import torch
from PIL import Image

from eventspikeseg.data import (
    DSEC_CLASS_COUNT,
    DSECRawEventDataset,
    DSECRecord,
    discover_dsec_records,
    dsec_temporal_collate,
    split_dsec_records_by_sequence,
)
from eventspikeseg.model import build_model
from eventspikeseg.train import _epoch_train_dataset


def _write_dsec_sequence(root: Path, name: str) -> None:
    sequence = root / "train" / name
    labels = sequence / "11classes"
    labels.mkdir(parents=True)
    offset = 1_000_000
    relative_t = np.array(
        [1_000, 6_000, 26_000, 49_999, 50_000, 76_000, 99_999], dtype=np.uint32
    )
    x = np.array([100, 200, 300, 400, 120, 320, 500], dtype=np.uint16)
    y = np.array([40, 80, 120, 160, 50, 130, 200], dtype=np.uint16)
    polarity = np.array([0, 1, 0, 1, 0, 1, 0], dtype=np.uint8)
    milliseconds = np.arange(0, 102, dtype=np.int64)
    ms_to_idx = np.searchsorted(relative_t, milliseconds * 1_000).astype(np.uint64)
    with h5py.File(sequence / "events.h5", "w") as handle:
        events = handle.create_group("events")
        events.create_dataset("t", data=relative_t)
        events.create_dataset("x", data=x)
        events.create_dataset("y", data=y)
        events.create_dataset("p", data=polarity)
        handle.create_dataset("ms_to_idx", data=ms_to_idx)
        handle.create_dataset("t_offset", data=np.int64(offset))

    grid_y, grid_x = np.mgrid[:480, :640]
    rectify = np.stack((grid_x, grid_y), axis=-1).astype(np.float32)
    with h5py.File(sequence / "rectify_map.h5", "w") as handle:
        handle.create_dataset("rectify_map", data=rectify)

    timestamps = np.array([offset + 50_000, offset + 100_000], dtype=np.int64)
    np.savetxt(
        sequence / f"{name}_semantic_timestamps.txt", timestamps, fmt="%d"
    )
    for index in range(2):
        mask = np.full((440, 640), index + 9, dtype=np.uint8)
        Image.fromarray(mask).save(labels / f"{index:06d}.png")


def test_raw_dsec_events_are_rectified_and_scheduled_once(tmp_path: Path) -> None:
    _write_dsec_sequence(tmp_path, "zurich_city_00_a")
    records = discover_dsec_records(tmp_path, "train")
    assert len(records) == 2
    dataset = DSECRawEventDataset(
        tmp_path,
        split="train",
        output_size=(44, 64),
        internal_updates=10,
        records=records,
    )
    events, mask = dataset[0]
    assert events.shape == (10, 2, 44, 64)
    assert events.sum() == 4
    assert events[0, 0, 4, 10] == 1
    assert events[1, 1, 8, 20] == 1
    assert events[5, 0, 12, 30] == 1
    assert events[9, 1, 16, 40] == 1
    assert mask.shape == (44, 64)
    assert torch.unique(mask).tolist() == [9]

    sequence, targets = dsec_temporal_collate([(events, mask)])
    assert sequence.shape == (10, 1, 2, 44, 64)
    assert targets.shape == (1, 44, 64)
    dataset.close()


def test_140k_accepts_pre_scheduled_raw_event_clocks() -> None:
    model = build_model(
        architecture="EventSpikeSeg140k",
        class_count=DSEC_CLASS_COUNT,
        input_channels=2,
        internal_updates=5,
    )
    model.eval()
    source = torch.zeros(5, 1, 2, 16, 16)
    source[2, 0, 1, 8, 8] = 1
    with torch.no_grad():
        outputs = model(source)
    assert outputs["segmentation_logits"].shape == (1, DSEC_CLASS_COUNT, 16, 16)


def test_dsec_validation_scales_complete_sequence_count_with_train_fraction() -> None:
    counts = {
        "zurich_city_00_a": 938,
        "zurich_city_01_a": 680,
        "zurich_city_02_a": 234,
        "zurich_city_04_a": 700,
        "zurich_city_05_a": 1752,
        "zurich_city_06_a": 1522,
        "zurich_city_07_a": 1462,
        "zurich_city_08_a": 786,
    }
    records = [
        DSECRecord(
            split="train",
            sequence_id=sequence_id,
            frame_index=index,
            timestamp_us=(index + 1) * 50_000,
            event_path=Path(f"{sequence_id}/events.h5"),
            rectify_path=Path(f"{sequence_id}/rectify_map.h5"),
            label_path=Path(f"{sequence_id}/{index:06d}.png"),
        )
        for sequence_id, count in counts.items()
        for index in range(count)
    ]
    half_training, half_validation = split_dsec_records_by_sequence(
        records, validation_fraction=0.10, train_samples=0.5
    )
    half_sequences = {record.sequence_id for record in half_validation}
    assert half_sequences == {"zurich_city_02_a"}
    assert len(half_validation) == 234
    assert {record.sequence_id for record in half_training}.isdisjoint(half_sequences)

    broad_training, broad_validation = split_dsec_records_by_sequence(
        records, validation_fraction=0.10, train_samples=0.7
    )
    broad_sequences = {record.sequence_id for record in broad_validation}
    assert broad_sequences == {"zurich_city_01_a", "zurich_city_02_a"}
    assert len(broad_validation) == 914
    assert {record.sequence_id for record in broad_training}.isdisjoint(broad_sequences)


def test_dsec_fractional_epochs_advance_one_circular_stream_cursor(tmp_path: Path) -> None:
    for sequence_id in (
        "zurich_city_00_a",
        "zurich_city_01_a",
        "zurich_city_02_a",
        "zurich_city_04_a",
    ):
        _write_dsec_sequence(tmp_path, sequence_id)
    dataset = DSECRawEventDataset(
        tmp_path,
        split="train",
        internal_updates=10,
    )
    epoch1 = _epoch_train_dataset(
        dataset, train_samples=0.5, seed=17, epoch=1
    )
    epoch2 = _epoch_train_dataset(
        dataset, train_samples=0.5, seed=17, epoch=2
    )
    epoch3 = _epoch_train_dataset(
        dataset, train_samples=0.5, seed=999, epoch=3
    )
    assert len(epoch1) == len(epoch2) == 4
    def ids(selected):
        return [
            (record.sequence_id, record.frame_index) for record in selected.records
        ]
    complete_ids = [
        (record.sequence_id, record.frame_index) for record in dataset.records
    ]
    assert ids(epoch1) + ids(epoch2) == complete_ids
    assert ids(epoch3) == ids(epoch1)
