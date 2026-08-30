import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def edge(dut):
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def reset_dut(dut):
    dut.reset.value = 1
    dut.contribution_valid.value = 0
    dut.epoch_end_valid.value = 0
    dut.spike_ready.value = 1
    dut.epoch_done_ready.value = 1
    dut.beta_i.value = 1 << 15
    dut.threshold_i.value = 100
    for _ in range(3):
        await edge(dut)
    dut.reset.value = 0
    while not int(dut.contribution_ready.value):
        await edge(dut)


async def send_contribution(dut, address: int, weight: int):
    while not int(dut.contribution_ready.value):
        await edge(dut)
    dut.destination_i.value = address
    dut.weight_i.value = weight
    dut.contribution_valid.value = 1
    await edge(dut)
    dut.contribution_valid.value = 0


async def close_epoch(dut, tag: int):
    while not int(dut.epoch_end_ready.value):
        await edge(dut)
    dut.epoch_tag_i.value = tag
    dut.epoch_end_valid.value = 1
    await edge(dut)
    dut.epoch_end_valid.value = 0


async def collect_epoch(dut, limit: int = 250):
    spikes = []
    for _ in range(limit):
        await edge(dut)
        if int(dut.spike_valid.value):
            spikes.append(int(dut.spike_destination_o.value))
        if int(dut.epoch_done_valid.value):
            return spikes, int(dut.epoch_tag_o.value)
    raise AssertionError("SRAM actor did not finish epoch")


@cocotb.test()
async def packed_state_matches_duplicate_accumulation_and_lazy_membrane(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_contribution(dut, 3, 60)
    await send_contribution(dut, 3, 60)
    await close_epoch(dut, 1)
    spikes, tag = await collect_epoch(dut)
    assert spikes == [3]
    assert tag == 1

    await edge(dut)
    await send_contribution(dut, 3, 70)
    await close_epoch(dut, 2)
    spikes, tag = await collect_epoch(dut)
    assert spikes == []
    assert tag == 2


@cocotb.test()
async def SRAM_actor_holds_spike_and_completion_under_backpressure(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    dut.spike_ready.value = 0
    dut.epoch_done_ready.value = 0
    await send_contribution(dut, 2, 127)
    await close_epoch(dut, 7)
    for _ in range(100):
        await edge(dut)
        if int(dut.spike_valid.value):
            break
    else:
        raise AssertionError("expected held spike")
    for _ in range(3):
        await edge(dut)
        assert int(dut.spike_valid.value) == 1
        assert int(dut.spike_destination_o.value) == 2
    dut.spike_ready.value = 1
    while not int(dut.epoch_done_valid.value):
        await edge(dut)
    for _ in range(3):
        await edge(dut)
        assert int(dut.epoch_done_valid.value) == 1
        assert int(dut.epoch_tag_o.value) == 7
    dut.epoch_done_ready.value = 1
    await edge(dut)
    assert int(dut.epoch_end_ready.value) == 1


@cocotb.test()
async def first_touch_queue_latency_is_independent_of_destination_address(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_contribution(dut, 15, 1)
    await close_epoch(dut, 9)
    cycles = 0
    while not int(dut.epoch_done_valid.value):
        await edge(dut)
        cycles += 1
        assert cycles < 20
    assert int(dut.epoch_tag_o.value) == 9
