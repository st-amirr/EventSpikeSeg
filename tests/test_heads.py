import torch

from eventscnn.model import (
    ClassificationHead,
    ObjectnessHead,
    PixelAttentionHead,
    attention_gated_spike_counts,
    attention_weighted_spike_pool,
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


def test_pixel_attention_head_is_local_spiking_and_bias_free() -> None:
    head = PixelAttentionHead(2)
    assert head.conv.bias is None
    assert head.conv.kernel_size == (3, 3)
    output = head(torch.zeros((2, 1, 2, 3, 4)))
    assert output.shape == (2, 1, 1, 3, 4)


def test_roi_pool_clips_and_empty_roi_is_zero() -> None:
    features = torch.ones((2, 2, 3, 4, 5))
    rois = torch.tensor([[-1, -1, 3, 3], [9, 9, 2, 2]])
    pooled = roi_spike_count_pool(features, rois)
    assert pooled[0].tolist() == [8.0, 8.0, 8.0]
    assert pooled[1].tolist() == [0.0, 0.0, 0.0]


def test_attention_pool_uses_selected_pixels_and_handles_empty_attention() -> None:
    features = torch.tensor([[[[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]]])
    attention = torch.zeros((1, 1, 1, 4, 4))
    attention[..., :2, :2] = 1.0
    pooled = attention_weighted_spike_pool(features, attention)
    assert pooled.tolist() == [[1.0, 5.0]]
    empty = attention_weighted_spike_pool(features, torch.zeros_like(attention))
    assert empty.tolist() == [[0.0, 0.0]]


def test_attention_gating_returns_per_timestep_feature_spike_counts() -> None:
    features = torch.tensor([[[[[1.0, 0.0], [1.0, 1.0]], [[0.0, 1.0], [1.0, 0.0]]]]])
    attention = torch.zeros((1, 1, 1, 4, 4))
    attention[..., :2, :2] = 1.0
    assert attention_gated_spike_counts(features, attention).tolist() == [[[1.0, 0.0]]]


def test_attention_classification_is_bias_free_spiking_and_deterministic() -> None:
    head = ClassificationHead(2, 2)
    assert head.synapse.bias is None
    with torch.no_grad():
        head.synapse.weight.copy_(torch.tensor([[1.0, 0.0], [0.0, 0.0]]))
    features = torch.tensor([[[[[1.0]], [[0.0]]]]])
    attention = torch.ones((1, 1, 1, 2, 2))
    spikes = head.forward_attention(features, attention)
    assert spikes.shape == (1, 1, 2)
    assert spikes.tolist() == [[[1.0, 0.0]]]


def test_classification_trace_exposes_current_candidate_and_spikes() -> None:
    head = ClassificationHead(2, 2)
    with torch.no_grad():
        head.synapse.weight.copy_(torch.tensor([[1.0, 0.0], [0.0, 0.0]]))
    features = torch.tensor([[[[[1.0]], [[0.0]]]]])
    attention = torch.ones((1, 1, 1, 2, 2))
    trace = head.forward_attention_trace(features, attention)
    assert set(trace) == {"currents", "candidate_membranes", "spikes"}
    assert trace["currents"].tolist() == [[[1.0, 0.0]]]
    assert trace["candidate_membranes"].tolist() == [[[1.0, 0.0]]]
    assert trace["spikes"].tolist() == [[[1.0, 0.0]]]


def test_classification_current_uses_power_of_two_scale() -> None:
    head = ClassificationHead(2, 2, current_scale_shift=2)
    with torch.no_grad():
        head.synapse.weight.copy_(torch.tensor([[1.0, 0.0], [0.0, 0.0]]))
    features = torch.tensor([[[[[1.0]], [[0.0]]]]])
    attention = torch.ones((1, 1, 1, 2, 2))
    trace = head.forward_attention_trace(features, attention)
    assert trace["currents"].tolist() == [[[0.25, 0.0]]]
    assert trace["spikes"].tolist() == [[[0.0, 0.0]]]
