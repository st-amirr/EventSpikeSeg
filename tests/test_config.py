import pytest

from eventscnn.config import BackboneConfig, EventBinningConfig, LIFConfig


def test_canonical_configuration() -> None:
    config = BackboneConfig()
    assert [(layer.in_channels, layer.out_channels) for layer in config.layers] == [
        (2, 8),
        (8, 16),
        (16, 32),
    ]
    assert LIFConfig(beta_shift=4).beta == 0.9375


@pytest.mark.parametrize("duration", [0, -1])
def test_invalid_bin_duration(duration: int) -> None:
    with pytest.raises(ValueError):
        EventBinningConfig(bin_duration_us=duration)
