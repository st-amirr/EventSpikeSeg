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
from .dag_reference import (
    IntegerDAGReference,
    Prediction,
    SpikeEvent,
    write_golden_artifacts,
)
from .export import EVENTSPIKESEG140K_INFERENCE_STAGES, export_checkpoint, export_model
from .fixed_point import ASIC_FORMATS, FixedFormat
from .integer_reference import ActorLocalStateStore, IntegerPLIF, NeuronState
from .topology import (
    EVENTSPIKESEG140K_ACTORS,
    EVENTSPIKESEG140K_CURRENT_READOUT,
    EVENTSPIKESEG140K_EDGES,
    EVENTSPIKESEG140K_JOIN_NODES,
    eventspikeseg140k_graph_contract,
    validate_eventspikeseg140k_topology,
)

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
    "EVENTSPIKESEG140K_ACTORS",
    "EVENTSPIKESEG140K_CURRENT_READOUT",
    "EVENTSPIKESEG140K_EDGES",
    "EVENTSPIKESEG140K_JOIN_NODES",
    "FixedFormat",
    "IntegerPLIF",
    "IntegerDAGReference",
    "MANUFACTURABLE_TARGET_GATE",
    "NeuronState",
    "OPEN_PPA_TARGET",
    "Prediction",
    "SpikeEvent",
    "export_checkpoint",
    "export_model",
    "eventspikeseg140k_graph_contract",
    "state_capacity_contract",
    "validate_eventspikeseg140k_topology",
    "write_golden_artifacts",
]

# Descriptive alias for downstream tooling; ASIC_FORMATS remains the canonical name.
ACTOR_FORMATS = ASIC_FORMATS
