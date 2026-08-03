import torch

from eventscnn.models import EventSCNNBackbone


def test_canonical_backbone_shapes_bias_and_deterministic_reset() -> None:
    torch.manual_seed(7)
    model = EventSCNNBackbone()
    sequence = torch.zeros((1, 1, 2, 180, 240))
    sequence[0, 0, 1, 90, 120] = 2
    first = model(sequence, return_all=True)
    model.reset()
    second = model(sequence, return_all=True)
    assert [tuple(tensor.shape) for tensor in first] == [
        (1, 1, 8, 90, 120),
        (1, 1, 16, 45, 60),
        (1, 1, 32, 23, 30),
    ]
    assert all(block.conv.bias is None for block in model.blocks)
    assert all(torch.equal(left, right) for left, right in zip(first, second))


def test_backbone_rejects_wrong_layout() -> None:
    model = EventSCNNBackbone()
    try:
        model(torch.zeros((1, 2, 180, 240)))
    except ValueError as error:
        assert "TNCHW" in str(error)
    else:
        raise AssertionError("invalid layout was accepted")
