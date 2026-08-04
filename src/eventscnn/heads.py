"""Hardware-mappable proposal and classification heads."""

from dataclasses import dataclass
from typing import Optional

import torch
from torch import Tensor, nn

from .config import LIFConfig
from .dynamics import HardwareLIF


@dataclass(frozen=True)
class Proposal:
    x: int
    y: int
    width: int
    height: int
    confidence: float


class ObjectnessHead(nn.Module):
    """Bias-free 1×1 spiking objectness head."""

    def __init__(self, in_channels: int, lif: Optional[LIFConfig] = None) -> None:
        super().__init__()
        self.conv = nn.Conv2d(in_channels, 1, kernel_size=1, bias=False)
        self.neuron = HardwareLIF(1, lif)

    def reset(self) -> None:
        self.neuron.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        if sequence.ndim != 5:
            raise ValueError("expected TNCHW features")
        return torch.stack([self.neuron(self.conv(step)) for step in sequence])


class PixelAttentionHead(nn.Module):
    """Bias-free local spiking attention at the Conv1 spatial resolution."""

    def __init__(self, in_channels: int, lif: Optional[LIFConfig] = None) -> None:
        super().__init__()
        self.conv = nn.Conv2d(in_channels, 1, kernel_size=3, padding=1, bias=False)
        self.neuron = HardwareLIF(1, lif)

    def reset(self) -> None:
        self.neuron.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        if sequence.ndim != 5:
            raise ValueError("expected TNCHW features")
        return torch.stack([self.neuron(self.conv(step)) for step in sequence])


def connected_component_proposals(
    activity: Tensor,
    *,
    threshold: float = 1.0,
    scale_x: int = 1,
    scale_y: int = 1,
) -> list[Proposal]:
    """Extract deterministic 4-connected boxes from one 2-D activity map."""

    if activity.ndim != 2:
        raise ValueError("activity must be a 2-D map")
    if threshold <= 0 or scale_x <= 0 or scale_y <= 0:
        raise ValueError("threshold and scales must be positive")
    active = activity.detach().cpu() >= threshold
    height, width = active.shape
    visited = torch.zeros_like(active)
    proposals: list[Proposal] = []
    for y in range(height):
        for x in range(width):
            if not active[y, x] or visited[y, x]:
                continue
            stack = [(x, y)]
            visited[y, x] = True
            points: list[tuple[int, int]] = []
            score = 0.0
            while stack:
                px, py = stack.pop()
                points.append((px, py))
                score += float(activity[py, px])
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    in_bounds = 0 <= nx < width and 0 <= ny < height
                    if in_bounds and active[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((nx, ny))
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            proposals.append(
                Proposal(
                    min_x * scale_x,
                    min_y * scale_y,
                    (max_x - min_x + 1) * scale_x,
                    (max_y - min_y + 1) * scale_y,
                    score / len(points),
                )
            )
    return proposals


def roi_spike_count_pool(features: Tensor, rois: Tensor) -> Tensor:
    """Sum TNCHW spike features inside one clipped ``x,y,w,h`` ROI per batch."""

    if features.ndim != 5:
        raise ValueError("features must be TNCHW")
    if rois.shape != (features.shape[1], 4):
        raise ValueError("rois must have shape [N,4]")
    _, batch, channels, height, width = features.shape
    pooled = torch.zeros((batch, channels), device=features.device, dtype=features.dtype)
    for index in range(batch):
        x, y, roi_width, roi_height = (int(value) for value in rois[index].tolist())
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(width, x + roi_width), min(height, y + roi_height)
        if x1 > x0 and y1 > y0:
            pooled[index] = features[:, index, :, y0:y1, x0:x1].sum(dim=(0, 2, 3))
    return pooled


def attention_weighted_spike_pool(features: Tensor, attention: Tensor) -> Tensor:
    """Pool TNCHW features using predicted TN1HW binary or rate attention.

    Attention may have a higher integer-multiple spatial resolution than the features;
    it is reduced with max/OR pooling, which has a direct FPGA mapping.
    """

    if features.ndim != 5 or attention.ndim != 5:
        raise ValueError("features and attention must be TNCHW")
    if features.shape[:2] != attention.shape[:2] or attention.shape[2] != 1:
        raise ValueError("attention must have shape [T,N,1,H,W] matching T and N")
    feature_height, feature_width = features.shape[-2:]
    attention_height, attention_width = attention.shape[-2:]
    if attention_height % feature_height or attention_width % feature_width:
        raise ValueError("attention resolution must be an integer multiple of features")
    ratio_y = attention_height // feature_height
    ratio_x = attention_width // feature_width
    if ratio_y > 1 or ratio_x > 1:
        time, batch = attention.shape[:2]
        attention = torch.nn.functional.max_pool2d(
            attention.flatten(0, 1),
            kernel_size=(ratio_y, ratio_x),
            stride=(ratio_y, ratio_x),
        ).view(time, batch, 1, feature_height, feature_width)
    numerator = (features * attention).sum(dim=(0, 3, 4))
    denominator = attention.sum(dim=(0, 3, 4)).clamp_min(1.0)
    return numerator / denominator


def attention_gated_spike_counts(features: Tensor, attention: Tensor) -> Tensor:
    """Return per-timestep TNC counts of feature spikes selected by attention spikes."""

    if features.ndim != 5 or attention.ndim != 5:
        raise ValueError("features and attention must be TNCHW")
    if features.shape[:2] != attention.shape[:2] or attention.shape[2] != 1:
        raise ValueError("attention must have shape [T,N,1,H,W] matching T and N")
    feature_height, feature_width = features.shape[-2:]
    attention_height, attention_width = attention.shape[-2:]
    if attention_height % feature_height or attention_width % feature_width:
        raise ValueError("attention resolution must be an integer multiple of features")
    ratio_y = attention_height // feature_height
    ratio_x = attention_width // feature_width
    if ratio_y > 1 or ratio_x > 1:
        time, batch = attention.shape[:2]
        attention = torch.nn.functional.max_pool2d(
            attention.flatten(0, 1),
            kernel_size=(ratio_y, ratio_x),
            stride=(ratio_y, ratio_x),
        ).view(time, batch, 1, feature_height, feature_width)
    return (features * attention).sum(dim=(3, 4))


class ClassificationHead(nn.Module):
    """Bias-free class synapses followed by stateful class LIF neurons."""

    def __init__(
        self,
        channels: int,
        class_count: int,
        lif: Optional[LIFConfig] = None,
    ) -> None:
        super().__init__()
        if channels <= 0 or class_count <= 0:
            raise ValueError("channels and class_count must be positive")
        self.synapse = nn.Linear(channels, class_count, bias=False)
        self.neuron = HardwareLIF(class_count, lif)

    def reset(self) -> None:
        self.neuron.reset()

    def forward_attention(self, features: Tensor, attention: Tensor) -> Tensor:
        """Emit TNK class spikes from attended feature-spike events."""

        counts = attention_gated_spike_counts(features, attention)
        emitted = []
        for step in counts:
            current = self.synapse(step).unsqueeze(-1).unsqueeze(-1)
            emitted.append(self.neuron(current).squeeze(-1).squeeze(-1))
        return torch.stack(emitted)
