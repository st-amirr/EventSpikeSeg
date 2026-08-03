"""Trainable convolutional SNN modules built on PyTorch and SpikingJelly surrogates."""

from collections.abc import Sequence
from typing import Optional

import torch
from torch import Tensor, nn

from .config import BackboneConfig, LayerConfig, LIFConfig
from .dynamics import HardwareLIF


class ConvLIFBlock(nn.Module):
    """Bias-free shared convolution followed by hardware-ordered LIF dynamics."""

    def __init__(self, layer: LayerConfig, lif: Optional[LIFConfig] = None) -> None:
        super().__init__()
        self.layer_config = layer
        self.conv = nn.Conv2d(
            layer.in_channels,
            layer.out_channels,
            layer.kernel_size,
            stride=layer.stride,
            padding=layer.padding,
            bias=False,
        )
        self.neuron = HardwareLIF(layer.out_channels, lif)

    def reset(self) -> None:
        self.neuron.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        if sequence.ndim != 5 or sequence.shape[2] != self.layer_config.in_channels:
            raise ValueError("expected TNCHW sequence with configured input channels")
        return torch.stack([self.neuron(self.conv(step.float())) for step in sequence])


class EventSCNNBackbone(nn.Module):
    """Canonical three-layer 2→8→16→32 spiking convolutional backbone."""

    def __init__(self, config: Optional[BackboneConfig] = None) -> None:
        super().__init__()
        config = config or BackboneConfig()
        self.config = config
        self.blocks = nn.ModuleList(
            [ConvLIFBlock(layer, config.lif) for layer in config.layers]
        )

    def reset(self) -> None:
        for block in self.blocks:
            block.reset()

    def forward(self, sequence: Tensor, *, return_all: bool = False):
        activations: list[Tensor] = []
        output = sequence
        for block in self.blocks:
            output = block(output)
            activations.append(output)
        return activations if return_all else output


def assert_hardware_compatible_convolutions(modules: Sequence[nn.Module]) -> None:
    """Reject convolution bias, which would require updates without input spikes."""

    for module in modules:
        if isinstance(module, nn.Conv2d) and module.bias is not None:
            raise ValueError("spiking backbone convolutions must use bias=False")
