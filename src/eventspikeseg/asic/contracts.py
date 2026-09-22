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

WEIGHT_BYTES_INT24 = EXECUTED_SYNAPTIC_WEIGHTS * 3
MEMBRANE_BYTES_INT16 = LOGICAL_MEMBRANES * 2
COMBINED_ACCUMULATOR_BYTES_INT32 = LOGICAL_MEMBRANES * 4
ADAPTATION_AGE_BITS = 6
ADAPTATION_AMPLITUDE_BITS = 19
ADAPTATION_STATE_BITS = ADAPTATION_ENABLED_NEURONS * (
    ADAPTATION_AGE_BITS + ADAPTATION_AMPLITUDE_BITS
)
DENSE_EXACT_STATE_BITS = (
    LOGICAL_MEMBRANES * 32 + ADAPTATION_STATE_BITS
)
DENSE_EXACT_STATE_BYTES = (DENSE_EXACT_STATE_BITS + 7) // 8

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


def state_capacity_contract(
    *,
    logical_membranes: int = LOGICAL_MEMBRANES,
    adaptation_enabled_neurons: int = ADAPTATION_ENABLED_NEURONS,
    executed_synaptic_weights: int = EXECUTED_SYNAPTIC_WEIGHTS,
) -> dict[str, object]:
    """Return exact logical storage totals without pretending a RAM macro is selected."""

    weight_bytes = executed_synaptic_weights * 3
    accumulator_bytes = logical_membranes * 4
    adaptation_bits = adaptation_enabled_neurons * (
        ADAPTATION_AGE_BITS + ADAPTATION_AMPLITUDE_BITS
    )
    dense_bits = logical_membranes * 32 + adaptation_bits
    dense_bytes = (dense_bits + 7) // 8

    return {
        "logical_membranes": logical_membranes,
        "adaptation_enabled_neurons": adaptation_enabled_neurons,
        "weight_bytes_int24": weight_bytes,
        "combined_accumulator_bytes_int32": accumulator_bytes,
        "adaptation_age_bits_per_enabled_neuron": ADAPTATION_AGE_BITS,
        "adaptation_amplitude_bits_per_enabled_neuron": ADAPTATION_AMPLITUDE_BITS,
        "adaptation_state_bits": adaptation_bits,
        "last_bin_tag_bytes": 0,
        "dense_exact_state_bytes": dense_bytes,
        "dense_exact_state_mib": dense_bytes / 2**20,
        "full_chip_PPA_gate": "complete_direct_register_or_latch_resident_hierarchy_required",
    }
