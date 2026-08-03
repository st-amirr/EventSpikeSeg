import torch

from eventscnn.heads import (
    ClassificationHead,
    ObjectnessHead,
    connected_component_proposals,
    roi_spike_count_pool,
)


def test_connected_components_empty_border_and_scale() -> None:
    assert connected_component_proposals(torch.zeros((3, 4))) == []
    activity = torch.zeros((3, 4))
    activity[0, 0] = 2
    activity[0, 1] = 1
    activity[2, 3] = 3
    proposals = connected_component_proposals(activity, scale_x=2, scale_y=4)
    assert [(p.x, p.y, p.width, p.height) for p in proposals] == [
        (0, 0, 4, 4),
        (6, 8, 2, 4),
    ]
    assert [p.confidence for p in proposals] == [1.5, 3.0]


def test_objectness_head_is_spiking_and_bias_free() -> None:
    head = ObjectnessHead(2)
    assert head.conv.bias is None
    output = head(torch.zeros((2, 1, 2, 3, 4)))
    assert output.shape == (2, 1, 1, 3, 4)


def test_roi_pool_clips_and_empty_roi_is_zero() -> None:
    features = torch.ones((2, 2, 3, 4, 5))
    rois = torch.tensor([[-1, -1, 3, 3], [9, 9, 2, 2]])
    pooled = roi_spike_count_pool(features, rois)
    assert pooled[0].tolist() == [8.0, 8.0, 8.0]
    assert pooled[1].tolist() == [0.0, 0.0, 0.0]


def test_classification_logits_are_deterministic() -> None:
    head = ClassificationHead(2, 3)
    with torch.no_grad():
        head.classifier.weight.copy_(torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, -1.0]]))
        head.classifier.bias.zero_()
    features = torch.tensor([[[[[1.0]], [[2.0]]]]])
    logits = head(features, torch.tensor([[0, 0, 1, 1]]))
    assert logits.tolist() == [[1.0, 2.0, -1.0]]
