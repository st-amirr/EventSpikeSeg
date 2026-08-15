"""Event-camera spiking semantic segmentation."""

from .data import (
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    DDD17TimestampEventDataset,
    build_temporal_dataset,
    resolve_ddd17_root,
)
from .model import EventSpikeSeg, EventSpikeSeg140k, build_model

DDD17Dataset = DDD17TimestampEventDataset

__all__ = [
    "DEFAULT_DDD17_ROOT",
    "DDD17_CLASS_NAMES",
    "DDD17Dataset",
    "DDD17TimestampEventDataset",
    "EventSpikeSeg",
    "EventSpikeSeg140k",
    "build_model",
    "build_temporal_dataset",
    "resolve_ddd17_root",
]
