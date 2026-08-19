import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

import eventspikeseg.data as data_module
from eventspikeseg.data import temporal_collate
from eventspikeseg.evaluate import _records_for_checkpoint
from eventspikeseg.train import (
    LossProfile,
    TrainResult,
    _epoch_train_dataset,
    _prepare_datasets,
    _training_objective,
    apply_resume_learning_rate,
    architecture_presets,
    estimate_class_weights,
    infer_model_suite,
    loss_profile_for_suite,
    refinement_phase_for_epoch,
    select_winner,
    soft_dice_loss,
    split_temporal_chunks,
)


def _result(name: str, miou: float, parameters: int, spike_rate: float) -> TrainResult:
    return TrainResult(
        architecture=name,
        seed=17,
        epochs=1,
        train_samples=2,
        validation_samples=1,
        parameter_count=parameters,
        mean_iou=miou,
        pixel_accuracy=0.9,
        mean_spike_rate=spike_rate,
        checkpoint=f"{name}.pt",
        per_class_iou=(miou,) * 6,
        ground_truth_pixels=(1,) * 6,
        predicted_pixels=(1,) * 6,
        layer_spike_rates={"segmentation_spikes": spike_rate},
        neuron_diagnostics={},
    )


def _write_sequence(root: Path, sequence: str, count: int = 5) -> None:
    events_dir = root / "events" / "train"
    labels_dir = root / "labels" / "train"
    events_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "ddd17_temporal_manifest.json"
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {"schema_version": 1, "train": [], "test": []}
    )
    for index in range(count):
        event_path = events_dir / f"{sequence}_{index:03d}.npy"
        label_path = labels_dir / f"{sequence}_{index:03d}.png"
        np.save(event_path, np.zeros((24, 32, 6), dtype=np.float32))
        Image.fromarray(np.zeros((24, 32), dtype=np.uint8)).save(label_path)
        manifest["train"].append({
            "event": str(event_path.relative_to(root)),
            "label": str(label_path.relative_to(root)),
            "sequence_id": sequence,
            "frame_index": index,
        })
    manifest_path.write_text(json.dumps(manifest))


def test_winner_prefers_smaller_model_within_half_point() -> None:
    winner = select_winner(
        [
            _result("large", 0.500, 100_000, 0.05),
            _result("small", 0.497, 50_000, 0.06),
            _result("weak", 0.480, 10_000, 0.01),
        ]
    )
    assert winner.architecture == "small"


def test_prepare_datasets_holds_out_complete_sequences(tmp_path: Path) -> None:
    for sequence in ("recA", "recB", "recC", "recD"):
        _write_sequence(tmp_path, sequence, count=5)
    train_pool, held_out, protocol, fingerprint = _prepare_datasets(
        tmp_path,
        seed=17,
        output_size=(32, 32),
        validation_fraction=0.25,
        input_mode="timestamp-events",
        manifest=None,
    )
    train_sequences = {record.sequence_id for record in train_pool.records}
    validation_sequences = {record.sequence_id for record in held_out.records}
    assert train_sequences.isdisjoint(validation_sequences)
    assert protocol["input_mode"] == "timestamp-events"
    assert protocol["stateful_stream"] is True
    assert protocol["internal_updates"] == 10
    assert protocol["event_clock_us"] == 5_000
    assert len(fingerprint) == 64




def test_prepare_datasets_single_sequence_uses_contiguous_temporal_holdout(tmp_path: Path) -> None:
    _write_sequence(tmp_path, "recA", count=30)
    train_pool, held_out, protocol, fingerprint = _prepare_datasets(
        tmp_path,
        seed=17,
        output_size=(32, 32),
        validation_fraction=0.20,
        input_mode="timestamp-events",
        manifest=None,
    )
    validation_frames = [record.frame_index for record in held_out.records]
    assert validation_frames == list(range(validation_frames[0], validation_frames[-1] + 1))
    training_frames = {
        record.frame_index
        for record in train_pool.records
    }
    validation_record_frames = {
        record.frame_index
        for record in held_out.records
    }
    assert training_frames.isdisjoint(validation_record_frames)
    assert protocol["training_sequences"] == ["recA"]
    assert protocol["validation_sequences"] == ["recA"]
    assert len(protocol["training_record_ids"]) + len(protocol["validation_record_ids"]) == 30
    assert {
        tuple(record_id) for record_id in protocol["training_record_ids"]
    }.isdisjoint(
        {tuple(record_id) for record_id in protocol["validation_record_ids"]}
    )
    assert len(protocol["validation_record_digest"]) == 64
    assert len(fingerprint) == 64

    checkpoint = {"temporal_protocol": protocol}
    validation_records, split = _records_for_checkpoint(
        tmp_path, checkpoint, split="validation", manifest=None
    )
    assert split == "train"
    assert {
        (record.sequence_id, record.frame_index) for record in validation_records
    } == {tuple(record_id) for record_id in protocol["validation_record_ids"]}


def test_prepare_datasets_can_freeze_stateless_record_protocol(tmp_path: Path) -> None:
    for sequence in ("recA", "recB"):
        _write_sequence(tmp_path, sequence, count=5)
    _, _, protocol, _ = _prepare_datasets(
        tmp_path,
        seed=17,
        output_size=(32, 32),
        validation_fraction=0.20,
        input_mode="timestamp-events",
        manifest=None,
        stateful_stream=False,
    )
    assert protocol["stateful_stream"] is False


def test_epoch_train_subset_changes_across_epochs(tmp_path: Path) -> None:
    for sequence in ("recA", "recB", "recC", "recD"):
        _write_sequence(tmp_path, sequence, count=8)
    train_pool, _, _, _ = _prepare_datasets(
        tmp_path,
        seed=17,
        output_size=(32, 32),
        validation_fraction=0.25,
        input_mode="timestamp-events",
        manifest=None,
    )
    epoch1 = _epoch_train_dataset(train_pool, train_samples=0.5, seed=17, epoch=1)
    epoch2 = _epoch_train_dataset(train_pool, train_samples=0.5, seed=17, epoch=2)
    epoch1_again = _epoch_train_dataset(train_pool, train_samples=0.5, seed=17, epoch=1)
    ids1 = [(record.sequence_id, record.frame_index) for record in epoch1.records]
    ids2 = [(record.sequence_id, record.frame_index) for record in epoch2.records]
    assert ids1 == [
        (record.sequence_id, record.frame_index) for record in epoch1_again.records
    ]
    assert ids1 != ids2
    expected_count = max(1, int(round(len(train_pool) * 0.5)))
    assert len(ids1) == expected_count
    assert all(
        current.frame_index == previous.frame_index + 1
        for previous, current in zip(epoch1.records, epoch1.records[1:])
        if previous.sequence_id == current.sequence_id
    )


def test_temporal_collate_preserves_one_record_per_batch_item() -> None:
    events_a = torch.zeros((6, 4, 5))
    events_b = events_a + 10.0
    mask = torch.zeros((4, 5), dtype=torch.long)
    sequence, masks = temporal_collate([(events_a, mask), (events_b, mask)])
    assert sequence.shape == (2, 6, 4, 5)
    assert masks.shape == (2, 4, 5)
    assert not torch.equal(sequence[0], sequence[1])


def test_sequential_chunks_preserve_chronological_raw_event_order() -> None:
    sequence = torch.arange(10).view(10, 1, 1, 1, 1)
    chunks = split_temporal_chunks(sequence, 2)
    assert [chunk.flatten().tolist() for chunk in chunks] == [
        [0, 1, 2, 3, 4],
        [5, 6, 7, 8, 9],
    ]
    assert split_temporal_chunks(sequence, 1)[0] is sequence


def test_sequential_chunks_reject_invalid_temporal_partitions() -> None:
    sequence = torch.zeros((10, 1, 2, 4, 5))
    with pytest.raises(ValueError, match="divide evenly"):
        split_temporal_chunks(sequence, 3)
    with pytest.raises(ValueError, match="raw-event"):
        split_temporal_chunks(torch.zeros((1, 6, 4, 5)), 2)


def test_class_weight_estimation_reads_masks_without_temporal_events(
    tmp_path: Path, monkeypatch
) -> None:
    _write_sequence(tmp_path, "recA", count=10)
    train_pool, _, _, _ = _prepare_datasets(
        tmp_path,
        seed=17,
        output_size=(32, 32),
        validation_fraction=0.20,
        input_mode="timestamp-events",
        manifest=None,
    )

    def unexpected_load(_record):
        raise AssertionError("class weights must not load temporal event tensors")

    monkeypatch.setattr(data_module, "_load_record_events", unexpected_load)
    weights = estimate_class_weights(train_pool)
    assert weights.shape == (6,)


def test_class_weight_estimation_uses_capped_median_frequency_weights() -> None:
    class ToyDataset:
        def __len__(self) -> int:
            return 1

        def target_mask(self, _index: int) -> torch.Tensor:
            return torch.tensor([0] * 100 + [1] * 50 + [2] * 20 + [3] * 10 + [4] * 5 + [5])

    weights = estimate_class_weights(ToyDataset())
    assert weights[0] < weights[1] < weights[2] < weights[3] < weights[4]
    assert weights[5] == 8.0


def test_architecture_suites_are_isolated() -> None:
    assert len(architecture_presets("top-ten")) == 10
    assert len(architecture_presets("top-five")) == 5
    assert len(architecture_presets("top-three")) == 3
    assert infer_model_suite("f01_base24_multiscale") == "top-five"
    assert infer_model_suite("v03_dw_dilated") == "top-ten"
    assert infer_model_suite("t02_dualpath_detail") == "top-three"


def test_loss_profiles_remain_explicit() -> None:
    for suite in ("top-ten", "top-five", "top-three"):
        assert loss_profile_for_suite(suite).cross_entropy == 0.5
    assert loss_profile_for_suite("final").cross_entropy == 1.0


def test_soft_dice_loss_reports_each_class() -> None:
    logits = torch.zeros((1, 6, 2, 2))
    target = torch.tensor([[[0, 1], [2, 3]]])
    losses = soft_dice_loss(logits, target, class_count=6)
    assert losses.shape == (6,)
    assert torch.all((losses >= 0.0) & (losses <= 1.0))


def test_training_dice_reduction_excludes_target_absent_classes() -> None:
    logits = torch.tensor(
        [[[[2.0, 2.0], [2.0, 2.0]], [[4.0, 4.0], [4.0, 4.0]]]]
    )
    target = torch.zeros((1, 2, 2), dtype=torch.long)
    outputs = {
        "segmentation_logits": logits,
        "segmentation_rate": torch.tensor(0.05),
        "enc1_rate": torch.tensor(0.05),
        "enc2_rate": torch.tensor(0.05),
        "enc3_rate": torch.tensor(0.05),
        "enc4_rate": torch.tensor(0.05),
        "decoder_rate": torch.tensor(0.05),
    }
    loss, dice_losses, _ = _training_objective(
        outputs,
        target,
        class_weights=torch.ones(2),
        class_count=2,
        loss_profile=LossProfile(cross_entropy=0.0, focal=0.0, dice=1.0),
        is_final_run=True,
        training_phase="joint",
    )
    assert dice_losses[1] > dice_losses[0]
    assert torch.allclose(loss, dice_losses[0])


def test_final_refinement_schedule_phases() -> None:
    schedule = (0.70, 0.90)
    assert refinement_phase_for_epoch(1, 10, schedule) == ("joint", True)
    assert refinement_phase_for_epoch(8, 10, schedule) == ("decoder_detail_refinement", False)
    assert refinement_phase_for_epoch(10, 10, schedule) == ("final_joint_low_lr", True)


def test_resume_cli_learning_rate_overrides_checkpoint_parameter_groups() -> None:
    parameter = torch.nn.Parameter(torch.ones(()))
    optimizer = torch.optim.AdamW([{"params": [parameter], "lr": 0.0015}])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80)
    checkpoint_optimizer = optimizer.state_dict()
    checkpoint_scheduler = scheduler.state_dict()

    resumed_parameter = torch.nn.Parameter(torch.ones(()))
    resumed_optimizer = torch.optim.AdamW([{"params": [resumed_parameter], "lr": 0.001}])
    resumed_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        resumed_optimizer, T_max=80
    )
    resumed_optimizer.load_state_dict(checkpoint_optimizer)
    resumed_scheduler.load_state_dict(checkpoint_scheduler)
    applied = apply_resume_learning_rate(
        resumed_optimizer,
        resumed_scheduler,
        learning_rate=0.001,
    )

    assert applied == [0.001]
    assert resumed_optimizer.param_groups[0]["lr"] == 0.001
    assert resumed_scheduler.base_lrs == [0.001]
