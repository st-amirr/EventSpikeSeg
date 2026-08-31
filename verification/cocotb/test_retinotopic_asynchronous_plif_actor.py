import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def send_contribution(dut, destination: int, weight: int):
    while not int(dut.contribution_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.destination_i.value = destination
    dut.weight_i.value = weight
    dut.contribution_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.contribution_valid.value = 0


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
            spikes.append(int(dut.spike_destination_o.value))
        if int(dut.epoch_done_valid.value):
            dut.epoch_done_ready.value = 1
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            dut.epoch_done_ready.value = 0
            return spikes
    raise AssertionError("retinotopic actor did not finish")


@cocotb.test()
async def group_commit_preserves_peer_inhibition_state_across_epochs(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.contribution_valid.value = 0
    dut.epoch_end_valid.value = 0
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.reset.value = 0

    await send_contribution(dut, 0, 12)
    await send_contribution(dut, 4, 6)
    assert await finish_epoch(dut, 1) == [0]

    await send_contribution(dut, 4, 13)
    assert await finish_epoch(dut, 2) == [4]
    assert int(dut.address_error_o.value) == 0
