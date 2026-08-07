"""Event-camera spiking semantic segmentation."""

from .data import DDD17_CLASS_NAMES, DEFAULT_DDD17_ROOT, DDD17Dataset, resolve_ddd17_root
from .model import FINAL_ARCHITECTURE_NAME, EventSpikeSeg, build_model

__all__ = [
    "DEFAULT_DDD17_ROOT",
    "DDD17_CLASS_NAMES",
    "DDD17Dataset",
    "FINAL_ARCHITECTURE_NAME",
    "EventSpikeSeg",
    "build_model",
    "resolve_ddd17_root",
]
