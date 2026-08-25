"""ASIC export, fixed-point, capacity, and integer-reference contracts."""

from .contracts import (
    BIN_TAG_MODULUS,
    BIN_TAG_WIDTH,
    BIN_US,
    DEFAULT_PREDICTION_BINS,
    DENSE_EXACT_STATE_BYTES,
    MANUFACTURABLE_TARGET_GATE,
    OPEN_PPA_TARGET,
    state_capacity_contract,
)
from .export import EVENTSPIKESEG140K_INFERENCE_STAGES, export_checkpoint, export_model
from .fixed_point import ASIC_FORMATS, FixedFormat
from .integer_reference import ActorLocalStateStore, IntegerPLIF, NeuronState

__all__ = [
    "ACTOR_FORMATS",
    "ASIC_FORMATS",
    "ActorLocalStateStore",
    "BIN_TAG_MODULUS",
    "BIN_TAG_WIDTH",
    "BIN_US",
    "DEFAULT_PREDICTION_BINS",
    "DENSE_EXACT_STATE_BYTES",
    "EVENTSPIKESEG140K_INFERENCE_STAGES",
    "FixedFormat",
    "IntegerPLIF",
    "MANUFACTURABLE_TARGET_GATE",
    "NeuronState",
    "OPEN_PPA_TARGET",
    "export_checkpoint",
    "export_model",
    "state_capacity_contract",
]

# Descriptive alias for downstream tooling; ASIC_FORMATS remains the canonical name.
ACTOR_FORMATS = ASIC_FORMATS
