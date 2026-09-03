import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def reset_dut(dut) -> None:
    dut.reset.value = 1
    dut.presynaptic_valid.value = 0
    dut.presynaptic_channel_i.value = 0
    dut.presynaptic_x_i.value = 1
    dut.presynaptic_y_i.value = 1
    dut.epoch_end_valid.value = 0
    dut.epoch_tag_i.value = 0
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    while not int(dut.initialization_done_o.value):
        await RisingEdge(dut.clk)


async def send_spike(dut) -> None:
    while not int(dut.presynaptic_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid.value = 0


async def close_and_collect(dut, tag: int) -> list[tuple[int, int, int]]:
    dut.epoch_tag_i.value = tag
    dut.epoch_end_valid.value = 1
    while not int(dut.epoch_end_ready.value):
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.epoch_end_valid.value = 0
    spikes = []
    for _ in range(100):
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
            assert int(dut.epoch_tag_o.value) == tag
            return spikes
    raise AssertionError("parallel banked actor did not complete")


@cocotb.test()
async def parallel_scatter_and_state_lanes_preserve_plif_state(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_spike(dut)
    assert await close_and_collect(dut, 1) == [(0, 1, 1)]
    await send_spike(dut)
    assert sorted(await close_and_collect(dut, 2)) == [(0, 1, 1), (1, 1, 1)]
    assert int(dut.routing_error_o.value) == 0


@cocotb.test()
async def contribution_fifos_accept_back_to_back_presynaptic_events(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid.value = 1
    for _ in range(4):
        assert int(dut.presynaptic_ready.value) == 1
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
    dut.presynaptic_valid.value = 0

    assert sorted(await close_and_collect(dut, 1)) == [(0, 1, 1), (1, 1, 1)]
    assert int(dut.routing_error_o.value) == 0
