"""Deterministic single-object alpha-beta tracking reference."""

from dataclasses import dataclass, replace
from math import hypot
from typing import Optional

import torch
from torch import Tensor


@dataclass(frozen=True)
class Detection:
    x: float
    y: float
    width: float
    height: float
    confidence: float
    class_id: int


@dataclass(frozen=True)
class TrackState(Detection):
    vx: float = 0.0
    vy: float = 0.0
    missed: int = 0


@dataclass(frozen=True)
class AttentionObservation:
    """Centroid and spread measured directly from attended pixels."""

    x: float
    y: float
    spread_x: float
    spread_y: float
    confidence: float
    class_id: int


@dataclass(frozen=True)
class AttentionTrackState(AttentionObservation):
    vx: float = 0.0
    vy: float = 0.0
    missed: int = 0


def attention_observation(
    activity: Tensor,
    *,
    class_id: int,
    class_confidence: float,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> Optional[AttentionObservation]:
    """Convert one non-negative attention map to centroid/spread statistics."""

    if activity.ndim != 2 or (activity < 0).any():
        raise ValueError("activity must be a non-negative 2-D map")
    total = activity.sum()
    if float(total) <= 0.0:
        return None
    height, width = activity.shape
    xs = (torch.arange(width, device=activity.device, dtype=activity.dtype) + 0.5) * scale_x
    ys = (torch.arange(height, device=activity.device, dtype=activity.dtype) + 0.5) * scale_y
    x = (activity * xs.view(1, -1)).sum() / total
    y = (activity * ys.view(-1, 1)).sum() / total
    variance_x = (activity * (xs.view(1, -1) - x).square()).sum() / total
    variance_y = (activity * (ys.view(-1, 1) - y).square()).sum() / total
    density = total / float(height * width)
    return AttentionObservation(
        x=float(x),
        y=float(y),
        spread_x=float(torch.sqrt(variance_x)),
        spread_y=float(torch.sqrt(variance_y)),
        confidence=float(density) * class_confidence,
        class_id=class_id,
    )


class AttentionCentroidTracker:
    """Single-target alpha-beta tracker over attention centroids, without box ROIs."""

    def __init__(
        self,
        *,
        alpha: float = 0.8,
        beta: float = 0.2,
        max_distance: float = 30.0,
        max_missed: int = 3,
    ) -> None:
        if not (0.0 <= alpha <= 1.0 and 0.0 <= beta <= 1.0):
            raise ValueError("alpha and beta must be in [0,1]")
        self.alpha = alpha
        self.beta = beta
        self.max_distance = max_distance
        self.max_missed = max_missed
        self.state: Optional[AttentionTrackState] = None

    def reset(self) -> None:
        self.state = None

    def update(
        self, observation: Optional[AttentionObservation]
    ) -> Optional[AttentionTrackState]:
        if self.state is None:
            if observation is None:
                return None
            self.state = AttentionTrackState(**observation.__dict__)
            return self.state
        predicted_x = self.state.x + self.state.vx
        predicted_y = self.state.y + self.state.vy
        if observation is None or observation.class_id != self.state.class_id:
            missed = self.state.missed + 1
            if missed > self.max_missed:
                self.state = None
            else:
                self.state = replace(
                    self.state, x=predicted_x, y=predicted_y, missed=missed
                )
            return self.state
        innovation_x = observation.x - predicted_x
        innovation_y = observation.y - predicted_y
        if hypot(innovation_x, innovation_y) > self.max_distance:
            return self.update(None)
        self.state = AttentionTrackState(
            x=predicted_x + self.alpha * innovation_x,
            y=predicted_y + self.alpha * innovation_y,
            spread_x=self.state.spread_x
            + self.alpha * (observation.spread_x - self.state.spread_x),
            spread_y=self.state.spread_y
            + self.alpha * (observation.spread_y - self.state.spread_y),
            vx=self.state.vx + self.beta * innovation_x,
            vy=self.state.vy + self.beta * innovation_y,
            confidence=observation.confidence,
            class_id=observation.class_id,
            missed=0,
        )
        return self.state


def _center(box: Detection) -> tuple[float, float]:
    return box.x + box.width / 2.0, box.y + box.height / 2.0


def intersection_over_union(left: Detection, right: Detection) -> float:
    x0, y0 = max(left.x, right.x), max(left.y, right.y)
    x1 = min(left.x + left.width, right.x + right.width)
    y1 = min(left.y + left.height, right.y + right.height)
    intersection = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    union = left.width * left.height + right.width * right.height - intersection
    return intersection / union if union > 0 else 0.0


class SingleObjectTracker:
    """One-track alpha-beta filter with deterministic distance/IoU/class gating."""

    def __init__(
        self,
        *,
        alpha: float = 0.8,
        beta: float = 0.2,
        max_center_distance: float = 30.0,
        min_iou: float = 0.0,
        max_missed: int = 3,
    ) -> None:
        if not (0.0 <= alpha <= 1.0 and 0.0 <= beta <= 1.0):
            raise ValueError("alpha and beta must be in [0,1]")
        self.alpha = alpha
        self.beta = beta
        self.max_center_distance = max_center_distance
        self.min_iou = min_iou
        self.max_missed = max_missed
        self.state: Optional[TrackState] = None

    def reset(self) -> None:
        self.state = None

    def _predict(self) -> Optional[TrackState]:
        if self.state is None:
            return None
        return replace(
            self.state,
            x=self.state.x + self.state.vx,
            y=self.state.y + self.state.vy,
            missed=self.state.missed + 1,
        )

    def update(self, detections: list[Detection]) -> Optional[TrackState]:
        if self.state is None:
            if not detections:
                return None
            selected = max(detections, key=lambda item: item.confidence)
            self.state = TrackState(**selected.__dict__)
            return self.state

        predicted = self._predict()
        assert predicted is not None
        px, py = _center(predicted)
        compatible = []
        for detection in detections:
            dx, dy = _center(detection)
            distance = hypot(dx - px, dy - py)
            if (
                detection.class_id == predicted.class_id
                and distance <= self.max_center_distance
                and intersection_over_union(predicted, detection) >= self.min_iou
            ):
                compatible.append((distance, -detection.confidence, detection))
        if not compatible:
            self.state = None if predicted.missed > self.max_missed else predicted
            return self.state

        measurement = min(compatible, key=lambda item: (item[0], item[1]))[2]
        mx, my = _center(measurement)
        innovation_x, innovation_y = mx - px, my - py
        center_x = px + self.alpha * innovation_x
        center_y = py + self.alpha * innovation_y
        width = predicted.width + self.alpha * (measurement.width - predicted.width)
        height = predicted.height + self.alpha * (measurement.height - predicted.height)
        self.state = TrackState(
            x=center_x - width / 2.0,
            y=center_y - height / 2.0,
            width=width,
            height=height,
            vx=predicted.vx + self.beta * innovation_x,
            vy=predicted.vy + self.beta * innovation_y,
            confidence=measurement.confidence,
            class_id=measurement.class_id,
            missed=0,
        )
        return self.state
