import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def direct_bitmap_convolution_commits_resident_plifs(dut) -> None:
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

    # Both input pixels spike; a direct 1x1 weight of +6 reaches threshold 5.
    dut.presynaptic_spike_vector_i.value = 0b11
    dut.presynaptic_valid_i.value = 1
    assert int(dut.presynaptic_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid_i.value = 0
    dut.completion_valid_i.value = 1
    dut.completion_tag_i.value = 9
    await Timer(1, units="ns")
    assert int(dut.completion_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.completion_valid_i.value = 0
    assert int(dut.result_valid_o.value) == 1
    assert int(dut.spike_vector_o.value) == 0b11
    assert int(dut.completion_tag_o.value) == 9
    assert int(dut.error_o.value) == 0
