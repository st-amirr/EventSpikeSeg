import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


async def reset_dut(dut) -> None:
    dut.reset.value = 1
    dut.contribution_valid.value = 0
    dut.destination_i.value = 0
    dut.weight_i.value = 0
    dut.epoch_end_valid.value = 0
    dut.epoch_tag_i.value = 0
    dut.beta_i.value = 1 << 15
    dut.threshold_i.value = 10
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    for _ in range(20):
        await RisingEdge(dut.clk)
        if int(dut.initialization_done_o.value):
            return
    raise AssertionError("banked actor did not initialize")


async def send_continuous(dut, items: list[tuple[int, int]]) -> None:
    for address, weight in items:
        await FallingEdge(dut.clk)
        dut.destination_i.value = address
        dut.weight_i.value = weight
        dut.contribution_valid.value = 1
        await Timer(1, units="ns")
        assert int(dut.contribution_ready.value), (
            f"destination bank for address {address} did not accept a continuous input"
        )
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.contribution_valid.value = 0


async def send_with_backpressure(dut, address: int, weight: int) -> None:
    await FallingEdge(dut.clk)
    dut.destination_i.value = address
    dut.weight_i.value = weight
    dut.contribution_valid.value = 1
    await Timer(1, units="ns")
    while not int(dut.contribution_ready.value):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.contribution_valid.value = 0


async def close_epoch(dut, tag: int) -> None:
    dut.epoch_tag_i.value = tag
    dut.epoch_end_valid.value = 1
    while not int(dut.epoch_end_ready.value):
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.epoch_end_valid.value = 0


async def collect_epoch(dut, limit: int = 200) -> tuple[list[int], int]:
    spikes: list[int] = []
    for _ in range(limit):
        await RisingEdge(dut.clk)
        if int(dut.spike_valid.value):
            spikes.append(int(dut.spike_destination_o.value))
        if int(dut.epoch_done_valid.value):
            return spikes, int(dut.epoch_tag_o.value)
    raise AssertionError("banked actor did not finish the epoch")


@cocotb.test()
async def independent_banks_overlap_and_reconstruct_global_addresses(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Each lane receives one contribution every four clocks, allowing the
    # scalar ingress to accept eight additions on consecutive clocks.
    await send_continuous(
        dut,
        [(0, 6), (1, 6), (8, 11), (9, 11), (0, 6), (1, 6), (8, 11), (9, 11)],
    )
    await close_epoch(dut, 1)
    spikes, tag = await collect_epoch(dut)
    assert sorted(spikes) == [0, 1, 8, 9]
    assert tag == 1
    assert int(dut.address_error_o.value) == 0


@cocotb.test()
async def interleaved_local_addresses_select_global_channel_parameters(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Global address 0 is channel 0 (threshold 10); address 8 is channel 1
    # (threshold 20), even though both map to local row 0 in different lanes.
    await send_with_backpressure(dut, 0, 12)
    await send_with_backpressure(dut, 8, 12)
    await close_epoch(dut, 7)
    spikes, tag = await collect_epoch(dut)
    assert spikes == [0]
    assert tag == 7
    assert int(dut.address_error_o.value) == 0
