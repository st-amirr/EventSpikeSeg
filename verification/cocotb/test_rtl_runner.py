from pathlib import Path

import pytest
from cocotb.runner import get_runner

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("top", "source", "test_module"),
    [
        ("lif_pe", "rtl/neuron/lif_pe.vhd", "test_lif_pe"),
        ("f_inst_top1", "rtl/inhibition/f_inst_top1.vhd", "test_f_inst"),
        (
            "channel_homeostasis",
            "rtl/homeostasis/channel_homeostasis.vhd",
            "test_homeostasis",
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
    ],
    ids=["lif", "f_inst", "homeostasis", "event_conv_address", "event_accumulator"],
)
def test_rtl_unit(top: str, source: str, test_module: str, tmp_path: Path) -> None:
    runner = get_runner("ghdl")
    runner.build(
        vhdl_sources=[ROOT / source],
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
