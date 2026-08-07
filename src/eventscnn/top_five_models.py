"""Current five neuromorphic DDD17 semantic-segmentation contenders."""

from __future__ import annotations

from .model_components import EventSpikeSegBase, SegmentationArchitecture


# The mechanism names describe their actual operation:
# - threshold_adaptation: local triangular rise/fall threshold penalty
# - winner_peer: one retinotopic winner spikes; peer feature membranes are inhibited
# - peer_membrane: simultaneous spikes are preserved; peer feature membranes are inhibited
TOP_FIVE_PRESETS: dict[str, SegmentationArchitecture] = {
    "f01_v10_plif_threshold_wta": SegmentationArchitecture(
        name="f01_v10_plif_threshold_wta",
        context="multiscale",
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        learnable_threshold=True,
        f_long_enabled=False,
        output_f_inst_enabled=True,
    ),
    "f02_v10_plif_threshold_adaptation": SegmentationArchitecture(
        name="f02_v10_plif_threshold_adaptation",
        context="multiscale",
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        learnable_threshold=True,
        f_long_enabled=True,
        f_long_scope="encoder",
        homeostasis_kind="triangular_threshold",
        threshold_adaptation_strength_init=0.30,
        adaptation_duration_init=6.0,
        output_f_inst_enabled=True,
    ),
    "f03_v10_plif_winner_peer_inhibition": SegmentationArchitecture(
        name="f03_v10_plif_winner_peer_inhibition",
        context="multiscale",
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        learnable_threshold=True,
        f_inst_enabled=True,
        f_inst_scope="encoder",
        inhibition_kind="winner_peer",
        inhibition_strength_init=0.20,
        f_long_enabled=True,
        f_long_scope="encoder",
        homeostasis_kind="triangular_threshold",
        threshold_adaptation_strength_init=0.25,
        adaptation_duration_init=6.0,
        output_f_inst_enabled=True,
    ),
    "f04_v03_dilated_threshold_adaptation": SegmentationArchitecture(
        name="f04_v03_dilated_threshold_adaptation",
        context="dilated",
        context_dilations=(2,),
        norm="none",
        auxiliary_head=False,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        learnable_threshold=True,
        f_long_enabled=True,
        f_long_scope="encoder",
        homeostasis_kind="triangular_threshold",
        threshold_adaptation_strength_init=0.25,
        adaptation_duration_init=5.0,
        output_f_inst_enabled=True,
    ),
    "f05_v02_light_peer_membrane_inhibition": SegmentationArchitecture(
        name="f05_v02_light_peer_membrane_inhibition",
        context="none",
        norm="affine",
        auxiliary_head=True,
        skip_kind="two",
        residual=True,
        adaptive_threshold=False,
        neuron_kind="plif",
        learnable_threshold=True,
        f_inst_enabled=True,
        f_inst_scope="stem",
        inhibition_kind="peer_membrane",
        inhibition_strength_init=0.20,
        f_long_enabled=True,
        f_long_scope="encoder",
        homeostasis_kind="triangular_threshold",
        threshold_adaptation_strength_init=0.20,
        adaptation_duration_init=5.0,
        output_f_inst_enabled=True,
    ),
}

TOP_FIVE_DEFAULT = "f02_v10_plif_threshold_adaptation"


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
