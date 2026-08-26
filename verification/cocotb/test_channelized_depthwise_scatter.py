import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def depthwise_group_routes_only_matching_channel(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.spike_valid.value = 0
    dut.contribution_ready.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await FallingEdge(dut.clk)
    dut.spike_channel_i.value = 1
    dut.spike_x_i.value = 2
    dut.spike_y_i.value = 3
    dut.spike_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.spike_valid.value = 0

    await Timer(1, units="ns")
    assert int(dut.contribution_valid.value) == 1
    assert int(dut.destination_channel_o.value) == 1
    assert int(dut.destination_x_o.value) == 2
    assert int(dut.destination_y_o.value) == 3
    assert int(dut.weight_o.value) == 8
    dut.contribution_ready.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.contribution_valid.value) == 0
