"""Timestamped event fixtures and fixed-duration TNCHW binning."""

from dataclasses import dataclass
from typing import Iterable, List, Optional

import torch
from torch import Tensor

from .config import EventBinningConfig


@dataclass(frozen=True, order=True)
class Event:
    """One timestamped contrast event; polarity false is OFF and true is ON."""

    timestamp_us: int
    x: int
    y: int
    polarity: bool
    batch: int = 0


def bin_events(
    events: Iterable[Event],
    config: EventBinningConfig = EventBinningConfig(),
    *,
    num_bins: Optional[int] = None,
    batch_size: Optional[int] = None,
    start_us: int = 0,
) -> Tensor:
    """Return integer counts with shape ``[T,N,2,H,W]``.

    Bins are half-open intervals beginning at ``start_us``. Events outside the selected
    time window or image are rejected, preventing silent software/hardware divergence.
    """

    materialized = list(events)
    if start_us < 0:
        raise ValueError("start_us cannot be negative")
    if any(event.timestamp_us < start_us for event in materialized):
        raise ValueError("event timestamp precedes start_us")
    inferred_bins = (
        max((event.timestamp_us - start_us) // config.bin_duration_us for event in materialized)
        + 1
        if materialized
        else 0
    )
    if num_bins is None:
        num_bins = inferred_bins
    if num_bins <= 0:
        raise ValueError("num_bins must be positive, especially for empty input")
    inferred_batch = max((event.batch for event in materialized), default=-1) + 1
    if batch_size is None:
        batch_size = max(inferred_batch, 1)
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    output = torch.zeros(
        (num_bins, batch_size, 2, config.height, config.width), dtype=torch.int32
    )
    for event in materialized:
        if not (0 <= event.x < config.width and 0 <= event.y < config.height):
            raise ValueError(f"event coordinate out of bounds: ({event.x}, {event.y})")
        if not (0 <= event.batch < batch_size):
            raise ValueError(f"event batch out of bounds: {event.batch}")
        timestep = (event.timestamp_us - start_us) // config.bin_duration_us
        if timestep >= num_bins:
            raise ValueError("event lies beyond the configured time window")
        channel = 1 if event.polarity else 0
        output[timestep, event.batch, channel, event.y, event.x] += 1
    return output


def synthetic_events(
    *,
    steps: int = 4,
    bin_duration_us: int = 1_000,
    x0: int = 20,
    y0: int = 30,
) -> List[Event]:
    """Generate a deterministic diagonal ON target with an OFF trailing edge."""

    if steps <= 0:
        raise ValueError("steps must be positive")
    events: List[Event] = []
    for step in range(steps):
        timestamp = step * bin_duration_us + bin_duration_us // 2
        x = x0 + step
        y = y0 + step
        events.extend(
            [
                Event(timestamp, x, y, True),
                Event(timestamp, x, y, True),
                Event(timestamp, max(0, x - 1), y, False),
            ]
        )
    return events
