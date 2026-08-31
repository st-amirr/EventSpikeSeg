import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


async def reset_dut(dut):
    dut.reset.value = 1
    dut.spike_valid.value = 0
    dut.contribution_ready.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def send(dut, channel: int, x: int, y: int):
    while not int(dut.spike_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.spike_channel_i.value = channel
    dut.spike_x_i.value = x
    dut.spike_y_i.value = y
    dut.spike_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.spike_valid.value = 0


async def collect(dut, limit: int = 20):
    values = []
    for _ in range(limit):
        await Timer(1, units="ns")
        if int(dut.contribution_valid.value):
            weight = int(dut.weight_o.value)
            if weight & 0x80:
                weight -= 0x100
            values.append(
                (
                    int(dut.destination_channel_o.value),
                    int(dut.destination_x_o.value),
                    int(dut.destination_y_o.value),
                    weight,
                )
            )
            dut.contribution_ready.value = 1
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            dut.contribution_ready.value = 0
            continue
        if int(dut.spike_ready.value):
            return values
        await RisingEdge(dut.clk)
    raise AssertionError("scatter did not drain")


@cocotb.test()
async def standard_convolution_fans_one_input_channel_to_all_weighted_outputs(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send(dut, channel=1, x=4, y=5)
    # Packed [out][in] weights are [1,2], [3,0], [-4,5]. Zero is suppressed.
    assert await collect(dut) == [(0, 4, 5, 2), (2, 4, 5, 5)]
