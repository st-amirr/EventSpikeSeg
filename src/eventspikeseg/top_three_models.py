"""Accuracy-oriented top-three DDD17 SNN segmentation contenders.

This round follows the completed top-five structural benchmark.  The strongest
findings were:

* the compact 16/32/64 single-dilated model had the best mIoU/parameter tradeoff;
* the 32/64/128 model showed that extra channel capacity can improve feature diversity;
* the four-stage model recovered more rare-class signal, especially vehicles/nature;
* early 5x5 kernels were not helpful;
* averaging parallel dilation branches likely destroys sparse branch-specific evidence.

The three models below therefore keep 3x3 spatial kernels, fully spiking feature
transmission, PLIF + learnable thresholds, stem-only peer-membrane inhibition,
encoder triangular threshold adaptation, auxiliary supervision, and output class
competition, while testing three new structural hypotheses:

1. concatenate multi-scale spike branches before a learned 1x1 spiking fusion;
2. preserve a narrow high-resolution detail stream for small semantic regions;
3. combine a four-level semantic encoder with low-resolution spike-driven mask
   attention and concatenative FPN decoding.
"""

from __future__ import annotations

import torch
from torch import Tensor, nn

from .model_components import (
    EventSpikeSegBase,
    LIFConfig,
    SegmentationArchitecture,
    SpikingClassHead,
    SpikingConvBlock,
    SpikingStage,
)

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


TOP_THREE_PRESETS: dict[str, SegmentationArchitecture] = {
    "t01_spike_pyramid_concat": SegmentationArchitecture(
        name="t01_spike_pyramid_concat",
        channel_schedule=(24, 48, 96),
        context="none",
        **_COMMON_DYNAMICS,
    ),
    "t02_dualpath_detail": SegmentationArchitecture(
        name="t02_dualpath_detail",
        channel_schedule=(16, 32, 64),
        context="none",
        **_COMMON_DYNAMICS,
    ),
    "t03_deep_attention_fpn": SegmentationArchitecture(
        name="t03_deep_attention_fpn",
        channel_schedule=(24, 48, 96, 128),
        context="none",
        **_COMMON_DYNAMICS,
    ),
}

TOP_THREE_DEFAULT = "t01_spike_pyramid_concat"


def _block_lif(block: SpikingConvBlock) -> LIFConfig:
    """Return the LIF configuration used by the block's final spiking stage."""
    stage = block.pointwise if block.pointwise is not None else block.standard
    assert stage is not None
    return stage.neuron.config


class SpikeCountChannelAttention(nn.Module):
    """Binary channel attention driven only by spike counts.

    Spatial/time spike counts are pooled once per sample, passed through a very
    small bottleneck, and converted to a binary channel mask with a straight-
    through estimator.  Forward inference therefore gates spike channels with
    binary AND-like operations rather than multiplying feature maps by a dense
    floating-point attention tensor.
    """

    def __init__(self, channels: int, reduction: int = 8) -> None:
        super().__init__()
        hidden = max(4, channels // reduction)
        self.reduce = nn.Linear(channels, hidden, bias=True)
        self.expand = nn.Linear(hidden, channels, bias=True)

    def forward(self, sequence: Tensor) -> Tensor:
        # TNCHW -> NC.  On hardware this is a bank of spike counters plus a
        # small per-window channel-selection network.
        pooled = sequence.float().mean(dim=(0, 3, 4))
        soft = torch.sigmoid(self.expand(torch.relu(self.reduce(pooled))))
        hard = (soft >= 0.5).to(soft.dtype)
        gate = hard.detach() - soft.detach() + soft
        return sequence * gate.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)


class ConcatDilatedSpikeContext(nn.Module):
    """Multi-receptive-field spike context that preserves branch identity.

    A 1x1 spiking bottleneck reduces cost, three depthwise dilated branches
    extract d={1,2,4} evidence, the binary channel selector suppresses weak
    channels, and a final 1x1 spiking stage learns how to mix concatenated
    branch evidence.  No branch averaging is used.
    """

    def __init__(
        self,
        channels: int,
        bottleneck_channels: int,
        *,
        lif: LIFConfig,
        norm: str,
        neuron_kind: str,
        dilations: tuple[int, ...] = (1, 2, 4),
    ) -> None:
        super().__init__()
        self.pre = SpikingStage(
            channels,
            bottleneck_channels,
            kernel_size=1,
            norm=norm,
            lif=lif,
            neuron_kind=neuron_kind,
        )
        self.branches = nn.ModuleList(
            [
                SpikingStage(
                    bottleneck_channels,
                    bottleneck_channels,
                    kernel_size=3,
                    dilation=dilation,
                    groups=bottleneck_channels,
                    norm=norm,
                    lif=lif,
                    neuron_kind=neuron_kind,
                )
                for dilation in dilations
            ]
        )
        merged_channels = bottleneck_channels * len(dilations)
        self.attention = SpikeCountChannelAttention(merged_channels)
        self.fuse = SpikingStage(
            merged_channels,
            channels,
            kernel_size=1,
            norm=norm,
            lif=lif,
            neuron_kind=neuron_kind,
        )

    def forward(self, sequence: Tensor) -> Tensor:
        reduced = self.pre(sequence)
        merged = torch.cat([branch(reduced) for branch in self.branches], dim=2)
        fused = self.fuse(self.attention(merged))
        return torch.clamp(fused + sequence, 0.0, 1.0)


class SpikeDrivenMaskAttention(nn.Module):
    """Low-resolution SDMSA-style binary mask attention.

    Q, K, and V are spike projections.  Q/K coincidence is an elementwise
    binary AND followed by an addition across channels within each head.  A
    learned coincidence threshold creates a binary mask which gates V.  This
    avoids a dense spatial NxN attention matrix and maps naturally to spike
    masks, counters, comparators, and accumulation on FPGA/neuromorphic logic.
    """

    def __init__(
        self,
        channels: int,
        attention_channels: int,
        heads: int,
        *,
        lif: LIFConfig,
        norm: str,
        neuron_kind: str,
    ) -> None:
        super().__init__()
        if attention_channels % heads != 0:
            raise ValueError("attention_channels must be divisible by heads")
        self.heads = heads
        self.head_dim = attention_channels // heads
        self.q = SpikingStage(
            channels, attention_channels, kernel_size=1,
            norm=norm, lif=lif, neuron_kind=neuron_kind,
        )
        self.k = SpikingStage(
            channels, attention_channels, kernel_size=1,
            norm=norm, lif=lif, neuron_kind=neuron_kind,
        )
        self.v = SpikingStage(
            channels, attention_channels, kernel_size=1,
            norm=norm, lif=lif, neuron_kind=neuron_kind,
        )
        self.out = SpikingStage(
            attention_channels, channels, kernel_size=1,
            norm=norm, lif=lif, neuron_kind=neuron_kind,
        )
        # One threshold fraction per head.  0.25 means a quarter of Q/K bits
        # must coincide before V spikes are passed by that head.
        initial_fraction = torch.full((heads,), 0.25)
        self.attention_threshold_logit = nn.Parameter(torch.logit(initial_fraction))

    def forward(self, sequence: Tensor) -> Tensor:
        q = self.q(sequence)
        k = self.k(sequence)
        v = self.v(sequence)
        t, n, c, h, w = q.shape
        qh = q.view(t, n, self.heads, self.head_dim, h, w)
        kh = k.view(t, n, self.heads, self.head_dim, h, w)
        vh = v.view(t, n, self.heads, self.head_dim, h, w)

        # Binary AND + integer accumulation in forward inference.
        coincidence = (qh * kh).sum(dim=3)
        fraction = torch.sigmoid(self.attention_threshold_logit)
        threshold = 1.0 + fraction * float(max(1, self.head_dim - 1))
        threshold = threshold.view(1, 1, self.heads, 1, 1)

        # Hard binary forward gate with a smooth straight-through gradient.
        soft = torch.sigmoid(4.0 * (coincidence - threshold))
        hard = (coincidence >= threshold).to(soft.dtype)
        gate = hard.detach() - soft.detach() + soft
        attended = (vh * gate.unsqueeze(3)).reshape(t, n, c, h, w)
        projected = self.out(attended)
        return torch.clamp(projected + sequence, 0.0, 1.0)


class _TopThreeBase(EventSpikeSegBase):
    """Shared output packaging for the three custom experimental forwards."""

    def _pack(
        self,
        sequence: Tensor,
        *,
        x1: Tensor,
        x2: Tensor,
        x3: Tensor,
        decoder: Tensor,
        class_spikes: Tensor,
        auxiliary_spikes: Tensor | None,
        x4: Tensor | None = None,
    ) -> dict[str, Tensor]:
        logits = class_spikes.sum(dim=0) * (
            self.architecture.output_rate_scale / float(sequence.shape[0])
        )
        result = {
            "segmentation_spikes": class_spikes,
            "segmentation_logits": logits,
            "enc1_spikes": x1,
            "enc2_spikes": x2,
            "enc3_spikes": x3,
            "decoder_spikes": decoder,
        }
        if x4 is not None:
            result["enc4_spikes"] = x4
        if auxiliary_spikes is not None:
            result["auxiliary_spikes"] = auxiliary_spikes
            result["auxiliary_logits"] = auxiliary_spikes.sum(dim=0) * (
                self.architecture.output_rate_scale / float(sequence.shape[0])
            )
        return result


class SpikePyramidConcatNet(_TopThreeBase):
    """T1: three-stage encoder + concatenated multi-scale context/decoder."""

    def __init__(self, *, class_count: int, input_channels: int) -> None:
        architecture = TOP_THREE_PRESETS["t01_spike_pyramid_concat"]
        super().__init__(
            class_count=class_count,
            input_channels=input_channels,
            architecture=architecture,
        )
        encoder_lif = _block_lif(self.enc3)
        decoder_lif = self.project3.neuron.config
        self.context = ConcatDilatedSpikeContext(
            96,
            48,
            lif=encoder_lif,
            norm=architecture.norm,
            neuron_kind=architecture.neuron_kind,
        )
        # Concatenation preserves semantic and skip channels separately until a
        # depthwise/pointwise spiking fusion learns the mixture.
        self.fuse2 = SpikingConvBlock(
            96, 48, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.fuse1 = SpikingConvBlock(
            48, 24, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.refine2 = nn.Identity()
        self.refine1 = nn.Identity()

    def forward(self, sequence: Tensor) -> dict[str, Tensor]:
        x1 = self.enc1(self.stem(sequence))
        x2 = self.enc2(self.down2(x1))
        x3 = self.enc3(self.down3(x2))
        deepest = self.context(x3)
        d2 = self._upsample(self.project3(deepest), x2.shape[-2:])
        d2 = self.fuse2(torch.cat((d2, x2), dim=2))
        aux = self.aux_head(d2) if self.aux_head is not None else None
        d1 = self._upsample(self.project2(d2), x1.shape[-2:])
        d1 = self.fuse1(torch.cat((d1, x1), dim=2))
        class_spikes = self.head(d1)
        return self._pack(
            sequence, x1=x1, x2=x2, x3=x3, decoder=d1,
            class_spikes=class_spikes, auxiliary_spikes=aux,
        )


class DualPathDetailNet(_TopThreeBase):
    """T2: compact semantic path plus a persistent high-resolution detail path."""

    def __init__(self, *, class_count: int, input_channels: int) -> None:
        architecture = TOP_THREE_PRESETS["t02_dualpath_detail"]
        super().__init__(
            class_count=class_count,
            input_channels=input_channels,
            architecture=architecture,
        )
        encoder_lif = _block_lif(self.enc1)
        context_lif = _block_lif(self.enc3)
        decoder_lif = self.project3.neuron.config
        self.context = SpikingConvBlock(
            64, 64, dilation=2, depthwise=True, norm=architecture.norm,
            lif=context_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.detail1 = SpikingConvBlock(
            16, 16, depthwise=True, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.detail2 = SpikingConvBlock(
            16, 16, depthwise=True, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.detail_attention = SpikeCountChannelAttention(48, reduction=6)
        self.detail_fuse = SpikingConvBlock(
            48, 16, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.refine1 = nn.Identity()

    def forward(self, sequence: Tensor) -> dict[str, Tensor]:
        x1 = self.enc1(self.stem(sequence))
        detail = self.detail2(self.detail1(x1))
        x2 = self.enc2(self.down2(x1))
        x3 = self.enc3(self.down3(x2))
        deepest = self.context(x3)
        d2 = self._upsample(self.project3(deepest), x2.shape[-2:])
        d2 = self.refine2(torch.clamp(d2 + x2, 0.0, 1.0))
        aux = self.aux_head(d2) if self.aux_head is not None else None
        semantic = self._upsample(self.project2(d2), x1.shape[-2:])
        merged = torch.cat((semantic, x1, detail), dim=2)
        d1 = self.detail_fuse(self.detail_attention(merged))
        class_spikes = self.head(d1)
        return self._pack(
            sequence, x1=x1, x2=x2, x3=x3, decoder=d1,
            class_spikes=class_spikes, auxiliary_spikes=aux,
        )


class DeepAttentionFPNNet(_TopThreeBase):
    """T3: four-level semantic encoder + low-res spike attention + concat FPN."""

    def __init__(self, *, class_count: int, input_channels: int) -> None:
        architecture = TOP_THREE_PRESETS["t03_deep_attention_fpn"]
        super().__init__(
            class_count=class_count,
            input_channels=input_channels,
            architecture=architecture,
        )
        assert self.enc4 is not None
        context_lif = _block_lif(self.enc4)
        decoder_lif = self.project3.neuron.config
        self.lowres_context = SpikingStage(
            128, 128, kernel_size=3, dilation=2, groups=128,
            norm=architecture.norm, lif=context_lif,
            neuron_kind=architecture.neuron_kind,
        )
        self.lowres_attention = SpikeDrivenMaskAttention(
            128,
            attention_channels=32,
            heads=4,
            lif=context_lif,
            norm=architecture.norm,
            neuron_kind=architecture.neuron_kind,
        )
        # Compressed FPN widths keep the accuracy-oriented four-stage encoder
        # near the ~100k-parameter target instead of carrying 96/48 channels
        # through every decoder fusion.
        self.project4 = SpikingStage(
            128, 64, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.lateral3 = SpikingStage(
            96, 64, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.fuse3 = SpikingConvBlock(
            128, 64, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.project3 = SpikingStage(
            64, 32, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.lateral2 = SpikingStage(
            48, 32, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.fuse2 = SpikingConvBlock(
            64, 32, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.project2 = SpikingStage(
            32, 24, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.lateral1 = SpikingStage(
            24, 24, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.fuse1 = SpikingConvBlock(
            48, 24, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.aux_head = SpikingClassHead(
            32, class_count, decoder_lif, architecture.neuron_kind,
            output_competition=architecture.output_competition_enabled,
        )
        self.refine3 = nn.Identity()
        self.refine2 = nn.Identity()
        self.refine1 = nn.Identity()

    def forward(self, sequence: Tensor) -> dict[str, Tensor]:
        assert self.down4 is not None and self.enc4 is not None
        assert self.project4 is not None
        x1 = self.enc1(self.stem(sequence))
        x2 = self.enc2(self.down2(x1))
        x3 = self.enc3(self.down3(x2))
        x4 = self.enc4(self.down4(x3))
        local_context = torch.clamp(self.lowres_context(x4) + x4, 0.0, 1.0)
        deepest = self.lowres_attention(local_context)

        d3 = self._upsample(self.project4(deepest), x3.shape[-2:])
        d3 = self.fuse3(torch.cat((d3, self.lateral3(x3)), dim=2))
        d2 = self._upsample(self.project3(d3), x2.shape[-2:])
        d2 = self.fuse2(torch.cat((d2, self.lateral2(x2)), dim=2))
        aux = self.aux_head(d2) if self.aux_head is not None else None
        d1 = self._upsample(self.project2(d2), x1.shape[-2:])
        d1 = self.fuse1(torch.cat((d1, self.lateral1(x1)), dim=2))
        class_spikes = self.head(d1)
        return self._pack(
            sequence, x1=x1, x2=x2, x3=x3, x4=x4, decoder=d1,
            class_spikes=class_spikes, auxiliary_spikes=aux,
        )


def build_top_three_model(
    name: str = TOP_THREE_DEFAULT,
    *,
    class_count: int = 6,
    input_channels: int = 6,
) -> EventSpikeSegBase:
    if name == "t01_spike_pyramid_concat":
        return SpikePyramidConcatNet(class_count=class_count, input_channels=input_channels)
    if name == "t02_dualpath_detail":
        return DualPathDetailNet(class_count=class_count, input_channels=input_channels)
    if name == "t03_deep_attention_fpn":
        return DeepAttentionFPNNet(class_count=class_count, input_channels=input_channels)
    raise KeyError(f"unknown top-three architecture {name!r}")
