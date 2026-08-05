import pytest
import torch
from torch.nn import functional as functional

from eventscnn.hardware import event_scatter_conv2d


@pytest.mark.parametrize(
    ("shape", "kernel", "stride", "padding"),
    [
        ((1, 2, 5, 6), (3, 2, 3, 3), 1, 1),
        ((2, 2, 7, 8), (4, 2, 3, 3), 2, 1),
        ((1, 1, 6, 7), (2, 1, 5, 5), 2, 2),
    ],
)
def test_seeded_sparse_scatter_equals_dense(shape, kernel, stride, padding) -> None:
    generator = torch.Generator().manual_seed(13)
    counts = torch.randint(0, 3, shape, generator=generator).float()
    counts *= torch.rand(shape, generator=generator) > 0.75
    weights = torch.randint(-3, 4, kernel, generator=generator).float()
    expected = functional.conv2d(counts, weights, stride=stride, padding=padding)
    actual = event_scatter_conv2d(counts, weights, stride=stride, padding=padding)
    assert torch.equal(actual, expected)


def test_repeated_and_border_events_use_shared_kernel() -> None:
    counts = torch.zeros((1, 1, 4, 4))
    counts[0, 0, 0, 0] = 3
    counts[0, 0, 3, 3] = 2
    weights = torch.arange(9).reshape(1, 1, 3, 3).float()
    expected = functional.conv2d(counts, weights, padding=1)
    actual = event_scatter_conv2d(counts, weights, padding=1)
    assert torch.equal(actual, expected)


def test_rejects_fractional_or_negative_event_counts() -> None:
    weights = torch.ones((1, 1, 1, 1))
    with pytest.raises(ValueError, match="non-negative integers"):
        event_scatter_conv2d(torch.tensor([[[[0.5]]]]), weights)
    with pytest.raises(ValueError, match="non-negative integers"):
        event_scatter_conv2d(torch.tensor([[[[-1.0]]]]), weights)
