"""Frozen Artix-7 target and exact memory-budget calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FPGATarget:
    board: str
    family: str
    device: str
    logic_cells: int
    lookup_tables: int
    flip_flops: int
    dsp_slices: int
    bram_kibits: int
    onboard_memory_mib: int
    onboard_memory_kind: str

    @property
    def bram_mib(self) -> float:
        return self.bram_kibits / 8.0 / 1024.0

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["bram_mib"] = self.bram_mib
        return result


# Reference implementation target: Artix-7 XC7A200T on the widely available
# Digilent Nexys Video board.  The board DDR3 exists physically, but the active
# no-external-memory experiment forbids using it as persistent neuron backing store.
ARTIX7_XC7A200T = FPGATarget(
    board="Digilent Nexys Video",
    family="AMD/Xilinx Artix-7",
    device="XC7A200T-1SBG484C",
    logic_cells=215_360,
    lookup_tables=134_600,
    flip_flops=269_200,
    dsp_slices=740,
    bram_kibits=13_140,
    onboard_memory_mib=512,
    onboard_memory_kind="DDR3-800 16-bit (present, forbidden by active experiment)",
)

# Compatibility alias for older scripts/checkpoints/docs.
NEXYS_VIDEO_XC7A200T = ARTIX7_XC7A200T

ARTIX7_BRAM_KIBITS = {
    "XC7A35T": 1_800,
    "XC7A100T": 4_860,
    "XC7A200T": 13_140,
}

# Native DSEC 440x640, 25 deployed PLIF populations. Concatenative quarter fusion
# and standard native fusion remove the two intermediate DW/PW membrane banks.
DSEC_MEMBRANE_STATES = 30_976_000
DSEC_ADAPTATION_STATES = 10_982_400
BIN_TAG_WIDTH = 24
BIN_TAG_BYTES = 3
DENSE_STATE_BYTES = (
    DSEC_MEMBRANE_STATES * 2  # int16 membrane
    + DSEC_ADAPTATION_STATES * (2 + 2)  # int16 age + int16 amplitude
    + DSEC_MEMBRANE_STATES * BIN_TAG_BYTES  # compact 5 ms last-bin tag for lazy touched state
)


def memory_budget(bram_kibits: int, *, state_bytes: int = DENSE_STATE_BYTES) -> dict[str, float]:
    """Return exact binary-unit BRAM shortfall figures for one target device."""

    if bram_kibits <= 0 or state_bytes <= 0:
        raise ValueError("memory sizes must be positive")
    bram_bytes = bram_kibits * 1024 // 8
    missing_bytes = max(0, state_bytes - bram_bytes)
    return {
        "state_mib": state_bytes / 2**20,
        "bram_mib": bram_bytes / 2**20,
        "missing_mib": missing_bytes / 2**20,
        "required_over_available": state_bytes / bram_bytes,
        "percent_missing": 100.0 * missing_bytes / state_bytes,
    }
