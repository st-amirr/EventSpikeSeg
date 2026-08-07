"""Canonical production model only.

The current canonical model is the measured round-one winner.  After the top-five
neuromorphic benchmark is reproduced and accepted, this file is the only file that
should be changed to install the new final architecture.
"""

from __future__ import annotations

from .model_components import EventSpikeSegBase, SegmentationArchitecture

FINAL_ARCHITECTURE = SegmentationArchitecture(
    name="v10_fpga_hybrid",
    context="multiscale",
    norm="affine",
    auxiliary_head=True,
    skip_kind="two",
    residual=True,
    adaptive_threshold=True,
)
FINAL_ARCHITECTURE_NAME = FINAL_ARCHITECTURE.name


class EventSpikeSeg(EventSpikeSegBase):
    """Canonical DDD17 semantic-segmentation SNN."""

    def __init__(self, *, class_count: int = 6, input_channels: int = 6) -> None:
        super().__init__(
            class_count=class_count,
            input_channels=input_channels,
            architecture=FINAL_ARCHITECTURE,
        )


def build_model(*, class_count: int = 6, input_channels: int = 6) -> EventSpikeSeg:
    return EventSpikeSeg(class_count=class_count, input_channels=input_channels)
