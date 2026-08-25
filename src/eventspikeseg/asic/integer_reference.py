"""Bit-oriented lazy PLIF and sparse-state primitives for RTL comparison."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from .contracts import BIN_TAG_MODULUS, BIN_US
from .fixed_point import ASIC_FORMATS, FixedFormat, round_shift_ties_away

REFERENCE_STEP_US = BIN_US


@dataclass
class NeuronState:
    """Persistent state owned by one logical PLIF neuron.

    ``last_bin_tag`` is a compact global 5 ms-bin index, not a microsecond timestamp.
    It lets touched-neuron runtime reproduce training's lazy ``beta**delta_bins`` leak
    without updating untouched neurons every bin.
    """

    membrane: int = 0
    adaptation_age: int = -1
    adaptation_amplitude: int = 0
    last_bin_tag: int = -1

    @property
    def adaptation_active(self) -> bool:
        return self.adaptation_age >= 0 or self.adaptation_amplitude != 0


@dataclass(frozen=True)
class PLIFResult:
    membrane: int
    spike: int
    candidate: int
    elapsed_bins: int
    retention_q: int


class IntegerPLIF:
    """Fixed-point touched-neuron PLIF matching the trained 5 ms lazy-time rule."""

    def __init__(
        self,
        *,
        membrane_format: FixedFormat = ASIC_FORMATS["membrane"],
        beta_format: FixedFormat = ASIC_FORMATS["beta"],
    ) -> None:
        self.membrane_format = membrane_format
        self.beta_format = beta_format

    def retention_for_bins(self, beta_q: int, elapsed_bins: int) -> int:
        """Return fixed-point ``beta**elapsed_bins`` using RTL-equivalent rounding.

        The first RTL baseline performs the same operation iteratively, one beta multiply
        per elapsed bin.  A later LUT/exponentiation accelerator may replace it only after
        bit-exact equivalence is demonstrated.
        """

        if elapsed_bins < 0:
            raise ValueError("elapsed_bins must be non-negative")
        beta_q = self.beta_format.saturate(int(beta_q))
        retention_q = self.beta_format.scale
        for _ in range(int(elapsed_bins)):
            retention_q = self.beta_format.saturate(
                round_shift_ties_away(
                    retention_q * beta_q, self.beta_format.fractional_bits
                )
            )
        return retention_q

    @staticmethod
    def elapsed_bins(current_bin_tag: int, last_bin_tag: int) -> int:
        """Return modular 5 ms-bin distance for a stored sparse entry."""

        if current_bin_tag < 0:
            raise ValueError("current_bin_tag must be non-negative")
        if last_bin_tag < 0:
            # A missing/reset state contains zero membrane and inactive adaptation.
            # One is the natural first-touch step; larger elapsed time is irrelevant
            # because beta**n * 0 remains exactly zero.
            return 1
        delta = (int(current_bin_tag) - int(last_bin_tag)) % BIN_TAG_MODULUS
        return delta

    @staticmethod
    def triangular_age_increment(elapsed_bins: int) -> int:
        """Return the lazy equivalent of elapsed adaptation-age advancement."""

        if elapsed_bins < 0:
            raise ValueError("elapsed_bins must be non-negative")
        return int(elapsed_bins)

    def step(
        self,
        *,
        membrane_q: int,
        current_q: int,
        beta_q: int,
        threshold_q: int,
        elapsed_bins: int = 1,
    ) -> PLIFResult:
        """Advance one touched logical neuron at the current 5 ms bin."""

        retention_q = self.retention_for_bins(beta_q, elapsed_bins)
        leaked = round_shift_ties_away(
            int(membrane_q) * retention_q, self.beta_format.fractional_bits
        )
        candidate = self.membrane_format.saturate(leaked + int(current_q))
        spike = int(candidate >= int(threshold_q))
        membrane = self.membrane_format.saturate(
            candidate - (int(threshold_q) if spike else 0)
        )
        return PLIFResult(
            membrane=membrane,
            spike=spike,
            candidate=candidate,
            elapsed_bins=int(elapsed_bins),
            retention_q=retention_q,
        )

    def touch_state(
        self,
        state: NeuronState,
        *,
        current_bin_tag: int,
        current_q: int,
        beta_q: int,
        threshold_q: int,
    ) -> tuple[NeuronState, PLIFResult]:
        """Apply one complete touched-neuron update and refresh its compact bin tag."""

        elapsed = self.elapsed_bins(current_bin_tag, state.last_bin_tag)
        result = self.step(
            membrane_q=state.membrane,
            current_q=current_q,
            beta_q=beta_q,
            threshold_q=threshold_q,
            elapsed_bins=elapsed,
        )
        age = state.adaptation_age
        if age >= 0:
            age += self.triangular_age_increment(elapsed)
        new_state = NeuronState(
            membrane=result.membrane,
            adaptation_age=age,
            adaptation_amplitude=state.adaptation_amplitude,
            last_bin_tag=int(current_bin_tag) % BIN_TAG_MODULUS,
        )
        return new_state, result


class ActorLocalStateStore:
    """Zero-default reference for one actor's directly addressed local state."""

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
        copied = NeuronState(**vars(state))
        if copied.last_bin_tag >= 0:
            copied.last_bin_tag %= BIN_TAG_MODULUS
        self._states[address] = copied
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
