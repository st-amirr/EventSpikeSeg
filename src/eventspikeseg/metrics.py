"""Semantic-segmentation metrics for DDD17."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor


@dataclass(frozen=True)
class SegmentationMetrics:
    mean_iou: float
    pixel_accuracy: float
    per_class_iou: tuple[float, ...]
    valid_classes: int
    ground_truth_pixels: tuple[int, ...]
    predicted_pixels: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "mean_iou": self.mean_iou,
            "pixel_accuracy": self.pixel_accuracy,
            "per_class_iou": list(self.per_class_iou),
            "valid_classes": self.valid_classes,
            "ground_truth_pixels": list(self.ground_truth_pixels),
            "predicted_pixels": list(self.predicted_pixels),
        }


class ConfusionMatrix:
    def __init__(self, class_count: int, ignore_index: int = 255) -> None:
        self.class_count = class_count
        self.ignore_index = ignore_index
        self.matrix = torch.zeros((class_count, class_count), dtype=torch.int64)

    def update(self, prediction: Tensor, target: Tensor) -> None:
        prediction = prediction.detach().cpu().long().reshape(-1)
        target = target.detach().cpu().long().reshape(-1)
        valid = target != self.ignore_index
        valid &= (target >= 0) & (target < self.class_count)
        valid &= (prediction >= 0) & (prediction < self.class_count)
        encoded = target[valid] * self.class_count + prediction[valid]
        self.matrix += torch.bincount(
            encoded, minlength=self.class_count * self.class_count
        ).reshape(self.class_count, self.class_count)

    def compute(self) -> SegmentationMetrics:
        matrix = self.matrix.float()
        true_positive = matrix.diag()
        union = matrix.sum(dim=0) + matrix.sum(dim=1) - true_positive
        valid = union > 0
        iou = torch.full((self.class_count,), float("nan"))
        iou[valid] = true_positive[valid] / union[valid]
        total = matrix.sum()
        accuracy = float(true_positive.sum() / total) if total > 0 else 0.0
        mean_iou = float(iou[valid].mean()) if valid.any() else 0.0
        return SegmentationMetrics(
            mean_iou=mean_iou,
            pixel_accuracy=accuracy,
            per_class_iou=tuple(float(value) for value in iou),
            valid_classes=int(valid.sum()),
            ground_truth_pixels=tuple(int(value) for value in self.matrix.sum(dim=1)),
            predicted_pixels=tuple(int(value) for value in self.matrix.sum(dim=0)),
        )
