"""Event-camera spiking semantic segmentation."""

from .data import (
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    DEFAULT_DSEC_ROOT,
    DSEC_CLASS_NAMES,
    DDD17TimestampEventDataset,
    DSECRawEventDataset,
    build_temporal_dataset,
    resolve_ddd17_root,
    resolve_dsec_root,
)
from .model import EventSpikeSeg140k, EventSpikeSegXL, build_model

DDD17Dataset = DDD17TimestampEventDataset

__all__ = [
    "DEFAULT_DDD17_ROOT",
    "DEFAULT_DSEC_ROOT",
    "DDD17_CLASS_NAMES",
    "DDD17Dataset",
    "DDD17TimestampEventDataset",
    "DSEC_CLASS_NAMES",
    "DSECRawEventDataset",
    "EventSpikeSeg140k",
    "EventSpikeSegXL",
    "build_model",
    "build_temporal_dataset",
    "resolve_ddd17_root",
    "resolve_dsec_root",
]
