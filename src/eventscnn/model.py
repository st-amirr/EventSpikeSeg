"""Complete EventSCNN neural model and compatibility inference interface.

This module is the single source of truth for the trainable SNN: hardware-compatible
LIF dynamics, convolutional backbone, attention and classification heads, and the
integrated EventSCNN system. Tracking algorithms remain in ``tracking.py`` because they
are deterministic post-processing rather than part of the neural model.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Optional

import torch
from spikingjelly.activation_based import surrogate
from torch import Tensor, nn

from .tracking import (
    AttentionCentroidTracker,
    AttentionObservation,
    AttentionTrackState,
    Detection,
    SingleObjectTracker,
    TrackState,
    attention_observation,
)



# ---------------------------------------------------------------------------
# Model and event configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EventBinningConfig:
    """Fixed-duration event binning configuration, using microsecond timestamps."""

    width: int = 240
    height: int = 180
    bin_duration_us: int = 1_000

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("event resolution must be positive")
        if self.bin_duration_us <= 0:
            raise ValueError("bin_duration_us must be positive")


@dataclass(frozen=True)
class LIFConfig:
    """Hardware-compatible LIF and competition/homeostasis parameters."""

    beta_shift: int = 4
    threshold: float = 1.0
    f_inst_enabled: bool = True
    competitor_decrement: float = 0.25
    f_long_enabled: bool = True
    adaptation_increment: float = 0.0625
    adaptation_decay: float = 1.0 / 32.0

    def __post_init__(self) -> None:
        if self.beta_shift < 1:
            raise ValueError("beta_shift must be at least one")
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")
        if self.competitor_decrement < 0:
            raise ValueError("competitor_decrement cannot be negative")
        if self.adaptation_increment < 0 or self.adaptation_decay < 0:
            raise ValueError("adaptation parameters cannot be negative")

    @property
    def beta(self) -> float:
        return 1.0 - 2.0 ** (-self.beta_shift)


@dataclass(frozen=True)
class LayerConfig:
    in_channels: int
    out_channels: int
    kernel_size: tuple[int, int]
    stride: tuple[int, int]
    padding: tuple[int, int]

    def __post_init__(self) -> None:
        if self.in_channels <= 0 or self.out_channels <= 0:
            raise ValueError("channel counts must be positive")
        if any(value <= 0 for value in self.kernel_size + self.stride):
            raise ValueError("kernel and stride dimensions must be positive")
        if any(value < 0 for value in self.padding):
            raise ValueError("padding cannot be negative")


def _default_layers() -> tuple[LayerConfig, ...]:
    return (
        LayerConfig(2, 32, (5, 5), (2, 2), (2, 2)),
        LayerConfig(32, 64, (3, 3), (2, 2), (1, 1)),
        LayerConfig(64, 128, (3, 3), (1, 1), (1, 1)),
    )


@dataclass(frozen=True)
class BackboneConfig:
    layers: tuple[LayerConfig, ...] = field(default_factory=_default_layers)
    lif: LIFConfig = field(default_factory=LIFConfig)

    def __post_init__(self) -> None:
        if len(self.layers) != 3:
            raise ValueError("the version-1 backbone requires exactly three layers")
        for previous, current in zip(self.layers, self.layers[1:]):
            if previous.out_channels != current.in_channels:
                raise ValueError("adjacent layer channel counts do not match")

class HardwareLIF(nn.Module):
    """Stateful LIF with top-1 competition and per-channel homeostasis.

    Input/current and membrane tensors use NCHW. Forward ordering is frozen as leak,
    current, threshold, competition, subtractive reset, spike, adaptation.
    """

    def __init__(self, channels: int, config: Optional[LIFConfig] = None) -> None:
        super().__init__()
        if channels <= 0:
            raise ValueError("channels must be positive")
        self.channels = channels
        self.config = config or LIFConfig()
        self.spike_function = surrogate.ATan()
        self.register_buffer("membrane", torch.empty(0), persistent=False)
        self.register_buffer("adaptation", torch.zeros(channels), persistent=False)

    def reset(self) -> None:
        self.membrane = torch.empty(0, device=self.adaptation.device)
        self.adaptation.zero_()

    def _ensure_state(self, current: Tensor) -> None:
        if self.membrane.shape != current.shape:
            self.membrane = torch.zeros_like(current)
        if self.adaptation.device != current.device or self.adaptation.dtype != current.dtype:
            self.adaptation = self.adaptation.to(device=current.device, dtype=current.dtype)

    def forward(self, current: Tensor) -> Tensor:
        if current.ndim != 4 or current.shape[1] != self.channels:
            raise ValueError(f"expected N,{self.channels},H,W current")
        self._ensure_state(current)
        leaked = self.membrane - self.membrane / float(1 << self.config.beta_shift)
        candidate = leaked + current
        effective = self.config.threshold + self.adaptation
        threshold = effective.view(1, -1, 1, 1)
        raw_spikes = self.spike_function(candidate - threshold)
        above = candidate >= threshold

        if self.config.f_inst_enabled:
            masked = candidate.masked_fill(~above, -torch.inf)
            winner_index = masked.argmax(dim=1, keepdim=True)
            gate = torch.zeros_like(above).scatter_(1, winner_index, True)
            gate &= above.any(dim=1, keepdim=True)
            emitted = raw_spikes * gate.to(raw_spikes.dtype)
        else:
            gate = above
            # The surrogate already has the exact hard-spike forward value. Avoid a
            # second detached threshold mask, which would erase subthreshold gradients.
            emitted = raw_spikes

        winner_reset = gate.to(candidate.dtype) * threshold
        loser_mask = above & ~gate
        loser_decrement = loser_mask.to(candidate.dtype) * self.config.competitor_decrement
        self.membrane = candidate - winner_reset - loser_decrement

        if self.config.f_long_enabled:
            decayed = torch.clamp(self.adaptation - self.config.adaptation_decay, min=0.0)
            # One feature-map activity event per channel and timestep. A spatial mean
            # makes sparse maps effectively zero and changes with resolution; an OR is
            # deterministic, batch-size independent, and maps to a hardware reduction.
            activity = emitted.detach().amax(dim=(0, 2, 3))
            self.adaptation = decayed + self.config.adaptation_increment * activity
        return emitted

    def state(self) -> tuple[Optional[Tensor], Tensor]:
        membrane = None if self.membrane.numel() == 0 else self.membrane
        return membrane, self.adaptation


class ConvLIFBlock(nn.Module):
    """Bias-free shared convolution followed by hardware-ordered LIF dynamics."""

    def __init__(self, layer: LayerConfig, lif: Optional[LIFConfig] = None) -> None:
        super().__init__()
        self.layer_config = layer
        self.conv = nn.Conv2d(
            layer.in_channels,
            layer.out_channels,
            layer.kernel_size,
            stride=layer.stride,
            padding=layer.padding,
            bias=False,
        )
        self.neuron = HardwareLIF(layer.out_channels, lif)

    def reset(self) -> None:
        self.neuron.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        if sequence.ndim != 5 or sequence.shape[2] != self.layer_config.in_channels:
            raise ValueError("expected TNCHW sequence with configured input channels")
        return torch.stack([self.neuron(self.conv(step.float())) for step in sequence])


class EventSCNNBackbone(nn.Module):
    """Canonical three-layer 2→8→16→32 spiking convolutional backbone."""

    def __init__(self, config: Optional[BackboneConfig] = None) -> None:
        super().__init__()
        config = config or BackboneConfig()
        self.config = config
        self.blocks = nn.ModuleList(
            [ConvLIFBlock(layer, config.lif) for layer in config.layers]
        )

    def reset(self) -> None:
        for block in self.blocks:
            block.reset()

    def forward(self, sequence: Tensor, *, return_all: bool = False):
        activations: list[Tensor] = []
        output = sequence
        for block in self.blocks:
            output = block(output)
            activations.append(output)
        return activations if return_all else output


def assert_hardware_compatible_convolutions(modules: Sequence[nn.Module]) -> None:
    """Reject convolution bias, which would require updates without input spikes."""

    for module in modules:
        if isinstance(module, nn.Conv2d) and module.bias is not None:
            raise ValueError("spiking backbone convolutions must use bias=False")


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
        current_scale_shift: int = 0,
    ) -> None:
        super().__init__()
        if channels <= 0 or class_count <= 0:
            raise ValueError("channels and class_count must be positive")
        if current_scale_shift < 0:
            raise ValueError("current_scale_shift cannot be negative")
        self.synapse = nn.Linear(channels, class_count, bias=False)
        self.neuron = HardwareLIF(class_count, lif)
        self.current_scale_shift = current_scale_shift

    def _synaptic_current(self, step: Tensor) -> Tensor:
        return self.synapse(step) / float(1 << self.current_scale_shift)

    def reset(self) -> None:
        self.neuron.reset()

    def forward_attention(self, features: Tensor, attention: Tensor) -> Tensor:
        """Emit TNK class spikes from attended feature-spike events."""

        counts = attention_gated_spike_counts(features, attention)
        emitted = []
        for step in counts:
            current = self._synaptic_current(step).unsqueeze(-1).unsqueeze(-1)
            emitted.append(self.neuron(current).squeeze(-1).squeeze(-1))
        return torch.stack(emitted)

    def forward_attention_trace(self, features: Tensor, attention: Tensor) -> dict[str, Tensor]:
        """Emit class spikes plus differentiable current and pre-reset membrane traces."""

        counts = attention_gated_spike_counts(features, attention)
        currents = []
        candidates = []
        emitted = []
        for step in counts:
            current = self._synaptic_current(step).unsqueeze(-1).unsqueeze(-1)
            membrane, _ = self.neuron.state()
            prior = torch.zeros_like(current) if membrane is None else membrane
            leaked = prior - prior / float(1 << self.neuron.config.beta_shift)
            candidates.append((leaked + current).squeeze(-1).squeeze(-1))
            currents.append(current.squeeze(-1).squeeze(-1))
            emitted.append(self.neuron(current).squeeze(-1).squeeze(-1))
        return {
            "currents": torch.stack(currents),
            "candidate_membranes": torch.stack(candidates),
            "spikes": torch.stack(emitted),
        }


class EventSCNNSystem(nn.Module):
    """Connect backbone, pixel attention, classification, and centroid tracking."""

    def __init__(
        self,
        *,
        class_count: int,
        backbone_config: Optional[BackboneConfig] = None,
        classification_current_scale_shift: int = 0,
    ) -> None:
        super().__init__()
        self.backbone = EventSCNNBackbone(backbone_config)
        attention_channels = self.backbone.config.layers[0].out_channels
        classification_channels = self.backbone.config.layers[-1].out_channels
        self.attention = PixelAttentionHead(attention_channels, self.backbone.config.lif)
        class_lif = replace(
            self.backbone.config.lif,
            f_inst_enabled=False,
            f_long_enabled=False,
        )
        self.classification = ClassificationHead(
            classification_channels,
            class_count,
            class_lif,
            current_scale_shift=classification_current_scale_shift,
        )
        self.tracker = SingleObjectTracker()
        self.attention_tracker = AttentionCentroidTracker()

    @property
    def objectness(self) -> PixelAttentionHead:
        """Compatibility name for older proposal tests and checkpoints."""

        return self.attention

    def reset(self, *, reset_tracker: bool = True) -> None:
        self.backbone.reset()
        self.attention.reset()
        self.classification.reset()
        if reset_tracker:
            self.tracker.reset()
            self.attention_tracker.reset()

    def trainable_outputs(self, sequence: Tensor) -> dict[str, Tensor]:
        """Return differentiable spike outputs and class spike-count scores."""

        activations = self.backbone(sequence, return_all=True)
        attention = self.attention(activations[0])
        classification_attention = attention.detach() if self.training else attention
        class_spikes = self.classification.forward_attention(
            activations[2], classification_attention
        )
        return {
            "conv1_spikes": activations[0],
            "conv2_spikes": activations[1],
            "conv3_spikes": activations[2],
            "attention_spikes": attention,
            "objectness_spikes": attention,
            "classification_spikes": class_spikes,
            "classification_scores": class_spikes.sum(dim=0),
        }

    def decode_attention_single(
        self, outputs: dict[str, Tensor]
    ) -> tuple[Optional[AttentionObservation], Optional[AttentionTrackState]]:
        """Decode predicted pixels into a centroid observation and tracking state."""

        attention = outputs["attention_spikes"]
        scores = outputs["classification_scores"]
        if attention.shape[1] != 1 or scores.shape[0] != 1:
            raise ValueError("decode_attention_single requires batch size one")
        winning_count, class_index = scores[0].detach().max(0)
        total_count = scores[0].detach().sum()
        confidence = float(winning_count / total_count.clamp_min(1.0))
        if float(total_count) == 0.0:
            confidence = 1.0
        observation = attention_observation(
            attention[:, 0, 0].sum(dim=0),
            class_id=int(class_index),
            class_confidence=confidence,
            scale_x=2.0,
            scale_y=2.0,
        )
        return observation, self.attention_tracker.update(observation)

    def infer_attention_single(
        self, sequence: Tensor
    ) -> tuple[Optional[AttentionObservation], Optional[AttentionTrackState]]:
        """Run the primary box-free attention/classification/tracking path."""

        if sequence.shape[1] != 1:
            raise ValueError("infer_attention_single requires batch size one")
        return self.decode_attention_single(self.trainable_outputs(sequence))

    def decode_single(
        self,
        outputs: dict[str, Tensor],
        *,
        activity_threshold: float = 1.0,
    ) -> tuple[list[Detection], Optional[TrackState]]:
        """Decode batch-size-one outputs into detections and one tracking update."""

        objectness = outputs["objectness_spikes"]
        scores = outputs["classification_scores"]
        if objectness.shape[1] != 1 or scores.shape[0] != 1:
            raise ValueError("decode_single requires batch size one")
        activity = objectness[:, 0, 0].sum(dim=0)
        proposals = connected_component_proposals(
            activity,
            threshold=activity_threshold,
            scale_x=2,
            scale_y=2,
        )
        if not proposals:
            return [], self.tracker.update([])
        winning_count, class_index = scores[0].detach().max(dim=0)
        total_count = scores[0].detach().sum().clamp_min(1.0)
        class_confidence = winning_count / total_count
        detections = [
            Detection(
                float(proposal.x),
                float(proposal.y),
                float(proposal.width),
                float(proposal.height),
                proposal.confidence * float(class_confidence),
                int(class_index),
            )
            for proposal in proposals
        ]
        return detections, self.tracker.update(detections)

    def infer_single(
        self,
        sequence: Tensor,
        *,
        activity_threshold: float = 1.0,
    ) -> tuple[list[Detection], Optional[TrackState]]:
        """Run box-free spike-attention classification/tracking for batch size one."""

        if sequence.shape[1] != 1:
            raise ValueError("infer_single requires batch size one")
        return self.decode_single(
            self.trainable_outputs(sequence), activity_threshold=activity_threshold
        )
