from pathlib import Path

import pytest
from cocotb.runner import get_runner

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("top", "sources", "test_module", "parameters"),
    [
        ("plif_update", ["asic/rtl/plif_update.sv"], "test_plif_update", {}),
        (
            "presynaptic_tap_array",
            ["asic/rtl/presynaptic_tap_array.sv"],
            "test_presynaptic_tap_array",
            {},
        ),
        (
            "asynchronous_plif_actor",
            ["asic/rtl/plif_update.sv", "asic/rtl/asynchronous_plif_actor.sv"],
            "test_asynchronous_plif_actor",
            {},
        ),
        (
            "convolution_plif_actor",
            [
                "asic/rtl/presynaptic_tap_array.sv",
                "asic/rtl/plif_update.sv",
                "asic/rtl/asynchronous_plif_actor.sv",
                "asic/rtl/convolution_plif_actor.sv",
            ],
            "test_convolution_plif_actor",
            {"KERNEL_WEIGHTS": sum(20 << (8 * tap) for tap in range(9))},
        ),
        (
            "peer_membrane_inhibition",
            ["asic/rtl/peer_membrane_inhibition.sv"],
            "test_peer_membrane_inhibition",
            {},
        ),
        (
            "triangular_threshold_adaptation",
            ["asic/rtl/triangular_threshold_adaptation.sv"],
            "test_triangular_threshold_adaptation",
            {},
        ),
        ("class_argmax", ["asic/rtl/class_argmax.sv"], "test_class_argmax", {}),
        (
            "class_current_update",
            ["asic/rtl/class_current_update.sv"],
            "test_class_current_update",
            {},
        ),
        ("event_fork2", ["asic/rtl/event_fork2.sv"], "test_event_fork2", {}),
        ("event_join2", ["asic/rtl/event_join2.sv"], "test_event_join2", {}),
        (
            "binary_event_union2",
            ["asic/rtl/binary_event_union2.sv"],
            "test_binary_event_union2",
            {"MAX_EVENTS": 8},
        ),
        (
            "event_channel_offset",
            ["asic/rtl/event_channel_offset.sv"],
            "test_event_channel_offset",
            {"CHANNEL_OFFSET": 64},
        ),
        ("event_upsample2x", ["asic/rtl/event_upsample2x.sv"], "test_event_upsample2x", {}),
        (
            "channelized_convolution_scatter",
            ["asic/rtl/channelized_convolution_scatter.sv"],
            "test_channelized_convolution_scatter",
            {
                "INPUT_CHANNELS": 2,
                "OUTPUT_CHANNELS": 3,
                "GROUPS": 1,
                "KERNEL_WIDTH": 1,
                "KERNEL_HEIGHT": 1,
                "PAD_X": 0,
                "PAD_Y": 0,
                "KERNEL_WEIGHTS": 0x05FC00030201,
            },
        ),
        (
            "channelized_convolution_scatter",
            ["asic/rtl/channelized_convolution_scatter.sv"],
            "test_channelized_grouped_scatter",
            {
                "INPUT_CHANNELS": 4,
                "OUTPUT_CHANNELS": 4,
                "GROUPS": 2,
                "KERNEL_WIDTH": 1,
                "KERNEL_HEIGHT": 1,
                "PAD_X": 0,
                "PAD_Y": 0,
                "KERNEL_WEIGHTS": 0x0807060504030201,
            },
        ),
        (
            "channelized_convolution_scatter",
            ["asic/rtl/channelized_convolution_scatter.sv"],
            "test_channelized_depthwise_scatter",
            {
                "INPUT_CHANNELS": 3,
                "OUTPUT_CHANNELS": 3,
                "GROUPS": 3,
                "KERNEL_WIDTH": 1,
                "KERNEL_HEIGHT": 1,
                "PAD_X": 0,
                "PAD_Y": 0,
                "KERNEL_WEIGHTS": 0x090807,
            },
        ),
    ],
    ids=[
        "plif_update",
        "presynaptic_tap_array",
        "asynchronous_plif_actor",
        "convolution_plif_actor",
        "peer_membrane_inhibition",
        "triangular_threshold_adaptation",
        "class_argmax",
        "class_current_update",
        "event_fork2",
        "event_join2",
        "binary_event_union2",
        "event_channel_offset",
        "event_upsample2x",
        "channelized_standard_scatter",
        "channelized_grouped_scatter",
        "channelized_depthwise_scatter",
    ],
)
def test_asic_rtl(
    top: str,
    sources: list[str],
    test_module: str,
    parameters: dict[str, int],
    tmp_path: Path,
) -> None:
    runner = get_runner("icarus")
    runner.build(
        verilog_sources=[ROOT / item for item in sources],
        hdl_toplevel=top,
        build_dir=tmp_path / top,
        always=True,
        build_args=["-g2012"],
        parameters=parameters,
    )
    runner.test(
        hdl_toplevel=top,
        test_module=test_module,
        test_dir=tmp_path / top,
    )
