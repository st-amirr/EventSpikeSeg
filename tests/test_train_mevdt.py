import torch

from eventscnn.datasets import MEVDTBox
from eventscnn.train_mevdt import box_to_feature_roi, objectness_target


def test_mevdt_box_projects_to_conv3_roi() -> None:
    box = MEVDTBox(1, 0.0, 0.0, 240.0, 180.0)
    assert torch.equal(box_to_feature_roi(box), torch.tensor([[0, 0, 30, 23]]))


def test_mevdt_objectness_target_uses_xyxy_extent() -> None:
    box = MEVDTBox(1, 20.0, 40.0, 60.0, 80.0)
    target = objectness_target((box,), 90, 120)
    assert target.shape == (1, 1, 90, 120)
    assert target[0, 0, 20:40, 10:30].all()
    assert target.sum() == 400
