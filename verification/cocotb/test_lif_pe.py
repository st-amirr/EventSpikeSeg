import json
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def cycle(dut, current: int, threshold: int) -> tuple[int, int]:
    dut.current.value = current
    dut.threshold.value = threshold
    dut.valid.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    return dut.membrane.value.signed_integer, int(dut.spike.value)


@cocotb.test()
async def lif_matches_frozen_integer_order(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.valid.value = 0
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.reset.value = 0
    # The active helper consumes learned beta directly.  15/16 reproduces the
    # historical beta_shift=4 golden vector.
    dut.beta.value = 30_720
    path = Path(__file__).resolve().parents[1] / "golden_vectors" / "lif.json"
    vectors = json.loads(path.read_text())
    for step in vectors["steps"]:
        actual = await cycle(dut, step["current"], step["threshold"])
        assert actual == (step["membrane"], step["spike"])
