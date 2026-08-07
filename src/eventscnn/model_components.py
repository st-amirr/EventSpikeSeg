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
HomeostasisKind = Literal["legacy", "rate", "triangular_threshold"]
InhibitionKind = Literal["gate", "peer_membrane", "winner_peer"]
CompetitionScope = Literal["none", "stem", "encoder", "all"]
HomeostasisScope = Literal["none", "encoder", "all"]


@dataclass(frozen=True)
class LIFConfig:
    beta_shift: int = 4
    threshold: float = 0.5
    threshold_min: float = 0.15
    threshold_max: float = 1.25
    learnable_threshold: bool = False
    f_inst_enabled: bool = False
    f_inst_top_k: int = 1
    f_inst_group_size: int = 0
    competitor_decrement: float = 0.0
    inhibition_kind: InhibitionKind = "gate"
    inhibition_strength_init: float = 0.35
    inhibition_strength_min: float = 0.0
    inhibition_strength_max: float = 4.0
    f_long_enabled: bool = True
    homeostasis_kind: HomeostasisKind = "legacy"
    adaptation_increment: float = 1.0 / 64.0
    adaptation_decay: float = 1.0 / 128.0
    t_thresh_steps: int = 0
    target_rate: float = 0.08
    target_rate_min: float = 0.01
    target_rate_max: float = 0.20
    adaptation_tau_init: float = 4.0
    adaptation_tau_min: float = 1.0
    adaptation_tau_max: float = 20.0
    adaptation_strength_init: float = 0.05
    adaptation_strength_min: float = 0.001
    adaptation_strength_max: float = 0.25
    adaptation_clip: float = 0.35
    # Debat et al. (2021)-inspired membrane-energy inhibition/homeostasis.
    # The published fInst/fLong/TThresh values were optimized as layer-level
    # hyperparameters.  Here their continuous counterparts are learnable.
    threshold_adaptation_strength_init: float = 0.35
    threshold_adaptation_strength_min: float = 0.0
    threshold_adaptation_strength_max: float = 4.0
    adaptation_duration_init: float = 6.0
    adaptation_duration_min: float = 1.0
    adaptation_duration_max: float = 16.0
    membrane_energy_clip: float = 1.5

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
    learnable_threshold: bool = False
    f_inst_enabled: bool = False
    f_inst_scope: CompetitionScope = "all"
    f_inst_top_k: int = 1
    f_inst_group_size: int = 0
    inhibition_kind: InhibitionKind = "gate"
    inhibition_strength_init: float = 0.35
    f_long_enabled: bool = False
    f_long_scope: HomeostasisScope = "all"
    homeostasis_kind: HomeostasisKind = "legacy"
    homeostasis_target_rate: float = 0.08
    homeostasis_tau_init: float = 4.0
    homeostasis_strength_init: float = 0.05
    threshold_adaptation_strength_init: float = 0.35
    adaptation_duration_init: float = 6.0
    t_thresh_steps: int = 0
    output_f_inst_enabled: bool = True
    output_rate_scale: float = 6.0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class HardwareLIF(nn.Module):
    """Discrete-time LIF with optional competition and adaptive threshold state.

    Three modes are retained deliberately:

    * ``legacy`` preserves the completed round-one/two checkpoints.
    * ``rate`` preserves the first v2 rate-homeostasis experiment.
    * ``custom`` uses the project retinotopic inhibition and triangular threshold adaptation derived from Debat et al. (2021): inhibition and threshold penalty are
      driven by the local mean squared membrane potential ``UPropInh``.  The
      published inverted-V threshold response is implemented directly as a
      triangular rise/fall process with a learnable continuous TThresh-like time
      scale.  UPropInh follows the supplementary equation as the local RMS of
      membrane potential after subtracting the active threshold adaptation.

    The source mechanism is asynchronous: the first neuron to spike prevents retinotopic
    peers from spiking and reduces their membrane by UInst.  ``winner_peer``
    emulates that winner/inhibition rule inside a synchronous timestep;
    ``peer_membrane`` keeps simultaneous spikes but still applies the UInst-like
    membrane decrement.  Keeping both lets dense semantic segmentation test the
    published rule against a less destructive adaptation.
    """

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
        self.register_buffer("homeostasis_scale", torch.tensor(1.0), persistent=False)
        # Threshold-adaptation state follows every retinotopic neuron. Each spiking
        # neuron owns one triangular ULong process; all active processes at the
        # same (x,y) are summed to form the shared UAT threshold penalty.
        self.register_buffer("threshold_adaptation_age", torch.empty(0), persistent=False)
        self.register_buffer("threshold_adaptation_amplitude", torch.empty(0), persistent=False)
        self.register_buffer("threshold_adaptation_penalty", torch.empty(0), persistent=False)
        self.competition_enabled = True

        if config.f_long_enabled and config.homeostasis_kind == "rate":
            self.adaptation_tau_logit = nn.Parameter(
                self._bounded_logit(
                    config.adaptation_tau_init,
                    config.adaptation_tau_min,
                    config.adaptation_tau_max,
                    channels,
                )
            )
            self.adaptation_strength_logit = nn.Parameter(
                self._bounded_logit(
                    config.adaptation_strength_init,
                    config.adaptation_strength_min,
                    config.adaptation_strength_max,
                    channels,
                )
            )
            self.target_rate_logit = nn.Parameter(
                self._bounded_logit(
                    config.target_rate,
                    config.target_rate_min,
                    config.target_rate_max,
                    channels,
                )
            )
        else:
            self.register_parameter("adaptation_tau_logit", None)
            self.register_parameter("adaptation_strength_logit", None)
            self.register_parameter("target_rate_logit", None)

        if config.f_inst_enabled and config.inhibition_kind in {"peer_membrane", "winner_peer"}:
            self.inhibition_strength_logit = nn.Parameter(
                self._bounded_logit(
                    config.inhibition_strength_init,
                    config.inhibition_strength_min,
                    config.inhibition_strength_max,
                    1,
                )
            )
        else:
            self.register_parameter("inhibition_strength_logit", None)

        if config.f_long_enabled and config.homeostasis_kind == "triangular_threshold":
            self.threshold_adaptation_strength_logit = nn.Parameter(
                self._bounded_logit(
                    config.threshold_adaptation_strength_init,
                    config.threshold_adaptation_strength_min,
                    config.threshold_adaptation_strength_max,
                    1,
                )
            )
            self.adaptation_duration_logit = nn.Parameter(
                self._bounded_logit(
                    config.adaptation_duration_init,
                    config.adaptation_duration_min,
                    config.adaptation_duration_max,
                    1,
                )
            )
        else:
            self.register_parameter("threshold_adaptation_strength_logit", None)
            self.register_parameter("adaptation_duration_logit", None)

    @staticmethod
    def _bounded_logit(value: float, minimum: float, maximum: float, channels: int) -> Tensor:
        fraction = (value - minimum) / max(maximum - minimum, 1e-8)
        fraction = min(max(fraction, 1e-4), 1.0 - 1e-4)
        return torch.full((channels,), torch.logit(torch.tensor(fraction)).item())

    @staticmethod
    def _bounded(parameter: Tensor, minimum: float, maximum: float) -> Tensor:
        return minimum + (maximum - minimum) * torch.sigmoid(parameter)

    @property
    def adaptation_tau(self) -> Tensor | None:
        if self.adaptation_tau_logit is None:
            return None
        return self._bounded(
            self.adaptation_tau_logit,
            self.config.adaptation_tau_min,
            self.config.adaptation_tau_max,
        )

    @property
    def adaptation_strength(self) -> Tensor | None:
        if self.adaptation_strength_logit is None:
            return None
        return self._bounded(
            self.adaptation_strength_logit,
            self.config.adaptation_strength_min,
            self.config.adaptation_strength_max,
        )

    @property
    def target_rate(self) -> Tensor | None:
        if self.target_rate_logit is None:
            return None
        return self._bounded(
            self.target_rate_logit,
            self.config.target_rate_min,
            self.config.target_rate_max,
        )

    @property
    def inhibition_strength(self) -> Tensor | None:
        if self.inhibition_strength_logit is None:
            return None
        return self._bounded(
            self.inhibition_strength_logit,
            self.config.inhibition_strength_min,
            self.config.inhibition_strength_max,
        )

    @property
    def threshold_adaptation_strength(self) -> Tensor | None:
        if self.threshold_adaptation_strength_logit is None:
            return None
        return self._bounded(
            self.threshold_adaptation_strength_logit,
            self.config.threshold_adaptation_strength_min,
            self.config.threshold_adaptation_strength_max,
        )

    @property
    def adaptation_duration(self) -> Tensor | None:
        if self.adaptation_duration_logit is None:
            return None
        return self._bounded(
            self.adaptation_duration_logit,
            self.config.adaptation_duration_min,
            self.config.adaptation_duration_max,
        )

    def reset(self) -> None:
        self.membrane = torch.empty(0, device=self.adaptation.device)
        self.adaptation = torch.zeros_like(self.adaptation).detach()
        self.threshold_timer.zero_()
        self.threshold_adaptation_age = torch.empty(0, device=self.adaptation.device)
        self.threshold_adaptation_amplitude = torch.empty(0, device=self.adaptation.device)
        self.threshold_adaptation_penalty = torch.empty(0, device=self.adaptation.device)

    def set_homeostasis_scale(self, value: float) -> None:
        self.homeostasis_scale.fill_(float(value))

    def set_competition_enabled(self, enabled: bool) -> None:
        self.competition_enabled = bool(enabled)

    def _ensure_state(self, current: Tensor) -> None:
        if self.membrane.shape != current.shape:
            self.membrane = torch.zeros_like(current)
        if self.adaptation.device != current.device or self.adaptation.dtype != current.dtype:
            self.adaptation = self.adaptation.to(current)
        if self.threshold_timer.device != current.device:
            self.threshold_timer = self.threshold_timer.to(current.device)
        if self.homeostasis_scale.device != current.device:
            self.homeostasis_scale = self.homeostasis_scale.to(current.device)
        if self.config.homeostasis_kind == "triangular_threshold":
            if self.threshold_adaptation_age.shape != current.shape:
                self.threshold_adaptation_age = torch.full_like(current, -1.0)
                self.threshold_adaptation_amplitude = torch.zeros_like(current)
                self.threshold_adaptation_penalty = torch.zeros(
                    (current.shape[0], 1, current.shape[2], current.shape[3]),
                    device=current.device,
                    dtype=current.dtype,
                )
            elif self.threshold_adaptation_age.device != current.device or self.threshold_adaptation_age.dtype != current.dtype:
                self.threshold_adaptation_age = self.threshold_adaptation_age.to(current)
                self.threshold_adaptation_amplitude = self.threshold_adaptation_amplitude.to(current)
                self.threshold_adaptation_penalty = self.threshold_adaptation_penalty.to(current)

    def _leaked_membrane(self) -> Tensor:
        return self.membrane - self.membrane / float(1 << self.config.beta_shift)

    def _base_threshold(self, current: Tensor) -> Tensor:
        return torch.full(
            (self.channels,), self.config.threshold, device=current.device, dtype=current.dtype
        )

    def _competition_gate(self, candidate: Tensor, above: Tensor) -> Tensor:
        if not self.config.f_inst_enabled or not self.competition_enabled:
            return above
        if self.config.inhibition_kind == "peer_membrane":
            # Synchronous adaptation: keep simultaneous feature spikes, then
            # apply Debat et al. UInst membrane decrement to their peers.
            return above
        if self.config.inhibition_kind == "winner_peer":
            # Published retinotopic competition: the first/strongest neuron at
            # one location wins the current instant and peers are prevented from
            # spiking.  We use maximum membrane because bins have no event order.
            masked = candidate.masked_fill(~above, -torch.inf)
            winner = masked.argmax(dim=1, keepdim=True)
            gate = torch.zeros_like(above).scatter_(1, winner, True)
            any_above = above.any(dim=1, keepdim=True)
            return gate & any_above
        group_size = self.config.f_inst_group_size or self.channels
        if group_size <= 0 or self.channels % group_size != 0:
            group_size = self.channels
        groups = self.channels // group_size
        n, _, h, w = candidate.shape
        grouped_candidate = candidate.view(n, groups, group_size, h, w)
        grouped_above = above.view(n, groups, group_size, h, w)
        masked = grouped_candidate.masked_fill(~grouped_above, -torch.inf)
        k = min(max(1, self.config.f_inst_top_k), group_size)
        indices = masked.topk(k, dim=2).indices
        gate = torch.zeros_like(grouped_above).scatter_(2, indices, True)
        gate &= grouped_above
        return gate.view_as(above)

    def _retinotopic_membrane_energy(self, candidate: Tensor) -> Tensor:
        """Local UPropInh from Debat et al. supplementary Eq. 7.

        Debat et al. uses the RMS membrane potential of neurons connected to the
        same retinotopic patch after subtracting the active threshold adaptation.
        The scalar is therefore shared across feature maps at one (x,y).
        """
        if self.threshold_adaptation_penalty.numel() == 0:
            adjusted = candidate
        else:
            adjusted = candidate - self.threshold_adaptation_penalty
        rms = torch.sqrt(adjusted.square().mean(dim=1, keepdim=True) + 1e-8)
        return rms.clamp(max=self.config.membrane_energy_clip)

    def _triangular_threshold_penalty(self) -> Tensor:
        """Sum triangular ULong processes at each retinotopic location.

        Debat et al. Eq. 6 rises linearly from zero to UMaxThresh over TThresh,
        then falls linearly to zero over another TThresh.  Each feature neuron
        keeps its own last-spike process; Eq. 5 sums them across filters.
        """
        if self.threshold_adaptation_age.numel() == 0:
            return self.threshold_adaptation_penalty
        t_thresh = self.adaptation_duration
        assert t_thresh is not None
        t = t_thresh.view(1, 1, 1, 1)
        age = self.threshold_adaptation_age
        active = age >= 0.0
        phase = torch.where(active, age / t, torch.zeros_like(age))
        triangle = torch.where(
            phase <= 1.0,
            phase,
            torch.where(phase < 2.0, 2.0 - phase, torch.zeros_like(phase)),
        )
        triangle = torch.where(active, triangle.clamp(min=0.0), torch.zeros_like(triangle))
        per_neuron = self.threshold_adaptation_amplitude * triangle
        return per_neuron.sum(dim=1, keepdim=True)

    def _apply_peer_membrane_inhibition(self, candidate: Tensor, spikes: Tensor) -> None:
        if (
            not self.config.f_inst_enabled
            or self.config.inhibition_kind not in {"peer_membrane", "winner_peer"}
            or not self.competition_enabled
        ):
            return
        strength = self.inhibition_strength
        assert strength is not None
        # An output spike at a retinotopic location inhibits peer feature maps.
        # The spiking neuron itself is excluded because it has already reset.
        u_prop = self._retinotopic_membrane_energy(candidate)
        trigger = (spikes.detach().sum(dim=1, keepdim=True) > 0).to(candidate.dtype)
        peers = (spikes.detach() <= 0).to(candidate.dtype)
        decrement = (
            self.homeostasis_scale
            * strength.view(1, 1, 1, 1)
            * u_prop
            * trigger
        )
        self.membrane = self.membrane - decrement * peers

    def _update_homeostasis(self, spikes: Tensor, candidate: Tensor) -> None:
        if not self.config.f_long_enabled:
            return
        if self.config.homeostasis_kind == "legacy":
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
                    torch.clamp(self.adaptation - self.config.adaptation_decay, min=0.0),
                    self.adaptation,
                )
            else:
                decayed = torch.clamp(
                    self.adaptation - self.config.adaptation_decay, min=0.0
                )
            self.adaptation = decayed + self.config.adaptation_increment * activity
            return

        if self.config.homeostasis_kind == "rate":
            tau = self.adaptation_tau
            strength = self.adaptation_strength
            target = self.target_rate
            assert tau is not None and strength is not None and target is not None
            activity = spikes.mean(dim=(0, 2, 3))
            retention = torch.exp(-1.0 / tau)
            error = activity - target
            updated = retention * self.adaptation + self.homeostasis_scale * strength * error
            self.adaptation = torch.clamp(
                updated, -self.config.adaptation_clip, self.config.adaptation_clip
            )
            return

        # Triangular-threshold mode: every neuron keeps one inverted-V ULong process keyed
        # to its latest spike.  Its peak amplitude is fLong * UPropInh.  TThresh
        # is continuous and learnable because it appears directly in the
        # triangular phase calculation used on the next forward pass.
        strength = self.threshold_adaptation_strength
        assert strength is not None
        u_prop = self._retinotopic_membrane_energy(candidate)
        scaled_amplitude = (
            self.homeostasis_scale
            * strength.view(1, 1, 1, 1)
            * u_prop
        )
        spiked = spikes > 0
        # A new spike resets that neuron's triangular process. Existing ages
        # were advanced at the start of this forward step, before thresholding.
        self.threshold_adaptation_age = torch.where(spiked, torch.zeros_like(self.threshold_adaptation_age), self.threshold_adaptation_age)
        self.threshold_adaptation_amplitude = torch.where(
            spiked,
            scaled_amplitude.expand_as(self.threshold_adaptation_amplitude),
            self.threshold_adaptation_amplitude,
        )
        # Keep a detached-looking state name for diagnostics/tests, but preserve
        # the autograd graph because learned fLong/TThresh are trained through it.
        self.threshold_adaptation_penalty = self._triangular_threshold_penalty()

    def _advance_threshold_adaptation(self) -> None:
        if (
            self.config.homeostasis_kind == "triangular_threshold"
            and self.config.f_long_enabled
            and self.threshold_adaptation_age.numel() > 0
        ):
            self.threshold_adaptation_age = torch.where(
                self.threshold_adaptation_age >= 0.0,
                self.threshold_adaptation_age + 1.0,
                self.threshold_adaptation_age,
            )

    def _threshold_tensor(self, current: Tensor) -> Tensor:
        base = self._base_threshold(current).view(1, -1, 1, 1)
        if self.config.homeostasis_kind == "triangular_threshold" and self.config.f_long_enabled:
            self.threshold_adaptation_penalty = self._triangular_threshold_penalty()
            effective = base + self.threshold_adaptation_penalty
            return effective.clamp(self.config.threshold_min, self.config.threshold_max)
        effective = base + self.adaptation.view(1, -1, 1, 1)
        if self.config.homeostasis_kind == "rate" or self.config.learnable_threshold:
            effective = effective.clamp(
                self.config.threshold_min, self.config.threshold_max
            )
        return effective

    def forward(self, current: Tensor) -> Tensor:
        if current.ndim != 4 or current.shape[1] != self.channels:
            raise ValueError(f"expected [N,{self.channels},H,W] current")
        self._ensure_state(current)
        self._advance_threshold_adaptation()
        leaked = self._leaked_membrane()
        candidate = leaked + current
        threshold = self._threshold_tensor(current)
        raw = self.spike_function(candidate - threshold)
        above = candidate >= threshold
        gate = self._competition_gate(candidate, above)
        spikes = raw * gate.to(raw.dtype)
        reset = gate.to(candidate.dtype) * threshold
        loser = (above & ~gate).to(candidate.dtype) * self.config.competitor_decrement
        self.membrane = candidate - reset - loser
        self._apply_peer_membrane_inhibition(candidate, spikes)
        self._update_homeostasis(spikes, candidate)
        return spikes


class ParametricLIF(HardwareLIF):
    """PLIF with learnable per-channel retention and optional base threshold."""

    def __init__(self, channels: int, config: LIFConfig) -> None:
        super().__init__(channels, config)
        beta = torch.full((channels,), config.beta).clamp(1e-4, 1.0 - 1e-4)
        self.beta_logit = nn.Parameter(torch.logit(beta))
        if config.learnable_threshold:
            self.threshold_logit = nn.Parameter(
                self._bounded_logit(
                    config.threshold,
                    config.threshold_min,
                    config.threshold_max,
                    channels,
                )
            )
        else:
            self.register_parameter("threshold_logit", None)

    @property
    def beta(self) -> Tensor:
        return torch.sigmoid(self.beta_logit)

    @property
    def learned_threshold(self) -> Tensor | None:
        if self.threshold_logit is None:
            return None
        return self._bounded(
            self.threshold_logit,
            self.config.threshold_min,
            self.config.threshold_max,
        )

    def _leaked_membrane(self) -> Tensor:
        return self.membrane * self.beta.view(1, -1, 1, 1)

    def _base_threshold(self, current: Tensor) -> Tensor:
        learned = self.learned_threshold
        if learned is None:
            return super()._base_threshold(current)
        return learned.to(device=current.device, dtype=current.dtype)


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
        *,
        output_competition: bool = True,
    ) -> None:
        super().__init__()
        output_lif = replace(
            lif,
            f_inst_enabled=output_competition,
            f_inst_top_k=1,
            f_inst_group_size=0,
            inhibition_kind="gate",
            f_long_enabled=False,
        )
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
            f_inst_top_k=architecture.f_inst_top_k,
            f_inst_group_size=architecture.f_inst_group_size,
            inhibition_kind=architecture.inhibition_kind,
            inhibition_strength_init=architecture.inhibition_strength_init,
            f_long_enabled=(architecture.adaptive_threshold or architecture.f_long_enabled),
            homeostasis_kind=architecture.homeostasis_kind,
            target_rate=architecture.homeostasis_target_rate,
            adaptation_tau_init=architecture.homeostasis_tau_init,
            adaptation_strength_init=architecture.homeostasis_strength_init,
            threshold_adaptation_strength_init=architecture.threshold_adaptation_strength_init,
            adaptation_duration_init=architecture.adaptation_duration_init,
            t_thresh_steps=architecture.t_thresh_steps,
            learnable_threshold=architecture.learnable_threshold,
        )
        neuron_kind = architecture.neuron_kind

        def enabled_for(scope: str, stage: str) -> bool:
            if scope == "none":
                return False
            if scope == "all":
                return True
            if scope == "stem":
                return stage == "stem"
            if scope == "encoder":
                return stage in {"stem", "encoder", "context"}
            raise ValueError(f"unknown stage scope {scope!r}")

        def lif_for(stage: str) -> LIFConfig:
            return replace(
                base_lif,
                f_inst_enabled=(
                    architecture.f_inst_enabled
                    and enabled_for(architecture.f_inst_scope, stage)
                ),
                f_long_enabled=(
                    (architecture.adaptive_threshold or architecture.f_long_enabled)
                    and enabled_for(architecture.f_long_scope, stage)
                ),
            )

        stem_lif = lif_for("stem")
        encoder_lif = lif_for("encoder")
        context_lif = lif_for("context")
        decoder_lif = lif_for("decoder")
        c1 = architecture.base_channels
        c2 = c1 * 2
        c3 = c1 * 4

        self.input_channels = input_channels
        self.stem = SpikingStage(
            input_channels, c1, kernel_size=3, norm=architecture.norm,
            lif=stem_lif, neuron_kind=neuron_kind,
        )
        self.enc1 = SpikingConvBlock(
            c1, c1, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.down2 = SpikingConvBlock(
            c1, c2, stride=2, depthwise=architecture.depthwise,
            norm=architecture.norm, lif=encoder_lif, neuron_kind=neuron_kind,
        )
        self.enc2 = SpikingConvBlock(
            c2, c2, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.down3 = SpikingConvBlock(
            c2, c3, stride=2, depthwise=architecture.depthwise,
            norm=architecture.norm, lif=encoder_lif, neuron_kind=neuron_kind,
        )
        self.enc3 = SpikingConvBlock(
            c3, c3, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=encoder_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        if architecture.context == "none":
            self.context: nn.Module = nn.Identity()
        else:
            dilations = architecture.context_dilations
            if architecture.context == "dilated":
                dilations = (dilations[0],)
            self.context = MultiScaleContext(
                c3, dilations, norm=architecture.norm, lif=context_lif,
                gap_gate=architecture.gap_gate, neuron_kind=neuron_kind,
            )

        self.project3 = SpikingStage(
            c3, c2, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=neuron_kind,
        )
        self.refine2 = SpikingConvBlock(
            c2, c2, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.project2 = SpikingStage(
            c2, c1, kernel_size=1, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=neuron_kind,
        )
        self.refine1 = SpikingConvBlock(
            c1, c1, depthwise=architecture.depthwise, norm=architecture.norm,
            lif=decoder_lif, neuron_kind=neuron_kind, residual=architecture.residual,
        )
        self.head = SpikingClassHead(
            c1, class_count, decoder_lif, neuron_kind,
            output_competition=architecture.output_f_inst_enabled,
        )
        self.aux_head = (
            SpikingClassHead(
                c2, class_count, decoder_lif, neuron_kind,
                output_competition=architecture.output_f_inst_enabled,
            )
            if architecture.auxiliary_head else None
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

    def set_homeostasis_scale(self, value: float) -> None:
        for module in self.modules():
            if isinstance(module, HardwareLIF):
                module.set_homeostasis_scale(value)

    def set_competition_enabled(self, enabled: bool) -> None:
        for module in self.modules():
            if isinstance(module, HardwareLIF):
                module.set_competition_enabled(enabled)

    def set_hidden_inhibition_enabled(self, enabled: bool) -> None:
        """Enable/disable only hidden retinotopic inhibition modules.

        The semantic class head intentionally uses the historical ``gate`` WTA,
        so it remains active while an exact hidden retinotopic competition is
        delayed during training.  This avoids reintroducing the abrupt early
        feature starvation observed in v2.
        """
        for module in self.modules():
            if (
                isinstance(module, HardwareLIF)
                and module.config.inhibition_kind in {"peer_membrane", "winner_peer"}
            ):
                module.set_competition_enabled(enabled)

    def neuron_diagnostics(self) -> dict[str, float]:
        betas: list[Tensor] = []
        thresholds: list[Tensor] = []
        taus: list[Tensor] = []
        strengths: list[Tensor] = []
        targets: list[Tensor] = []
        inhibition_values: list[Tensor] = []
        threshold_adaptation_values: list[Tensor] = []
        adaptation_duration_values: list[Tensor] = []
        for module in self.modules():
            if isinstance(module, ParametricLIF):
                betas.append(module.beta.detach().flatten())
                learned = module.learned_threshold
                if learned is not None:
                    thresholds.append(learned.detach().flatten())
            if isinstance(module, HardwareLIF):
                if module.adaptation_tau is not None:
                    taus.append(module.adaptation_tau.detach().flatten())
                if module.adaptation_strength is not None:
                    strengths.append(module.adaptation_strength.detach().flatten())
                if module.target_rate is not None:
                    targets.append(module.target_rate.detach().flatten())
                if module.inhibition_strength is not None:
                    inhibition_values.append(module.inhibition_strength.detach().flatten())
                if module.threshold_adaptation_strength is not None:
                    threshold_adaptation_values.append(module.threshold_adaptation_strength.detach().flatten())
                if module.adaptation_duration is not None:
                    adaptation_duration_values.append(module.adaptation_duration.detach().flatten())

        def mean(values: list[Tensor]) -> float:
            return float(torch.cat(values).mean()) if values else float("nan")

        return {
            "mean_beta": mean(betas),
            "mean_base_threshold": mean(thresholds),
            "mean_adaptation_tau": mean(taus),
            "mean_adaptation_strength": mean(strengths),
            "mean_target_rate": mean(targets),
            "mean_inhibition_strength": mean(inhibition_values),
            "mean_threshold_adaptation_strength": mean(threshold_adaptation_values),
            "mean_adaptation_duration": mean(adaptation_duration_values),
        }

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
        return sum(
            parameter.numel() for parameter in self.parameters()
            if parameter.requires_grad
        )

