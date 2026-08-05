import torch

from eventscnn.model import ARCHITECTURE_PRESETS, DEFAULT_ARCHITECTURE, build_model


def test_all_presets_produce_class_spike_maps() -> None:
    sequence = torch.zeros((2, 1, 6, 32, 32))
    sequence[:, :, 0, 8:16, 8:16] = 1.0
    for name in ARCHITECTURE_PRESETS:
        model = build_model(name)
        model.eval()
        model.reset()
        outputs = model(sequence)
        assert outputs["segmentation_spikes"].shape == (2, 1, 6, 32, 32)
        assert outputs["segmentation_logits"].shape == (1, 6, 32, 32)
        assert model.stem.conv.in_channels == 6
        assert model.parameter_count() > 0


def test_default_architecture_has_auxiliary_head_and_gradients() -> None:
    torch.manual_seed(17)
    model = build_model(DEFAULT_ARCHITECTURE)
    sequence = torch.rand((2, 1, 6, 32, 32))
    outputs = model(sequence)
    assert "auxiliary_logits" in outputs
    loss = outputs["segmentation_logits"].square().mean()
    loss.backward()
    assert model.stem.conv.weight.grad is not None
