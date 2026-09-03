import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def actor_uses_global_coordinates_but_owns_only_tile_state(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.presynaptic_valid_i.value = 0
    dut.presynaptic_spike_vector_i.value = 0
    dut.completion_valid_i.value = 0
    dut.completion_tag_i.value = 0
    dut.result_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    # Full coordinates x=2 and x=3 feed a tile covering only those positions.
    dut.presynaptic_spike_vector_i.value = 0b1100
    dut.presynaptic_valid_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid_i.value = 0
    dut.completion_valid_i.value = 1
    dut.completion_tag_i.value = 3
    await Timer(1, units="ns")
    assert int(dut.completion_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.result_valid_o.value) == 1
    assert int(dut.spike_vector_o.value) == 0b11
    assert int(dut.completion_tag_o.value) == 3
    assert int(dut.error_o.value) == 0
