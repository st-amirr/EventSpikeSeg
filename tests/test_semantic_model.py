import torch

from eventscnn.model import FINAL_ARCHITECTURE_NAME, build_model
from eventscnn.model_components import HardwareLIF, LIFConfig, ParametricLIF
from eventscnn.top_five_models import TOP_FIVE_PRESETS, build_top_five_model
from eventscnn.top_ten_models import TOP_TEN_PRESETS, build_top_ten_model


def _sample_sequence() -> torch.Tensor:
    sequence = torch.zeros((2, 1, 6, 16, 16))
    sequence[:, :, 0, 4:8, 4:8] = 1.0
    return sequence


def test_top_ten_presets_remain_buildable() -> None:
    sequence = _sample_sequence()
    for name in TOP_TEN_PRESETS:
        model = build_top_ten_model(name)
        model.eval()
        model.reset()
        outputs = model(sequence)
        assert outputs["segmentation_spikes"].shape == (2, 1, 6, 16, 16)
        assert outputs["segmentation_logits"].shape == (1, 6, 16, 16)


def test_top_five_presets_use_plif_and_remain_buildable() -> None:
    sequence = _sample_sequence()
    for name, architecture in TOP_FIVE_PRESETS.items():
        assert architecture.neuron_kind == "plif"
        assert architecture.f_long_enabled
        assert architecture.t_thresh_steps > 0
        model = build_top_five_model(name)
        model.eval()
        model.reset()
        outputs = model(sequence)
        assert outputs["segmentation_spikes"].shape == (2, 1, 6, 16, 16)
        assert any(isinstance(module, ParametricLIF) for module in model.modules())


def test_final_model_contains_only_canonical_architecture() -> None:
    model = build_model()
    assert model.architecture.name == FINAL_ARCHITECTURE_NAME
    assert FINAL_ARCHITECTURE_NAME == "v10_fpga_hybrid"


def test_f_inst_selects_one_channel_per_position() -> None:
    neuron = HardwareLIF(
        3,
        LIFConfig(
            threshold=0.5,
            f_inst_enabled=True,
            f_long_enabled=False,
        ),
    )
    current = torch.tensor([[[[0.6]], [[0.9]], [[0.7]]]])
    spikes = neuron(current)
    assert spikes.flatten().tolist() == [0.0, 1.0, 0.0]


def test_f_long_holds_threshold_for_t_thresh_then_decays() -> None:
    neuron = HardwareLIF(
        1,
        LIFConfig(
            threshold=0.5,
            f_long_enabled=True,
            adaptation_increment=0.1,
            adaptation_decay=0.05,
            t_thresh_steps=2,
        ),
    )
    neuron(torch.tensor([[[[0.6]]]]))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.1]))
    assert neuron.threshold_timer.item() == 2
    neuron(torch.zeros((1, 1, 1, 1)))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.1]))
    assert neuron.threshold_timer.item() == 1
    neuron(torch.zeros((1, 1, 1, 1)))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.05]))
    assert neuron.threshold_timer.item() == 0


def test_plif_leak_is_trainable() -> None:
    neuron = ParametricLIF(1, LIFConfig(threshold=0.5, f_long_enabled=False))
    first = neuron(torch.tensor([[[[0.2]]]]))
    second = neuron(torch.tensor([[[[0.2]]]]))
    (first.sum() + second.sum()).backward()
    assert neuron.beta_logit.grad is not None


def test_canonical_v10_accepts_round_one_v10_state_dict() -> None:
    archived = build_top_ten_model("v10_fpga_hybrid")
    canonical = build_model()
    canonical.load_state_dict(archived.state_dict(), strict=True)
    assert list(canonical.state_dict()) == list(archived.state_dict())
