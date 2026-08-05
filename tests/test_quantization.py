import torch

from eventscnn.hardware import (
    IntegerFormat,
    arithmetic_shift_right,
    integer_lif_step,
    quantize,
    saturate,
    update_integer_adaptation,
)


def test_rounding_clipping_and_signed_ranges() -> None:
    fmt = IntegerFormat(8)
    values = torch.tensor([-200.0, -1.5, -0.5, 0.5, 1.5, 200.0])
    assert quantize(values, scale=1, integer_format=fmt).tolist() == [
        -128,
        -2,
        -1,
        1,
        2,
        127,
    ]
    assert saturate(torch.tensor([-1, 300]), IntegerFormat(8, signed=False)).tolist() == [0, 255]


def test_arithmetic_shift_and_integer_lif_ordering() -> None:
    assert arithmetic_shift_right(torch.tensor([-5, 5]), 1).tolist() == [-3, 2]
    membrane = torch.tensor([[[[8]], [[8]]]])
    current = torch.tensor([[[[4]], [[5]]]])
    updated, spikes = integer_lif_step(
        membrane,
        current,
        threshold=torch.tensor([9, 9]),
        adaptation=torch.tensor([0, 0]),
        beta_shift=2,
        competitor_decrement=2,
    )
    assert spikes.flatten().tolist() == [0, 1]
    assert updated.flatten().tolist() == [8, 2]


def test_integer_saturation_reset_and_adaptation() -> None:
    updated, spikes = integer_lif_step(
        torch.tensor([[[[127]]]]),
        torch.tensor([[[[100]]]]),
        threshold=torch.tensor([100]),
        adaptation=torch.tensor([0]),
        beta_shift=1,
        membrane_format=IntegerFormat(8),
        competition=False,
    )
    assert spikes.item() == 1
    assert updated.item() == 27
    adaptation = update_integer_adaptation(
        torch.tensor([5]), torch.tensor([3]), decay=2, increment=4
    )
    assert adaptation.item() == 15


def test_positive_fixed_point_lif_matches_scaled_float_equation() -> None:
    membrane = torch.tensor([[[[64]]]])
    current = torch.tensor([[[[32]]]])
    updated, spikes = integer_lif_step(
        membrane,
        current,
        threshold=torch.tensor([256]),
        adaptation=torch.tensor([0]),
        beta_shift=4,
    )
    assert updated.item() == int(64 * 0.9375 + 32)
    assert spikes.item() == 0
