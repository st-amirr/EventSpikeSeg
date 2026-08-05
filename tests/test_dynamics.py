import torch

from eventscnn.model import LIFConfig
from eventscnn.model import HardwareLIF


def test_f_inst_selects_highest_channel_and_decrements_candidate_loser() -> None:
    neuron = HardwareLIF(
        2,
        LIFConfig(
            beta_shift=1,
            threshold=1.0,
            competitor_decrement=0.25,
            f_long_enabled=False,
        ),
    )
    spikes = neuron(torch.tensor([[[[2.0]], [[3.0]]]]))
    assert spikes.flatten().tolist() == [0.0, 1.0]
    assert torch.allclose(neuron.membrane.flatten(), torch.tensor([1.75, 2.0]))


def test_f_inst_tie_uses_lowest_channel_priority() -> None:
    neuron = HardwareLIF(3, LIFConfig(f_long_enabled=False))
    spikes = neuron(torch.full((1, 3, 1, 1), 2.0))
    assert spikes.flatten().tolist() == [1.0, 0.0, 0.0]


def test_f_inst_ablation_allows_all_candidates() -> None:
    neuron = HardwareLIF(
        2,
        LIFConfig(f_inst_enabled=False, f_long_enabled=False),
    )
    spikes = neuron(torch.full((1, 2, 1, 1), 2.0))
    assert spikes.flatten().tolist() == [1.0, 1.0]


def test_f_inst_ablation_preserves_subthreshold_surrogate_gradient() -> None:
    neuron = HardwareLIF(1, LIFConfig(f_inst_enabled=False, f_long_enabled=False))
    current = torch.tensor([[[[0.5]]]], requires_grad=True)
    neuron(current).sum().backward()
    assert current.grad is not None
    assert current.grad.item() > 0.0


def test_homeostasis_rises_after_spike_then_decays_toward_zero() -> None:
    neuron = HardwareLIF(
        1,
        LIFConfig(
            beta_shift=1,
            adaptation_increment=0.5,
            adaptation_decay=0.25,
            f_inst_enabled=False,
        ),
    )
    assert neuron(torch.tensor([[[[2.0]]]])).item() == 1.0
    assert neuron.adaptation.item() == 0.5
    assert neuron(torch.zeros((1, 1, 1, 1))).item() == 0.0
    assert neuron.adaptation.item() == 0.25
    neuron(torch.zeros((1, 1, 1, 1)))
    assert neuron.adaptation.item() == 0.0


def test_homeostasis_detects_one_spike_on_a_large_sparse_feature_map() -> None:
    neuron = HardwareLIF(
        1,
        LIFConfig(
            threshold=0.25,
            adaptation_increment=0.0625,
            adaptation_decay=0.03125,
            f_inst_enabled=False,
        ),
    )
    current = torch.zeros((1, 1, 90, 120))
    current[0, 0, 40, 50] = 1.0
    neuron(current)
    assert neuron.adaptation.item() == 0.0625
    neuron.membrane.zero_()
    neuron(torch.zeros_like(current))
    assert neuron.adaptation.item() == 0.03125


def test_reset_clears_membrane_and_adaptation() -> None:
    neuron = HardwareLIF(1, LIFConfig(adaptation_increment=0.5))
    neuron(torch.tensor([[[[2.0]]]]))
    neuron.reset()
    assert neuron.membrane.numel() == 0
    assert neuron.adaptation.item() == 0.0
