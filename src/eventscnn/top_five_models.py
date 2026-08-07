"""Second-round neuromorphic contenders derived from the top-ten benchmark."""

from __future__ import annotations

from .model_components import EventSpikeSegBase, SegmentationArchitecture

# The completed round-one ranking was v10, v03, v02, v08, then v04 by mIoU.
# These contenders combine those structural strengths with PLIF, f_long/T_thresh,
# and selected f_inst competition.  Ordinary BatchNorm and GAP are excluded from
# this round because the goal is a more spike-native, FPGA-oriented comparison.
TOP_FIVE_PRESETS: dict[str, SegmentationArchitecture] = {
    "f01_v10_plif_long": SegmentationArchitecture(
        name="f01_v10_plif_long",
        context="multiscale",
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        f_long_enabled=True,
        t_thresh_steps=4,
    ),
    "f02_v10_plif_inst_long": SegmentationArchitecture(
        name="f02_v10_plif_inst_long",
        context="multiscale",
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        f_inst_enabled=True,
        f_long_enabled=True,
        t_thresh_steps=4,
    ),
    "f03_v03_dilated_plif_long": SegmentationArchitecture(
        name="f03_v03_dilated_plif_long",
        context="dilated",
        context_dilations=(2,),
        norm="none",
        auxiliary_head=False,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        f_long_enabled=True,
        t_thresh_steps=4,
    ),
    "f04_v02_light_plif_inst_long": SegmentationArchitecture(
        name="f04_v02_light_plif_inst_long",
        context="none",
        norm="none",
        auxiliary_head=False,
        skip_kind="two",
        residual=False,
        adaptive_threshold=False,
        neuron_kind="plif",
        f_inst_enabled=True,
        f_long_enabled=True,
        t_thresh_steps=4,
    ),
    "f05_dilated_aux_plif_long": SegmentationArchitecture(
        name="f05_dilated_aux_plif_long",
        context="dilated",
        context_dilations=(2,),
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        f_long_enabled=True,
        t_thresh_steps=4,
    ),
}

TOP_FIVE_DEFAULT = "f01_v10_plif_long"


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
