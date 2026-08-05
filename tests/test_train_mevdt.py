from types import SimpleNamespace

import torch

from eventscnn.data import MEVDTBox
from eventscnn.train import (
    attention_centroid_loss,
    balanced_training_records,
    box_to_feature_roi,
    dice_loss,
    event_activity_target,
    event_supported_attention_target,
    objectness_target,
    window_spike_presence,
)


def test_mevdt_box_projects_to_conv3_roi() -> None:
    box = MEVDTBox(1, 0.0, 0.0, 240.0, 180.0)
    assert torch.equal(box_to_feature_roi(box), torch.tensor([[0, 0, 60, 45]]))


def test_mevdt_objectness_target_uses_xyxy_extent() -> None:
    box = MEVDTBox(1, 20.0, 40.0, 60.0, 80.0)
    target = objectness_target((box,), 90, 120)
    assert target.shape == (1, 1, 90, 120)
    assert target[0, 0, 20:40, 10:30].all()
    assert target.sum() == 400


def test_attention_target_keeps_only_events_inside_box() -> None:
    events = torch.zeros((2, 1, 2, 180, 240))
    events[0, 0, 0, 40, 20] = 1
    events[0, 0, 1, 120, 180] = 1
    box = MEVDTBox(1, 10.0, 30.0, 40.0, 60.0)
    target = event_supported_attention_target(events, (box,), 90, 120, dilation=0)
    assert target.shape == (1, 1, 90, 120)
    assert target[0, 0, 20, 10] == 1
    assert target.sum() == 1


def test_attention_centroid_loss_prefers_box_center() -> None:
    box = MEVDTBox(1, 100.0, 80.0, 140.0, 100.0)
    centered = torch.zeros((1, 1, 90, 120))
    centered[0, 0, 45, 60] = 1
    far = torch.zeros_like(centered)
    far[0, 0, 5, 5] = 1
    assert attention_centroid_loss(centered, (box,)) < attention_centroid_loss(far, (box,))


def test_window_presence_matches_at_least_one_spike_not_mean_rate() -> None:
    spikes = torch.zeros((50, 1, 1, 2, 2), requires_grad=True)
    spikes.data[17, 0, 0, 1, 0] = 1
    presence = window_spike_presence(spikes)
    assert presence[0, 0, 1, 0] == 1
    assert presence.sum() == 1
    presence.sum().backward()
    assert spikes.grad is not None


def test_event_activity_target_and_dice_preserve_sparse_support() -> None:
    events = torch.zeros((2, 1, 2, 180, 240))
    events[0, 0, 1, 40, 20] = 1
    target = event_activity_target(events, 90, 120)
    assert target.shape == (1, 1, 90, 120)
    assert target[0, 0, 20, 10] == 1
    assert target.sum() == 9
    assert dice_loss(target, target) == 0
    assert dice_loss(torch.zeros_like(target), target) > 0.99


def test_balanced_training_selection_is_seeded_and_not_dataset_ordered(tmp_path) -> None:
    records = []
    for index in range(6):
        positive = tmp_path / f"positive-{index}.txt"
        negative = tmp_path / f"negative-{index}.txt"
        positive.write_text("1 0 0 1 1\n", encoding="utf-8")
        negative.write_text("", encoding="utf-8")
        records.extend(
            [SimpleNamespace(label_path=positive), SimpleNamespace(label_path=negative)]
        )
    first = balanced_training_records(records, 6, seed=17)
    second = balanced_training_records(records, 6, seed=17)
    assert [record.label_path for record in first] == [record.label_path for record in second]
    assert sum(bool(record.label_path.stat().st_size) for record in first) == 3
    assert first != records[:6]
