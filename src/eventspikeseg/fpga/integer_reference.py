"""Bit-oriented PLIF and sparse state primitives for golden RTL comparison."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from .fixed_point import FPGA_FORMATS, FixedFormat, round_shift_ties_away

REFERENCE_STEP_US = 5_000


@dataclass
class NeuronState:
    membrane: int = 0
    last_timestamp_us: int = 0
    adaptation_age: int = -1
    adaptation_amplitude: int = 0

    @property
    def adaptation_active(self) -> bool:
        return self.adaptation_age >= 0 or self.adaptation_amplitude != 0


@dataclass(frozen=True)
class PLIFResult:
    membrane: int
    spike: int
    candidate: int


class IntegerPLIF:
    """Integer soft-reset PLIF operation used by the first exact RTL baseline."""

    def __init__(
        self,
        *,
        membrane_format: FixedFormat = FPGA_FORMATS["membrane"],
        beta_format: FixedFormat = FPGA_FORMATS["beta"],
    ) -> None:
        self.membrane_format = membrane_format
        self.beta_format = beta_format

    def retention_for_delta(self, beta_q: int, delta_us: int) -> int:
        """Return quantized beta**(delta/5ms) for a lazy timestamp update.

        This coefficient generator belongs to the integer reference/export side.
        RTL consumes an equivalent coefficient from its retention approximation
        block; coefficient-level equivalence is checked separately.
        """

        if delta_us < 0:
            raise ValueError("timestamps must be monotonic")
        beta = self.beta_format.saturate(beta_q) / self.beta_format.scale
        retention = beta ** (delta_us / REFERENCE_STEP_US)
        return self.beta_format.saturate(round(retention * self.beta_format.scale))

    def step(
        self,
        *,
        membrane_q: int,
        current_q: int,
        retention_q: int,
        threshold_q: int,
    ) -> PLIFResult:
        leaked = round_shift_ties_away(
            int(membrane_q) * int(retention_q), self.beta_format.fractional_bits
        )
        candidate = self.membrane_format.saturate(leaked + int(current_q))
        spike = int(candidate >= int(threshold_q))
        membrane = self.membrane_format.saturate(
            candidate - (int(threshold_q) if spike else 0)
        )
        return PLIFResult(membrane=membrane, spike=spike, candidate=candidate)


class SparseStateStore:
    """Zero-default sparse logical-neuron store with occupancy instrumentation."""

    def __init__(self) -> None:
        self._states: dict[Hashable, NeuronState] = {}
        self.high_watermark = 0
        self.touches = 0
        self.reclaims = 0

    def __len__(self) -> int:
        return len(self._states)

    def read(self, address: Hashable) -> NeuronState:
        state = self._states.get(address)
        return NeuronState() if state is None else NeuronState(**vars(state))

    def write(self, address: Hashable, state: NeuronState) -> None:
        self.touches += 1
        if state.membrane == 0 and not state.adaptation_active:
            if address in self._states:
                del self._states[address]
                self.reclaims += 1
            return
        self._states[address] = NeuronState(**vars(state))
        self.high_watermark = max(self.high_watermark, len(self._states))

    def clear(self) -> None:
        self._states.clear()

    def profile(self) -> dict[str, int]:
        return {
            "live_entries": len(self._states),
            "high_watermark": self.high_watermark,
            "touches": self.touches,
            "reclaims": self.reclaims,
        }
