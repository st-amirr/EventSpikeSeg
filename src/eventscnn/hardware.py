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


# ---------------------------------------------------------------------------
# Sparse event-address convolution reference
# ---------------------------------------------------------------------------

import torch
from torch import Tensor


def _pair(value: int | tuple[int, int]) -> tuple[int, int]:
    return value if isinstance(value, tuple) else (value, value)


def event_scatter_conv2d(
    counts: Tensor,
    weights: Tensor,
    *,
    stride: int | tuple[int, int] = 1,
    padding: int | tuple[int, int] = 0,
    output_dtype: torch.dtype | None = None,
) -> Tensor:
    """Convolve NCHW counts by repeated additions from active input addresses.

    Kernels remain `[Cout,Cin,Kh,Kw]`. Each positive count is processed as that many
    active events, mirroring FPGA address scattering rather than matrix flattening.
    """

    if counts.ndim != 4 or weights.ndim != 4:
        raise ValueError("counts and weights must be NCHW/OIHW")
    batch, in_channels, input_height, input_width = counts.shape
    out_channels, weight_channels, kernel_height, kernel_width = weights.shape
    if in_channels != weight_channels:
        raise ValueError("input and weight channels differ")
    if torch.any(counts < 0) or torch.any(counts != counts.round()):
        raise ValueError("event counts must be non-negative integers")
    stride_y, stride_x = _pair(stride)
    pad_y, pad_x = _pair(padding)
    output_height = (input_height + 2 * pad_y - kernel_height) // stride_y + 1
    output_width = (input_width + 2 * pad_x - kernel_width) // stride_x + 1
    if output_height <= 0 or output_width <= 0:
        raise ValueError("kernel does not fit the padded input")
    dtype = output_dtype or weights.dtype
    output = torch.zeros(
        (batch, out_channels, output_height, output_width),
        dtype=dtype,
        device=weights.device,
    )
    for index in counts.nonzero(as_tuple=False):
        batch_index, input_channel, input_y, input_x = (int(value) for value in index)
        repetitions = int(counts[batch_index, input_channel, input_y, input_x])
        for kernel_y in range(kernel_height):
            numerator_y = input_y + pad_y - kernel_y
            if numerator_y % stride_y:
                continue
            output_y = numerator_y // stride_y
            if not 0 <= output_y < output_height:
                continue
            for kernel_x in range(kernel_width):
                numerator_x = input_x + pad_x - kernel_x
                if numerator_x % stride_x:
                    continue
                output_x = numerator_x // stride_x
                if not 0 <= output_x < output_width:
                    continue
                contribution = weights[:, input_channel, kernel_y, kernel_x].to(dtype)
                for _ in range(repetitions):
                    output[batch_index, :, output_y, output_x] += contribution
    return output



# ---------------------------------------------------------------------------
# Golden-vector export
# ---------------------------------------------------------------------------

import json
from pathlib import Path

import numpy as np
import torch



def export_lif_golden_vectors(directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    currents = torch.tensor([32, 230, 40_000, -40_000], dtype=torch.int64)
    thresholds = torch.tensor([256, 256, 30_000, 256], dtype=torch.int64)
    adaptation = torch.tensor([0], dtype=torch.int64)
    membrane = torch.zeros((1, 1, 1, 1), dtype=torch.int64)
    membranes = []
    spikes = []
    for value, threshold_value in zip(currents, thresholds):
        membrane, spike = integer_lif_step(
            membrane,
            value.reshape(1, 1, 1, 1),
            threshold=threshold_value.reshape(1),
            adaptation=adaptation,
            beta_shift=4,
            competition=False,
        )
        membranes.append(int(membrane.item()))
        spikes.append(int(spike.item()))
    vector_path = directory / "golden_lif_vectors.npz"
    np.savez(
        vector_path,
        currents=currents.numpy(),
        thresholds=thresholds.numpy(),
        membranes=np.asarray(membranes),
        spikes=np.asarray(spikes),
    )
    metadata_path = directory / "golden_lif_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "operation_order": [
                    "leak",
                    "add_current",
                    "saturate_membrane",
                    "compare_threshold",
                    "competition",
                    "subtractive_reset",
                    "emit",
                    "homeostasis",
                ],
                "beta_shift": 4,
                "threshold": "per_step",
                "membrane_bits": 16,
            },
            indent=2,
        )
        + "\n"
    )
    return vector_path, metadata_path
