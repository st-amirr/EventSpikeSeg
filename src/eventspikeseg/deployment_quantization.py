"""Canonical ASIC fixed-point formats and training-time fake quantization."""

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


ASIC_FORMATS: dict[str, FixedFormat] = {
    "weight": FixedFormat("weight_q7_16", bits=24, fractional_bits=16),
    "membrane": FixedFormat("membrane_q7_16", bits=24, fractional_bits=16),
    "current": FixedFormat("combined_accumulator_q15_16", bits=32, fractional_bits=16),
    "beta": FixedFormat("beta_uq1_23", bits=24, fractional_bits=23, signed=False),
    "threshold": FixedFormat("threshold_q7_16", bits=24, fractional_bits=16),
    "inhibition_strength": FixedFormat(
        "inhibition_strength_uq3_16", bits=19, fractional_bits=16, signed=False
    ),
    "adaptation_strength": FixedFormat(
        "adaptation_strength_uq3_16", bits=19, fractional_bits=16, signed=False
    ),
    "adaptation_duration": FixedFormat(
        "adaptation_duration_uq5_16", bits=21, fractional_bits=16, signed=False
    ),
    "adaptation_age": FixedFormat(
        "adaptation_age_bins_u6", bits=6, fractional_bits=0, signed=False
    ),
    "adaptation_amplitude": FixedFormat(
        "adaptation_amplitude_uq3_16", bits=19, fractional_bits=16, signed=False
    ),
}


def fake_quantize_ste(value: Tensor, format_name: str) -> Tensor:
    """Emulate one ASIC format while preserving an identity training gradient."""
    fixed_format = ASIC_FORMATS[format_name]
    scale = float(fixed_format.scale)
    quantized = torch.clamp(
        torch.round(value.float() * scale),
        fixed_format.minimum,
        fixed_format.maximum,
    ) / scale
    quantized = quantized.to(value.dtype)
    return value + (quantized - value).detach()
