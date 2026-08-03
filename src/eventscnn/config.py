"""Typed, validated configuration for the canonical EventSCNN model."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventBinningConfig:
    """Fixed-duration event binning configuration, using microsecond timestamps."""

    width: int = 240
    height: int = 180
    bin_duration_us: int = 1_000

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("event resolution must be positive")
        if self.bin_duration_us <= 0:
            raise ValueError("bin_duration_us must be positive")


@dataclass(frozen=True)
class LIFConfig:
    """Hardware-compatible LIF and competition/homeostasis parameters."""

    beta_shift: int = 4
    threshold: float = 1.0
    f_inst_enabled: bool = True
    competitor_decrement: float = 0.25
    f_long_enabled: bool = True
    adaptation_increment: float = 0.0625
    adaptation_decay: float = 1.0 / 32.0

    def __post_init__(self) -> None:
        if self.beta_shift < 1:
            raise ValueError("beta_shift must be at least one")
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")
        if self.competitor_decrement < 0:
            raise ValueError("competitor_decrement cannot be negative")
        if self.adaptation_increment < 0 or self.adaptation_decay < 0:
            raise ValueError("adaptation parameters cannot be negative")

    @property
    def beta(self) -> float:
        return 1.0 - 2.0 ** (-self.beta_shift)


@dataclass(frozen=True)
class LayerConfig:
    in_channels: int
    out_channels: int
    kernel_size: tuple[int, int]
    stride: tuple[int, int]
    padding: tuple[int, int]

    def __post_init__(self) -> None:
        if self.in_channels <= 0 or self.out_channels <= 0:
            raise ValueError("channel counts must be positive")
        if any(value <= 0 for value in self.kernel_size + self.stride):
            raise ValueError("kernel and stride dimensions must be positive")
        if any(value < 0 for value in self.padding):
            raise ValueError("padding cannot be negative")


def _default_layers() -> tuple[LayerConfig, ...]:
    return (
        LayerConfig(2, 8, (5, 5), (2, 2), (2, 2)),
        LayerConfig(8, 16, (3, 3), (2, 2), (1, 1)),
        LayerConfig(16, 32, (3, 3), (2, 2), (1, 1)),
    )


@dataclass(frozen=True)
class BackboneConfig:
    layers: tuple[LayerConfig, ...] = field(default_factory=_default_layers)
    lif: LIFConfig = field(default_factory=LIFConfig)

    def __post_init__(self) -> None:
        if len(self.layers) != 3:
            raise ValueError("the version-1 backbone requires exactly three layers")
        for previous, current in zip(self.layers, self.layers[1:]):
            if previous.out_channels != current.in_channels:
                raise ValueError("adjacent layer channel counts do not match")
