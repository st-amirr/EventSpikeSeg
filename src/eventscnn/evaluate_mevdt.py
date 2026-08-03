"""Held-out MEVDT evaluation for a floating-point baseline checkpoint."""

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from .config import BackboneConfig, EventBinningConfig, LIFConfig
from .datasets import discover_mevdt_frames, load_mevdt_window
from .heads import Proposal, connected_component_proposals
from .system import EventSCNNSystem
from .train_mevdt import box_to_feature_roi, objectness_target


@dataclass(frozen=True)
class MEVDTEvaluationResult:
    samples: int
    positive_samples: int
    negative_samples: int
    oracle_roi_classification_accuracy: float
    positive_objectness_mean_iou: float
    negative_objectness_empty_rate: float
    positive_proposal_mean_best_iou: float
    positive_proposal_recall_at_0_5: float
    negative_mean_proposal_count: float
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
    activity_threshold: float = 0.05,
) -> MEVDTEvaluationResult:
    """Measure binary classification with oracle ROIs and objectness-map overlap."""

    if max_samples <= 0:
        raise ValueError("max_samples must be positive")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    window_steps = int(checkpoint["window_steps"])
    lif = LIFConfig(f_inst_enabled=False, f_long_enabled=False)
    system = EventSCNNSystem(class_count=2, backbone_config=BackboneConfig(lif=lif))
    system.load_state_dict(checkpoint["model_state_dict"])
    system.eval()

    correct = 0
    positive = 0
    negative = 0
    positive_ious: list[float] = []
    proposal_best_ious: list[float] = []
    negative_empty = 0
    negative_proposals = 0
    config = EventBinningConfig(bin_duration_us=int(checkpoint["bin_duration_us"]))
    records = _balanced_records(root, max_samples)
    with torch.no_grad():
        for record in records:
            sample = load_mevdt_window(record, config=config, window_steps=window_steps)
            if sample.boxes:
                roi = box_to_feature_roi(max(sample.boxes, key=lambda box: box.area))
                class_id = 1
                positive += 1
            else:
                roi = torch.tensor([[0, 0, 30, 23]])
                class_id = 0
                negative += 1
            system.reset()
            outputs = system.trainable_outputs(sample.events.float(), roi)
            predicted_class = int(outputs["classification_logits"].argmax(dim=1).item())
            correct += int(predicted_class == class_id)

            activity = outputs["objectness_spikes"].mean(dim=0)
            predicted = activity >= activity_threshold
            target = objectness_target(sample.boxes, activity.shape[-2], activity.shape[-1]) > 0
            proposals = connected_component_proposals(
                activity[0, 0], threshold=activity_threshold, scale_x=2, scale_y=2
            )
            if sample.boxes:
                intersection = int((predicted & target).sum())
                union = int((predicted | target).sum())
                positive_ious.append(intersection / union if union else 1.0)
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
                negative_proposals += len(proposals)

    return MEVDTEvaluationResult(
        samples=len(records),
        positive_samples=positive,
        negative_samples=negative,
        oracle_roi_classification_accuracy=correct / len(records),
        positive_objectness_mean_iou=sum(positive_ious) / len(positive_ious),
        negative_objectness_empty_rate=negative_empty / negative,
        positive_proposal_mean_best_iou=sum(proposal_best_ious) / len(proposal_best_ious),
        positive_proposal_recall_at_0_5=sum(iou >= 0.5 for iou in proposal_best_ious)
        / len(proposal_best_ious),
        negative_mean_proposal_count=negative_proposals / negative,
        activity_threshold=activity_threshold,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--max-samples", type=int, default=64)
    parser.add_argument("--activity-threshold", type=float, default=0.05)
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
