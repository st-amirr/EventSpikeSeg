"""Hardware-oriented helpers retained for the later FPGA implementation stage."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn


@dataclass(frozen=True)
class FixedPointConfig:
    bits: int = 8
    fractional_bits: int = 6

    @property
    def minimum(self) -> int:
        return -(1 << (self.bits - 1))

    @property
    def maximum(self) -> int:
        return (1 << (self.bits - 1)) - 1


DEFAULT_FIXED_POINT_CONFIG = FixedPointConfig()


def quantize_tensor(
    tensor: Tensor, config: FixedPointConfig = DEFAULT_FIXED_POINT_CONFIG
) -> Tensor:
    scale = float(1 << config.fractional_bits)
    return torch.clamp(torch.round(tensor * scale), config.minimum, config.maximum) / scale


def quantize_model_weights(
    model: nn.Module, config: FixedPointConfig = DEFAULT_FIXED_POINT_CONFIG
) -> None:
    with torch.no_grad():
        for module in model.modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                module.weight.copy_(quantize_tensor(module.weight, config))
                if module.bias is not None:
                    module.bias.copy_(quantize_tensor(module.bias, config))


def count_convolution_weights(model: nn.Module) -> int:
    return sum(
        module.weight.numel()
        for module in model.modules()
        if isinstance(module, nn.Conv2d)
    )
