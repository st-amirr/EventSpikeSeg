import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def adaptation_rises_decays_and_saturates(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.valid.value = 0
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    dut.valid.value = 1
    dut.decay.value = 2
    dut.increment.value = 4
    dut.spike_count.value = 3
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.adaptation.value) == 12
    dut.spike_count.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.adaptation.value) == 10
    dut.increment.value = 65535
    dut.spike_count.value = 2
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.adaptation.value) == 65535
