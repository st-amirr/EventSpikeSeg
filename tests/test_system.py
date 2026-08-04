import torch

from eventscnn.system import EventSCNNSystem


def _configured_system() -> EventSCNNSystem:
    system = EventSCNNSystem(class_count=2)
    with torch.no_grad():
        for block in system.backbone.blocks:
            block.conv.weight.zero_()
        system.backbone.blocks[0].conv.weight[0, 1, 2, 2] = 1.0
        system.backbone.blocks[1].conv.weight[0, 0, 1, 1] = 1.0
        system.backbone.blocks[2].conv.weight[0, 0, 1, 1] = 1.0
        system.objectness.conv.weight.zero_()
        system.attention.conv.weight[0, 0, 1, 1] = 1.0
        system.classification.synapse.weight.zero_()
        system.classification.synapse.weight[1, 0] = 1.0
    return system


def test_integrated_synthetic_attention_classification_and_tracking() -> None:
    system = _configured_system()
    assert system.backbone.config.lif.f_inst_enabled
    assert not system.classification.neuron.config.f_inst_enabled
    assert not system.classification.neuron.config.f_long_enabled
    sequence = torch.zeros((1, 1, 2, 180, 240))
    sequence[0, 0, 1, 88, 120] = 2
    outputs = system.trainable_outputs(sequence)
    system.reset()
    observation, track = system.infer_attention_single(sequence)
    assert outputs["conv3_spikes"].shape == (1, 1, 32, 45, 60)
    assert outputs["attention_spikes"].shape == (1, 1, 1, 90, 120)
    assert outputs["classification_spikes"].shape == (1, 1, 2)
    assert observation is not None and observation.class_id == 1
    assert track is not None and track.class_id == 1


def test_integrated_reset_is_deterministic() -> None:
    system = _configured_system()
    sequence = torch.zeros((1, 1, 2, 32, 32))
    sequence[0, 0, 1, 16, 16] = 2
    first = system.trainable_outputs(sequence)
    system.reset()
    second = system.trainable_outputs(sequence)
    assert all(torch.equal(first[key], second[key]) for key in first)
