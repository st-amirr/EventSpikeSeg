"""Frozen fixed-point arithmetic contract shared by export, reference, and RTL.

The first RTL baseline deliberately uses explicit formats and saturation.  Format
changes are architecture changes: they require regeneration of golden vectors and
semantic-accuracy validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import torch
from torch import Tensor


@dataclass(frozen=True)
class FixedFormat:
    """Signed or unsigned fixed-point storage description."""

    name: str
    bits: int
    fractional_bits: int
    signed: bool = True

    def __post_init__(self) -> None:
        if self.bits < 1:
            raise ValueError("bits must be positive")
        if self.fractional_bits < 0 or self.fractional_bits >= self.bits:
            raise ValueError("fractional_bits must be in [0, bits)")

    @property
    def scale(self) -> int:
        return 1 << self.fractional_bits

    @property
    def minimum(self) -> int:
        return -(1 << (self.bits - 1)) if self.signed else 0

    @property
    def maximum(self) -> int:
        return (1 << (self.bits - 1)) - 1 if self.signed else (1 << self.bits) - 1

    def saturate(self, value: int) -> int:
        return min(max(int(value), self.minimum), self.maximum)

    def quantize(self, value: Tensor | float) -> Tensor:
        tensor = torch.as_tensor(value, dtype=torch.float64)
        return torch.clamp(
            torch.round(tensor * self.scale), self.minimum, self.maximum
        ).to(torch.int64)

    def dequantize(self, value: Tensor | int) -> Tensor:
        return torch.as_tensor(value, dtype=torch.float64) / self.scale

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result.update(
            {
                "minimum_integer": self.minimum,
                "maximum_integer": self.maximum,
                "rounding": "round_to_nearest_ties_to_even_on_float_export",
                "overflow": "saturate",
            }
        )
        return result


# Baseline formats.  Weight storage is compact; state is wider because repeated
# signed synaptic additions and fixed-step learned-beta decay must not wrap.
ASIC_FORMATS: dict[str, FixedFormat] = {
    "weight": FixedFormat("weight_q1_6", bits=8, fractional_bits=6),
    "membrane": FixedFormat("membrane_q5_10", bits=16, fractional_bits=10),
    "current": FixedFormat("current_q13_10", bits=24, fractional_bits=10),
    "beta": FixedFormat("beta_uq1_15", bits=16, fractional_bits=15, signed=False),
    "threshold": FixedFormat("threshold_q5_10", bits=16, fractional_bits=10),
    "adaptation": FixedFormat("adaptation_q5_10", bits=16, fractional_bits=10),
}


def round_shift_ties_away(value: int, shift: int) -> int:
    """Arithmetic right shift with deterministic nearest rounding.

    RTL must use the same rule after fixed-point multiplication.  Export uses
    PyTorch's ties-to-even rule only when converting a float coefficient to an
    integer; integer datapath products use this ties-away rule.
    """

    if shift < 0:
        return int(value) << -shift
    if shift == 0:
        return int(value)
    magnitude = abs(int(value))
    rounded = (magnitude + (1 << (shift - 1))) >> shift
    return rounded if value >= 0 else -rounded
