import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut) -> None:
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def capture(dut, value: int) -> None:
    assert int(dut.capture_ready_o.value) == 1
    dut.capture_data_i.value = value
    dut.capture_valid_i.value = 1
    await tick(dut)
    dut.capture_valid_i.value = 0


async def seal(dut) -> None:
    assert int(dut.seal_ready_o.value) == 1
    dut.seal_i.value = 1
    await tick(dut)
    dut.seal_i.value = 0


@cocotb.test()
async def capture_overlaps_active_bank_and_preserves_event_order(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.capture_valid_i.value = 0
    dut.seal_i.value = 0
    dut.sealed_ready_i.value = 0
    dut.event_ready_i.value = 0
    dut.release_i.value = 0
    await tick(dut)
    dut.reset.value = 0

    await capture(dut, 11)
    await capture(dut, 12)
    await seal(dut)
    assert int(dut.sealed_valid_o.value) == 1
    assert int(dut.sealed_buffer_o.value) == 0

    dut.sealed_ready_i.value = 1
    await tick(dut)
    dut.sealed_ready_i.value = 0
    assert int(dut.active_valid_o.value) == 1
    assert int(dut.active_event_count_o.value) == 2

    # Bank 1 captures the next bin while bank 0 is being consumed.
    await capture(dut, 21)
    await seal(dut)

    seen = []
    dut.event_ready_i.value = 1
    while int(dut.event_valid_o.value):
        seen.append((int(dut.event_data_o.value), int(dut.event_last_o.value)))
        await tick(dut)
    dut.event_ready_i.value = 0
    assert seen == [(11, 0), (12, 1)]

    dut.release_i.value = 1
    await tick(dut)
    dut.release_i.value = 0
    assert int(dut.active_valid_o.value) == 0
    assert int(dut.sealed_valid_o.value) == 1
    assert int(dut.sealed_buffer_o.value) == 1


@cocotb.test()
async def empty_bins_advance_and_full_capture_reports_overflow(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.capture_valid_i.value = 0
    dut.seal_i.value = 0
    dut.sealed_ready_i.value = 0
    dut.event_ready_i.value = 0
    dut.release_i.value = 0
    await tick(dut)
    dut.reset.value = 0

    await seal(dut)
    dut.sealed_ready_i.value = 1
    await tick(dut)
    dut.sealed_ready_i.value = 0
    assert int(dut.active_valid_o.value) == 1
    assert int(dut.active_event_count_o.value) == 0
    assert int(dut.event_valid_o.value) == 0
