from pathlib import Path

import h5py
import numpy as np
import torch
from PIL import Image

from eventspikeseg.data import (
    DSEC_6_CLASS_COUNT,
    DSEC_6_CLASS_NAMES,
    DSEC_6_PROTOCOL_VERSION,
    DSEC_CLASS_COUNT,
    IGNORE_INDEX,
    DSECRawEventDataset,
    DSECRecord,
    _translate_dsec_mask,
    discover_dsec_records,
    dsec_temporal_collate,
    split_dsec_records_by_sequence,
)
from eventspikeseg.model import build_model
from eventspikeseg.train import _epoch_train_dataset, train_architecture


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
    events, mask, deltas_us = dataset[0]
    assert events.shape == (10, 2, 44, 64)
    assert events.sum() == 4
    assert events[0, 0, 4, 10] == 1
    assert events[1, 1, 8, 20] == 1
    assert events[5, 0, 12, 30] == 1
    assert events[9, 1, 16, 40] == 1
    assert torch.equal(deltas_us, torch.full((10,), 5_000.0))
    assert deltas_us.sum() == 50_000
    assert mask.shape == (44, 64)
    assert torch.unique(mask).tolist() == [9]

    sequence, targets, batch_deltas = dsec_temporal_collate(
        [(events, mask, deltas_us)]
    )
    assert sequence.shape == (10, 1, 2, 44, 64)
    assert targets.shape == (1, 44, 64)
    assert torch.equal(batch_deltas, deltas_us)
    dataset.close()


def test_dsec_six_class_profile_remaps_masks_and_survives_subset(tmp_path: Path) -> None:
    _write_dsec_sequence(tmp_path, "zurich_city_00_a")
    dataset = DSECRawEventDataset(
        tmp_path,
        split="train",
        output_size=(44, 64),
        internal_updates=10,
        class_count=DSEC_6_CLASS_COUNT,
    )
    assert dataset.class_count == 6
    assert dataset.class_names == DSEC_6_CLASS_NAMES
    assert dataset.protocol_version == DSEC_6_PROTOCOL_VERSION
    assert torch.unique(dataset.target_mask(0)).tolist() == [1]  # wall -> construction+sky
    assert torch.unique(dataset.target_mask(1)).tolist() == [2]  # traffic-sign -> object
    subset = dataset.subset([1])
    assert subset.class_count == 6
    assert torch.unique(subset.target_mask(0)).tolist() == [2]
    subset.close()
    dataset.close()


def test_raw_dsec_events_preserve_repeated_event_density(tmp_path: Path) -> None:
    _write_dsec_sequence(tmp_path, "zurich_city_00_a")
    event_path = tmp_path / "train" / "zurich_city_00_a" / "events.h5"
    with h5py.File(event_path, "r+") as handle:
        original_t = handle["events/t"][()]
        original_x = handle["events/x"][()]
        original_y = handle["events/y"][()]
        original_p = handle["events/p"][()]
        repeated_t = np.sort(np.concatenate((original_t, np.array([1_000, 1_000]))))
        order = np.argsort(np.concatenate((original_t, np.array([1_000, 1_000]))))
        for name, values in {
            "t": repeated_t,
            "x": np.concatenate((original_x, np.array([100, 100], dtype=np.uint16)))[order],
            "y": np.concatenate((original_y, np.array([40, 40], dtype=np.uint16)))[order],
            "p": np.concatenate((original_p, np.array([0, 0], dtype=np.uint8)))[order],
        }.items():
            del handle[f"events/{name}"]
            handle["events"].create_dataset(name, data=values)
        milliseconds = np.arange(0, 102, dtype=np.int64)
        del handle["ms_to_idx"]
        handle.create_dataset(
            "ms_to_idx",
            data=np.searchsorted(repeated_t, milliseconds * 1_000).astype(np.uint64),
        )

    records = discover_dsec_records(tmp_path, "train")
    dataset = DSECRawEventDataset(
        tmp_path,
        split="train",
        output_size=(44, 64),
        internal_updates=10,
        records=records,
    )
    events, _, _ = dataset[0]
    assert torch.isclose(events[0, 0, 4, 10], torch.tensor(3.0))
    assert torch.isclose(events.sum(), torch.tensor(6.0))
    dataset.close()


def test_dsec_mask_translation_does_not_wrap() -> None:
    mask = torch.arange(12).reshape(3, 4)
    translated = _translate_dsec_mask(mask, dx=1, dy=-1)
    assert torch.equal(translated[:2, 1:], mask[1:, :3])
    assert torch.all(translated[:, 0] == IGNORE_INDEX)
    assert torch.all(translated[2] == IGNORE_INDEX)


def test_dsec_augmentation_is_record_aligned_and_validation_can_disable_it(
    tmp_path: Path,
) -> None:
    _write_dsec_sequence(tmp_path, "zurich_city_00_a")
    records = discover_dsec_records(tmp_path, "train")
    training = DSECRawEventDataset(
        tmp_path,
        split="train",
        output_size=(44, 64),
        internal_updates=10,
        records=records,
        augmentation_seed=17,
    )
    validation = DSECRawEventDataset(
        tmp_path,
        split="train",
        output_size=(44, 64),
        internal_updates=10,
        records=records,
    )
    assert training._spatial_augmentation(records[0]) == training._spatial_augmentation(
        records[1]
    )
    assert validation._spatial_augmentation(records[0]) == (False, 0, 0)
    augmented_events, augmented_mask, _ = training[0]
    plain_events, plain_mask, _ = validation[0]
    assert augmented_events.shape == plain_events.shape
    assert augmented_mask.shape == plain_mask.shape
    assert not torch.equal(augmented_mask, plain_mask)
    training.close()
    validation.close()


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


def test_dsec_memory_bounded_replay_trains_one_complete_record(tmp_path: Path) -> None:
    for sequence in ("zurich_city_00_a", "zurich_city_01_a", "zurich_city_02_a"):
        _write_dsec_sequence(tmp_path, sequence)
    result = train_architecture(
        tmp_path,
        architecture="EventSpikeSeg140k",
        suite="final",
        seed=17,
        epochs=1,
        batch_size=1,
        input_mode="raw-events",
        manifest=None,
        train_samples=0.25,
        validation_fraction=0.10,
        learning_rate=5e-4,
        output_dir=tmp_path / "checkpoints",
        output_size=(16, 16),
        device="cpu",
        checkpoint_every=1,
        internal_updates=10,
        sequential_chunks=5,
        continuous_state=True,
        dataset_name="dsec",
        dsec_class_count=6,
        data_workers=4,
    )
    assert result.epochs == 1
    assert len(result.per_class_iou) == 6
    assert Path(result.checkpoint).is_file()
    checkpoint = torch.load(result.checkpoint, map_location="cpu", weights_only=False)
    assert tuple(checkpoint["class_names"]) == DSEC_6_CLASS_NAMES
    assert checkpoint["architecture_config"]["name"] == "EventSpikeSeg140k"
    assert checkpoint["temporal_protocol_version"] == DSEC_6_PROTOCOL_VERSION
    preview_paths = sorted((tmp_path / "checkpoints" / "images").glob("*.png"))
    assert len(preview_paths) == 2
    with Image.open(preview_paths[0]) as preview:
        assert preview.size == (48, 16)


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
