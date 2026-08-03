"""SpikingJelly-compatible hardware-ordered spiking dynamics."""

from typing import Optional

import torch
from spikingjelly.activation_based import surrogate
from torch import Tensor, nn

from .config import LIFConfig


class HardwareLIF(nn.Module):
    """Stateful LIF with top-1 competition and per-channel homeostasis.

    Input/current and membrane tensors use NCHW. Forward ordering is frozen as leak,
    current, threshold, competition, subtractive reset, spike, adaptation.
    """

    def __init__(self, channels: int, config: Optional[LIFConfig] = None) -> None:
        super().__init__()
        if channels <= 0:
            raise ValueError("channels must be positive")
        self.channels = channels
        self.config = config or LIFConfig()
        self.spike_function = surrogate.ATan()
        self.register_buffer("membrane", torch.empty(0), persistent=False)
        self.register_buffer("adaptation", torch.zeros(channels), persistent=False)

    def reset(self) -> None:
        self.membrane = torch.empty(0, device=self.adaptation.device)
        self.adaptation.zero_()

    def _ensure_state(self, current: Tensor) -> None:
        if self.membrane.shape != current.shape:
            self.membrane = torch.zeros_like(current)
        if self.adaptation.device != current.device or self.adaptation.dtype != current.dtype:
            self.adaptation = self.adaptation.to(device=current.device, dtype=current.dtype)

    def forward(self, current: Tensor) -> Tensor:
        if current.ndim != 4 or current.shape[1] != self.channels:
            raise ValueError(f"expected N,{self.channels},H,W current")
        self._ensure_state(current)
        leaked = self.membrane - self.membrane / float(1 << self.config.beta_shift)
        candidate = leaked + current
        effective = self.config.threshold + self.adaptation
        threshold = effective.view(1, -1, 1, 1)
        raw_spikes = self.spike_function(candidate - threshold)
        above = candidate >= threshold

        if self.config.f_inst_enabled:
            masked = candidate.masked_fill(~above, -torch.inf)
            winner_index = masked.argmax(dim=1, keepdim=True)
            gate = torch.zeros_like(above).scatter_(1, winner_index, True)
            gate &= above.any(dim=1, keepdim=True)
            emitted = raw_spikes * gate.to(raw_spikes.dtype)
        else:
            gate = above
            # The surrogate already has the exact hard-spike forward value. Avoid a
            # second detached threshold mask, which would erase subthreshold gradients.
            emitted = raw_spikes

        winner_reset = gate.to(candidate.dtype) * threshold
        loser_mask = above & ~gate
        loser_decrement = loser_mask.to(candidate.dtype) * self.config.competitor_decrement
        self.membrane = candidate - winner_reset - loser_decrement

        if self.config.f_long_enabled:
            decayed = torch.clamp(self.adaptation - self.config.adaptation_decay, min=0.0)
            activity = emitted.detach().mean(dim=(0, 2, 3))
            self.adaptation = decayed + self.config.adaptation_increment * activity
        return emitted

    def state(self) -> tuple[Optional[Tensor], Tensor]:
        membrane = None if self.membrane.numel() == 0 else self.membrane
        return membrane, self.adaptation
