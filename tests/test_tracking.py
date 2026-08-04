import torch

from eventscnn.tracking import (
    AttentionCentroidTracker,
    AttentionObservation,
    Detection,
    SingleObjectTracker,
    attention_observation,
    intersection_over_union,
)


def _detection(x: float, confidence: float = 0.9, class_id: int = 1) -> Detection:
    return Detection(x, 10.0, 4.0, 4.0, confidence, class_id)


def test_deterministic_constant_velocity_tracking_and_prediction() -> None:
    tracker = SingleObjectTracker(alpha=1.0, beta=0.5, max_center_distance=10.0)
    first = tracker.update([_detection(0.0)])
    second = tracker.update([_detection(2.0)])
    assert first is not None and second is not None
    assert second.x == 2.0
    assert second.vx == 1.0
    predicted = tracker.update([])
    assert predicted is not None
    assert predicted.x == 3.0
    assert predicted.missed == 1


def test_rejects_wrong_class_and_loses_track_after_limit() -> None:
    tracker = SingleObjectTracker(max_missed=1)
    tracker.update([_detection(0.0)])
    state = tracker.update([_detection(0.0, class_id=2)])
    assert state is not None and state.missed == 1
    assert tracker.update([]) is None


def test_acquisition_uses_highest_confidence_and_iou() -> None:
    tracker = SingleObjectTracker()
    state = tracker.update([_detection(2.0, 0.5), _detection(5.0, 0.8)])
    assert state is not None and state.x == 5.0
    assert intersection_over_union(_detection(0), _detection(0)) == 1.0
    assert intersection_over_union(_detection(0), _detection(20)) == 0.0


def test_attention_pixels_convert_to_scaled_centroid() -> None:
    activity = torch.zeros((2, 2))
    activity[0, 1] = 2.0
    observation = attention_observation(
        activity, class_id=1, class_confidence=0.75, scale_x=2.0, scale_y=2.0
    )
    assert observation is not None
    assert (observation.x, observation.y) == (3.0, 1.0)
    assert (observation.spread_x, observation.spread_y) == (0.0, 0.0)


def test_attention_centroid_tracking_is_deterministic() -> None:
    tracker = AttentionCentroidTracker(alpha=1.0, beta=0.5, max_distance=10.0)
    first = AttentionObservation(1.0, 2.0, 0.0, 0.0, 0.8, 1)
    second = AttentionObservation(3.0, 2.0, 0.0, 0.0, 0.9, 1)
    tracker.update(first)
    state = tracker.update(second)
    assert state is not None and state.x == 3.0 and state.vx == 1.0
    predicted = tracker.update(None)
    assert predicted is not None and predicted.x == 4.0 and predicted.missed == 1
