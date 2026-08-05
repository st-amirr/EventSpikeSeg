"""Chronological MEVDT validation/test evaluation for a trained attention checkpoint."""

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from math import hypot
from pathlib import Path

import torch

from .config import BackboneConfig, EventBinningConfig, LIFConfig
from .datasets import (
    MEVDTBox,
    MEVDTFrameRecord,
    chronological_mevdt_records,
    discover_mevdt_frames,
    load_mevdt_tracking_sequence,
    load_mevdt_window,
)
from .model import Proposal, connected_component_proposals
from .model import EventSCNNSystem
from .tracking import (
    AttentionCentroidTracker,
    Detection,
    attention_observation,
    intersection_over_union,
)
from .tracking_metrics import (
    IdentifiedDetection,
    TrackingFrame,
    evaluate_tracking_frames,
)
from .train_mevdt import event_supported_attention_target


@dataclass(frozen=True)
class MEVDTEvaluationResult:
    evaluation_split: str
    sequences: int
    samples: int
    complete_sequences: bool
    positive_samples: int
    negative_samples: int
    predicted_attention_classification_accuracy: float
    classification_precision: float
    classification_recall: float
    classification_f1: float
    oracle_attention_classification_accuracy: float
    attention_precision: float
    attention_recall: float
    attention_dice: float
    attention_iou: float
    attention_centroid_detection_rate: float
    attention_centroid_mean_error_pixels: float
    tracking_success_auc: float
    tracked_centroid_mean_error_pixels: float
    tracked_center_precision_at_20: float
    hota: float
    hota_detection_accuracy: float
    hota_association_accuracy: float
    mota: float
    idf1: float
    tracking_ground_truth_detections: int
    tracking_predicted_detections: int
    tracking_true_positives_at_0_5: int
    tracking_false_positives_at_0_5: int
    tracking_false_negatives_at_0_5: int
    tracking_identity_switches_at_0_5: int
    negative_attention_empty_rate: float
    negative_attention_pixel_rate: float
    positive_proposal_mean_best_iou: float
    positive_proposal_recall_at_0_5: float
    activity_threshold: float
    box_spread_scale_x: float
    box_spread_scale_y: float


CORE_BENCHMARK_METRICS = (
    "classification_f1",
    "hota",
    "tracking_success_auc",
)


def require_nonzero_core_metrics(result: MEVDTEvaluationResult) -> None:
    """Fail the full benchmark when classification or tracking has collapsed to zero."""

    failures = [name for name in CORE_BENCHMARK_METRICS if float(getattr(result, name)) <= 0.0]
    if failures:
        joined = ", ".join(failures)
        raise RuntimeError(
            f"benchmark regression: zero core metrics ({joined}); return to the active bug-fix loop"
        )


def select_mevdt_evaluation_records(
    root: Path,
    checkpoint: dict,
    *,
    split: str,
    max_sequences: int = 0,
    max_samples: int = 0,
    sequence_key: str | None = None,
) -> list[MEVDTFrameRecord]:
    """Select complete chronological validation or official-test sequences."""

    if split in {"validation", "calibration"}:
        sequence_field = (
            "validation_sequences" if split == "validation" else "training_sequences"
        )
        allowed = set(checkpoint.get(sequence_field, []))
        if not allowed:
            raise ValueError(f"checkpoint does not freeze a {split} sequence partition")
        indexed = discover_mevdt_frames(root, split="train")
        records = [
            record for record in indexed if f"{record.scene}/{record.sequence}" in allowed
        ]
    elif split == "test":
        records = discover_mevdt_frames(root, split="test")
    else:
        raise ValueError("evaluation split must be 'calibration', 'validation', or 'test'")
    if sequence_key is not None:
        records = [
            record
            for record in records
            if f"{record.scene}/{record.sequence}" == sequence_key
        ]
    sequence_keys = sorted({(record.scene, record.sequence) for record in records})
    if max_sequences < 0 or max_samples < 0:
        raise ValueError("evaluation limits cannot be negative")
    if max_sequences:
        allowed_keys = set(sequence_keys[:max_sequences])
        records = [
            record for record in records if (record.scene, record.sequence) in allowed_keys
        ]
    records = chronological_mevdt_records(records)
    if max_samples:
        records = records[:max_samples]
    if not records:
        raise ValueError(f"MEVDT {split} evaluation contains no records")
    return records


def _proposal_iou(proposal: Proposal, box: MEVDTBox) -> float:
    x0 = max(float(proposal.x), box.x_min)
    y0 = max(float(proposal.y), box.y_min)
    x1 = min(float(proposal.x + proposal.width), box.x_max)
    y1 = min(float(proposal.y + proposal.height), box.y_max)
    intersection = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    union = proposal.width * proposal.height + box.area - intersection
    return intersection / union if union else 0.0


def _detection_from_attention_track(
    track, *, spread_scale_x: float = 4.0, spread_scale_y: float = 4.0
) -> Detection:
    width = min(240.0, max(2.0, spread_scale_x * track.spread_x))
    height = min(180.0, max(2.0, spread_scale_y * track.spread_y))
    x = min(240.0 - width, max(0.0, track.x - width / 2.0))
    y = min(180.0 - height, max(0.0, track.y - height / 2.0))
    return Detection(x, y, width, height, track.confidence, track.class_id)


def _detection_from_box(box: MEVDTBox) -> Detection:
    return Detection(
        box.x_min,
        box.y_min,
        box.x_max - box.x_min,
        box.y_max - box.y_min,
        1.0,
        box.class_id,
    )


def _center_error(left: Detection, right: Detection) -> float:
    left_x, left_y = left.x + left.width / 2.0, left.y + left.height / 2.0
    right_x, right_y = right.x + right.width / 2.0, right.y + right.height / 2.0
    return hypot(left_x - right_x, left_y - right_y)


def _detection_iou(left: Detection, right: Detection) -> float:
    return intersection_over_union(left, right)


def evaluate_mevdt_checkpoint(
    root: Path,
    checkpoint_path: Path,
    *,
    split: str = "validation",
    max_sequences: int = 0,
    max_samples: int = 0,
    sequence_key: str | None = None,
    activity_threshold: float = 0.04,
    box_spread_scale_x: float = 4.0,
    box_spread_scale_y: float = 4.0,
) -> MEVDTEvaluationResult:
    """Measure chronological classification, attention, SOT, and MOT quality."""

    root = root.expanduser().resolve()
    if box_spread_scale_x <= 0.0 or box_spread_scale_y <= 0.0:
        raise ValueError("box spread scales must be positive")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if checkpoint.get("architecture") != "fully_spiking_attention_v1":
        raise ValueError("checkpoint is not compatible with the fully spiking model")
    window_steps = int(checkpoint["window_steps"])
    lif = LIFConfig(
        threshold=float(checkpoint.get("lif_threshold", 1.0)),
        f_inst_enabled=bool(checkpoint.get("f_inst_enabled", False)),
        f_long_enabled=bool(checkpoint.get("f_long_enabled", False)),
        adaptation_increment=float(checkpoint.get("adaptation_increment", 0.0625)),
        adaptation_decay=float(checkpoint.get("adaptation_decay", 1.0 / 32.0)),
    )
    system = EventSCNNSystem(
        class_count=2,
        backbone_config=BackboneConfig(lif=lif),
        classification_current_scale_shift=int(
            checkpoint.get("classification_current_scale_shift", 0)
        ),
    )
    system.load_state_dict(checkpoint["model_state_dict"])
    system.eval()
    records = select_mevdt_evaluation_records(
        root,
        checkpoint,
        split=split,
        max_sequences=max_sequences,
        max_samples=max_samples,
        sequence_key=sequence_key,
    )
    sequence_keys = sorted({(record.scene, record.sequence) for record in records})
    source_split = "train" if split in {"validation", "calibration"} else "test"
    tracking_by_sequence = {
        key: load_mevdt_tracking_sequence(
            root, split=source_split, scene=key[0], sequence=key[1]
        )
        for key in sequence_keys
    }
    selected_timestamps = {
        key: {record.timestamp_ns for record in records if (record.scene, record.sequence) == key}
        for key in sequence_keys
    }
    target_track_ids: dict[tuple[str, str], str] = {}
    for key, annotations in tracking_by_sequence.items():
        counts = Counter(
            item.track_id
            for timestamp, items in annotations.items()
            if timestamp in selected_timestamps[key]
            for item in items
        )
        if counts:
            target_track_ids[key] = min(counts, key=lambda track_id: (-counts[track_id], track_id))

    predicted_correct = oracle_correct = 0
    class_tp = class_fp = class_fn = 0
    positive = negative = 0
    true_positive_pixels = false_positive_pixels = false_negative_pixels = 0
    negative_empty = negative_active_pixels = 0
    centroid_errors: list[float] = []
    proposal_best_ious: list[float] = []
    sot_ious: list[float] = []
    sot_center_errors: list[float] = []
    tracking_frames: list[TrackingFrame] = []
    sequence_trackers: dict[tuple[str, str], AttentionCentroidTracker] = {}
    sequence_generation: dict[tuple[str, str], int] = {}
    config = EventBinningConfig(bin_duration_us=int(checkpoint["bin_duration_us"]))
    activity_height = activity_width = 0

    with torch.no_grad():
        for record in records:
            key = (record.scene, record.sequence)
            sample = load_mevdt_window(record, config=config, window_steps=window_steps)
            class_id = int(bool(sample.boxes))
            positive += class_id
            negative += 1 - class_id
            system.reset()
            sequence = sample.events.float()
            outputs = system.trainable_outputs(sequence)
            predicted_class = int(outputs["classification_scores"].argmax(dim=1).item())
            predicted_correct += int(predicted_class == class_id)
            class_tp += int(predicted_class == 1 and class_id == 1)
            class_fp += int(predicted_class == 1 and class_id == 0)
            class_fn += int(predicted_class == 0 and class_id == 1)

            activity = outputs["attention_spikes"].mean(dim=0)
            activity_height, activity_width = activity.shape[-2:]
            predicted = activity >= activity_threshold
            target = event_supported_attention_target(
                sequence, sample.boxes, activity_height, activity_width
            ).bool()
            system.classification.reset()
            oracle_attention = target.float().unsqueeze(0).expand(
                outputs["conv3_spikes"].shape[0], -1, -1, -1, -1
            )
            oracle_scores = system.classification.forward_attention(
                outputs["conv3_spikes"], oracle_attention
            ).sum(dim=0)
            oracle_correct += int(oracle_scores.argmax(dim=1).item() == class_id)
            true_positive_pixels += int((predicted & target).sum())
            false_positive_pixels += int((predicted & ~target).sum())
            false_negative_pixels += int((~predicted & target).sum())

            proposals = connected_component_proposals(
                activity[0, 0], threshold=activity_threshold, scale_x=2, scale_y=2
            )
            observation = None
            if predicted_class == 1 and predicted.any():
                observation = attention_observation(
                    activity[0, 0] * predicted[0, 0],
                    class_id=1,
                    class_confidence=1.0,
                    scale_x=2,
                    scale_y=2,
                )
            tracker = sequence_trackers.setdefault(key, AttentionCentroidTracker())
            was_empty = tracker.state is None
            tracked = tracker.update(observation)
            if was_empty and tracked is not None:
                sequence_generation[key] = sequence_generation.get(key, -1) + 1
            predicted_identified: tuple[IdentifiedDetection, ...] = ()
            predicted_box = None
            if tracked is not None:
                predicted_box = _detection_from_attention_track(
                    tracked,
                    spread_scale_x=box_spread_scale_x,
                    spread_scale_y=box_spread_scale_y,
                )
                prediction_id = f"{key[0]}/{key[1]}/pred-{sequence_generation[key]}"
                predicted_identified = (IdentifiedDetection(prediction_id, predicted_box),)

            official_annotations = tracking_by_sequence[key].get(record.timestamp_ns, ())
            ground_truth_identified = tuple(
                IdentifiedDetection(
                    f"{key[0]}/{key[1]}/gt-{item.track_id}",
                    _detection_from_box(item.box),
                )
                for item in official_annotations
            )
            tracking_frames.append((ground_truth_identified, predicted_identified))

            target_id = target_track_ids.get(key)
            target_items = [item for item in official_annotations if item.track_id == target_id]
            if target_items:
                target_box = _detection_from_box(target_items[0].box)
                if predicted_box is None:
                    sot_ious.append(0.0)
                    sot_center_errors.append(float("inf"))
                else:
                    sot_ious.append(_detection_iou(predicted_box, target_box))
                    sot_center_errors.append(_center_error(predicted_box, target_box))

            if sample.boxes:
                if observation is not None:
                    largest = max(sample.boxes, key=lambda candidate: candidate.area)
                    centroid_errors.append(
                        hypot(
                            observation.x - (largest.x_min + largest.x_max) * 0.5,
                            observation.y - (largest.y_min + largest.y_max) * 0.5,
                        )
                    )
                proposal_best_ious.append(
                    max(
                        (
                            _proposal_iou(proposal, box)
                            for proposal in proposals
                            for box in sample.boxes
                        ),
                        default=0.0,
                    )
                )
            else:
                negative_empty += int(not predicted.any())
                negative_active_pixels += int(predicted.sum())

    precision_denominator = true_positive_pixels + false_positive_pixels
    recall_denominator = true_positive_pixels + false_negative_pixels
    dice_denominator = 2 * true_positive_pixels + false_positive_pixels + false_negative_pixels
    union = true_positive_pixels + false_positive_pixels + false_negative_pixels
    classification_precision = class_tp / max(1, class_tp + class_fp)
    classification_recall = class_tp / max(1, class_tp + class_fn)
    classification_f1 = 2 * class_tp / max(1, 2 * class_tp + class_fp + class_fn)
    tracking = evaluate_tracking_frames(tracking_frames)
    finite_center_errors = [error for error in sot_center_errors if error != float("inf")]
    return MEVDTEvaluationResult(
        evaluation_split=split,
        sequences=len(sequence_keys),
        samples=len(records),
        complete_sequences=max_samples == 0,
        positive_samples=positive,
        negative_samples=negative,
        predicted_attention_classification_accuracy=predicted_correct / len(records),
        classification_precision=classification_precision,
        classification_recall=classification_recall,
        classification_f1=classification_f1,
        oracle_attention_classification_accuracy=oracle_correct / len(records),
        attention_precision=true_positive_pixels / max(1, precision_denominator),
        attention_recall=true_positive_pixels / max(1, recall_denominator),
        attention_dice=2 * true_positive_pixels / max(1, dice_denominator),
        attention_iou=true_positive_pixels / max(1, union),
        attention_centroid_detection_rate=len(centroid_errors) / max(1, positive),
        attention_centroid_mean_error_pixels=sum(centroid_errors) / max(1, len(centroid_errors)),
        tracking_success_auc=sum(sot_ious) / max(1, len(sot_ious)),
        tracked_centroid_mean_error_pixels=sum(finite_center_errors)
        / max(1, len(finite_center_errors)),
        tracked_center_precision_at_20=sum(error <= 20.0 for error in sot_center_errors)
        / max(1, len(sot_center_errors)),
        hota=tracking.hota,
        hota_detection_accuracy=tracking.detection_accuracy,
        hota_association_accuracy=tracking.association_accuracy,
        mota=tracking.mota,
        idf1=tracking.idf1,
        tracking_ground_truth_detections=tracking.ground_truth_detections,
        tracking_predicted_detections=tracking.predicted_detections,
        tracking_true_positives_at_0_5=tracking.true_positives_at_0_5,
        tracking_false_positives_at_0_5=tracking.false_positives_at_0_5,
        tracking_false_negatives_at_0_5=tracking.false_negatives_at_0_5,
        tracking_identity_switches_at_0_5=tracking.identity_switches_at_0_5,
        negative_attention_empty_rate=negative_empty / max(1, negative),
        negative_attention_pixel_rate=negative_active_pixels
        / max(1, negative * activity_height * activity_width),
        positive_proposal_mean_best_iou=sum(proposal_best_ious)
        / max(1, len(proposal_best_ious)),
        positive_proposal_recall_at_0_5=sum(iou >= 0.5 for iou in proposal_best_ious)
        / max(1, len(proposal_best_ious)),
        activity_threshold=activity_threshold,
        box_spread_scale_x=box_spread_scale_x,
        box_spread_scale_y=box_spread_scale_y,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("calibration", "validation", "test"), default="validation"
    )
    parser.add_argument("--max-sequences", type=int, default=0)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--sequence", dest="sequence_key")
    parser.add_argument("--activity-threshold", type=float, default=0.04)
    parser.add_argument("--box-spread-scale-x", type=float, default=4.0)
    parser.add_argument("--box-spread-scale-y", type=float, default=4.0)
    parser.add_argument("--require-nonzero-core-metrics", action="store_true")
    args = parser.parse_args()
    result = evaluate_mevdt_checkpoint(
        args.root,
        args.checkpoint,
        split=args.split,
        max_sequences=args.max_sequences,
        max_samples=args.max_samples,
        sequence_key=args.sequence_key,
        activity_threshold=args.activity_threshold,
        box_spread_scale_x=args.box_spread_scale_x,
        box_spread_scale_y=args.box_spread_scale_y,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    if args.require_nonzero_core_metrics:
        require_nonzero_core_metrics(result)


if __name__ == "__main__":
    main()
