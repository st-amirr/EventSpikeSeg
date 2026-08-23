import pytest
import torch

from eventspikeseg.model import (
    EventSpikeSeg140k,
    EventSpikeSegXL,
    build_model,
)
from eventspikeseg.model_components import HardwareLIF, LIFConfig, ParametricLIF
from eventspikeseg.top_five_models import (
    TOP_FIVE_PRESETS,
    build_top_five_model,
)
from eventspikeseg.top_ten_models import TOP_TEN_PRESETS, build_top_ten_model


def _sample_sequence() -> torch.Tensor:
    sequence = torch.zeros((4, 1, 6, 16, 16))
    sequence[:, :, 0, 4:8, 4:8] = 1.0
    return sequence


def _timestamp_statistics(size: int, *, batch: int = 1) -> torch.Tensor:
    statistics = torch.zeros((batch, 6, size, size))
    statistics[:, :2, size // 4 : size // 2, size // 4 : size // 2] = 1.0
    statistics[:, 2:4] = 0.5
    statistics[:, 4:6] = 0.1
    return statistics


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
        assert architecture.inhibition_enabled
        assert architecture.inhibition_scope == "stem"
        assert architecture.inhibition_kind == "peer_membrane"
        assert architecture.threshold_adaptation_enabled
        assert architecture.threshold_adaptation_scope == "encoder"
        assert architecture.adaptation_kind == "triangular_threshold"
        assert architecture.output_competition_enabled
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

def test_rate_adaptation_v2_parameters_still_receive_gradients() -> None:
    neuron = ParametricLIF(
        2,
        LIFConfig(
            threshold=0.5,
            learnable_threshold=True,
            threshold_adaptation_enabled=True,
            adaptation_kind="rate",
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


@pytest.mark.parametrize("neuron_type", [HardwareLIF, ParametricLIF])
def test_elapsed_time_controls_physical_membrane_decay(neuron_type) -> None:
    neuron = neuron_type(
        1,
        LIFConfig(threshold=10.0, threshold_adaptation_enabled=False),
    )
    current = torch.tensor([[[[0.4]]]])
    neuron(current, elapsed_steps=0.0)
    neuron(torch.zeros_like(current), elapsed_steps=2.0)
    retention = (
        float(neuron.beta.detach())
        if isinstance(neuron, ParametricLIF)
        else neuron.config.beta
    )
    expected = 0.4 * retention**2
    assert neuron.membrane.item() == pytest.approx(expected, rel=1e-5)


def test_asynchronous_neuron_lazily_decays_only_when_touched() -> None:
    neuron = HardwareLIF(1, LIFConfig(threshold=10.0, threshold_adaptation_enabled=False))
    neuron.set_asynchronous_updates(True)
    first = torch.tensor([[[[0.4, 0.0]]]])
    left = torch.tensor([[[[True, False]]]])
    right = torch.tensor([[[[False, True]]]])
    neuron(first, elapsed_steps=0.0, update_mask=left)
    neuron(torch.zeros_like(first), elapsed_steps=2.0, update_mask=right)
    assert neuron.membrane[0, 0, 0, 0].item() == pytest.approx(0.4)
    neuron(torch.zeros_like(first), elapsed_steps=1.0, update_mask=left)
    assert neuron.membrane[0, 0, 0, 0].item() == pytest.approx(
        0.4 * neuron.config.beta**3,
        rel=1e-5,
    )


def test_triangular_threshold_adaptation_is_local_and_learnable() -> None:
    neuron = ParametricLIF(
        2,
        LIFConfig(
            threshold=0.5,
            learnable_threshold=True,
            threshold_adaptation_enabled=True,
            adaptation_kind="triangular_threshold",
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
    assert neuron.threshold_adaptation_strength_logit is not None
    assert neuron.threshold_adaptation_strength_logit.grad is not None
    assert neuron.adaptation_duration_logit is not None
    assert neuron.adaptation_duration_logit.grad is not None


def test_membrane_energy_has_finite_half_precision_gradient_at_zero() -> None:
    neuron = HardwareLIF(
        2,
        LIFConfig(
            threshold_adaptation_enabled=True,
            adaptation_kind="triangular_threshold",
        ),
    )
    candidate = torch.zeros((1, 2, 1, 1), dtype=torch.float16, requires_grad=True)
    energy = neuron._retinotopic_membrane_energy(candidate)
    energy.sum().backward()

    assert candidate.grad is not None
    assert torch.isfinite(candidate.grad).all()


def test_zero_mechanism_scale_bypasses_membrane_energy() -> None:
    neuron = HardwareLIF(
        2,
        LIFConfig(
            inhibition_enabled=True,
            inhibition_kind="peer_membrane",
            threshold_adaptation_enabled=True,
            adaptation_kind="triangular_threshold",
        ),
    )
    neuron.set_mechanism_scale(0.0)
    neuron._retinotopic_membrane_energy = pytest.fail  # type: ignore[method-assign]

    current = torch.zeros((1, 2, 1, 1), requires_grad=True)
    neuron(current).sum().backward()
    assert current.grad is not None


def test_peer_membrane_inhibition_reduces_peers_without_hard_gating() -> None:
    neuron = HardwareLIF(
        3,
        LIFConfig(
            threshold=0.5,
            inhibition_enabled=True,
            inhibition_kind="peer_membrane",
            inhibition_strength_init=0.5,
            threshold_adaptation_enabled=False,
        ),
    )
    current = torch.tensor([[[[0.8]], [[0.7]], [[0.2]]]], requires_grad=True)
    spikes = neuron(current)
    # Time-binned adaptation preserves both simultaneous suprathreshold features.
    assert spikes.flatten().tolist() == [1.0, 1.0, 0.0]
    # The non-spiking peer is inhibited below its uninhibited 0.2 membrane value.
    assert neuron.membrane[0, 2, 0, 0].detach().item() < 0.2
    neuron(torch.full((1, 3, 1, 1), 0.1)).sum().backward()
    assert neuron.inhibition_strength_logit is not None
    assert neuron.inhibition_strength_logit.grad is not None



def test_winner_peer_inhibition_keeps_one_winner_and_inhibits_peers() -> None:
    neuron = HardwareLIF(
        3,
        LIFConfig(
            threshold=0.5,
            inhibition_enabled=True,
            inhibition_kind="winner_peer",
            inhibition_strength_init=0.5,
            threshold_adaptation_enabled=False,
        ),
    )
    current = torch.tensor([[[[0.8]], [[0.7]], [[0.2]]]], requires_grad=True)
    spikes = neuron(current)
    assert spikes.flatten().tolist() == [1.0, 0.0, 0.0]
    # Winner resets; both retinotopic peers receive the membrane-energy decrement.
    assert neuron.membrane[0, 1, 0, 0].detach().item() < 0.7
    assert neuron.membrane[0, 2, 0, 0].detach().item() < 0.2
    neuron(torch.full((1, 3, 1, 1), 0.1)).sum().backward()
    assert neuron.inhibition_strength_logit is not None
    assert neuron.inhibition_strength_logit.grad is not None

def test_legacy_grouped_top_two_competition_is_preserved() -> None:
    neuron = HardwareLIF(
        8,
        LIFConfig(
            threshold=0.5,
            inhibition_enabled=True,
            inhibition_top_k=2,
            inhibition_group_size=4,
            threshold_adaptation_enabled=False,
        ),
    )
    current = torch.tensor(
        [[[[0.6]], [[0.9]], [[0.7]], [[0.8]], [[0.55]], [[0.75]], [[0.95]], [[0.65]]]]
    )
    spikes = neuron(current)
    assert int(spikes.sum()) == 4


def test_legacy_adaptation_hold_behavior_is_preserved() -> None:
    neuron = HardwareLIF(
        1,
        LIFConfig(
            threshold=0.5,
            threshold_adaptation_enabled=True,
            adaptation_kind="legacy",
            adaptation_increment=0.1,
            adaptation_decay=0.05,
            adaptation_hold_steps=2,
        ),
    )
    neuron(torch.tensor([[[[0.6]]]]))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.1]))
    neuron(torch.zeros((1, 1, 1, 1)))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.1]))
    neuron(torch.zeros((1, 1, 1, 1)))
    assert torch.allclose(neuron.adaptation, torch.tensor([0.05]))


def test_canonical_model_is_140k_and_xl_is_selectable() -> None:
    model = build_model()
    assert isinstance(model, EventSpikeSeg140k)
    assert model.architecture.name == "EventSpikeSeg140k"
    xl = build_model(architecture="EventSpikeSegXL")
    assert isinstance(xl, EventSpikeSegXL)
    assert xl.architecture.name == "EventSpikeSegXL"
    assert model.architecture.channel_schedule == (32, 64, 128)
    assert model.architecture.neuron_kind == "plif"
    assert model.architecture.inhibition_kind == "peer_membrane"
    assert model.architecture.adaptation_kind == "triangular_threshold"
    assert model.architecture.threshold_adaptation_scope == "encoder_context"
    assert not model.stem.neuron.config.threshold_adaptation_enabled
    assert model.stem.conv.stride == (2, 2)
    assert model.stem.conv.kernel_size == (5, 5)
    assert model.enc1.standard is not None
    assert not model.enc1.standard.neuron.config.threshold_adaptation_enabled
    assert model.enc2.depthwise is not None
    assert model.enc2.depthwise.neuron.config.threshold_adaptation_enabled
    assert model.detail_stem.conv.out_channels == 8
    assert model.detail1.standard is not None
    assert not model.detail1.standard.neuron.config.threshold_adaptation_enabled
    assert not model.architecture.output_competition_enabled
    assert model.parameter_count() == 141_867
    assert xl.parameter_count() == 236_445


def test_final_140k_model_is_selectable() -> None:
    model = build_model(architecture="EventSpikeSeg140k")
    assert isinstance(model, EventSpikeSeg140k)
    assert model.architecture.name == "EventSpikeSeg140k"
    assert model.parameter_count() == 141_867


def test_final_model_freezes_only_semantic_backbone_for_refinement() -> None:
    model = build_model()
    model.set_semantic_backbone_trainable(False)
    assert not any(parameter.requires_grad for parameter in model.stem.parameters())
    assert not any(parameter.requires_grad for parameter in model.enc3.parameters())
    assert any(parameter.requires_grad for parameter in model.detail1.parameters())
    assert any(parameter.requires_grad for parameter in model.final_fuse.parameters())
    assert any(parameter.requires_grad for parameter in model.head.parameters())
    model.set_semantic_backbone_trainable(True)
    assert all(parameter.requires_grad for parameter in model.stem.parameters())


def test_final_model_uses_native_detail_and_continuous_current_readout() -> None:
    model = build_model()
    assert isinstance(model.final_selector, torch.nn.Identity)
    assert model.final_fuse.depthwise is not None
    assert model.final_fuse.depthwise.conv.in_channels == 40
    assert model.final_fuse.pointwise is not None
    assert model.final_fuse.pointwise.conv.out_channels == 16
    assert model.head.synapse.in_channels == 16
    assert model.head.synapse.out_channels == 6


def test_xl_model_richer_spiking_paths_and_residual_bridges() -> None:
    model = build_model(architecture="EventSpikeSegXL")
    assert model.bridge12.conv.kernel_size == (1, 1)
    assert model.bridge12.conv.stride == (2, 2)
    assert model.bridge23.conv.kernel_size == (1, 1)
    assert model.decoder2_fuse.depthwise is not None
    assert model.decoder2_fuse.depthwise.conv.in_channels == 128
    assert model.parallel_context.fuse.conv.in_channels == 384
    assert model.deep_attention.q.conv.out_channels == 32
    assert model.detail2.vertical.conv.kernel_size == (3, 1)
    assert model.detail2.horizontal.conv.kernel_size == (1, 3)

    statistics = _timestamp_statistics(64)
    outputs = model(statistics)
    assert outputs["segmentation_logits"].shape == (1, 6, 64, 64)
    assert "segmentation_spikes" not in outputs
    assert outputs["segmentation_rate"].ndim == 0
    assert outputs["enc1_rate"].ndim == 0
    assert outputs["auxiliary_logits"].shape[-2:] == (32, 32)
    assert outputs["deep_auxiliary_logits"].shape[-2:] == (16, 16)
    assert model.parameter_count() == 236_445


def test_xl_dsec_parameter_accounting_matches_fpga_spec() -> None:
    model = build_model(
        architecture="EventSpikeSegXL", class_count=11, input_channels=2
    )
    assert model.parameter_count() == 237_115
    omitted = ("refine2.", "aux_head.", "deep_aux_head.")
    inference_parameters = sum(
        parameter.numel()
        for name, parameter in model.named_parameters()
        if not name.startswith(omitted)
    )
    assert inference_parameters == 226_767


def test_final_eval_returns_native_continuous_logits_without_class_spike_raster() -> None:
    model = build_model()
    model.eval()
    statistics = _timestamp_statistics(16)
    with torch.no_grad():
        outputs = model(statistics)
    assert outputs["segmentation_logits"].shape == (1, 6, 16, 16)
    assert "segmentation_spikes" not in outputs
    assert "boundary_logits" not in outputs
    assert "enc1_spikes" not in outputs
    assert "decoder_spikes" not in outputs

def test_xl_deep_paths_receive_gradients() -> None:
    model = build_model(architecture="EventSpikeSegXL")
    outputs = model(_timestamp_statistics(32))
    loss = (
        outputs["segmentation_logits"].mean()
        + outputs["auxiliary_logits"].mean()
        + outputs["deep_auxiliary_logits"].mean()
    )
    loss.backward()
    assert model.bridge12.conv.weight.grad is not None
    assert model.parallel_context.fuse.conv.weight.grad is not None
    assert model.deep_attention.q.conv.weight.grad is not None
    assert model.final_selector.selector.conv.weight.grad is not None

def test_plif_keeps_per_channel_retention_and_optional_spikingjelly_core() -> None:
    neuron = ParametricLIF(4, LIFConfig(learnable_threshold=True))
    assert neuron.beta.shape == (4,)
    assert neuron.reciprocal_tau.shape == (4,)
    if neuron.plif_core is not None:
        assert neuron.plif_core.__class__.__name__ == "ParametricLIFNode"


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


def test_final_model_bypasses_statistic_scheduler_for_raw_event_clocks() -> None:
    model = build_model(input_channels=2, architecture="EventSpikeSeg140k")
    assert model.source_input_channels == 2
    assert model.timestamp_input.__class__.__name__ == "Identity"


def test_timestamp_scheduler_conserves_activity_and_orders_arrivals() -> None:
    model = build_model(architecture="EventSpikeSeg140k")
    statistics = torch.zeros((1, 6, 2, 2))
    statistics[:, 0, 0, 0] = 0.8
    statistics[:, 2, 0, 0] = 0.5
    statistics[:, 4, 0, 0] = 0.2
    scheduled = model.timestamp_input(statistics)
    assert scheduled.shape == (10, 1, 2, 2, 2)
    assert scheduled[:, 0, 0, 0, 0].sum().item() == pytest.approx(0.8)
    assert torch.count_nonzero(scheduled[:, 0, 0, 0, 0]) == 3

    five_update_model = build_model(
        architecture="EventSpikeSeg140k", internal_updates=5
    )
    assert five_update_model.timestamp_input.clock_updates == 5
    with pytest.raises(ValueError, match="divide"):
        build_model(architecture="EventSpikeSeg140k", internal_updates=7)


def test_detach_state_keeps_membrane_values_without_autograd_history() -> None:
    neuron = ParametricLIF(1, LIFConfig(threshold=2.0))
    neuron(torch.ones((1, 1, 1, 1), requires_grad=True))
    value = neuron.membrane.detach().clone()
    neuron.detach_state()
    assert torch.equal(neuron.membrane, value)
    assert neuron.membrane.grad_fn is None


def test_named_runtime_state_is_serializable_and_restorable() -> None:
    model = build_model(architecture="EventSpikeSeg140k")
    model(_timestamp_statistics(16))
    snapshot = model.capture_named_runtime_state("cpu")

    assert snapshot
    assert all("membrane" in layer_state for layer_state in snapshot.values())
    expected = {
        layer_name: layer_state["membrane"].clone()
        for layer_name, layer_state in snapshot.items()
    }

    model.reset()
    model.restore_named_runtime_state(snapshot)
    modules = dict(model.named_modules())
    for layer_name, membrane in expected.items():
        assert torch.equal(modules[layer_name].membrane.cpu(), membrane)


def test_silent_neuron_keeps_surrogate_gradient_below_threshold() -> None:
    neuron = ParametricLIF(1, LIFConfig(threshold=2.0))
    current = torch.ones((1, 1, 1, 1), requires_grad=True)
    spikes = neuron(current)
    assert spikes.item() == 0.0
    spikes.sum().backward()
    assert current.grad is not None
    assert current.grad.abs().item() > 0.0


def test_model_detach_clears_spikingjelly_internal_graph_roots() -> None:
    model = build_model(architecture="EventSpikeSeg140k")
    outputs = model(_timestamp_statistics(16))
    outputs["segmentation_logits"].sum().backward()
    active = [
        module
        for module in model.modules()
        if isinstance(module, ParametricLIF)
        and module.plif_core is not None
        and isinstance(module.plif_core.v, torch.Tensor)
        and module.plif_core.v.grad_fn is not None
    ]
    assert active
    model.detach_state()
    assert all(module.plif_core.v.grad_fn is None for module in active)
    assert all(module.membrane.grad_fn is None for module in active)
