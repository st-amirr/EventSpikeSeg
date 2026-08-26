import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


@cocotb.test()
async def behavioral_boundary_matches_one_cycle_compiler_contract(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.read_enable_i.value = 0
    dut.write_enable_i.value = 0
    await FallingEdge(dut.clk)
    dut.write_address_i.value = 3
    dut.write_data_i.value = 0x12345678
    dut.write_enable_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.write_enable_i.value = 0
    dut.read_address_i.value = 3
    dut.read_enable_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.read_valid_o.value) == 1
    assert int(dut.read_data_o.value) == 0x12345678
    dut.read_enable_i.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.read_valid_o.value) == 0
