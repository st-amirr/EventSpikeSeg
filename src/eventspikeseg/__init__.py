"""Event-camera spiking semantic segmentation."""

from .data import DDD17_CLASS_NAMES, DEFAULT_DDD17_ROOT, DDD17Dataset, resolve_ddd17_root
from .model import EventSpikeSeg, EventSpikeSeg140k, build_model

__all__ = [
    "DEFAULT_DDD17_ROOT",
    "DDD17_CLASS_NAMES",
    "DDD17Dataset",
    "EventSpikeSeg",
    "EventSpikeSeg140k",
    "build_model",
    "resolve_ddd17_root",
]
