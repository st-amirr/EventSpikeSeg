import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def output_channels_reach_independent_banks_in_one_clock(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.spike_valid.value = 0
    dut.spike_channel_i.value = 0
    dut.spike_x_i.value = 1
    dut.spike_y_i.value = 1
    dut.contribution_ready.value = 0b1111
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    dut.spike_valid.value = 1
    await Timer(1, units="ns")
    assert int(dut.spike_ready.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    await Timer(1, units="ns")

    valid = int(dut.contribution_valid.value)
    assert valid == 0b1010
    assert int(dut.spike_ready.value) == 1
    observed = []
    for lane in (1, 3):
        channel = (int(dut.destination_channel_o.value) >> lane) & 1
        x = (int(dut.destination_x_o.value) >> (lane * 10)) & 0x3FF
        y = (int(dut.destination_y_o.value) >> (lane * 10)) & 0x3FF
        weight = (int(dut.weight_o.value) >> (lane * 8)) & 0xFF
        observed.append((channel, y, x, weight))
    assert observed == [(0, 1, 1, 6), (1, 1, 1, 7)]
    # The accepted projection set is replaced without an empty bubble.
    dut.spike_x_i.value = 2
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.spike_valid.value = 0
    await Timer(1, units="ns")
    assert int(dut.contribution_valid.value) == 0b0101
    assert int(dut.spike_ready.value) == 1
