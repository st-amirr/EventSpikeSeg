"""Integrated trainable outputs and deterministic decoded inference path."""

from math import ceil, floor
from typing import Optional

import torch
from torch import Tensor, nn

from .config import BackboneConfig
from .heads import ClassificationHead, ObjectnessHead, connected_component_proposals
from .models import EventSCNNBackbone
from .tracking import Detection, SingleObjectTracker, TrackState


class EventSCNNSystem(nn.Module):
    """Connect backbone, objectness, ROI classification, and single-object tracking."""

    def __init__(
        self,
        *,
        class_count: int,
        backbone_config: Optional[BackboneConfig] = None,
    ) -> None:
        super().__init__()
        self.backbone = EventSCNNBackbone(backbone_config)
        self.objectness = ObjectnessHead(8, self.backbone.config.lif)
        self.classification = ClassificationHead(32, class_count)
        self.tracker = SingleObjectTracker()

    def reset(self, *, reset_tracker: bool = True) -> None:
        self.backbone.reset()
        self.objectness.reset()
        if reset_tracker:
            self.tracker.reset()

    def trainable_outputs(self, sequence: Tensor, feature_rois: Tensor) -> dict[str, Tensor]:
        """Return differentiable tensors; ROI coordinates refer to Conv3 feature space."""

        activations = self.backbone(sequence, return_all=True)
        objectness = self.objectness(activations[0])
        logits = self.classification(activations[2], feature_rois)
        return {
            "conv1_spikes": activations[0],
            "conv2_spikes": activations[1],
            "conv3_spikes": activations[2],
            "objectness_spikes": objectness,
            "classification_logits": logits,
        }

    def decode_single(
        self,
        outputs: dict[str, Tensor],
        *,
        activity_threshold: float = 1.0,
    ) -> tuple[list[Detection], Optional[TrackState]]:
        """Decode batch-size-one outputs into detections and one tracking update."""

        objectness = outputs["objectness_spikes"]
        logits = outputs["classification_logits"]
        if objectness.shape[1] != 1 or logits.shape[0] != 1:
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
        probabilities = torch.softmax(logits[0].detach(), dim=0)
        class_confidence, class_index = probabilities.max(dim=0)
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
        """Run proposal-driven ROI classification and tracking for batch size one."""

        if sequence.shape[1] != 1:
            raise ValueError("infer_single requires batch size one")
        activations = self.backbone(sequence, return_all=True)
        objectness = self.objectness(activations[0])
        activity = objectness[:, 0, 0].sum(dim=0)
        proposals = connected_component_proposals(
            activity,
            threshold=activity_threshold,
            scale_x=2,
            scale_y=2,
        )
        if not proposals:
            return [], self.tracker.update([])

        feature_height, feature_width = activations[2].shape[-2:]
        model_height, model_width = activity.shape[0] * 2, activity.shape[1] * 2
        feature_rois = []
        for proposal in proposals:
            x0 = floor(proposal.x * feature_width / model_width)
            y0 = floor(proposal.y * feature_height / model_height)
            x1 = ceil((proposal.x + proposal.width) * feature_width / model_width)
            y1 = ceil((proposal.y + proposal.height) * feature_height / model_height)
            feature_rois.append([x0, y0, max(1, x1 - x0), max(1, y1 - y0)])
        repeated_features = activations[2].expand(-1, len(proposals), -1, -1, -1)
        logits = self.classification(
            repeated_features,
            torch.tensor(feature_rois, device=sequence.device),
        )
        detections = []
        for proposal, proposal_logits in zip(proposals, logits):
            class_confidence, class_index = torch.softmax(proposal_logits.detach(), dim=0).max(0)
            detections.append(
                Detection(
                    float(proposal.x),
                    float(proposal.y),
                    float(proposal.width),
                    float(proposal.height),
                    proposal.confidence * float(class_confidence),
                    int(class_index),
                )
            )
        return detections, self.tracker.update(detections)
