import torch

from eventscnn.model import FINAL_ARCHITECTURE_NAME, build_model
from eventscnn.model_components import HardwareLIF, LIFConfig, ParametricLIF
from eventscnn.top_five_models import (
    TOP_FIVE_PRESETS,
    build_top_five_model,
)
from eventscnn.top_ten_models import TOP_TEN_PRESETS, build_top_ten_model


def _sample_sequence() -> torch.Tensor:
    sequence = torch.zeros((4, 1, 6, 16, 16))
    sequence[:, :, 0, 4:8, 4:8] = 1.0
    return sequence


def test_top_ten_presets_remain_buildable() -> None:
    sequence = _sample_sequence()
    for name in TOP_TEN_PRESETS:
        model = build_top_ten_model(name)
        model.eval()
        model.reset()
        outputs = model(sequence)
        assert outputs["segmentation_spikes"].shape == (4, 1, 6, 16, 16)
        assert outputs["segmentation_logits"].shape == (1, 6, 16, 16)


def test_active_top_five_share_winning_dynamics_and_are_buildable() -> None:
    expected = {
        "f01_base24_multiscale",
        "f02_wide32_multiscale",
        "f03_early5x5_multiscale",
        "f04_deep4_dilated",
        "f05_compact16_dilated",
    }
    assert set(TOP_FIVE_PRESETS) == expected
    sequence = _sample_sequence()
    for name, architecture in TOP_FIVE_PRESETS.items():
        assert architecture.neuron_kind == "plif"
        assert architecture.learnable_threshold
        assert architecture.f_inst_enabled
        assert architecture.f_inst_scope == "stem"
        assert architecture.inhibition_kind == "peer_membrane"
        assert architecture.f_long_enabled
        assert architecture.f_long_scope == "encoder"
        assert architecture.homeostasis_kind == "triangular_threshold"
        assert architecture.output_f_inst_enabled
        model = build_top_five_model(name)
        model.eval()
        model.reset()
        outputs = model(sequence)
        assert outputs["segmentation_spikes"].shape == (4, 1, 6, 16, 16)
        plif = [module for module in model.modules() if isinstance(module, ParametricLIF)]
        assert plif
        assert all(module.threshold_logit is not None for module in plif)


def test_top_five_structural_variations_cover_width_kernel_and_depth() -> None:
    assert TOP_FIVE_PRESETS["f01_base24_multiscale"].channel_schedule == (24, 48, 96)
    assert TOP_FIVE_PRESETS["f02_wide32_multiscale"].channel_schedule == (32, 64, 128)
    early = TOP_FIVE_PRESETS["f03_early5x5_multiscale"]
    assert early.stem_kernel_size == 5
    assert early.first_block_kernel_size == 5
    deep = TOP_FIVE_PRESETS["f04_deep4_dilated"]
    assert deep.channel_schedule == (24, 48, 96, 128)
    assert deep.context == "dilated"
    compact = TOP_FIVE_PRESETS["f05_compact16_dilated"]
    assert compact.channel_schedule == (16, 32, 64)

    early_model = build_top_five_model("f03_early5x5_multiscale")
    assert early_model.stem.conv.kernel_size == (5, 5)
    assert early_model.enc1.depthwise is not None
    assert early_model.enc1.depthwise.conv.kernel_size == (5, 5)

    deep_model = build_top_five_model("f04_deep4_dilated")
    deep_model.eval()
    deep_model.reset()
    deep_outputs = deep_model(_sample_sequence())
    assert "enc4_spikes" in deep_outputs
    assert deep_outputs["enc4_spikes"].shape[-2:] == (2, 2)

def test_rate_homeostasis_v2_parameters_still_receive_gradients() -> None:
    neuron = ParametricLIF(
        2,
        LIFConfig(
            threshold=0.5,
            learnable_threshold=True,
            f_long_enabled=True,
            homeostasis_kind="rate",
            adaptation_tau_init=4.0,
        ),
    )
    loss = 0.0
    for _ in range(4):
        loss = loss + neuron(torch.full((1, 2, 2, 2), 0.6)).sum()
    loss.backward()
    assert neuron.beta_logit.grad is not None
    assert neuron.threshold_logit is not None and neuron.threshold_logit.grad is not None
    assert neuron.adaptation_tau_logit is not None
    assert neuron.adaptation_tau_logit.grad is not None
    assert neuron.adaptation_strength_logit is not None
    assert neuron.adaptation_strength_logit.grad is not None
    assert neuron.target_rate_logit is not None
    assert neuron.target_rate_logit.grad is not None


def test_triangular_threshold_adaptation_is_local_and_learnable() -> None:
    neuron = ParametricLIF(
        2,
        LIFConfig(
            threshold=0.5,
            learnable_threshold=True,
            f_long_enabled=True,
            homeostasis_kind="triangular_threshold",
            threshold_adaptation_strength_init=0.3,
            adaptation_duration_init=4.0,
        ),
    )
    # Only the top-left neuron crosses threshold. The threshold-adaptation penalty must remain
    # spatial rather than globally changing the entire feature-map threshold.
    current = torch.zeros((1, 2, 2, 2))
    current[:, 0, 0, 0] = 0.8
# Only the top-left neuron crosses threshold. The threshold-adaptation penalty must remain
    # spatial rather than globally changing the entire feature-map threshold.
    current = torch.zeros((1, 2, 2, 2))
    current[:, 0, 0, 0] = 0.8
    loss = neuron(current).sum()
    for _ in range(3):
        loss = loss + neuron(torch.zeros_like(current)).sum()
    assert neuron.threshold_adaptation_penalty.shape == (1, 1, 2, 2)
    assert neuron.threshold_adaptation_penalty[0, 0, 0, 0].detach().item() > 0.0
    assert neuron.threshold_adaptation_penalty[0, 0, 1, 1].detach().item() == 0.0
    loss.backward()
    assert neuron.threshold_adaptation_strength_logit is not None and neuron.threshold_adaptation_strength_logit.grad is not None
    assert neuron.adaptation_duration_logit is not None and neuron.adaptation_duration_logit.grad is not None


def test_peer_membrane_inhibition_reduces_peers_without_hard_gating() -> None:
    neuron = HardwareLIF(
        3,
        LIFConfig(
            threshold=0.5,
            f_inst_enabled=True,
            inhibition_kind="peer_membrane",
            inhibition_strength_init=0.5,
            f_long_enabled=False,
        ),
    )
    current = torch.tensor([[[[0.8]], [[0.7]], [[0.2]]]], requires_grad=True)
    spikes = neuron(current)
    # Time-binned adaptation preserves both simultaneous suprathreshold features.
    assert spikes.flatten().tolist() == [1.0, 1.0, 0.0]
    # The non-spiking peer is inhibited below its uninhibited 0.2 membrane value.
    assert neuron.membrane[0, 2, 0, 0].detach().item() < 0.2
    neuron(torch.full((1, 3, 1, 1), 0.1)).sum().backward()
    assert neuron.inhibition_strength_logit is not None and neuron.inhibition_strength_logit.grad is not None



def test_winner_peer_inhibition_keeps_one_winner_and_inhibits_peers() -> None:
    neuron = HardwareLIF(
        3,
        LIFConfig(
            threshold=0.5,
            f_inst_enabled=True,
            inhibition_kind="winner_peer",
            inhibition_strength_init=0.5,
            f_long_enabled=False,
        ),
    )
    current = torch.tensor([[[[0.8]], [[0.7]], [[0.2]]]], requires_grad=True)
    spikes = neuron(current)
    assert spikes.flatten().tolist() == [1.0, 0.0, 0.0]
    # Winner resets; both retinotopic peers receive the UInst-like decrement.
    assert neuron.membrane[0, 1, 0, 0].detach().item() < 0.7
    assert neuron.membrane[0, 2, 0, 0].detach().item() < 0.2
    neuron(torch.full((1, 3, 1, 1), 0.1)).sum().backward()
    assert neuron.inhibition_strength_logit is not None and neuron.inhibition_strength_logit.grad is not None

def test_legacy_grouped_top_two_competition_is_preserved() -> None:
    neuron = HardwareLIF(
        8,
        LIFConfig(
            threshold=0.5,
            f_inst_enabled=True,
            f_inst_top_k=2,
            f_inst_group_size=4,
            f_long_enabled=False,
        ),
    )
    current = torch.tensor(
        [[[[0.6]], [[0.9]], [[0.7]], [[0.8]], [[0.55]], [[0.75]], [[0.95]], [[0.65]]]]
    )
    spikes = neuron(current)
    assert int(spikes.sum()) == 4


def test_legacy_t_thresh_behavior_is_preserved() -> None:
    neuron = HardwareLIF(
        1,
        LIFConfig(
            threshold=0.5,
            f_long_enabled=True,
            homeostasis_kind="legacy",
            adaptation_increment=0.1,
            adaptation_decay=0.05,
            t_thresh_steps=2,
        ),
    )
    neuron(torch.tensor([[[[0.6]]]]))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.1]))
    neuron(torch.zeros((1, 1, 1, 1)))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.1]))
    neuron(torch.zeros((1, 1, 1, 1)))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.05]))


def test_final_model_contains_only_canonical_architecture() -> None:
    model = build_model()
    assert model.architecture.name == FINAL_ARCHITECTURE_NAME
    assert FINAL_ARCHITECTURE_NAME == "v10_fpga_hybrid"


def test_canonical_v10_accepts_round_one_v10_state_dict() -> None:
    archived = build_top_ten_model("v10_fpga_hybrid")
    canonical = build_model()
    canonical.load_state_dict(archived.state_dict(), strict=True)
    assert list(canonical.state_dict()) == list(archived.state_dict())


def test_hidden_peer_membrane_inhibition_can_warm_up_without_disabling_class_wta() -> None:
    model = build_top_five_model("f01_base24_multiscale")
    model.set_competition_enabled(True)
    model.set_hidden_inhibition_enabled(False)
    inhibition_modules = [
        module
        for module in model.modules()
        if isinstance(module, HardwareLIF)
        and module.config.inhibition_kind in {"peer_membrane", "winner_peer"}
    ]
    assert inhibition_modules
    assert all(not module.competition_enabled for module in inhibition_modules)
    output_modules = [
        module
        for module in model.head.modules()
        if isinstance(module, HardwareLIF) and module.config.inhibition_kind == "gate"
    ]
    assert output_modules
    assert all(module.competition_enabled for module in output_modules)
