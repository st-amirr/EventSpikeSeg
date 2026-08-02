import pytest
import torch

from eventscnn.config import EventBinningConfig
from eventscnn.events import Event, bin_events, synthetic_events


def test_canonical_shape_polarity_repetition_and_boundaries() -> None:
    events = [
        Event(0, 0, 0, False),
        Event(999, 239, 179, True),
        Event(1_000, 3, 4, True),
        Event(1_000, 3, 4, True),
    ]
    bins = bin_events(events, num_bins=2)
    assert bins.shape == (2, 1, 2, 180, 240)
    assert bins.dtype == torch.int32
    assert bins[0, 0, 0, 0, 0] == 1
    assert bins[0, 0, 1, 179, 239] == 1
    assert bins[1, 0, 1, 4, 3] == 2
    assert bins.sum() == 4


def test_configurable_duration_and_deterministic_fixture() -> None:
    config = EventBinningConfig(bin_duration_us=500)
    events = synthetic_events(steps=3, bin_duration_us=500)
    first = bin_events(events, config, num_bins=3)
    second = bin_events(events, config, num_bins=3)
    assert torch.equal(first, second)
    assert first.sum(dim=(1, 2, 3, 4)).tolist() == [3, 3, 3]


def test_empty_input_requires_explicit_window() -> None:
    with pytest.raises(ValueError):
        bin_events([])
    assert bin_events([], num_bins=2).shape == (2, 1, 2, 180, 240)


def test_rejects_invalid_events_instead_of_silently_dropping() -> None:
    with pytest.raises(ValueError, match="coordinate"):
        bin_events([Event(0, 240, 0, True)], num_bins=1)
    with pytest.raises(ValueError, match="time window"):
        bin_events([Event(1_000, 0, 0, True)], num_bins=1)
