import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def reset_dut(dut):
    dut.reset.value = 1
    dut.presynaptic_valid.value = 0
    dut.epoch_end_valid.value = 0
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def send_spike(dut, channel: int, x: int, y: int):
    while not int(dut.presynaptic_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_channel_i.value = channel
    dut.presynaptic_x_i.value = x
    dut.presynaptic_y_i.value = y
    dut.presynaptic_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid.value = 0


async def finish_epoch(dut, tag: int):
    while not int(dut.epoch_end_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.epoch_tag_i.value = tag
    dut.epoch_end_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.epoch_end_valid.value = 0

    spikes = []
    for _ in range(200):
        await RisingEdge(dut.clk)
        if int(dut.spike_valid.value):
            spikes.append(
                (
                    int(dut.spike_channel_o.value),
                    int(dut.spike_x_o.value),
                    int(dut.spike_y_o.value),
                )
            )
        if int(dut.epoch_done_valid.value):
            assert int(dut.epoch_tag_o.value) == tag
            dut.epoch_done_ready.value = 1
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            dut.epoch_done_ready.value = 0
            return spikes
    raise AssertionError("channelized actor did not complete the epoch")


@cocotb.test()
async def channel_state_and_parameters_are_independent_at_the_same_coordinate(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # One input spike contributes six to output channels 0 and 1 at (2,3).
    # Channel thresholds are five and ten, respectively.
    await send_spike(dut, channel=0, x=2, y=3)
    assert await finish_epoch(dut, tag=1) == [(0, 2, 3)]

    # State persists independently: channel 0 retained one after subtractive
    # reset, while channel 1 retained six. On the second epoch both spike.
    await send_spike(dut, channel=0, x=2, y=3)
    assert await finish_epoch(dut, tag=2) == [(0, 2, 3), (1, 2, 3)]
    assert int(dut.routing_error_o.value) == 0
