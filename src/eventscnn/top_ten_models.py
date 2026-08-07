"""Frozen definitions from the completed ten-model DDD17 benchmark."""

from __future__ import annotations

from .model_components import EventSpikeSegBase, SegmentationArchitecture

TOP_TEN_PRESETS: dict[str, SegmentationArchitecture] = {
    "v01_std_unet_light": SegmentationArchitecture(
        name="v01_std_unet_light",
        depthwise=False,
        context="none",
        norm="none",
        auxiliary_head=False,
        residual=False,
        adaptive_threshold=False,
    ),
    "v02_dw_light": SegmentationArchitecture(
        name="v02_dw_light",
        context="none",
        norm="none",
        residual=False,
        adaptive_threshold=False,
    ),
    "v03_dw_dilated": SegmentationArchitecture(
        name="v03_dw_dilated",
        context="dilated",
        context_dilations=(2,),
        norm="none",
        residual=True,
        adaptive_threshold=False,
    ),
    "v04_dw_multiscale": SegmentationArchitecture(
        name="v04_dw_multiscale",
        context="multiscale",
        norm="none",
        residual=True,
        adaptive_threshold=False,
    ),
    "v05_dw_multiscale_affine": SegmentationArchitecture(
        name="v05_dw_multiscale_affine",
        context="multiscale",
        norm="affine",
        residual=True,
        adaptive_threshold=False,
    ),
    "v06_dw_multiscale_bn": SegmentationArchitecture(
        name="v06_dw_multiscale_bn",
        context="multiscale",
        norm="bn",
        residual=True,
        adaptive_threshold=False,
    ),
    "v07_dw_multiscale_gap": SegmentationArchitecture(
        name="v07_dw_multiscale_gap",
        context="multiscale",
        norm="affine",
        gap_gate=True,
        residual=True,
        adaptive_threshold=False,
    ),
    "v08_dw_multiscale_aux": SegmentationArchitecture(
        name="v08_dw_multiscale_aux",
        context="multiscale",
        norm="affine",
        auxiliary_head=True,
        residual=True,
        adaptive_threshold=False,
    ),
    "v09_dw_single_skip": SegmentationArchitecture(
        name="v09_dw_single_skip",
        context="multiscale",
        norm="affine",
        skip_kind="one",
        residual=True,
        adaptive_threshold=True,
    ),
    "v10_fpga_hybrid": SegmentationArchitecture(
        name="v10_fpga_hybrid",
        context="multiscale",
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=True,
    ),
}

TOP_TEN_DEFAULT = "v10_fpga_hybrid"


def build_top_ten_model(
    name: str = TOP_TEN_DEFAULT,
    *,
    class_count: int = 6,
    input_channels: int = 6,
) -> EventSpikeSegBase:
    if name not in TOP_TEN_PRESETS:
        raise KeyError(f"unknown top-ten architecture {name!r}")
    return EventSpikeSegBase(
        class_count=class_count,
        input_channels=input_channels,
        architecture=TOP_TEN_PRESETS[name],
    )
