import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def scrub_then_single_port_transactions_are_deterministic(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.read_valid_i.value = 0
    dut.write_valid_i.value = 0
    dut.read_address_i.value = 0
    dut.write_address_i.value = 0
    dut.write_data_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    for _ in range(7):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.initialization_done_o.value) == 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.initialization_done_o.value) == 1

    dut.read_valid_i.value = 1
    dut.read_address_i.value = 3
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.read_response_valid_o.value) == 1
    assert int(dut.read_data_o.value) == 0
    dut.read_valid_i.value = 0

    dut.write_valid_i.value = 1
    dut.write_address_i.value = 3
    dut.write_data_i.value = 0xA5A55A5A
    await RisingEdge(dut.clk)
    dut.write_valid_i.value = 0
    dut.read_valid_i.value = 1
    dut.read_address_i.value = 3
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.read_response_valid_o.value) == 1
    assert int(dut.read_data_o.value) == 0xA5A55A5A

    dut.write_valid_i.value = 1
    dut.write_address_i.value = 4
    dut.write_data_i.value = 0x12345678
    await Timer(1, units="ns")
    assert int(dut.read_ready_o.value) == 0
    assert int(dut.write_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.request_conflict_o.value) == 1
