import torch

from eventscnn.config import LIFConfig, LayerConfig
from eventscnn.events import bin_events, synthetic_events
from eventscnn.models import ConvLIFBlock


def _block() -> ConvLIFBlock:
    block = ConvLIFBlock(
        LayerConfig(2, 2, (3, 3), (1, 1), (1, 1)),
        LIFConfig(threshold=1.0, f_inst_enabled=True, f_long_enabled=False),
    )
    with torch.no_grad():
        block.conv.weight.zero_()
        block.conv.weight[0, 1, 1, 1] = 1.0
        block.conv.weight[1, 1, 1, 1] = 0.5
    return block


def test_synthetic_events_to_deterministic_conv_lif_spikes() -> None:
    sequence = bin_events(synthetic_events(steps=3), num_bins=3)
    block = _block()
    first = block(sequence)
    block.reset()
    second = block(sequence)
    assert first.shape == (3, 1, 2, 180, 240)
    assert torch.equal(first, second)
    assert first[:, :, 0].sum() == 3
    assert first[:, :, 1].sum() == 0
    assert block.conv.bias is None


def test_reset_clears_subthreshold_membrane() -> None:
    block = _block()
    sequence = torch.zeros((1, 1, 2, 2, 2))
    sequence[0, 0, 1, 0, 0] = 1
    block(sequence)
    assert block.neuron.membrane.numel() > 0
    block.reset()
    assert block.neuron.membrane.numel() == 0
