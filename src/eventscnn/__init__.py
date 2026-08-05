"""Event-camera spiking semantic segmentation."""

from .data import DDD17_CLASS_NAMES, DEFAULT_DDD17_ROOT, DDD17Dataset, resolve_ddd17_root
from .model import ARCHITECTURE_PRESETS, DEFAULT_ARCHITECTURE, EventSpikeSeg, build_model

__all__ = [
    "ARCHITECTURE_PRESETS",
    "DEFAULT_DDD17_ROOT",
    "DDD17_CLASS_NAMES",
    "DDD17Dataset",
    "DEFAULT_ARCHITECTURE",
    "EventSpikeSeg",
    "build_model",
    "resolve_ddd17_root",
]
