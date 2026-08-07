"""Shared SNN segmentation components used by final and ablation models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Literal

import torch
from torch import Tensor, nn

try:
    from spikingjelly.activation_based import surrogate
except ImportError:  # lightweight test environments; Docker installs SpikingJelly
    class _ATanSpike(torch.autograd.Function):
        @staticmethod
        def forward(ctx, input_tensor: Tensor) -> Tensor:
            ctx.save_for_backward(input_tensor)
            return (input_tensor >= 0).to(input_tensor.dtype)

        @staticmethod
        def backward(ctx, grad_output: Tensor) -> Tensor:
            (input_tensor,) = ctx.saved_tensors
            return grad_output / (1.0 + input_tensor.square())

    class _ATanModule(nn.Module):
        def forward(self, input_tensor: Tensor) -> Tensor:
            return _ATanSpike.apply(input_tensor)

    class _SurrogateNamespace:
        ATan = _ATanModule

    surrogate = _SurrogateNamespace()
from torch.nn import functional as F

NormKind = Literal["none", "affine", "bn"]
ContextKind = Literal["none", "dilated", "multiscale"]
SkipKind = Literal["one", "two"]
NeuronKind = Literal["lif", "plif"]


@dataclass(frozen=True)
class LIFConfig:
    beta_shift: int = 4
    threshold: float = 0.5
    f_inst_enabled: bool = False
    competitor_decrement: float = 0.0
    f_long_enabled: bool = True
    adaptation_increment: float = 1.0 / 64.0
    adaptation_decay: float = 1.0 / 128.0
    t_thresh_steps: int = 0

    @property
    def beta(self) -> float:
        return 1.0 - 2.0 ** (-self.beta_shift)


@dataclass(frozen=True)
class SegmentationArchitecture:
    name: str
    base_channels: int = 24
    depthwise: bool = True
    context: ContextKind = "multiscale"
    context_dilations: tuple[int, ...] = (1, 2, 4)
    norm: NormKind = "affine"
    gap_gate: bool = False
    auxiliary_head: bool = False
    skip_kind: SkipKind = "two"
    residual: bool = True
    adaptive_threshold: bool = True
    neuron_kind: NeuronKind = "lif"
    f_inst_enabled: bool = False
    f_long_enabled: bool = False
    t_thresh_steps: int = 0
    output_rate_scale: float = 6.0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class HardwareLIF(nn.Module):
    """Discrete-time LIF with optional local competition and channel homeostasis."""

    def __init__(self, channels: int, config: LIFConfig) -> None:
        super().__init__()
        self.channels = channels
        self.config = config
        self.spike_function = surrogate.ATan()
        self.register_buffer("membrane", torch.empty(0), persistent=False)
        self.register_buffer("adaptation", torch.zeros(channels), persistent=False)
        self.register_buffer(
            "threshold_timer", torch.zeros(channels, dtype=torch.long), persistent=False
        )

    def reset(self) -> None:
        self.membrane = torch.empty(0, device=self.adaptation.device)
        self.adaptation.zero_()
        self.threshold_timer.zero_()

    def _ensure_state(self, current: Tensor) -> None:
        if self.membrane.shape != current.shape:
            self.membrane = torch.zeros_like(current)
        if self.adaptation.device != current.device or self.adaptation.dtype != current.dtype:
            self.adaptation = self.adaptation.to(current)
        if self.threshold_timer.device != current.device:
            self.threshold_timer = self.threshold_timer.to(current.device)

    def _leaked_membrane(self) -> Tensor:
        return self.membrane - self.membrane / float(1 << self.config.beta_shift)

    def forward(self, current: Tensor) -> Tensor:
        if current.ndim != 4 or current.shape[1] != self.channels:
            raise ValueError(f"expected [N,{self.channels},H,W] current")
        self._ensure_state(current)
        leaked = self._leaked_membrane()
        candidate = leaked + current
        threshold = (self.config.threshold + self.adaptation).view(1, -1, 1, 1)
        raw = self.spike_function(candidate - threshold)
        above = candidate >= threshold
        if self.config.f_inst_enabled:
            masked = candidate.masked_fill(~above, -torch.inf)
            winner = masked.argmax(dim=1, keepdim=True)
            gate = torch.zeros_like(above).scatter_(1, winner, True)
            gate &= above.any(dim=1, keepdim=True)
            spikes = raw * gate.to(raw.dtype)
        else:
            gate = above
            spikes = raw
        reset = gate.to(candidate.dtype) * threshold
        loser = (above & ~gate).to(candidate.dtype) * self.config.competitor_decrement
        self.membrane = candidate - reset - loser
        if self.config.f_long_enabled:
            activity = spikes.detach().amax(dim=(0, 2, 3))
            active = activity > 0
            if self.config.t_thresh_steps > 0:
                self.threshold_timer = torch.where(
                    active,
                    torch.full_like(self.threshold_timer, self.config.t_thresh_steps),
                    torch.clamp(self.threshold_timer - 1, min=0),
                )
                may_decay = self.threshold_timer == 0
                decayed = torch.where(
                    may_decay,
                    torch.clamp(
                        self.adaptation - self.config.adaptation_decay, min=0.0
                    ),
                    self.adaptation,
                )
            else:
                decayed = torch.clamp(
                    self.adaptation - self.config.adaptation_decay, min=0.0
                )
            self.adaptation = decayed + self.config.adaptation_increment * activity
        return spikes


class ParametricLIF(HardwareLIF):
    """PLIF neuron with learnable per-channel membrane retention."""

    def __init__(self, channels: int, config: LIFConfig) -> None:
        super().__init__(channels, config)
        beta = torch.full((channels,), config.beta).clamp(1e-4, 1.0 - 1e-4)
        self.beta_logit = nn.Parameter(torch.logit(beta))

    @property
    def beta(self) -> Tensor:
        return torch.sigmoid(self.beta_logit)

    def _leaked_membrane(self) -> Tensor:
        return self.membrane * self.beta.view(1, -1, 1, 1)


class ChannelAffine(nn.Module):
    """Per-channel gain without batch statistics; foldable into convolution weights."""

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.gain = nn.Parameter(torch.ones(channels))

    def forward(self, x: Tensor) -> Tensor:
        return x * self.gain.view(1, -1, 1, 1)


class ChannelGate(nn.Module):
    """SLTNet-inspired GAP channel gate used only in the dedicated ablation.

    This is a hybrid analog gate.  It is intentionally isolated so its value can be
    measured against the simpler FPGA-friendly affine alternative.
    """

    def __init__(self, channels: int, reduction: int = 4) -> None:
        super().__init__()
        hidden = max(4, channels // reduction)
        self.reduce = nn.Conv2d(channels, hidden, 1, bias=True)
        self.expand = nn.Conv2d(hidden, channels, 1, bias=True)

    def forward(self, x: Tensor) -> Tensor:
        pooled = x.mean(dim=(2, 3), keepdim=True)
        gate = torch.sigmoid(self.expand(F.relu(self.reduce(pooled))))
        return x * gate


class CurrentTransform(nn.Module):
    def __init__(self, channels: int, kind: NormKind) -> None:
        super().__init__()
        if kind == "none":
            self.op: nn.Module = nn.Identity()
        elif kind == "affine":
            self.op = ChannelAffine(channels)
        elif kind == "bn":
            self.op = nn.BatchNorm2d(channels)
        else:  # pragma: no cover
            raise ValueError(f"unknown norm kind: {kind}")

    def forward(self, x: Tensor) -> Tensor:
        return self.op(x)


class SpikingStage(nn.Module):
    """One convolution/current transform/LIF stage over a TNCHW sequence."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        *,
        kernel_size: int,
        stride: int = 1,
        dilation: int = 1,
        groups: int = 1,
        norm: NormKind = "none",
        lif: LIFConfig,
        neuron_kind: NeuronKind = "lif",
    ) -> None:
        super().__init__()
        padding = dilation * (kernel_size // 2)
        self.conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size,
            stride=stride,
            padding=padding,
            dilation=dilation,
            groups=groups,
            bias=False,
        )
        self.transform = CurrentTransform(out_channels, norm)
        neuron_type = ParametricLIF if neuron_kind == "plif" else HardwareLIF
        self.neuron = neuron_type(out_channels, lif)

    def reset(self) -> None:
        self.neuron.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        return torch.stack(
            [self.neuron(self.transform(self.conv(step.float()))) for step in sequence]
        )


class SpikingConvBlock(nn.Module):
    """Standard or depthwise/pointwise spiking convolution block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        *,
        stride: int = 1,
        dilation: int = 1,
        depthwise: bool,
        norm: NormKind,
        lif: LIFConfig,
        neuron_kind: NeuronKind = "lif",
        residual: bool = False,
    ) -> None:
        super().__init__()
        self.residual = residual and stride == 1 and in_channels == out_channels
        if depthwise:
            self.depthwise = SpikingStage(
                in_channels,
                in_channels,
                kernel_size=3,
                stride=stride,
                dilation=dilation,
                groups=in_channels,
                norm=norm,
                lif=lif,
                neuron_kind=neuron_kind,
            )
            self.pointwise = SpikingStage(
                in_channels,
                out_channels,
                kernel_size=1,
                norm=norm,
                lif=lif,
                neuron_kind=neuron_kind,
            )
            self.standard = None
        else:
            self.standard = SpikingStage(
                in_channels,
                out_channels,
                kernel_size=3,
                stride=stride,
                dilation=dilation,
                norm=norm,
                lif=lif,
                neuron_kind=neuron_kind,
            )
            self.depthwise = None
            self.pointwise = None

    def reset(self) -> None:
        for module in (self.standard, self.depthwise, self.pointwise):
            if module is not None:
                module.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        if self.standard is not None:
            output = self.standard(sequence)
        else:
            assert self.depthwise is not None and self.pointwise is not None
            output = self.pointwise(self.depthwise(sequence))
        if self.residual:
            output = torch.clamp(output + sequence, 0.0, 1.0)
        return output


class MultiScaleContext(nn.Module):
    """Parallel dilated depthwise branches followed by pointwise spiking fusion."""

    def __init__(
        self,
        channels: int,
        dilations: tuple[int, ...],
        *,
        norm: NormKind,
        lif: LIFConfig,
        gap_gate: bool,
        neuron_kind: NeuronKind = "lif",
    ) -> None:
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
                    neuron_kind=neuron_kind,
                )
                for dilation in dilations
            ]
        )
        self.fuse = SpikingStage(
            channels,
            channels,
            kernel_size=1,
            norm=norm,
            lif=lif,
            neuron_kind=neuron_kind,
        )
        self.gate = ChannelGate(channels) if gap_gate else None

    def reset(self) -> None:
        for branch in self.branches:
            branch.reset()
        self.fuse.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        branch_outputs = [branch(sequence) for branch in self.branches]
        merged = torch.stack(branch_outputs).mean(dim=0)
        if self.gate is not None:
            merged = torch.stack([self.gate(step) for step in merged])
        return self.fuse(merged)


class SpikingClassHead(nn.Module):
    def __init__(
        self,
        in_channels: int,
        class_count: int,
        lif: LIFConfig,
        neuron_kind: NeuronKind = "lif",
    ) -> None:
        super().__init__()
        output_lif = replace(lif, f_inst_enabled=True, f_long_enabled=False)
        self.stage = SpikingStage(
            in_channels,
            class_count,
            kernel_size=1,
            norm="none",
            lif=output_lif,
            neuron_kind=neuron_kind,
        )

    def reset(self) -> None:
        self.stage.reset()

    def forward(self, sequence: Tensor) -> Tensor:
        return self.stage(sequence)


class EventSpikeSegBase(nn.Module):
    """Lightweight event-only spiking encoder/decoder for DDD17 segmentation."""

    def __init__(
        self,
        *,
        class_count: int = 6,
        input_channels: int = 6,
        architecture: SegmentationArchitecture,
        lif: LIFConfig | None = None,
    ) -> None:
        super().__init__()
        self.architecture = architecture
        base_lif = lif or LIFConfig(
            f_inst_enabled=architecture.f_inst_enabled,
            f_long_enabled=(
                architecture.adaptive_threshold or architecture.f_long_enabled
            ),
            t_thresh_steps=architecture.t_thresh_steps,
        )
        neuron_kind = architecture.neuron_kind
        c1 = architecture.base_channels
        c2 = c1 * 2
        c3 = c1 * 4

        self.input_channels = input_channels
        self.stem = SpikingStage(
            input_channels,
            c1,
            kernel_size=3,
            norm=architecture.norm,
            lif=base_lif,
            neuron_kind=neuron_kind,
        )
        self.enc1 = SpikingConvBlock(
            c1, c1, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=base_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.down2 = SpikingConvBlock(
            c1, c2, stride=2, depthwise=architecture.depthwise,
            norm=architecture.norm, lif=base_lif, neuron_kind=neuron_kind,
        )
        self.enc2 = SpikingConvBlock(
            c2, c2, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=base_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.down3 = SpikingConvBlock(
            c2, c3, stride=2, depthwise=architecture.depthwise,
            norm=architecture.norm, lif=base_lif, neuron_kind=neuron_kind,
        )
        self.enc3 = SpikingConvBlock(
            c3, c3, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=base_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        if architecture.context == "none":
            self.context: nn.Module = nn.Identity()
        else:
            dilations = architecture.context_dilations
            if architecture.context == "dilated":
                dilations = (dilations[0],)
            self.context = MultiScaleContext(
                c3, dilations, norm=architecture.norm, lif=base_lif,
                gap_gate=architecture.gap_gate, neuron_kind=neuron_kind,
            )

        self.project3 = SpikingStage(
            c3,
            c2,
            kernel_size=1,
            norm=architecture.norm,
            lif=base_lif,
            neuron_kind=neuron_kind,
        )
        self.refine2 = SpikingConvBlock(
            c2, c2, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=base_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.project2 = SpikingStage(
            c2,
            c1,
            kernel_size=1,
            norm=architecture.norm,
            lif=base_lif,
            neuron_kind=neuron_kind,
        )
        self.refine1 = SpikingConvBlock(
            c1, c1, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=base_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.head = SpikingClassHead(c1, class_count, base_lif, neuron_kind)
        self.aux_head = (
            SpikingClassHead(c2, class_count, base_lif, neuron_kind)
            if architecture.auxiliary_head
            else None
        )
        self.class_count = class_count

    @staticmethod
    def _upsample(sequence: Tensor, size: tuple[int, int]) -> Tensor:
        t, n, c, _, _ = sequence.shape
        up = F.interpolate(sequence.flatten(0, 1), size=size, mode="nearest")
        return up.view(t, n, c, *size)

    def reset(self) -> None:
        for module in self.modules():
            if module is self:
                continue
            reset = getattr(module, "reset", None)
            if callable(reset) and not isinstance(module, EventSpikeSegBase):
                reset()

    def forward(self, sequence: Tensor) -> dict[str, Tensor]:
        if sequence.ndim != 5 or sequence.shape[2] != self.input_channels:
            raise ValueError(
                f"expected [T,N,{self.input_channels},H,W] direct-encoded event sequence"
            )
        x1 = self.enc1(self.stem(sequence))
        x2 = self.enc2(self.down2(x1))
        x3 = self.enc3(self.down3(x2))
        z3 = self.context(x3) if not isinstance(self.context, nn.Identity) else x3
        d2 = self._upsample(self.project3(z3), x2.shape[-2:])
        if self.architecture.skip_kind == "two":
            d2 = torch.clamp(d2 + x2, 0.0, 1.0)
        d2 = self.refine2(d2)
        aux_spikes = self.aux_head(d2) if self.aux_head is not None else None
        d1 = self._upsample(self.project2(d2), x1.shape[-2:])
        d1 = torch.clamp(d1 + x1, 0.0, 1.0)
        d1 = self.refine1(d1)
        class_spikes = self.head(d1)
        logits = class_spikes.sum(dim=0) * (
            self.architecture.output_rate_scale / float(sequence.shape[0])
        )
        result = {
            "segmentation_spikes": class_spikes,
            "segmentation_logits": logits,
            "enc1_spikes": x1,
            "enc2_spikes": x2,
            "enc3_spikes": x3,
            "decoder_spikes": d1,
        }
        if aux_spikes is not None:
            result["auxiliary_spikes"] = aux_spikes
            result["auxiliary_logits"] = aux_spikes.sum(dim=0) * (
                self.architecture.output_rate_scale / float(sequence.shape[0])
            )
        return result

    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters() if parameter.requires_grad)
