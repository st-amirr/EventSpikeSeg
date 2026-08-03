"""Frozen fixed-point arithmetic for the bit-accurate hardware reference."""

from dataclasses import dataclass
from typing import Optional

import torch
from torch import Tensor


@dataclass(frozen=True)
class IntegerFormat:
    bits: int
    signed: bool = True

    def __post_init__(self) -> None:
        if self.bits < 1 or (self.signed and self.bits < 2):
            raise ValueError("invalid integer width")

    @property
    def minimum(self) -> int:
        return -(1 << (self.bits - 1)) if self.signed else 0

    @property
    def maximum(self) -> int:
        return (1 << (self.bits - int(self.signed))) - 1


def saturate(values: Tensor, integer_format: IntegerFormat) -> Tensor:
    return values.to(torch.int64).clamp(integer_format.minimum, integer_format.maximum)


def round_half_away_from_zero(values: Tensor) -> Tensor:
    """Deterministic rounding rule shared with exporter and RTL vector generation."""

    return torch.sign(values) * torch.floor(torch.abs(values) + 0.5)


def quantize(values: Tensor, *, scale: int, integer_format: IntegerFormat) -> Tensor:
    if scale <= 0:
        raise ValueError("scale must be positive")
    return saturate(round_half_away_from_zero(values * scale), integer_format)


def arithmetic_shift_right(values: Tensor, shift: int) -> Tensor:
    if shift < 0:
        raise ValueError("shift cannot be negative")
    return torch.bitwise_right_shift(values.to(torch.int64), shift)


def integer_lif_step(
    membrane: Tensor,
    current: Tensor,
    *,
    threshold: Tensor,
    adaptation: Tensor,
    beta_shift: int,
    membrane_format: Optional[IntegerFormat] = None,
    competition: bool = True,
    competitor_decrement: int = 0,
) -> tuple[Tensor, Tensor]:
    """Integer leak→current→threshold→competition→subtractive-reset transition.

    All tensors are NCHW except threshold/adaptation, which contain one value per C.
    Arithmetic shift rounds negative values toward negative infinity, matching two's
    complement RTL arithmetic shift.
    """

    membrane_format = membrane_format or IntegerFormat(16)
    if membrane.shape != current.shape or membrane.ndim != 4:
        raise ValueError("membrane and current must be equal NCHW tensors")
    channels = membrane.shape[1]
    if threshold.shape != (channels,) or adaptation.shape != (channels,):
        raise ValueError("threshold and adaptation must have shape [C]")
    leaked = membrane.to(torch.int64) - arithmetic_shift_right(membrane, beta_shift)
    candidate = saturate(leaked + current.to(torch.int64), membrane_format)
    effective = (threshold + adaptation).to(torch.int64).view(1, channels, 1, 1)
    above = candidate >= effective
    if competition:
        minimum = torch.iinfo(torch.int64).min
        winner_index = candidate.masked_fill(~above, minimum).argmax(dim=1, keepdim=True)
        winners = torch.zeros_like(above).scatter_(1, winner_index, True)
        winners &= above.any(dim=1, keepdim=True)
    else:
        winners = above
    losers = above & ~winners
    updated = candidate - winners.to(torch.int64) * effective
    updated -= losers.to(torch.int64) * competitor_decrement
    return saturate(updated, membrane_format), winners.to(torch.uint8)


def update_integer_adaptation(
    adaptation: Tensor,
    spike_counts: Tensor,
    *,
    decay: int,
    increment: int,
    integer_format: Optional[IntegerFormat] = None,
) -> Tensor:
    integer_format = integer_format or IntegerFormat(16, signed=False)
    if decay < 0 or increment < 0:
        raise ValueError("decay and increment cannot be negative")
    decayed = torch.clamp(adaptation.to(torch.int64) - decay, min=0)
    return saturate(decayed + spike_counts.to(torch.int64) * increment, integer_format)
