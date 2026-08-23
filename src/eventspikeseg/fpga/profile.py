"""Quantized live-state occupancy profiling for the no-external-memory target."""

from __future__ import annotations

from dataclasses import dataclass, field

import torch
from torch import Tensor

from ..model_components import ParametricLIF
from .fixed_point import FPGA_FORMATS
from .target import ARTIX7_XC7A200T

EXECUTED_WEIGHT_BYTES = 135_624
# Conservative aligned sparse-entry budgets. Raw payload now includes the 24-bit
# last-bin tag; it still fits within these 12/16-byte alignment envelopes.
NON_ADAPTIVE_ENTRY_BYTES = 12
ADAPTIVE_ENTRY_BYTES = 16


def live_state_mask(
    membrane: Tensor,
    *,
    adaptation_age: Tensor | None = None,
    adaptation_amplitude: Tensor | None = None,
    adaptation_duration: Tensor | None = None,
) -> Tensor:
    """Return states that cannot be losslessly represented by the implicit zero entry."""

    membrane_format = FPGA_FORMATS["membrane"]
    membrane_q = torch.clamp(
        torch.round(membrane.detach() * membrane_format.scale),
        membrane_format.minimum,
        membrane_format.maximum,
    )
    live = membrane_q != 0
    if adaptation_age is None or adaptation_amplitude is None or adaptation_duration is None:
        return live
    age = adaptation_age.detach()
    adaptation_format = FPGA_FORMATS["adaptation"]
    amplitude_q = torch.clamp(
        torch.round(adaptation_amplitude.detach() * adaptation_format.scale),
        adaptation_format.minimum,
        adaptation_format.maximum,
    )
    duration = adaptation_duration.detach().view(1, -1, 1, 1)
    adaptation_live = (age >= 0) & (age < 2.0 * duration) & (amplitude_q != 0)
    return live | adaptation_live


def neuron_live_count(neuron: ParametricLIF) -> int:
    if neuron.membrane.numel() == 0:
        return 0
    if not neuron.config.threshold_adaptation_enabled:
        return int(live_state_mask(neuron.membrane).sum())
    duration = neuron.adaptation_duration
    assert duration is not None
    return int(
        live_state_mask(
            neuron.membrane,
            adaptation_age=neuron.threshold_adaptation_age,
            adaptation_amplitude=neuron.threshold_adaptation_amplitude,
            adaptation_duration=duration,
        ).sum()
    )


@dataclass
class LiveStateProfile:
    high_watermark_by_layer: dict[str, int] = field(default_factory=dict)
    current_by_layer: dict[str, int] = field(default_factory=dict)
    samples: int = 0

    def observe(self, layer: str, neuron: ParametricLIF) -> int:
        live = neuron_live_count(neuron)
        self.high_watermark_by_layer[layer] = max(
            live, self.high_watermark_by_layer.get(layer, 0)
        )
        self.current_by_layer[layer] = live
        return live

    def summary(self, *, bram_reserve_fraction: float = 0.25) -> dict[str, object]:
        if not 0.0 <= bram_reserve_fraction < 1.0:
            raise ValueError("BRAM reserve fraction must be in [0, 1)")
        bram_bytes = int(ARTIX7_XC7A200T.bram_mib * 2**20)
        reserved_bytes = int(bram_bytes * bram_reserve_fraction)
        state_budget_bytes = bram_bytes - reserved_bytes - EXECUTED_WEIGHT_BYTES
        entry_bytes = {
            layer: (
                ADAPTIVE_ENTRY_BYTES
                if layer.startswith(("down2", "enc2", "down3", "enc3", "context"))
                else NON_ADAPTIVE_ENTRY_BYTES
            )
            for layer in self.high_watermark_by_layer
        }
        required_bytes = sum(
            count * entry_bytes[layer]
            for layer, count in self.high_watermark_by_layer.items()
        )
        current_required_bytes = sum(
            count * entry_bytes[layer] for layer, count in self.current_by_layer.items()
        )
        return {
            "samples": self.samples,
            "high_watermark_by_layer": dict(sorted(self.high_watermark_by_layer.items())),
            "entry_bytes_by_layer": dict(sorted(entry_bytes.items())),
            "high_watermark_entries_sum": sum(self.high_watermark_by_layer.values()),
            "current_entries_sum": sum(self.current_by_layer.values()),
            "required_state_bytes": required_bytes,
            "current_required_state_bytes": current_required_bytes,
            "state_budget_bytes": state_budget_bytes,
            "bram_reserve_bytes": reserved_bytes,
            "weight_bytes": EXECUTED_WEIGHT_BYTES,
            "fits_on_chip_bram": required_bytes <= state_budget_bytes,
            "budget_utilization": (
                required_bytes / state_budget_bytes if state_budget_bytes > 0 else float("inf")
            ),
            "current_budget_utilization": (
                current_required_bytes / state_budget_bytes
                if state_budget_bytes > 0
                else float("inf")
            ),
        }
