from __future__ import annotations

import torch

from eventscnn.top_three_models import TOP_THREE_PRESETS, build_top_three_model
from eventscnn.train import build_experiment_model, infer_model_suite


def test_top_three_registry_and_forward_backward() -> None:
    expected = {
        "t01_spike_pyramid_concat",
        "t02_dualpath_detail",
        "t03_deep_attention_fpn",
    }
    assert set(TOP_THREE_PRESETS) == expected

    sequence = (torch.rand(2, 1, 6, 16, 16) > 0.93).float()
    for name in TOP_THREE_PRESETS:
        assert infer_model_suite(name) == "top-three"
        model = build_top_three_model(name)
        model.reset()
        outputs = model(sequence)
        assert outputs["segmentation_logits"].shape == (1, 6, 16, 16)
        assert outputs["segmentation_spikes"].shape[:3] == (2, 1, 6)
        assert "auxiliary_logits" in outputs
        loss = outputs["segmentation_logits"].square().mean()
        loss.backward()
        gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
        assert gradients
        assert all(torch.isfinite(gradient).all() for gradient in gradients)


def test_top_three_parameter_budget_and_train_builder() -> None:
    budgets = {
        "t01_spike_pyramid_concat": (55_000, 75_000),
        "t02_dualpath_detail": (20_000, 35_000),
        "t03_deep_attention_fpn": (95_000, 120_000),
    }
    for name, (minimum, maximum) in budgets.items():
        model = build_experiment_model(name, suite="top-three")
        assert minimum <= model.parameter_count() <= maximum
