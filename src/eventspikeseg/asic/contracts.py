"""Frozen ASIC timing, topology, and state-capacity contracts."""

BIN_US = 5_000
DEFAULT_PREDICTION_BINS = 10
BIN_TAG_WIDTH = 24
BIN_TAG_MODULUS = 1 << BIN_TAG_WIDTH

REGISTERED_PARAMETERS = 149_835
EXECUTED_PARAMETERS = 149_423
EXECUTED_SYNAPTIC_WEIGHTS = 143_824
LOGICAL_MEMBRANES = 30_976_000
ADAPTATION_ENABLED_NEURONS = 10_982_400

WEIGHT_BYTES_INT8 = EXECUTED_SYNAPTIC_WEIGHTS
MEMBRANE_BYTES_INT16 = LOGICAL_MEMBRANES * 2
ADAPTATION_BYTES_TWO_INT16 = ADAPTATION_ENABLED_NEURONS * 4
LAST_BIN_TAG_BYTES_24 = LOGICAL_MEMBRANES * 3
DENSE_EXACT_STATE_BYTES = (
    MEMBRANE_BYTES_INT16 + ADAPTATION_BYTES_TWO_INT16 + LAST_BIN_TAG_BYTES_24
)

OPEN_PPA_TARGET = {
    "flow": "Yosys_OpenROAD_Flow_Scripts",
    "platform": "ASAP7",
    "process_nm": 7,
    "purpose": "predictive_research_PPA",
    "manufacturable": False,
    "signoff": False,
}

MANUFACTURABLE_TARGET_GATE = {
    "status": "pending_library_access",
    "maximum_process_nm": 28,
    "requires": [
        "foundry_PDK",
        "characterized_high_density_actor_local_SRAM_macros",
        "standard_cell_liberty_LEF_GDS",
    ],
}


def state_capacity_contract() -> dict[str, object]:
    """Return exact logical storage totals without pretending a RAM macro is selected."""

    return {
        "logical_membranes": LOGICAL_MEMBRANES,
        "adaptation_enabled_neurons": ADAPTATION_ENABLED_NEURONS,
        "weight_bytes_int8": WEIGHT_BYTES_INT8,
        "membrane_bytes_int16": MEMBRANE_BYTES_INT16,
        "adaptation_bytes_two_int16": ADAPTATION_BYTES_TWO_INT16,
        "last_bin_tag_bytes_24": LAST_BIN_TAG_BYTES_24,
        "dense_exact_state_bytes": DENSE_EXACT_STATE_BYTES,
        "dense_exact_state_mib": DENSE_EXACT_STATE_BYTES / 2**20,
        "full_chip_PPA_gate": "characterized_actor_local_SRAM_macros_required",
    }
