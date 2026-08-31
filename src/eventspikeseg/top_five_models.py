"""Structural top-five DDD17 SNN segmentation contenders.

The completed mechanism comparison selected one common neuromorphic operating point for
all five candidates: PLIF + learnable thresholds, stem-only peer-membrane inhibition,
encoder triangular threshold adaptation, affine channel scaling, residual paths,
auxiliary supervision, and output class winner-take-all. This round varies only the
structural axes: width, early receptive field, encoder depth, and context strategy.
"""

from __future__ import annotations

from .model_components import EventSpikeSegBase, SegmentationArchitecture

_COMMON_DYNAMICS: dict[str, object] = {
    "norm": "affine",
    "auxiliary_head": True,
    "skip_kind": "two",
    "residual": True,
    "adaptive_threshold": False,
    "neuron_kind": "plif",
    "learnable_threshold": True,
    "inhibition_enabled": True,
    "inhibition_scope": "stem",
    "inhibition_kind": "peer_membrane",
    "inhibition_strength_init": 0.20,
    "threshold_adaptation_enabled": True,
    "threshold_adaptation_scope": "encoder",
    "adaptation_kind": "triangular_threshold",
    "threshold_adaptation_strength_init": 0.20,
    "adaptation_duration_init": 5.0,
    "output_competition_enabled": True,
}


TOP_FIVE_PRESETS: dict[str, SegmentationArchitecture] = {
    # Controlled 24/48/96 baseline using the strongest round-one context family.
    "f01_base24_multiscale": SegmentationArchitecture(
        name="f01_base24_multiscale",
        channel_schedule=(24, 48, 96),
        context="multiscale",
        context_dilations=(1, 2, 4),
        **_COMMON_DYNAMICS,
    ),
    # Capacity test: same depth and kernels, wider feature maps.
    "f02_wide32_multiscale": SegmentationArchitecture(
        name="f02_wide32_multiscale",
        channel_schedule=(32, 64, 128),
        context="multiscale",
        context_dilations=(1, 2, 4),
        **_COMMON_DYNAMICS,
    ),
    # Receptive-field test: 5x5 only where raw/local event structure first enters.
    "f03_early5x5_multiscale": SegmentationArchitecture(
        name="f03_early5x5_multiscale",
        channel_schedule=(24, 48, 96),
        stem_kernel_size=5,
        first_block_kernel_size=5,
        context="multiscale",
        context_dilations=(1, 2, 4),
        **_COMMON_DYNAMICS,
    ),
    # Depth/context test: one extra encoder scale, then a single cheap dilated branch.
    "f04_deep4_dilated": SegmentationArchitecture(
        name="f04_deep4_dilated",
        channel_schedule=(24, 48, 96, 128),
        context="dilated",
        context_dilations=(2,),
        **_COMMON_DYNAMICS,
    ),
    # FPGA-efficiency test: narrow channels plus the cheaper single dilated context.
    "f05_compact16_dilated": SegmentationArchitecture(
        name="f05_compact16_dilated",
        channel_schedule=(16, 32, 64),
        context="dilated",
        context_dilations=(2,),
        **_COMMON_DYNAMICS,
    ),
}

TOP_FIVE_DEFAULT = "f01_base24_multiscale"


def build_top_five_model(
    name: str = TOP_FIVE_DEFAULT,
    *,
    class_count: int = 6,
    input_channels: int = 6,
) -> EventSpikeSegBase:
    if name not in TOP_FIVE_PRESETS:
        raise KeyError(f"unknown top-five architecture {name!r}")
    return EventSpikeSegBase(
        class_count=class_count,
        input_channels=input_channels,
        architecture=TOP_FIVE_PRESETS[name],
    )
