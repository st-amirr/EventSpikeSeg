"""Standard detection/association metrics for chronological tracking sequences."""

from dataclasses import dataclass
from math import sqrt

import numpy as np
from scipy.optimize import linear_sum_assignment

from .tracking import Detection, intersection_over_union


@dataclass(frozen=True)
class IdentifiedDetection:
    track_id: str
    box: Detection


@dataclass(frozen=True)
class TrackingMetricResult:
    hota: float
    detection_accuracy: float
    association_accuracy: float
    mota: float
    idf1: float
    ground_truth_detections: int
    predicted_detections: int
    true_positives_at_0_5: int
    false_positives_at_0_5: int
    false_negatives_at_0_5: int
    identity_switches_at_0_5: int


TrackingFrame = tuple[tuple[IdentifiedDetection, ...], tuple[IdentifiedDetection, ...]]


def _similarity_matrix(
    ground_truth: tuple[IdentifiedDetection, ...],
    predictions: tuple[IdentifiedDetection, ...],
) -> np.ndarray:
    return np.asarray(
        [
            [intersection_over_union(target.box, prediction.box) for prediction in predictions]
            for target in ground_truth
        ],
        dtype=np.float64,
    ).reshape(len(ground_truth), len(predictions))


def _matched_pairs(similarity: np.ndarray, threshold: float) -> list[tuple[int, int]]:
    if not similarity.size:
        return []
    rows, columns = linear_sum_assignment(-similarity)
    return [
        (int(row), int(column))
        for row, column in zip(rows, columns)
        if similarity[row, column] >= threshold
    ]


def evaluate_tracking_frames(frames: list[TrackingFrame]) -> TrackingMetricResult:
    """Compute HOTA, CLEAR MOTA, and IDF1 from ordered frames.

    Track identifiers must already be namespaced by sequence so identities from separate
    recordings cannot be matched to one another.
    """

    gt_ids = sorted({item.track_id for ground_truth, _ in frames for item in ground_truth})
    pred_ids = sorted({item.track_id for _, predictions in frames for item in predictions})
    gt_index = {track_id: index for index, track_id in enumerate(gt_ids)}
    pred_index = {track_id: index for index, track_id in enumerate(pred_ids)}
    similarities = [
        _similarity_matrix(ground_truth, predictions)
        for ground_truth, predictions in frames
    ]
    gt_total = sum(len(ground_truth) for ground_truth, _ in frames)
    pred_total = sum(len(predictions) for _, predictions in frames)

    tp = fp = fn = identity_switches = 0
    previous_matches: dict[str, str] = {}
    identity_counts = np.zeros((len(gt_ids), len(pred_ids)), dtype=np.float64)
    for (ground_truth, predictions), similarity in zip(frames, similarities):
        matches = _matched_pairs(similarity, 0.5)
        tp += len(matches)
        fn += len(ground_truth) - len(matches)
        fp += len(predictions) - len(matches)
        for row, column in matches:
            target_id = ground_truth[row].track_id
            prediction_id = predictions[column].track_id
            if target_id in previous_matches and previous_matches[target_id] != prediction_id:
                identity_switches += 1
            previous_matches[target_id] = prediction_id
            identity_counts[gt_index[target_id], pred_index[prediction_id]] += 1

    mota = (
        1.0 - (fn + fp + identity_switches) / gt_total
        if gt_total
        else 0.0
    )
    if identity_counts.size:
        rows, columns = linear_sum_assignment(-identity_counts)
        identity_true_positives = int(identity_counts[rows, columns].sum())
    else:
        identity_true_positives = 0
    identity_false_negatives = gt_total - identity_true_positives
    identity_false_positives = pred_total - identity_true_positives
    idf1 = 2 * identity_true_positives / max(
        1,
        2 * identity_true_positives + identity_false_negatives + identity_false_positives,
    )

    hota_values: list[float] = []
    detection_accuracy_values: list[float] = []
    association_accuracy_values: list[float] = []
    if gt_ids and pred_ids:
        gt_counts = np.zeros((len(gt_ids), 1), dtype=np.float64)
        pred_counts = np.zeros((1, len(pred_ids)), dtype=np.float64)
        potential = np.zeros((len(gt_ids), len(pred_ids)), dtype=np.float64)
        for (ground_truth, predictions), similarity in zip(frames, similarities):
            rows = np.asarray([gt_index[item.track_id] for item in ground_truth], dtype=int)
            columns = np.asarray([pred_index[item.track_id] for item in predictions], dtype=int)
            if similarity.size:
                denominator = (
                    similarity.sum(axis=0)[None, :]
                    + similarity.sum(axis=1)[:, None]
                    - similarity
                )
                normalized = np.divide(
                    similarity,
                    denominator,
                    out=np.zeros_like(similarity),
                    where=denominator > np.finfo(float).eps,
                )
                potential[np.ix_(rows, columns)] += normalized
            gt_counts[rows] += 1
            pred_counts[0, columns] += 1
        alignment = np.divide(
            potential,
            gt_counts + pred_counts - potential,
            out=np.zeros_like(potential),
            where=(gt_counts + pred_counts - potential) > np.finfo(float).eps,
        )
        for threshold in np.arange(0.05, 1.0, 0.05):
            matches_by_identity = np.zeros_like(potential)
            threshold_tp = threshold_fp = threshold_fn = 0
            for (ground_truth, predictions), similarity in zip(frames, similarities):
                if not ground_truth:
                    threshold_fp += len(predictions)
                    continue
                if not predictions:
                    threshold_fn += len(ground_truth)
                    continue
                rows = np.asarray([gt_index[item.track_id] for item in ground_truth], dtype=int)
                columns = np.asarray([pred_index[item.track_id] for item in predictions], dtype=int)
                score = alignment[np.ix_(rows, columns)] * similarity
                match_rows, match_columns = linear_sum_assignment(-score)
                valid = similarity[match_rows, match_columns] >= threshold - np.finfo(float).eps
                match_rows, match_columns = match_rows[valid], match_columns[valid]
                threshold_tp += len(match_rows)
                threshold_fn += len(ground_truth) - len(match_rows)
                threshold_fp += len(predictions) - len(match_columns)
                matches_by_identity[rows[match_rows], columns[match_columns]] += 1
            association = np.divide(
                matches_by_identity,
                np.maximum(1.0, gt_counts + pred_counts - matches_by_identity),
            )
            association_accuracy = (
                float((matches_by_identity * association).sum()) / max(1, threshold_tp)
            )
            detection_accuracy = threshold_tp / max(
                1, threshold_tp + threshold_fn + threshold_fp
            )
            detection_accuracy_values.append(detection_accuracy)
            association_accuracy_values.append(association_accuracy)
            hota_values.append(sqrt(detection_accuracy * association_accuracy))
    else:
        hota_values = [0.0] * 19
        detection_accuracy_values = [0.0] * 19
        association_accuracy_values = [0.0] * 19

    return TrackingMetricResult(
        hota=float(np.mean(hota_values)),
        detection_accuracy=float(np.mean(detection_accuracy_values)),
        association_accuracy=float(np.mean(association_accuracy_values)),
        mota=mota,
        idf1=idf1,
        ground_truth_detections=gt_total,
        predicted_detections=pred_total,
        true_positives_at_0_5=tp,
        false_positives_at_0_5=fp,
        false_negatives_at_0_5=fn,
        identity_switches_at_0_5=identity_switches,
    )
