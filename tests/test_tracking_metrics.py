from eventscnn.tracking import Detection
from eventscnn.metrics import IdentifiedDetection, evaluate_tracking_frames


def _identified(track_id: str, x: float = 0.0) -> IdentifiedDetection:
    return IdentifiedDetection(track_id, Detection(x, 0.0, 10.0, 10.0, 1.0, 1))


def test_tracking_metrics_are_perfect_for_identical_track() -> None:
    frames = [((_identified("gt"),), (_identified("pred"),)) for _ in range(3)]
    result = evaluate_tracking_frames(frames)
    assert result.hota == 1.0
    assert result.detection_accuracy == 1.0
    assert result.association_accuracy == 1.0
    assert result.mota == 1.0
    assert result.idf1 == 1.0


def test_tracking_metrics_count_misses_false_positives_and_identity_switch() -> None:
    frames = [
        ((_identified("gt"),), (_identified("pred-a"),)),
        ((_identified("gt"),), ()),
        ((_identified("gt"),), (_identified("pred-b"),)),
        ((), (_identified("pred-b"),)),
    ]
    result = evaluate_tracking_frames(frames)
    assert result.true_positives_at_0_5 == 2
    assert result.false_negatives_at_0_5 == 1
    assert result.false_positives_at_0_5 == 1
    assert result.identity_switches_at_0_5 == 1
    assert result.mota == 0.0
    assert result.idf1 == 1 / 3


def test_empty_tracking_sequence_does_not_report_perfect_mota() -> None:
    result = evaluate_tracking_frames([((), ())])
    assert result.hota == 0.0
    assert result.detection_accuracy == 0.0
    assert result.association_accuracy == 0.0
    assert result.mota == 0.0
    assert result.idf1 == 0.0
