import torch
from eventspikeseg.data import discover_ddd17_records
from eventspikeseg.train import (
    TrainResult,
    _prepare_datasets,
    architecture_presets,
    infer_model_suite,
    refinement_phase_for_epoch,
    select_winner,
    temporal_collate,
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


def test_winner_prefers_smaller_model_within_half_point() -> None:
    winner = select_winner(
        [
            _result("large", 0.500, 100_000, 0.05),
            _result("small", 0.497, 50_000, 0.06),
            _result("weak", 0.480, 10_000, 0.01),
        ]
    )
    assert winner.architecture == "small"


def test_prepare_datasets_uses_train_and_test(tmp_path) -> None:
    import numpy as np
    from PIL import Image

    for split, count in (("train", 4), ("test", 3)):
        events_dir = tmp_path / "events" / split
        labels_dir = tmp_path / "labels" / split
        events_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)
        for index in range(count):
            np.save(events_dir / f"{split}_{index}.npy", np.zeros((24, 32, 6), dtype=np.float32))
            Image.fromarray(np.zeros((24, 32), dtype=np.uint8)).save(
                labels_dir / f"{split}_{index}.png"
            )

    train_dataset, held_out = _prepare_datasets(
        tmp_path, seed=17, train_samples=0, validation_samples=0, output_size=(32, 32)
    )
    assert len(train_dataset) == 4
    assert len(held_out) == 3
    assert all(record.split == "test" for record in held_out.records)
    assert len(discover_ddd17_records(tmp_path, "train")) == 4


def test_architecture_suites_are_isolated() -> None:
    assert len(architecture_presets("top-ten")) == 10
    assert len(architecture_presets("top-five")) == 5
    assert infer_model_suite("f01_base24_multiscale") == "top-five"
    assert infer_model_suite("f03_early5x5_multiscale") == "top-five"
    assert infer_model_suite("v03_dw_dilated") == "top-ten"


def test_final_refinement_schedule_phases() -> None:
    schedule = (0.70, 0.90)
    assert refinement_phase_for_epoch(1, 10, schedule) == ("joint", True)
    assert refinement_phase_for_epoch(8, 10, schedule) == ("decoder_detail_refinement", False)
    assert refinement_phase_for_epoch(9, 10, schedule) == ("decoder_detail_refinement", False)
    assert refinement_phase_for_epoch(10, 10, schedule) == ("final_joint_low_lr", True)
    assert refinement_phase_for_epoch(8, 10, None) == ("joint", True)


def test_temporal_collate_reuses_static_event_storage() -> None:
    events_a = torch.arange(6 * 4 * 5, dtype=torch.float32).reshape(1, 6, 4, 5)
    events_b = events_a + 1.0
    mask = torch.zeros((4, 5), dtype=torch.long)
    sequence, masks = temporal_collate(
        [(events_a, mask), (events_b, mask)], time_steps=15
    )
    assert sequence.shape == (15, 2, 6, 4, 5)
    assert masks.shape == (2, 4, 5)
    # Expanded direct encoding should share the same temporal storage rather
    # than materializing 15 physical input copies.
    assert sequence.stride(0) == 0
    assert torch.equal(sequence[0], sequence[-1])
