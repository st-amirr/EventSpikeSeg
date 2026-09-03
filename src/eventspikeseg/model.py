"""Canonical EventSpikeSeg models.

``EventSpikeSeg140k`` is the ~150k native-resolution dual-path model and is the project's
primary architecture for accuracy evaluation and digital neuromorphic deployment. Its
hidden feature path is spike-native; the final classifier accumulates continuous class
current over the complete temporal record.
``EventSpikeSegXL`` is the larger ~236k expansion retained as an
optional high-capacity comparison. The XL variant adds features beyond the canonical
model:

* 32/64/128 semantic encoder with residual depthwise/pointwise refinement;
* persistent 32-channel high-resolution detail stream;
* serial dilation-2 semantic context plus a residual d1/d2/d4 parallel context branch;
* one bottlenecked spike-mask attention residual at the deepest scale;
* projected residual bridges across 32->64 and 64->128 encoder transitions;
* concatenative mid-level decoder fusion instead of destructive addition;
* late semantic + shallow + detail concatenation followed by PLIF 1x1 cross-channel spike
  selection and depthwise/pointwise spiking fusion;
* asymmetric high-resolution detail refinement;
* deep and mid-level auxiliary semantic supervision;
* independent spiking class neurons with final temporal spike-count argmax;
* PLIF + learnable thresholds + stem-only peer-membrane inhibition +
  encoder/context triangular threshold adaptation.

The training engine may call ``set_semantic_backbone_trainable`` during the late
refinement phase.  The detail path, decoder, selector, auxiliary head, and final head
remain trainable while the semantic backbone is frozen.
"""

from __future__ import annotations

from dataclasses import replace

import torch
from torch import Tensor, nn

from .data import DEFAULT_INTERNAL_UPDATES, EVSEG_INTEGRATION_WINDOW_US
from .model_components import (
    EventSpikeSegBase,
    LIFConfig,
    SegmentationArchitecture,
    SpikingClassHead,
    SpikingConvBlock,
    SpikingStage,
    TimestampEventInput,
)

# Selectable finals: canonical EventSpikeSeg140k (~150k) and EventSpikeSegXL (~236k).
FINAL_ARCHITECTURE = SegmentationArchitecture(
    name="EventSpikeSeg140k",
    channel_schedule=(32, 64, 128),
    context="none",  # custom serial dilation-2 context below
    norm="affine",
    auxiliary_head=True,
    skip_kind="two",
    residual=True,
    adaptive_threshold=False,
    neuron_kind="plif",
    learnable_threshold=True,
    inhibition_enabled=True,
    inhibition_scope="stem",
    inhibition_kind="peer_membrane",
    inhibition_strength_init=0.20,
    threshold_adaptation_enabled=True,
    threshold_adaptation_scope="encoder_context",
    adaptation_kind="triangular_threshold",
    threshold_adaptation_strength_init=0.20,
    adaptation_duration_init=5.0,
    output_competition_enabled=False,
)

# Final-model-only late refinement schedule.  Keep the semantic backbone
# trainable until the final 10% so rare-class features can continue improving.
# A value of 1.0 leaves the backbone frozen through the last training epoch.
# The generic trainer discovers this attribute at runtime, so frozen historical
# benchmark models are unaffected.
FINAL_REFINEMENT_FREEZE_START = 0.90
FINAL_REFINEMENT_UNFREEZE_START = 1.00


def _block_lif(block: SpikingConvBlock) -> LIFConfig:
    """Return the LIF config used by the block's final spiking stage."""
    stage = block.pointwise if block.pointwise is not None else block.standard
    assert stage is not None
    return stage.neuron.config


class TemporalCurrentReadout(nn.Module):
    """Accumulate continuous class currents over a complete event record.

    Hidden features remain binary spikes.  Each active feature therefore causes a
    stored-weight addition in hardware, while the final classifier keeps the
    resulting multi-bit current instead of thresholding it into only ``T + 1``
    possible spike counts.  Processing one timestep at a time avoids materialising
    a full ``[T, N, Cclass, H, W]`` current tensor during memory-bound training.
    """

    def __init__(self, in_channels: int, out_channels: int, *, scale: float) -> None:
        super().__init__()
        self.synapse = nn.Conv2d(in_channels, out_channels, 1, bias=False)
        self.scale = float(scale)

    def forward(self, sequence: Tensor) -> Tensor:
        if sequence.ndim != 5:
            raise ValueError("expected a TNCHW spike sequence")
        accumulated: Tensor | None = None
        for step in sequence:
            current = self.synapse(step.float())
            accumulated = current if accumulated is None else accumulated + current
        assert accumulated is not None
        return accumulated * (self.scale / float(sequence.shape[0]))


class PLIFChannelSelector(nn.Module):
    """Spike-native cross-channel selector using a 1x1 synaptic projection + PLIF.

    The T2 selector learned cross-channel relationships from accumulated activity
    with a small dense count-domain network.  This replacement preserves the
    cross-channel learned decision while keeping the inference path spiking:

        fused spikes -> 1x1 synaptic mixing -> local PLIF selector spikes
                     -> per-neuron binary enable -> gate fused spikes

    The 1x1 operation is a normal spike-driven synaptic fan-out: an active input
    channel contributes its stored weight to selector-neuron membrane current.
    No dense multi-bit count-domain MLP, sigmoid attention, softmax, or global
    spatial reduction is needed at inference. Each selector spike gates only the
    corresponding retinotopic feature, so event-driven hardware can propagate it immediately
    without waiting for a complete frame.
    """

    def __init__(
        self,
        channels: int,
        *,
        lif: LIFConfig,
        norm: str = "affine",
    ) -> None:
        super().__init__()
        self.selector = SpikingStage(
            channels,
            channels,
            kernel_size=1,
            norm=norm,
            lif=lif,
            neuron_kind="plif",
        )

    def reset(self) -> None:
        self.selector.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        selector_spikes = self.selector(sequence)
        return sequence * selector_spikes


class ParallelDilatedResidualContext(nn.Module):
    """Residual d1/d2/d4 depthwise context with spiking 1x1 fusion."""

    def __init__(self, channels: int, *, lif: LIFConfig, norm: str) -> None:
        super().__init__()
        self.branches = nn.ModuleList(
            [
                SpikingStage(
                    channels,
                    channels,
                    kernel_size=3,
                    dilation=dilation,
                    groups=channels,
                    norm=norm,
                    lif=lif,
                    neuron_kind="plif",
                )
                for dilation in (1, 2, 4)
            ]
        )
        self.fuse = SpikingStage(
            channels * 3,
            channels,
            kernel_size=1,
            norm=norm,
            lif=lif,
            neuron_kind="plif",
        )

    def reset(self) -> None:
        for branch in self.branches:
            branch.reset()
        self.fuse.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        merged = torch.cat([branch(sequence) for branch in self.branches], dim=2)
        return torch.clamp(sequence + self.fuse(merged), 0.0, 1.0)


class SpikeDrivenMaskAttention(nn.Module):
    """Low-resolution spike-mask attention with no softmax or dense NxN matrix."""

    def __init__(
        self,
        channels: int,
        *,
        attention_channels: int,
        heads: int,
        lif: LIFConfig,
        norm: str,
    ) -> None:
        super().__init__()
        if attention_channels % heads != 0:
            raise ValueError("attention_channels must be divisible by heads")
        self.heads = heads
        self.head_dim = attention_channels // heads
        self.q = SpikingStage(
            channels, attention_channels, kernel_size=1, norm=norm, lif=lif, neuron_kind="plif"
        )
        self.k = SpikingStage(
            channels, attention_channels, kernel_size=1, norm=norm, lif=lif, neuron_kind="plif"
        )
        self.v = SpikingStage(
            channels, attention_channels, kernel_size=1, norm=norm, lif=lif, neuron_kind="plif"
        )
        self.out = SpikingStage(
            attention_channels, channels, kernel_size=1, norm=norm, lif=lif, neuron_kind="plif"
        )
        initial_fraction = torch.full((heads,), 0.25)
        self.attention_threshold_logit = nn.Parameter(torch.logit(initial_fraction))

    def reset(self) -> None:
        for module in (self.q, self.k, self.v, self.out):
            module.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        q = self.q(sequence)
        k = self.k(sequence)
        v = self.v(sequence)
        t, n, c, h, w = q.shape
        qh = q.view(t, n, self.heads, self.head_dim, h, w)
        kh = k.view(t, n, self.heads, self.head_dim, h, w)
        vh = v.view(t, n, self.heads, self.head_dim, h, w)

        coincidence = (qh * kh).sum(dim=3)
        fraction = torch.sigmoid(self.attention_threshold_logit)
        threshold = 1.0 + fraction * float(max(1, self.head_dim - 1))
        threshold = threshold.view(1, 1, self.heads, 1, 1)

        soft = torch.sigmoid(4.0 * (coincidence - threshold))
        hard = (coincidence >= threshold).to(soft.dtype)
        gate = hard.detach() - soft.detach() + soft
        attended = (vh * gate.unsqueeze(3)).reshape(t, n, c, h, w)
        return torch.clamp(sequence + self.out(attended), 0.0, 1.0)


class AsymmetricDetailResidual(nn.Module):
    """Spike-native 3x1 -> 1x3 depthwise detail refinement with residual."""

    def __init__(self, channels: int, *, lif: LIFConfig, norm: str) -> None:
        super().__init__()
        self.vertical = SpikingStage(
            channels,
            channels,
            kernel_size=(3, 1),
            groups=channels,
            norm=norm,
            lif=lif,
            neuron_kind="plif",
        )
        self.horizontal = SpikingStage(
            channels,
            channels,
            kernel_size=(1, 3),
            groups=channels,
            norm=norm,
            lif=lif,
            neuron_kind="plif",
        )
        self.mix = SpikingStage(
            channels,
            channels,
            kernel_size=1,
            norm=norm,
            lif=lif,
            neuron_kind="plif",
        )

    def reset(self) -> None:
        self.vertical.reset()
        self.horizontal.reset()
        self.mix.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        refined = self.mix(self.horizontal(self.vertical(sequence)))
        return torch.clamp(sequence + refined, 0.0, 1.0)


class DeepAuxiliaryHead(nn.Module):
    """Training-only deep semantic supervision branch."""

    def __init__(self, channels: int, class_count: int, *, lif: LIFConfig, norm: str) -> None:
        super().__init__()
        self.project = SpikingStage(
            channels, 32, kernel_size=1, norm=norm, lif=lif, neuron_kind="plif"
        )
        self.classifier = SpikingClassHead(
            32, class_count, lif, neuron_kind="plif", output_competition=False
        )

    def reset(self) -> None:
        self.project.reset()
        self.classifier.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        return self.classifier(self.project(sequence))


class EventSpikeSegXL(EventSpikeSegBase):
    """Expanded ~236k fully-spiking model retained as the XL comparison."""

    refinement_schedule = (
        FINAL_REFINEMENT_FREEZE_START,
        FINAL_REFINEMENT_UNFREEZE_START,
    )

    def __init__(
        self,
        *,
        class_count: int = 6,
        input_channels: int = 6,
        internal_updates: int = DEFAULT_INTERNAL_UPDATES,
    ) -> None:
        if input_channels not in (
            TimestampEventInput.source_channels,
            TimestampEventInput.event_channels,
        ):
            raise ValueError(
                "final models require six timestamp statistics or two raw-event channels"
            )
        if internal_updates < 1 or EVSEG_INTEGRATION_WINDOW_US % internal_updates != 0:
            raise ValueError("internal_updates must divide the 50,000 us interval exactly")
        super().__init__(
            class_count=class_count,
            input_channels=TimestampEventInput.event_channels,
            architecture=replace(FINAL_ARCHITECTURE, name="EventSpikeSegXL"),
        )
        self.source_input_channels = input_channels
        self.timestamp_input = (
            TimestampEventInput(
                integration_window_us=EVSEG_INTEGRATION_WINDOW_US,
                event_clock_us=EVSEG_INTEGRATION_WINDOW_US // internal_updates,
            )
            if input_channels == TimestampEventInput.source_channels
            else nn.Identity()
        )
        architecture = self.architecture
        encoder_lif = _block_lif(self.enc1)
        context_lif = _block_lif(self.enc3)
        decoder_lif = self.project3.neuron.config
        highres_lif = replace(encoder_lif, threshold_adaptation_enabled=False)

        # Keep triangular threshold adaptation from the first downsampled
        # semantic scale onward.
        # The full-resolution x1/detail stream preserves fine spatial evidence and
        # does not allocate per-pixel threshold-adaptation state.
        self.enc1 = SpikingConvBlock(
            32, 32, kernel_size=architecture.first_block_kernel_size,
            depthwise=architecture.depthwise, norm=architecture.norm,
            lif=highres_lif, neuron_kind=architecture.neuron_kind,
            residual=architecture.residual,
        )

        # The base encoder already contributes one residual block at each scale.
        # One additional block gives two residual DW/PW transformations per scale
        # without introducing a fourth spatial downsampling level.
        self.enc1_extra = SpikingConvBlock(
            32, 32, depthwise=True, norm=architecture.norm,
            lif=highres_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.enc2_extra = SpikingConvBlock(
            64, 64, depthwise=True, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.enc3_extra = SpikingConvBlock(
            128, 128, depthwise=True, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )

        # Projected residual bridges preserve earlier-stage spike evidence across
        # resolution/channel transitions rather than forcing all information through
        # the strided DW/PW path.
        self.bridge12 = SpikingStage(
            32, 64, kernel_size=1, stride=2, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.bridge23 = SpikingStage(
            64, 128, kernel_size=1, stride=2, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind,
        )

        # v03, the compact structural winner, and T2 all favored a simple
        # dilation-2 path over *averaged* multiscale branches. Keep that serial
        # path as the semantic backbone; the later parallel d1/d2/d4 module is a
        # residual branch-concatenation addition rather than a replacement/average.
        self.context1 = SpikingConvBlock(
            128, 128, dilation=2, depthwise=True, norm=architecture.norm,
            lif=context_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.context2 = SpikingConvBlock(
            128, 128, dilation=2, depthwise=True, norm=architecture.norm,
            lif=context_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )

        self.parallel_context = ParallelDilatedResidualContext(
            128, lif=context_lif, norm=architecture.norm
        )
        self.deep_attention = SpikeDrivenMaskAttention(
            128,
            attention_channels=32,
            heads=4,
            lif=context_lif,
            norm=architecture.norm,
        )
        # Auxiliary supervision should not allocate triangular adaptation state of
        # its own. It remains PLIF/learnable-threshold via decoder_lif.
        self.deep_aux_head = DeepAuxiliaryHead(
            128, class_count, lif=decoder_lif, norm=architecture.norm
        )

        # Persistent high-resolution path: the strongest new feature from T2.
        # High-resolution detail refinement is PLIF-only. Reusing encoder_lif
        # here unintentionally enabled per-pixel triangular adaptation state on every
        # detail stage, which is outside the intended scope and is very
        # expensive at native DDD17 resolution. decoder_lif preserves PLIF and
        # learned thresholds without inhibition or threshold adaptation.
        self.detail1 = SpikingConvBlock(
            32, 32, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.detail2 = AsymmetricDetailResidual(
            32, lif=decoder_lif, norm=architecture.norm,
        )
        self.detail3 = SpikingConvBlock(
            32, 32, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )

        # Preserve decoder and encoder identities until learned spiking fusion.
        self.decoder2_fuse = SpikingConvBlock(
            128, 64, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.decoder2_extra = SpikingConvBlock(
            64, 64, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.final_selector = PLIFChannelSelector(
            96, lif=decoder_lif, norm=architecture.norm
        )
        self.final_fuse = SpikingConvBlock(
            96, 32, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.decoder1_extra = SpikingConvBlock(
            32, 32, depthwise=True, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )

        # Base modules ``context`` and ``refine1`` are intentionally bypassed by the
        # custom forward; remove their trainable contribution if future base changes
        # ever make them non-identity / non-required for this architecture.
        self.context = nn.Identity()
        self.refine1 = nn.Identity()

    def set_semantic_backbone_trainable(self, trainable: bool) -> None:
        """Freeze/unfreeze only the semantic feature extractor for late refinement.

        The high-resolution detail stream, decoder projections/refinement, channel
        selector, auxiliary head, and final class head deliberately remain trainable.
        """
        semantic_modules: tuple[nn.Module, ...] = (
            self.stem,
            self.enc1,
            self.enc1_extra,
            self.down2,
            self.enc2,
            self.enc2_extra,
            self.down3,
            self.enc3,
            self.enc3_extra,
            self.bridge12,
            self.bridge23,
            self.context1,
            self.context2,
            self.parallel_context,
            self.deep_attention,
        )
        for module in semantic_modules:
            for parameter in module.parameters():
                parameter.requires_grad_(trainable)

    def forward(self, source: Tensor) -> dict[str, Tensor]:
        sequence = self.timestamp_input(source)
        x1 = self.enc1_extra(self.enc1(self.stem(sequence)))
        detail = self.detail3(self.detail2(self.detail1(x1)))

        x2_main = self.down2(x1)
        x2 = torch.clamp(x2_main + self.bridge12(x1), 0.0, 1.0)
        x2 = self.enc2_extra(self.enc2(x2))

        x3_main = self.down3(x2)
        x3 = torch.clamp(x3_main + self.bridge23(x2), 0.0, 1.0)
        x3 = self.enc3_extra(self.enc3(x3))

        deepest = self.context2(self.context1(x3))
        deepest = self.parallel_context(deepest)
        deepest = self.deep_attention(deepest)
        # Auxiliary branches optimize training only. Skipping them in eval/inference
        # preserves identical deployed logits while avoiding unnecessary spike state.
        deep_auxiliary_spikes = self.deep_aux_head(deepest) if self.training else None

        d2 = self._upsample(self.project3(deepest), x2.shape[-2:])
        d2 = self.decoder2_fuse(torch.cat((d2, x2), dim=2))
        d2 = self.decoder2_extra(d2)
        auxiliary_spikes = (
            self.aux_head(d2)
            if self.training and self.aux_head is not None
            else None
        )

        semantic = self._upsample(self.project2(d2), x1.shape[-2:])
        merged = torch.cat((semantic, x1, detail), dim=2)
        d1 = self.final_fuse(self.final_selector(merged))
        d1 = self.decoder1_extra(d1)

        class_spikes = self.head(d1)
        normalization = self.temporal_normalization_steps(sequence)
        logits = class_spikes.sum(dim=0) * (
            self.architecture.output_rate_scale / normalization
        )
        # Return exact scalar activity means instead of pinning full TNCHW
        # hidden sequences in the output dictionary until backward completes.
        # The activity regularizer depends only on these means, so its math and
        # gradients are unchanged.
        result = {
            "segmentation_logits": logits,
            "segmentation_rate": self.temporal_rate(class_spikes),
            "enc1_rate": self.temporal_rate(x1),
            "enc2_rate": self.temporal_rate(x2),
            "enc3_rate": self.temporal_rate(x3),
            "decoder_rate": self.temporal_rate(d1),
        }
        if not self.training:
            # Evaluation visualizations may still need the output spike raster;
            # under no_grad this does not retain a training autograd graph.
            result["segmentation_spikes"] = class_spikes
        if auxiliary_spikes is not None:
            result["auxiliary_logits"] = auxiliary_spikes.sum(dim=0) * (
                self.architecture.output_rate_scale / normalization
            )
        if deep_auxiliary_spikes is not None:
            result["deep_auxiliary_logits"] = deep_auxiliary_spikes.sum(dim=0) * (
                self.architecture.output_rate_scale / normalization
            )
        return result


class EventSpikeSeg140k(EventSpikeSegBase):
    """Memory-bounded native-resolution dual-path DSEC segmentation model."""

    refinement_schedule = (
        FINAL_REFINEMENT_FREEZE_START,
        FINAL_REFINEMENT_UNFREEZE_START,
    )

    def __init__(
        self,
        *,
        class_count: int = 6,
        input_channels: int = 6,
        internal_updates: int = DEFAULT_INTERNAL_UPDATES,
    ) -> None:
        if input_channels not in (
            TimestampEventInput.source_channels,
            TimestampEventInput.event_channels,
        ):
            raise ValueError(
                "final models require six timestamp statistics or two raw-event channels"
            )
        if internal_updates < 1 or EVSEG_INTEGRATION_WINDOW_US % internal_updates != 0:
            raise ValueError("internal_updates must divide the 50,000 us interval exactly")
        super().__init__(
            class_count=class_count,
            input_channels=TimestampEventInput.event_channels,
            architecture=FINAL_ARCHITECTURE,
        )
        self.source_input_channels = input_channels
        self.timestamp_input = (
            TimestampEventInput(
                integration_window_us=EVSEG_INTEGRATION_WINDOW_US,
                event_clock_us=EVSEG_INTEGRATION_WINDOW_US // internal_updates,
            )
            if input_channels == TimestampEventInput.source_channels
            else nn.Identity()
        )
        architecture = self.architecture
        stem_lif = self.stem.neuron.config
        encoder_lif = _block_lif(self.enc1)
        context_lif = _block_lif(self.enc3)
        decoder_lif = self.project3.neuron.config
        half_lif = replace(encoder_lif, threshold_adaptation_enabled=False)
        native_lif = replace(
            decoder_lif,
            inhibition_enabled=False,
            threshold_adaptation_enabled=False,
        )

        # Preserve native DSEC evidence until it reaches learned filters, but put
        # the wide semantic trunk at half resolution.  This is substantially less
        # expensive than executing the old 32/96-channel graph at 440x640.
        self.detail_stem = SpikingStage(
            2, 8, kernel_size=3, norm=architecture.norm,
            lif=native_lif, neuron_kind=architecture.neuron_kind,
        )
        self.detail1 = SpikingConvBlock(
            8, 8, depthwise=False, norm=architecture.norm,
            lif=native_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.detail2 = nn.Identity()
        self.detail3 = nn.Identity()

        self.stem = SpikingStage(
            2, 32, kernel_size=5, stride=2, norm=architecture.norm,
            lif=stem_lif, neuron_kind=architecture.neuron_kind,
        )
        # Early joint spatial/channel filtering is intentionally standard rather
        # than depthwise-separable; later stages retain efficient DW/PW blocks.
        self.enc1 = SpikingConvBlock(
            32, 32, depthwise=False, norm=architecture.norm,
            lif=half_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.enc1_extra = SpikingConvBlock(
            32, 32, depthwise=True, norm=architecture.norm,
            lif=half_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.down2 = SpikingConvBlock(
            32, 64, stride=2, depthwise=False, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.enc2_extra = SpikingConvBlock(
            64, 64, depthwise=True, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.enc3_extra = SpikingConvBlock(
            128, 128, depthwise=True, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.context1 = SpikingConvBlock(
            128, 128, dilation=2, depthwise=True, norm=architecture.norm,
            lif=context_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )
        self.context2 = SpikingConvBlock(
            128, 128, dilation=2, depthwise=True, norm=architecture.norm,
            lif=context_lif, neuron_kind=architecture.neuron_kind, residual=True,
        )

        # Keep encoder and decoder spike identities separate until one shared
        # synaptic accumulator has combined them. This replaces binary OR plus a
        # DW->PLIF->PW bottleneck with one cross-channel fusion before threshold.
        self.decoder2_fuse = SpikingStage(
            128, 64, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.final_selector = nn.Identity()
        self.final_fuse = SpikingConvBlock(
            40, 16, depthwise=False, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=architecture.neuron_kind,
        )
        self.decoder1_extra = nn.Identity()
        self.head = TemporalCurrentReadout(
            16, class_count, scale=architecture.output_rate_scale
        )
        self.boundary_head = TemporalCurrentReadout(
            16, 1, scale=architecture.output_rate_scale
        )
        self.context = nn.Identity()
        self.refine2 = nn.Identity()
        self.refine1 = nn.Identity()

    def set_semantic_backbone_trainable(self, trainable: bool) -> None:
        semantic_modules: tuple[nn.Module, ...] = (
            self.stem,
            self.enc1,
            self.enc1_extra,
            self.down2,
            self.enc2,
            self.enc2_extra,
            self.down3,
            self.enc3,
            self.enc3_extra,
            self.context1,
            self.context2,
        )
        for module in semantic_modules:
            for parameter in module.parameters():
                parameter.requires_grad_(trainable)

    def forward(self, source: Tensor) -> dict[str, Tensor]:
        sequence = self.timestamp_input(source)
        native_size = sequence.shape[-2:]
        detail = self.detail1(self.detail_stem(sequence))
        x1 = self.enc1_extra(self.enc1(self.stem(sequence)))

        x2 = self.enc2_extra(self.enc2(self.down2(x1)))
        x3 = self.enc3_extra(self.enc3(self.down3(x2)))
        deepest = self.context2(self.context1(x3))

        d2 = self._upsample(self.project3(deepest), x2.shape[-2:])
        d2 = self.decoder2_fuse(torch.cat((d2, x2), dim=2))
        auxiliary_spikes = (
            self.aux_head(d2)
            if self.training and self.aux_head is not None
            else None
        )

        semantic = self._upsample(self.project2(d2), x1.shape[-2:])
        # Preserve coincident encoder/decoder events as multiplicity 2 instead of
        # collapsing them with binary OR. The following standard convolution
        # accumulates both contributions before its single PLIF threshold.
        semantic = semantic + x1
        semantic = self._upsample(semantic, native_size)
        merged = torch.cat((semantic, detail), dim=2)
        d1 = self.final_fuse(merged)
        d1 = self.decoder1_extra(d1)

        logits = self.head(d1)
        result = {
            "segmentation_logits": logits,
            # There are no output class spikes; report the last hidden spike rate
            # for activity regularisation and run diagnostics.
            "segmentation_rate": self.temporal_rate(d1),
            "enc1_rate": self.temporal_rate(x1),
            "enc2_rate": self.temporal_rate(x2),
            "enc3_rate": self.temporal_rate(x3),
            "decoder_rate": self.temporal_rate(d1),
        }
        if self.training:
            result["boundary_logits"] = self.boundary_head(d1)
        if auxiliary_spikes is not None:
            normalization = self.temporal_normalization_steps(sequence)
            result["auxiliary_logits"] = auxiliary_spikes.sum(dim=0) * (
                self.architecture.output_rate_scale / normalization
            )
        return result



FINAL_MODELS = {
    "EventSpikeSeg140k": EventSpikeSeg140k,
    "EventSpikeSegXL": EventSpikeSegXL,
}


def build_model(
    *,
    class_count: int = 6,
    input_channels: int = 6,
    architecture: str = "EventSpikeSeg140k",
    internal_updates: int = DEFAULT_INTERNAL_UPDATES,
) -> EventSpikeSegBase:
    try:
        model_class = FINAL_MODELS[architecture]
    except KeyError as exc:
        raise KeyError(
            f"unknown final architecture {architecture!r}; "
            f"expected one of {tuple(FINAL_MODELS)}"
        ) from exc
    if internal_updates < 1 or EVSEG_INTEGRATION_WINDOW_US % internal_updates != 0:
        raise ValueError(
            "internal_updates must be positive and divide the 50,000 us interval exactly"
        )
    return model_class(
        class_count=class_count,
        input_channels=input_channels,
        internal_updates=internal_updates,
    )
