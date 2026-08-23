"""Streaming 5 ms FPGA runtime contract for the canonical DSEC deployment.

Training remains unchanged: DSEC is represented as fixed physical-time updates and
neuron populations use touched-neuron lazy state.  Live hardware therefore bins raw
camera events into consecutive 5 ms windows, propagates each completed bin through the
full deployed graph before accepting it for retirement, and keeps PLIF state persistent
between bins.  A prediction is emitted after a configurable number of completed bins;
the default is ten bins (50 ms) to match training/readout semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Iterable, Iterator, Sequence

BIN_US = 5_000
STEP_US = BIN_US  # compatibility name: one trained neuron-time quantum
DEFAULT_PREDICTION_BINS = 10
PREDICTION_BINS = DEFAULT_PREDICTION_BINS
RECORD_US = BIN_US * DEFAULT_PREDICTION_BINS  # training/default prediction horizon
STEPS_PER_RECORD = DEFAULT_PREDICTION_BINS
DEFAULT_TARGET_UTILIZATION = 0.80
HARD_MAX_UTILIZATION = 1.0
BIN_TAG_WIDTH = 24
BIN_TAG_MODULUS = 1 << BIN_TAG_WIDTH


@dataclass(frozen=True)
class RuntimeTiming:
    """Clock/budget contract for one end-to-end 5 ms input bin."""

    clock_hz: int
    bin_us: int = BIN_US
    prediction_bins: int = DEFAULT_PREDICTION_BINS
    target_utilization: float = DEFAULT_TARGET_UTILIZATION

    def __post_init__(self) -> None:
        if self.clock_hz <= 0:
            raise ValueError("clock_hz must be positive")
        if self.bin_us <= 0:
            raise ValueError("bin_us must be positive")
        if self.prediction_bins <= 0:
            raise ValueError("prediction_bins must be positive")
        if not 0.0 < self.target_utilization <= HARD_MAX_UTILIZATION:
            raise ValueError("target_utilization must be in (0, 1]")

    @property
    def hard_cycle_budget(self) -> int:
        """Maximum cycles per bin for sustained real-time execution."""

        return floor(self.clock_hz * self.bin_us / 1_000_000)

    @property
    def target_cycle_budget(self) -> int:
        """Preferred cycle budget including the configured timing headroom."""

        return floor(self.hard_cycle_budget * self.target_utilization)

    @property
    def prediction_period_us(self) -> int:
        return self.bin_us * self.prediction_bins

    @property
    def prediction_rate_hz(self) -> float:
        return 1_000_000.0 / self.prediction_period_us

    @property
    def required_bin_rate_hz(self) -> float:
        return 1_000_000.0 / self.bin_us

    def report(self, cycles_used: int) -> dict[str, float | int | bool]:
        if cycles_used <= 0:
            raise ValueError("cycles_used must be positive")
        hard = self.hard_cycle_budget
        utilization = cycles_used / hard
        headroom = hard / cycles_used
        compute_us = cycles_used / self.clock_hz * 1_000_000.0
        return {
            "clock_hz": self.clock_hz,
            "bin_us": self.bin_us,
            "cycles_used": cycles_used,
            "hard_cycle_budget": hard,
            "target_cycle_budget": self.target_cycle_budget,
            "compute_us": compute_us,
            "utilization": utilization,
            "throughput_headroom": headroom,
            "hard_realtime_met": utilization <= HARD_MAX_UTILIZATION,
            "target_utilization_met": utilization <= self.target_utilization,
            "slack_cycles": hard - cycles_used,
            "slack_us": self.bin_us - compute_us,
            "prediction_bins": self.prediction_bins,
            "prediction_period_us": self.prediction_period_us,
            "prediction_rate_hz": self.prediction_rate_hz,
            "required_bin_rate_hz": self.required_bin_rate_hz,
        }


@dataclass(frozen=True)
class ScheduledEvent:
    """Sparse camera event assigned to one physical 5 ms runtime bin."""

    bin_index: int
    channel: int
    y: int
    x: int
    multiplicity: int = 1

    def __post_init__(self) -> None:
        if self.bin_index < 0:
            raise ValueError("bin_index must be non-negative")
        if self.channel < 0 or self.y < 0 or self.x < 0:
            raise ValueError("channel/y/x must be non-negative")
        if self.multiplicity < 1:
            raise ValueError("multiplicity must be positive")

    @property
    def slice_index(self) -> int:
        """Compatibility view inside the default ten-bin prediction window."""

        return self.bin_index % DEFAULT_PREDICTION_BINS


@dataclass(frozen=True)
class ActorStep:
    """One bin-major scheduling slot: one deployed actor for one input bin."""

    actor_index: int
    actor_name: str
    bin_index: int


# Compatibility name retained for imports created during the earlier record-major iteration.
LayerStep = ActorStep


class StreamingBinRuntime:
    """Reference scheduler for end-to-end 5 ms streaming inference."""

    bin_us = BIN_US
    step_us = BIN_US
    prediction_bins = DEFAULT_PREDICTION_BINS
    record_us = RECORD_US
    steps_per_record = DEFAULT_PREDICTION_BINS
    bin_tag_width = BIN_TAG_WIDTH

    def __init__(
        self,
        *,
        prediction_bins: int = DEFAULT_PREDICTION_BINS,
        target_utilization: float = DEFAULT_TARGET_UTILIZATION,
    ) -> None:
        if prediction_bins <= 0:
            raise ValueError("prediction_bins must be positive")
        if not 0.0 < target_utilization <= HARD_MAX_UTILIZATION:
            raise ValueError("target_utilization must be in (0, 1]")
        self.prediction_bins = int(prediction_bins)
        self.target_utilization = float(target_utilization)

    @staticmethod
    def bin_for_timestamp(timestamp_us: int, *, stream_start_us: int) -> int:
        """Map a raw timestamp onto the global 5 ms hardware bin index."""

        delta = int(timestamp_us) - int(stream_start_us)
        if delta < 0:
            raise ValueError("timestamp precedes stream_start_us")
        return delta // BIN_US

    @staticmethod
    def bin_bounds(bin_index: int, *, stream_start_us: int) -> tuple[int, int]:
        if bin_index < 0:
            raise ValueError("bin_index must be non-negative")
        start = int(stream_start_us) + int(bin_index) * BIN_US
        return start, start + BIN_US

    @classmethod
    def schedule_bin_events(
        cls,
        events: Iterable[tuple[int, int, int, int] | tuple[int, int, int, int, int]],
        *,
        bin_index: int,
        stream_start_us: int,
    ) -> list[ScheduledEvent]:
        """Validate/encode sparse events belonging to one already-sealed 5 ms bin."""

        start, end = cls.bin_bounds(bin_index, stream_start_us=stream_start_us)
        scheduled: list[ScheduledEvent] = []
        for event in events:
            if len(event) == 4:
                timestamp_us, channel, y, x = event
                multiplicity = 1
            elif len(event) == 5:
                timestamp_us, channel, y, x, multiplicity = event
            else:  # pragma: no cover - defensive contract guard
                raise ValueError("event must contain 4 or 5 integer fields")
            if int(timestamp_us) < start or int(timestamp_us) >= end:
                raise ValueError("event is outside the selected 5 ms bin")
            scheduled.append(
                ScheduledEvent(
                    bin_index=int(bin_index),
                    channel=int(channel),
                    y=int(y),
                    x=int(x),
                    multiplicity=int(multiplicity),
                )
            )
        return scheduled

    @staticmethod
    def actor_schedule(actor_names: Sequence[str], *, bin_index: int) -> Iterator[ActorStep]:
        """Yield actor 0..N-1 for one bin before the next bin is committed."""

        if not actor_names:
            raise ValueError("at least one actor is required")
        if bin_index < 0:
            raise ValueError("bin_index must be non-negative")
        for actor_index, actor_name in enumerate(actor_names):
            yield ActorStep(
                actor_index=actor_index,
                actor_name=str(actor_name),
                bin_index=int(bin_index),
            )

    def prediction_due(self, completed_bins: int) -> bool:
        """Return true after every configured prediction window is complete."""

        if completed_bins < 0:
            raise ValueError("completed_bins must be non-negative")
        return completed_bins > 0 and completed_bins % self.prediction_bins == 0

    def timing(self, *, clock_hz: int) -> RuntimeTiming:
        return RuntimeTiming(
            clock_hz=clock_hz,
            bin_us=BIN_US,
            prediction_bins=self.prediction_bins,
            target_utilization=self.target_utilization,
        )


class FixedTimeRuntime(StreamingBinRuntime):
    """Compatibility wrapper for the old 50 ms helper API.

    The *active* hardware scheduler is :class:`StreamingBinRuntime`.  These methods
    remain only so existing preprocessing/tests can still split one known 50 ms record
    into ten 5 ms bins without implying record-major hardware execution.
    """

    @staticmethod
    def slice_for_timestamp(timestamp_us: int, *, record_start_us: int) -> int:
        delta = int(timestamp_us) - int(record_start_us)
        if delta < 0 or delta >= RECORD_US:
            raise ValueError("timestamp is outside the 50 ms record")
        return delta // BIN_US

    @classmethod
    def schedule_input_events(
        cls,
        events: Iterable[tuple[int, int, int, int] | tuple[int, int, int, int, int]],
        *,
        record_start_us: int,
    ) -> tuple[list[ScheduledEvent], ...]:
        bins: tuple[list[ScheduledEvent], ...] = tuple(
            [] for _ in range(DEFAULT_PREDICTION_BINS)
        )
        for event in events:
            timestamp_us = int(event[0])
            local_bin = cls.slice_for_timestamp(timestamp_us, record_start_us=record_start_us)
            bins[local_bin].extend(
                cls.schedule_bin_events(
                    [event],
                    bin_index=local_bin,
                    stream_start_us=record_start_us,
                )
            )
        return bins

    @staticmethod
    def validate_ten_slices(slices: Sequence[object]) -> None:
        if len(slices) != DEFAULT_PREDICTION_BINS:
            raise ValueError("training/default prediction windows contain ten 5 ms bins")

    @classmethod
    def layer_major_schedule(cls, layer_names: Sequence[str]) -> Iterator[ActorStep]:
        """Historical helper; do not use for active hardware scheduling."""

        for layer_index, layer_name in enumerate(layer_names):
            for slice_index in range(DEFAULT_PREDICTION_BINS):
                yield ActorStep(
                    actor_index=layer_index,
                    actor_name=str(layer_name),
                    bin_index=slice_index,
                )
