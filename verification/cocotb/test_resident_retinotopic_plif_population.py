import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def finish_bin(dut, tag: int) -> int:
    await FallingEdge(dut.clk)
    dut.contribution_valid_i.value = 0
    dut.completion_tag_i.value = tag
    dut.completion_valid_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.completion_valid_i.value = 0
    assert int(dut.spike_valid_o.value) == 1
    return int(dut.spike_vector_o.value)


@cocotb.test()
async def resident_peer_groups_commit_without_state_fetch(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.contribution_valid_i.value = 0
    dut.destination_i.value = 0
    dut.weight_i.value = 0
    dut.dense_current_valid_i.value = 0
    dut.dense_current_delta_i.value = 0
    dut.completion_valid_i.value = 0
    dut.completion_tag_i.value = 0
    dut.spike_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    # Channel-major destinations: c0/p0=0 and c1/p0=2. The two peers receive
    # their contributions concurrently and commit atomically at completion.
    dut.contribution_valid_i.value = 0b11
    dut.destination_i.value = 0 | (2 << 2)
    dut.weight_i.value = 12 | (6 << 8)
    assert int(dut.contribution_ready_o.value) == 1
    await RisingEdge(dut.clk)
    assert await finish_bin(dut, 3) == 0b0001
    assert int(dut.completion_tag_o.value) == 3
    assert int(dut.address_error_o.value) == 0

    # Consume the whole bitmap transaction, then commit another empty bin.
    dut.spike_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.spike_ready_i.value = 0
    assert await finish_bin(dut, 4) == 0
