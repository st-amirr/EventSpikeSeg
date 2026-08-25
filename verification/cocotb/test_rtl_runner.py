from pathlib import Path
from typing import Union

import pytest
from cocotb.runner import get_runner

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("top", "source", "test_module"),
    [
        ("lif_pe", "rtl/neuron/lif_pe.vhd", "test_lif_pe"),
        ("plif_update", "rtl/neuron/plif_update.vhd", "test_plif_update"),
        (
            "winner_peer_selector",
            "rtl/inhibition/winner_peer_selector.vhd",
            "test_winner_peer_selector",
        ),
        (
            "channel_rate_adaptation",
            "rtl/adaptation/channel_rate_adaptation.vhd",
            "test_rate_adaptation",
        ),
        (
            "event_conv_address",
            "rtl/event_conv/event_conv_address.vhd",
            "test_event_conv_address",
        ),
        (
            "event_accumulator",
            "rtl/event_conv/event_accumulator.vhd",
            "test_event_accumulator",
        ),
        (
            "sparse_state_bank",
            "rtl/state/sparse_state_bank.vhd",
            "test_sparse_state_bank",
        ),
        (
            "streaming_bin_controller",
            "rtl/control/streaming_bin_controller.vhd",
            "test_streaming_bin_controller",
        ),
        ("class_argmax", "rtl/control/class_argmax.vhd", "test_class_argmax"),
        (
            "class_current_update",
            "rtl/control/class_current_update.vhd",
            "test_class_current_update",
        ),
        (
            "ping_pong_event_buffer",
            "rtl/control/ping_pong_event_buffer.vhd",
            "test_ping_pong_event_buffer",
        ),
        (
            "touched_neuron_lane",
            [
                "rtl/state/sparse_state_bank.vhd",
                "rtl/neuron/plif_update.vhd",
                "rtl/neuron/touched_neuron_lane.vhd",
            ],
            "test_touched_neuron_lane",
        ),
    ],
    ids=[
        "lif",
        "plif_update",
        "winner_peer",
        "rate_adaptation",
        "event_conv_address",
        "event_accumulator",
        "sparse_state_bank",
        "streaming_bin_controller",
        "class_argmax",
        "class_current_update",
        "ping_pong_event_buffer",
        "touched_neuron_lane",
    ],
)
def test_rtl_unit(
    top: str, source: Union[str, list[str]], test_module: str, tmp_path: Path
) -> None:
    runner = get_runner("ghdl")
    sources = [source] if isinstance(source, str) else source
    runner.build(
        vhdl_sources=[ROOT / item for item in sources],
        hdl_toplevel=top,
        build_dir=tmp_path / top,
        always=True,
        build_args=["--std=08"],
    )
    runner.test(
        hdl_toplevel=top,
        test_module=test_module,
        test_dir=tmp_path / top,
        test_args=["--std=08"],
    )
