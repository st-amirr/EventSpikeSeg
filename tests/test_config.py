import pytest

from eventscnn.model import BackboneConfig, EventBinningConfig, LIFConfig


def test_canonical_configuration() -> None:
    config = BackboneConfig()
    assert [(layer.in_channels, layer.out_channels) for layer in config.layers] == [
        (2, 32),
        (32, 64),
        (64, 128),
    ]
    assert LIFConfig(beta_shift=4).beta == 0.9375


@pytest.mark.parametrize("duration", [0, -1])
def test_invalid_bin_duration(duration: int) -> None:
    with pytest.raises(ValueError):
        EventBinningConfig(bin_duration_us=duration)
