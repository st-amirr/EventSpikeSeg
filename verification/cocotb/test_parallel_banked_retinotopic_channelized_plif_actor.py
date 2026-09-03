import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def reset_dut(dut) -> None:
    dut.reset.value = 1
    dut.presynaptic_valid.value = 0
    dut.presynaptic_channel_i.value = 0
    dut.presynaptic_x_i.value = 0
    dut.presynaptic_y_i.value = 0
    dut.epoch_end_valid.value = 0
    dut.epoch_tag_i.value = 0
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    for _ in range(300):
        await RisingEdge(dut.clk)
        if int(dut.initialization_done_o.value):
            return
    raise AssertionError("parallel retinotopic actor did not initialize")


async def send_spike(dut, x: int, y: int) -> None:
    await FallingEdge(dut.clk)
    dut.presynaptic_x_i.value = x
    dut.presynaptic_y_i.value = y
    dut.presynaptic_valid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.presynaptic_ready.value):
            break
    await FallingEdge(dut.clk)
    dut.presynaptic_valid.value = 0


async def close_and_collect(dut, tag: int) -> list[tuple[int, int, int]]:
    await FallingEdge(dut.clk)
    dut.epoch_tag_i.value = tag
    dut.epoch_end_valid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.epoch_end_ready.value):
            break
    await FallingEdge(dut.clk)
    dut.epoch_end_valid.value = 0
    spikes = []
    for _ in range(400):
        await RisingEdge(dut.clk)
        if int(dut.spike_valid.value):
            spikes.append(
                (
                    int(dut.spike_channel_o.value),
                    int(dut.spike_y_o.value),
                    int(dut.spike_x_o.value),
                )
            )
        if int(dut.epoch_done_valid.value):
            return spikes
    raise AssertionError("parallel retinotopic actor did not complete")


@cocotb.test()
async def parallel_spatial_scatter_preserves_atomic_peer_inhibition(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # One input projects both output channels at one pixel into the same
    # retinotopic bank. Channel 0 exceeds threshold and suppresses channel 1.
    await send_spike(dut, 0, 0)
    # A second pixel uses a different spatial lane and must retain global coords.
    await send_spike(dut, 1, 0)
    assert sorted(await close_and_collect(dut, 1)) == [(0, 0, 0), (0, 0, 1)]
    assert int(dut.routing_error_o.value) == 0
