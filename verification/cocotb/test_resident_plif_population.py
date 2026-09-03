import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


@cocotb.test()
async def resident_state_updates_without_memory_fetch(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.contribution_valid_i.value = 0
    dut.destination_i.value = 0
    dut.weight_i.value = 0
    dut.dense_current_valid_i.value = 0
    dut.dense_current_delta_i.value = 0
    dut.completion_valid_i.value = 0
    dut.completion_tag_i.value = 0
    dut.spike_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    # Two simultaneous static-synapse contributions target neurons 0 and 3.
    dut.contribution_valid_i.value = 0b11
    dut.destination_i.value = 0 | (3 << 2)
    dut.weight_i.value = 6 | (12 << 8)
    assert int(dut.contribution_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.contribution_valid_i.value = 0
    dut.completion_valid_i.value = 1
    dut.completion_tag_i.value = 7
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.completion_valid_i.value = 0
    assert int(dut.spike_valid_o.value) == 1
    assert int(dut.spike_vector_o.value) == 0b1001
    assert int(dut.completion_tag_o.value) == 7

    dut.spike_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.spike_valid_o.value) == 0
