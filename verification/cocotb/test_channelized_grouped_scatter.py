import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def grouped_convolution_routes_only_within_matching_group(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.spike_valid.value = 0
    dut.contribution_ready.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    await FallingEdge(dut.clk)
    dut.spike_channel_i.value = 2
    dut.spike_x_i.value = 6
    dut.spike_y_i.value = 7
    dut.spike_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.spike_valid.value = 0

    observed = []
    while not int(dut.spike_ready.value):
        await Timer(1, units="ns")
        if int(dut.contribution_valid.value):
            observed.append(
                (
                    int(dut.destination_channel_o.value),
                    int(dut.destination_x_o.value),
                    int(dut.destination_y_o.value),
                    int(dut.weight_o.value),
                )
            )
            dut.contribution_ready.value = 1
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            dut.contribution_ready.value = 0
        else:
            await RisingEdge(dut.clk)

    # Four input/output channels split into two groups. Input channel 2 is local
    # channel 0 of group 1 and may therefore reach outputs 2 and 3 only.
    assert observed == [(2, 6, 7, 5), (3, 6, 7, 7)]
