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
        system.objectness.conv.weight[0, 0, 0, 0] = 1.0
        system.classification.classifier.weight.zero_()
        system.classification.classifier.bias.zero_()
        system.classification.classifier.weight[1, 0] = 1.0
    return system


def test_integrated_synthetic_proposal_classification_and_tracking() -> None:
    system = _configured_system()
    sequence = torch.zeros((1, 1, 2, 180, 240))
    sequence[0, 0, 1, 88, 120] = 2
    outputs = system.trainable_outputs(sequence, torch.tensor([[0, 0, 30, 23]]))
    system.reset()
    detections, track = system.infer_single(sequence)
    assert outputs["conv3_spikes"].shape == (1, 1, 32, 23, 30)
    assert len(detections) == 1
    assert detections[0].class_id == 1
    assert track is not None and track.class_id == 1


def test_integrated_reset_is_deterministic() -> None:
    system = _configured_system()
    sequence = torch.zeros((1, 1, 2, 32, 32))
    sequence[0, 0, 1, 16, 16] = 2
    rois = torch.tensor([[0, 0, 4, 4]])
    first = system.trainable_outputs(sequence, rois)
    system.reset()
    second = system.trainable_outputs(sequence, rois)
    assert all(torch.equal(first[key], second[key]) for key in first)
