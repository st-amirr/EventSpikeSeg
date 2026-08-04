"""Held-out MEVDT evaluation for a trained pixel-attention checkpoint."""

import argparse
import json
from dataclasses import asdict, dataclass
from math import hypot
from pathlib import Path

import torch

from .config import BackboneConfig, EventBinningConfig, LIFConfig
from .datasets import discover_mevdt_frames, load_mevdt_window
from .heads import Proposal, connected_component_proposals
from .system import EventSCNNSystem
from .tracking import AttentionCentroidTracker, attention_observation
from .train_mevdt import (
    event_supported_attention_target,
)


@dataclass(frozen=True)
class MEVDTEvaluationResult:
    samples: int
    positive_samples: int
    negative_samples: int
    predicted_attention_classification_accuracy: float
    oracle_attention_classification_accuracy: float
    attention_precision: float
    attention_recall: float
    attention_dice: float
    attention_iou: float
    attention_centroid_detection_rate: float
    attention_centroid_mean_error_pixels: float
    tracked_centroid_mean_error_pixels: float
    tracked_center_precision_at_20: float
    negative_attention_empty_rate: float
    negative_attention_pixel_rate: float
    positive_proposal_mean_best_iou: float
    positive_proposal_recall_at_0_5: float
    activity_threshold: float


def _balanced_records(root: Path, max_samples: int):
    indexed = discover_mevdt_frames(root, split="test")
    positive = [record for record in indexed if record.label_path.stat().st_size]
    negative = [record for record in indexed if not record.label_path.stat().st_size]
    records = []
    for index in range(max(len(positive), len(negative))):
        if index < len(positive):
            records.append(positive[index])
        if index < len(negative):
            records.append(negative[index])
        if len(records) >= max_samples:
            return records[:max_samples]
    return records


def _proposal_iou(proposal: Proposal, box) -> float:
    x0 = max(float(proposal.x), box.x_min)
    y0 = max(float(proposal.y), box.y_min)
    x1 = min(float(proposal.x + proposal.width), box.x_max)
    y1 = min(float(proposal.y + proposal.height), box.y_max)
    intersection = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    union = proposal.width * proposal.height + box.area - intersection
    return intersection / union if union else 0.0


def evaluate_mevdt_checkpoint(
    root: Path,
    checkpoint_path: Path,
    *,
    max_samples: int = 64,
    activity_threshold: float = 0.04,
) -> MEVDTEvaluationResult:
    """Measure attention, predicted-attention classification, and centroid quality."""

    if max_samples <= 0:
        raise ValueError("max_samples must be positive")
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
    system = EventSCNNSystem(class_count=2, backbone_config=BackboneConfig(lif=lif))
    system.load_state_dict(checkpoint["model_state_dict"])
    system.eval()

    predicted_correct = 0
    oracle_correct = 0
    positive = 0
    negative = 0
    true_positive_pixels = 0
    false_positive_pixels = 0
    false_negative_pixels = 0
    negative_empty = 0
    negative_active_pixels = 0
    centroid_errors: list[float] = []
    tracked_centroid_errors: list[float] = []
    sequence_trackers: dict[tuple[str, str], AttentionCentroidTracker] = {}
    proposal_best_ious: list[float] = []
    config = EventBinningConfig(bin_duration_us=int(checkpoint["bin_duration_us"]))
    records = _balanced_records(root, max_samples)
    with torch.no_grad():
        for record in records:
            sample = load_mevdt_window(record, config=config, window_steps=window_steps)
            class_id = int(bool(sample.boxes))
            positive += class_id
            negative += 1 - class_id
            system.reset()
            outputs = system.trainable_outputs(sample.events.float())
            predicted_class = int(outputs["classification_scores"].argmax(dim=1).item())
            predicted_correct += int(predicted_class == class_id)

            activity = outputs["attention_spikes"].mean(dim=0)
            predicted = activity >= activity_threshold
            target = event_supported_attention_target(
                sample.events.float(),
                sample.boxes,
                activity.shape[-2],
                activity.shape[-1],
            ).bool()
            system.classification.reset()
            oracle_attention = target.float().unsqueeze(0).expand(
                outputs["conv3_spikes"].shape[0], -1, -1, -1, -1
            )
            oracle_spikes = system.classification.forward_attention(
                outputs["conv3_spikes"], oracle_attention
            )
            oracle_scores = oracle_spikes.sum(dim=0)
            oracle_correct += int(oracle_scores.argmax(dim=1).item() == class_id)
            true_positive_pixels += int((predicted & target).sum())
            false_positive_pixels += int((predicted & ~target).sum())
            false_negative_pixels += int((~predicted & target).sum())

            proposals = connected_component_proposals(
                activity[0, 0], threshold=activity_threshold, scale_x=2, scale_y=2
            )
            if sample.boxes:
                observation = attention_observation(
                    activity[0, 0], class_id=1, class_confidence=1.0, scale_x=2, scale_y=2
                )
                if observation is not None:
                    box = max(sample.boxes, key=lambda candidate: candidate.area)
                    target_x = (box.x_min + box.x_max) * 0.5
                    target_y = (box.y_min + box.y_max) * 0.5
                    centroid_errors.append(
                        hypot(observation.x - target_x, observation.y - target_y)
                    )
                    tracker = sequence_trackers.setdefault(
                        (record.scene, record.sequence), AttentionCentroidTracker()
                    )
                    tracked = tracker.update(observation)
                    if tracked is not None:
                        tracked_centroid_errors.append(
                            hypot(tracked.x - target_x, tracked.y - target_y)
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
    return MEVDTEvaluationResult(
        samples=len(records),
        positive_samples=positive,
        negative_samples=negative,
        predicted_attention_classification_accuracy=predicted_correct / len(records),
        oracle_attention_classification_accuracy=oracle_correct / len(records),
        attention_precision=true_positive_pixels / max(1, precision_denominator),
        attention_recall=true_positive_pixels / max(1, recall_denominator),
        attention_dice=2 * true_positive_pixels / max(1, dice_denominator),
        attention_iou=true_positive_pixels / max(1, union),
        attention_centroid_detection_rate=len(centroid_errors) / max(1, positive),
        attention_centroid_mean_error_pixels=sum(centroid_errors) / max(1, len(centroid_errors)),
        tracked_centroid_mean_error_pixels=sum(tracked_centroid_errors)
        / max(1, len(tracked_centroid_errors)),
        tracked_center_precision_at_20=sum(error <= 20.0 for error in tracked_centroid_errors)
        / max(1, len(tracked_centroid_errors)),
        negative_attention_empty_rate=negative_empty / max(1, negative),
        negative_attention_pixel_rate=negative_active_pixels
        / max(1, negative * activity.shape[-2] * activity.shape[-1]),
        positive_proposal_mean_best_iou=sum(proposal_best_ious)
        / max(1, len(proposal_best_ious)),
        positive_proposal_recall_at_0_5=sum(iou >= 0.5 for iou in proposal_best_ious)
        / max(1, len(proposal_best_ious)),
        activity_threshold=activity_threshold,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--max-samples", type=int, default=64)
    parser.add_argument("--activity-threshold", type=float, default=0.04)
    args = parser.parse_args()
    result = evaluate_mevdt_checkpoint(
        args.root,
        args.checkpoint,
        max_samples=args.max_samples,
        activity_threshold=args.activity_threshold,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
