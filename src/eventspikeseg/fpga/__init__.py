"""Fixed-point export and fixed-time integer-reference tools for EventSpikeSeg140k RTL."""

from .export import (
    EVENTSPIKESEG140K_INFERENCE_STAGES,
    export_checkpoint,
    export_model,
)
from .fixed_point import FPGA_FORMATS, FixedFormat
from .integer_reference import IntegerPLIF, SparseStateStore
from .profile import LiveStateProfile, live_state_mask
from .runtime import (
    BIN_TAG_WIDTH,
    BIN_US,
    DEFAULT_PREDICTION_BINS,
    DEFAULT_TARGET_UTILIZATION,
    HARD_MAX_UTILIZATION,
    RECORD_US,
    STEP_US,
    STEPS_PER_RECORD,
    ActorStep,
    FixedTimeRuntime,
    LayerStep,
    RuntimeTiming,
    ScheduledEvent,
    StreamingBinRuntime,
)
from .target import ARTIX7_XC7A200T, NEXYS_VIDEO_XC7A200T, memory_budget

__all__ = [
    "ActorStep",
    "BIN_TAG_WIDTH",
    "BIN_US",
    "DEFAULT_PREDICTION_BINS",
    "DEFAULT_TARGET_UTILIZATION",
    "HARD_MAX_UTILIZATION",
    "RuntimeTiming",
    "StreamingBinRuntime",
    "ARTIX7_XC7A200T",
    "EVENTSPIKESEG140K_INFERENCE_STAGES",
    "FPGA_FORMATS",
    "FixedFormat",
    "FixedTimeRuntime",
    "IntegerPLIF",
    "LayerStep",
    "LiveStateProfile",
    "NEXYS_VIDEO_XC7A200T",
    "RECORD_US",
    "STEP_US",
    "STEPS_PER_RECORD",
    "ScheduledEvent",
    "SparseStateStore",
    "export_checkpoint",
    "export_model",
    "live_state_mask",
    "memory_budget",
]
