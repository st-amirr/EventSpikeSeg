import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut) -> None:
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def touch(dut, address: int, current: int, bin_tag: int) -> tuple[int, int, int]:
    while not int(dut.in_ready.value):
        await tick(dut)
    dut.address_i.value = address
    dut.current_i.value = current
    dut.beta_i.value = 24_576  # 0.75 in UQ1.15
    dut.threshold_i.value = 512
    dut.current_bin_tag_i.value = bin_tag
    dut.in_valid.value = 1
    await tick(dut)
    dut.in_valid.value = 0
    while not int(dut.out_valid.value):
        await tick(dut)
    result = (
        int(dut.candidate_o.value.signed_integer),
        int(dut.membrane_o.value.signed_integer),
        int(dut.spike_o.value),
    )
    dut.out_ready.value = 1
    await tick(dut)
    dut.out_ready.value = 0
    return result


@cocotb.test()
async def sparse_lookup_lazy_decay_update_and_reclaim(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    await tick(dut)
    dut.reset.value = 0

    # Missing state uses one natural 5 ms step, then stores the residual membrane.
    assert await touch(dut, 3, 700, 4) == (700, 188, 1)
    assert int(dut.live_entry_count_o.value) == 1

    # Two untouched bins apply beta twice before charging.
    assert await touch(dut, 3, 0, 6) == (106, 106, 0)
    assert int(dut.live_entry_count_o.value) == 1

    # A zero membrane is reclaimed exactly for a non-adaptive actor.
    assert await touch(dut, 9, 0, 6) == (0, 0, 0)
    assert int(dut.live_entry_count_o.value) == 1
    assert int(dut.state_overflow_o.value) == 0
