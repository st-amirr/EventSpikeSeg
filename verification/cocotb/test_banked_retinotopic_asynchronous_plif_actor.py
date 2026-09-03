import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def reset_dut(dut) -> None:
    dut.reset.value = 1
    dut.contribution_valid.value = 0
    dut.destination_i.value = 0
    dut.weight_i.value = 0
    dut.epoch_end_valid.value = 0
    dut.epoch_tag_i.value = 0
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    for _ in range(200):
        await RisingEdge(dut.clk)
        if int(dut.initialization_done_o.value):
            return
    raise AssertionError("banked retinotopic state initialization did not complete")


async def send_contribution(dut, destination: int, weight: int) -> None:
    await FallingEdge(dut.clk)
    dut.destination_i.value = destination
    dut.weight_i.value = weight
    dut.contribution_valid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.contribution_ready.value):
            break
    await FallingEdge(dut.clk)
    dut.contribution_valid.value = 0


async def finish_epoch(dut, tag: int) -> list[int]:
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
    for _ in range(300):
        await RisingEdge(dut.clk)
        if int(dut.spike_valid.value):
            spikes.append(int(dut.spike_destination_o.value))
        if int(dut.epoch_done_valid.value):
            dut.epoch_done_ready.value = 1
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            dut.epoch_done_ready.value = 0
            return spikes
    raise AssertionError("banked retinotopic actor did not finish")


@cocotb.test()
async def spatial_banks_preserve_cross_channel_mechanisms(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Spatial locations 0 and 1 reside in different banks.  At location 0,
    # channel 0 wins and inhibits channel 1 as one atomic retinotopic group.
    await send_contribution(dut, 0, 12)
    await send_contribution(dut, 4, 6)
    # Independent location 1 is updated in parallel-owned state bank 1.
    await send_contribution(dut, 1, 12)
    assert sorted(await finish_epoch(dut, 1)) == [0, 1]

    # Global channel/spatial reconstruction must remain exact after banking.
    await send_contribution(dut, 4, 13)
    assert await finish_epoch(dut, 2) == [4]
    assert int(dut.address_error_o.value) == 0
