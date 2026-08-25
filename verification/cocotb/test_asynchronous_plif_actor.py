import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


async def reset_dut(dut):
    dut.reset.value = 1
    dut.contribution_valid.value = 0
    dut.epoch_end_valid.value = 0
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 1
    dut.beta_i.value = 1 << 15
    dut.threshold_i.value = 100
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def send_contribution(dut, address: int, weight: int):
    while not int(dut.contribution_ready.value):
        await RisingEdge(dut.clk)
    dut.destination_i.value = address
    dut.weight_i.value = weight
    dut.contribution_valid.value = 1
    await RisingEdge(dut.clk)
    dut.contribution_valid.value = 0


async def close_epoch(dut, tag: int):
    while not int(dut.epoch_end_ready.value):
        await RisingEdge(dut.clk)
    dut.epoch_tag_i.value = tag
    dut.epoch_end_valid.value = 1
    await RisingEdge(dut.clk)
    dut.epoch_end_valid.value = 0


async def collect_epoch(dut, limit: int = 200):
    spikes = []
    for _ in range(limit):
        await RisingEdge(dut.clk)
        if int(dut.spike_valid.value):
            spikes.append(int(dut.spike_destination_o.value))
        if int(dut.epoch_done_valid.value):
            return spikes, int(dut.epoch_tag_o.value)
    raise AssertionError("actor did not finish epoch")


@cocotb.test()
async def duplicate_contributions_share_one_membrane_and_commit_on_completion(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    await send_contribution(dut, 3, 60)
    await send_contribution(dut, 3, 60)
    for _ in range(4):
        await RisingEdge(dut.clk)
        assert int(dut.spike_valid.value) == 0

    await close_epoch(dut, 1)
    spikes, tag = await collect_epoch(dut)
    assert spikes == [3]
    assert tag == 1

    # Subtractive reset left V=20. A later +70 reaches only 90, so no spike.
    await RisingEdge(dut.clk)
    await send_contribution(dut, 3, 70)
    await close_epoch(dut, 2)
    spikes, tag = await collect_epoch(dut)
    assert spikes == []
    assert tag == 2


@cocotb.test()
async def completion_and_spike_channels_preserve_backpressure(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.spike_ready.value = 0
    dut.epoch_done_ready.value = 0

    await send_contribution(dut, 2, 127)
    await close_epoch(dut, 7)
    for _ in range(100):
        await RisingEdge(dut.clk)
        if int(dut.spike_valid.value):
            break
    else:
        raise AssertionError("expected held spike")

    held_address = int(dut.spike_destination_o.value)
    for _ in range(3):
        await RisingEdge(dut.clk)
        assert int(dut.spike_valid.value) == 1
        assert int(dut.spike_destination_o.value) == held_address == 2

    dut.spike_ready.value = 1
    while not int(dut.epoch_done_valid.value):
        await RisingEdge(dut.clk)
    assert int(dut.epoch_tag_o.value) == 7
    assert int(dut.epoch_end_ready.value) == 0

    for _ in range(3):
        await RisingEdge(dut.clk)
        assert int(dut.epoch_done_valid.value) == 1
    dut.epoch_done_ready.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.epoch_end_ready.value) == 1


@cocotb.test()
async def high_address_uses_first_touch_queue_not_dense_destination_scan(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    await send_contribution(dut, 15, 1)
    await close_epoch(dut, 9)

    cycles = 0
    while not int(dut.epoch_done_valid.value):
        await RisingEdge(dut.clk)
        cycles += 1
        assert cycles < 12, "completion latency depends on destination address"

    assert int(dut.epoch_tag_o.value) == 9
