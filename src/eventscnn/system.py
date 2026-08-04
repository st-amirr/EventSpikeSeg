"""Integrated trainable outputs and deterministic decoded inference path."""

from dataclasses import replace
from typing import Optional

from torch import Tensor, nn

from .config import BackboneConfig
from .heads import ClassificationHead, PixelAttentionHead, connected_component_proposals
from .models import EventSCNNBackbone
from .tracking import (
    AttentionCentroidTracker,
    AttentionObservation,
    AttentionTrackState,
    Detection,
    SingleObjectTracker,
    TrackState,
    attention_observation,
)


class EventSCNNSystem(nn.Module):
    """Connect backbone, pixel attention, classification, and centroid tracking."""

    def __init__(
        self,
        *,
        class_count: int,
        backbone_config: Optional[BackboneConfig] = None,
    ) -> None:
        super().__init__()
        self.backbone = EventSCNNBackbone(backbone_config)
        self.attention = PixelAttentionHead(8, self.backbone.config.lif)
        class_lif = replace(
            self.backbone.config.lif,
            f_inst_enabled=False,
            f_long_enabled=False,
        )
        self.classification = ClassificationHead(32, class_count, class_lif)
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
