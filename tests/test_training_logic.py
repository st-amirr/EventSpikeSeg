import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from PIL import Image

from eventspikeseg.data import temporal_collate
from eventspikeseg.evaluate import _records_for_checkpoint
from eventspikeseg.train import (
    LossProfile,
    TrainResult,
    _epoch_train_dataset,
    _merge_temporal_outputs,
    _prepare_datasets,
    _temporal_parts,
    _training_objective,
    architecture_presets,
    cap_learning_rates,
    checkpoint_mechanism_scale,
    dsec_colour_mask,
    dsec_event_count_image,
    final_mechanism_scale,
    fixed_validation_preview_indices,
    format_class_validation_report,
    infer_model_suite,
    loss_profile_for_suite,
    macro_class_cross_entropy,
    refinement_phase_for_epoch,
    restored_resume_learning_rates,
    same_class_neighbor_consistency_loss,
    save_dsec_validation_previews,
    scale_learning_rates,
    select_winner,
    set_neuron_dynamics_trainable,
    soft_dice_loss,
)


def test_validation_preview_indices_are_random_but_reproducible() -> None:
    first = fixed_validation_preview_indices(234, seed=17)
    second = fixed_validation_preview_indices(234, seed=17)
    assert first == second
    assert len(first) == 3
    assert len(set(first)) == 3
    assert first != fixed_validation_preview_indices(234, seed=18)
    assert fixed_validation_preview_indices(2, seed=17) == (0, 1)


def test_dsec_preview_colours_polarity_by_complete_window_count() -> None:
    counts = torch.zeros(2, 2, 3)
    counts[0, 0, 0] = 1
    counts[0, 0, 1] = 8
    counts[1, 1, 1] = 8
    counts[:, 1, 2] = 8
    image = dsec_event_count_image(counts)
    assert image.shape == (2, 3, 3)
    assert 0 < image[0, 0, 0] < image[0, 1, 0] == 255
    assert image[0, 1, 2] == 0
    assert image[1, 1].tolist() == [0, 0, 255]
    assert image[1, 2].tolist() == [255, 0, 255]


def test_save_dsec_preview_is_event_target_prediction_panel(tmp_path: Path) -> None:
    dataset = SimpleNamespace(
        class_count=11,
        records=[SimpleNamespace(sequence_id="zurich_city_02_a", frame_index=12)]
    )
    previews = {
        0: (
            torch.zeros(2, 4, 5),
            torch.zeros(4, 5, dtype=torch.long),
            torch.full((4, 5), 10, dtype=torch.long),
        )
    }
    paths = save_dsec_validation_previews(
        tmp_path,
        epoch=3,
        preview_indices=(0,),
        previews=previews,
        dataset=dataset,
    )
    assert paths == (
        tmp_path / "epoch_003_sample_01_zurich_city_02_a_000012.png",
    )
    with Image.open(paths[0]) as panel:
        pixels = np.asarray(panel)
    assert pixels.shape == (4, 15, 3)
    assert np.array_equal(pixels[:, 5:10], dsec_colour_mask(previews[0][1]))
    assert np.array_equal(pixels[:, 10:15], dsec_colour_mask(previews[0][2]))


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
    parts = _temporal_parts(sequence, None, 2)
    assert [events.flatten().tolist() for events, _, _ in parts] == [
        [0, 1, 2, 3, 4],
        [5, 6, 7, 8, 9],
    ]
    assert _temporal_parts(sequence, None, 1)[0][0] is sequence


def test_sequential_chunks_reject_invalid_temporal_partitions() -> None:
    sequence = torch.zeros((10, 1, 2, 4, 5))
    parts = _temporal_parts(sequence, None, 3)
    assert [events.shape[0] for events, _, _ in parts] == [4, 3, 3]
    with pytest.raises(ValueError, match="raw-event"):
        _temporal_parts(torch.zeros((2, 6, 4, 5)), None, 2)


def test_temporal_chunk_outputs_form_one_weighted_full_window_prediction() -> None:
    early_logits = torch.tensor([1.0], requires_grad=True)
    late_logits = torch.tensor([3.0], requires_grad=True)
    outputs = _merge_temporal_outputs(
        [
            {
                "segmentation_logits": early_logits,
                "segmentation_rate": torch.tensor(0.25),
                "segmentation_spikes": torch.ones((2, 1, 1, 1, 1)),
            },
            {
                "segmentation_logits": late_logits,
                "segmentation_rate": torch.tensor(0.75),
                "segmentation_spikes": torch.zeros((3, 1, 1, 1, 1)),
            },
        ],
        [2, 3],
    )
    assert torch.allclose(outputs["segmentation_logits"], torch.tensor([2.2]))
    assert torch.allclose(outputs["segmentation_rate"], torch.tensor(0.55))
    assert outputs["segmentation_spikes"].shape[0] == 5
    outputs["segmentation_logits"].sum().backward()
    assert torch.allclose(early_logits.grad, torch.tensor([0.4]))
    assert torch.allclose(late_logits.grad, torch.tensor([0.6]))


def test_stable_final_mechanism_reaches_and_holds_best_checkpoint_scale() -> None:
    assert final_mechanism_scale(8, 80) == 0.0
    assert final_mechanism_scale(12, 80) == pytest.approx(0.03125)
    assert final_mechanism_scale(16, 80) == pytest.approx(0.0625)
    assert final_mechanism_scale(80, 80) == pytest.approx(0.0625)
    assert checkpoint_mechanism_scale({"epoch": 18, "epochs": 80}) == pytest.approx(
        0.0625
    )
    assert checkpoint_mechanism_scale(
        {"epoch": 24, "epochs": 80, "mechanism_scale": 0.25}
    ) == pytest.approx(0.25)
    assert checkpoint_mechanism_scale(
        {"epoch": 24, "epochs": 80, "homeostasis_scale": 0.125}
    ) == pytest.approx(0.125)


def test_neuron_dynamics_can_freeze_without_freezing_convolution_weights() -> None:
    class ToyModel(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.ones(()))
            self.beta_logit = torch.nn.Parameter(torch.ones(2))
            self.threshold_adaptation_strength_logit = torch.nn.Parameter(torch.ones(3))

    model = ToyModel()
    assert set_neuron_dynamics_trainable(model, False) == 5
    assert model.weight.requires_grad
    assert not model.beta_logit.requires_grad
    assert not model.threshold_adaptation_strength_logit.requires_grad


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
    assert loss_profile_for_suite("final") == LossProfile(
        cross_entropy=0.5,
        pixel_cross_entropy=0.5,
        focal=0.0,
        dice=0.30,
        region_consistency=0.05,
        auxiliary_ce=0.10,
        auxiliary_focal=0.0,
        boundary=0.02,
    )


def test_soft_dice_loss_reports_each_class() -> None:
    logits = torch.zeros((1, 6, 2, 2))
    target = torch.tensor([[[0, 1], [2, 3]]])
    losses = soft_dice_loss(logits, target, class_count=6)
    assert losses.shape == (6,)
    assert torch.all((losses >= 0.0) & (losses <= 1.0))


def test_macro_class_ce_gives_present_classes_equal_weight() -> None:
    logits = torch.tensor(
        [[[[3.0, 3.0], [3.0, 3.0]], [[0.0, 0.0], [0.0, 0.0]]]]
    )
    target = torch.tensor([[[0, 0], [0, 1]]])
    pixel_nll = torch.nn.functional.cross_entropy(logits, target, reduction="none")
    expected = 0.5 * (pixel_nll[target == 0].mean() + pixel_nll[target == 1].mean())
    assert torch.allclose(macro_class_cross_entropy(logits, target, 2), expected)
    assert not torch.allclose(expected, pixel_nll.mean())


def test_region_consistency_penalizes_only_same_target_class_discontinuities() -> None:
    probabilities = torch.tensor(
        [[[[0.9, 0.1], [0.9, 0.1]], [[0.1, 0.9], [0.1, 0.9]]]]
    )
    uniform_target = torch.zeros((1, 2, 2), dtype=torch.long)
    split_target = torch.tensor([[[0, 1], [0, 1]]])
    uniform_loss = same_class_neighbor_consistency_loss(
        probabilities, uniform_target
    )
    boundary_aware_loss = same_class_neighbor_consistency_loss(
        probabilities, split_target
    )
    assert uniform_loss > 0
    assert torch.allclose(boundary_aware_loss, torch.tensor(0.0))


def test_final_objective_applies_region_consistency_weight() -> None:
    logits = torch.tensor(
        [[[[3.0, -3.0], [3.0, -3.0]], [[-3.0, 3.0], [-3.0, 3.0]]]]
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
    loss, _, _ = _training_objective(
        outputs,
        target,
        class_count=2,
        loss_profile=LossProfile(
            cross_entropy=0.0,
            pixel_cross_entropy=0.0,
            focal=0.0,
            dice=0.0,
            region_consistency=0.05,
            auxiliary_ce=0.0,
            auxiliary_focal=0.0,
        ),
        is_final_run=True,
        training_phase="joint",
    )
    expected = 0.05 * same_class_neighbor_consistency_loss(
        logits.softmax(dim=1), target
    )
    assert torch.allclose(loss, expected)


def test_historical_suite_objective_also_uses_macro_class_ce() -> None:
    logits = torch.tensor(
        [[[[3.0, 3.0], [3.0, 3.0]], [[0.0, 0.0], [0.0, 0.0]]]]
    )
    target = torch.tensor([[[0, 0], [0, 1]]])
    outputs = {
        "segmentation_logits": logits,
        "segmentation_rate": torch.tensor(0.05),
        "enc1_rate": torch.tensor(0.05),
        "enc2_rate": torch.tensor(0.05),
        "enc3_rate": torch.tensor(0.05),
        "decoder_rate": torch.tensor(0.05),
    }
    loss, _, _ = _training_objective(
        outputs,
        target,
        class_count=2,
        loss_profile=LossProfile(
            cross_entropy=1.0,
            focal=0.0,
            dice=0.0,
            auxiliary_ce=0.0,
            auxiliary_focal=0.0,
        ),
        is_final_run=False,
        training_phase="joint",
    )
    assert torch.allclose(loss, macro_class_cross_entropy(logits, target, 2))


def test_final_objective_keeps_ce_dice_activity_and_auxiliary_supervision() -> None:
    logits = torch.tensor(
        [[[[2.0, 2.0], [2.0, 2.0]], [[4.0, 4.0], [4.0, 4.0]]]]
    )
    target = torch.tensor([[[0, 1], [0, 1]]])
    outputs = {
        "segmentation_logits": logits,
        "segmentation_rate": torch.tensor(0.0),
        "enc1_rate": torch.tensor(0.0),
        "enc2_rate": torch.tensor(0.0),
        "enc3_rate": torch.tensor(0.0),
        "enc4_rate": torch.tensor(0.0),
        "decoder_rate": torch.tensor(0.0),
        "auxiliary_logits": torch.full_like(logits, 100.0),
        "deep_auxiliary_logits": torch.full_like(logits, -100.0),
    }
    loss, dice_losses, _ = _training_objective(
        outputs,
        target,
        class_count=2,
        loss_profile=LossProfile(
            cross_entropy=0.5,
            pixel_cross_entropy=0.5,
            focal=100.0,
            dice=0.30,
            auxiliary_ce=0.10,
            auxiliary_focal=100.0,
        ),
        is_final_run=True,
        training_phase="decoder_detail_refinement",
    )
    pixel_ce = torch.nn.functional.cross_entropy(logits, target)
    auxiliary_ce = torch.nn.functional.cross_entropy(outputs["auxiliary_logits"], target)
    deep_auxiliary_ce = torch.nn.functional.cross_entropy(
        outputs["deep_auxiliary_logits"], target
    )
    activity_regularizer = torch.tensor(0.0055)
    expected = (
        0.5 * macro_class_cross_entropy(logits, target, 2)
        + 0.5 * pixel_ce
        + 0.30 * dice_losses.mean()
        + 0.10 * auxiliary_ce
        + 0.05 * deep_auxiliary_ce
        + activity_regularizer
    )
    assert torch.allclose(loss, expected)


def test_present_class_dice_excludes_target_absent_classes() -> None:
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
        class_count=2,
        loss_profile=LossProfile(cross_entropy=0.0, focal=0.0, dice=1.0),
        is_final_run=True,
        training_phase="joint",
    )
    assert dice_losses[1] > dice_losses[0]
    assert torch.allclose(loss, dice_losses[0])


def test_final_refinement_schedule_phases() -> None:
    schedule = (0.30, 0.85)
    assert refinement_phase_for_epoch(1, 10, schedule) == ("joint", True)
    assert refinement_phase_for_epoch(4, 10, schedule) == (
        "decoder_detail_refinement",
        False,
    )
    assert refinement_phase_for_epoch(10, 10, schedule) == ("final_joint_low_lr", True)


def test_resume_preserves_checkpoint_learning_rate_and_scheduler_position() -> None:
    parameter = torch.nn.Parameter(torch.ones(()))
    optimizer = torch.optim.AdamW([{"params": [parameter], "lr": 0.0015}])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80)
    for _ in range(12):
        optimizer.step()
        scheduler.step()
    checkpoint_optimizer = optimizer.state_dict()
    checkpoint_scheduler = scheduler.state_dict()
    checkpoint_rate = optimizer.param_groups[0]["lr"]

    resumed_parameter = torch.nn.Parameter(torch.ones(()))
    resumed_optimizer = torch.optim.AdamW([{"params": [resumed_parameter], "lr": 0.001}])
    resumed_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        resumed_optimizer, T_max=80
    )
    resumed_optimizer.load_state_dict(checkpoint_optimizer)
    resumed_scheduler.load_state_dict(checkpoint_scheduler)
    restored = restored_resume_learning_rates(resumed_optimizer, resumed_scheduler)

    assert restored == [checkpoint_rate]
    assert resumed_optimizer.param_groups[0]["lr"] == checkpoint_rate
    assert resumed_scheduler.last_epoch == 12
    scaled = scale_learning_rates(resumed_optimizer, resumed_scheduler, 0.25)
    assert scaled == [checkpoint_rate * 0.25]
    assert resumed_scheduler.get_last_lr() == scaled
    resumed_optimizer.step()
    resumed_scheduler.step()
    assert resumed_optimizer.param_groups[0]["lr"] < checkpoint_rate * 0.25


def test_resume_lr_cap_is_proportional_and_idempotent() -> None:
    parameters = [torch.nn.Parameter(torch.ones(())) for _ in range(2)]
    optimizer = torch.optim.AdamW(
        [
            {"params": [parameters[0]], "lr": 0.0008},
            {"params": [parameters[1]], "lr": 0.0002},
        ]
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80)
    capped = cap_learning_rates(optimizer, scheduler, 0.0002)
    assert capped == pytest.approx([0.0002, 0.00005])
    assert scheduler.base_lrs == pytest.approx([0.0002, 0.00005])
    assert cap_learning_rates(optimizer, scheduler, 0.0002) == pytest.approx(capped)
    assert scheduler.base_lrs == pytest.approx([0.0002, 0.00005])


def test_class_validation_report_tracks_iou_and_prediction_share() -> None:
    report = format_class_validation_report(
        ("road", "person"),
        {
            "per_class_iou": [0.625, 0.0],
            "predicted_pixels": [75, 25],
        },
    )
    assert report == (
        "Validation classes | road: IoU=0.6250, pred=75.00% | "
        "person: IoU=0.0000, pred=25.00%"
    )
