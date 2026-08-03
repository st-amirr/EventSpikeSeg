"""Independent sparse event-address shared-kernel convolution reference."""

from __future__ import annotations

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
