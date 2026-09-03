import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def wide_payload_is_held_at_source_until_both_branches_accept(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid_i.value = 0
    dut.in_vector_i.value = 0
    dut.in_completion_i.value = 0
    dut.in_tag_i.value = 0
    dut.out0_ready_i.value = 0
    dut.out1_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    dut.in_valid_i.value = 1
    dut.in_vector_i.value = 0xA5
    dut.in_tag_i.value = 3
    dut.out0_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out0_valid_o.value) == 0
    assert int(dut.out1_valid_o.value) == 1
    assert int(dut.in_ready_o.value) == 0
    assert int(dut.out1_vector_o.value) == 0xA5
    dut.out0_ready_i.value = 0
    dut.out1_ready_i.value = 1
    await Timer(1, units="ns")
    assert int(dut.in_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out0_valid_o.value) == 1
