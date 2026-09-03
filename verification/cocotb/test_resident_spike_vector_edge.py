import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def result_is_losslessly_split_into_vector_then_completion(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.result_valid_i.value = 0
    dut.spike_vector_i.value = 0
    dut.completion_tag_i.value = 0
    dut.out_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    dut.result_valid_i.value = 1
    dut.spike_vector_i.value = 0xA5
    dut.completion_tag_i.value = 12
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out_valid_o.value) == 1
    assert int(dut.out_vector_o.value) == 0xA5
    assert int(dut.out_completion_o.value) == 0
    dut.out_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out_valid_o.value) == 1
    assert int(dut.out_completion_o.value) == 1
    assert int(dut.out_tag_o.value) == 12
    dut.out_ready_i.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out_valid_o.value) == 1
    dut.out_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.result_valid_i.value = 0
    await Timer(1, units="ns")
    assert int(dut.out_valid_o.value) == 0
