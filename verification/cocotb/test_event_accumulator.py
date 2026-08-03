import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut) -> None:
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


@cocotb.test()
async def repeated_events_add_shared_weight_and_clear(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.clear.value = 0
    dut.valid.value = 0
    dut.weight.value = 0
    await tick(dut)
    dut.reset.value = 0
    dut.valid.value = 1
    dut.weight.value = -3
    for _ in range(4):
        await tick(dut)
    assert dut.accumulated_current.value.signed_integer == -12
    dut.clear.value = 1
    await tick(dut)
    assert dut.accumulated_current.value.signed_integer == 0
