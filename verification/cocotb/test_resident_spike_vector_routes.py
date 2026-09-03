import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def route_operation(dut) -> None:
    if hasattr(dut, "in_vector_i"):
        dut.in_valid_i.value = 1
        dut.in_completion_i.value = 0
        dut.in_tag_i.value = 2
        dut.out_ready_i.value = 1
        if not hasattr(dut, "configuration_error_o"):  # upsample: one channel, 2x2
            dut.in_vector_i.value = 0b0001
            await Timer(1, units="ns")
            assert int(dut.out_vector_o.value) == 0b00110011
        else:  # channel offset: two channels x two pixels into four channels
            dut.in_vector_i.value = 0b1001
            await Timer(1, units="ns")
            assert int(dut.out_vector_o.value) == 0b10010000
        return

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in0_valid_i.value = 0
    dut.in1_valid_i.value = 0
    dut.in0_vector_i.value = 0
    dut.in1_vector_i.value = 0
    dut.in0_completion_i.value = 0
    dut.in1_completion_i.value = 0
    dut.in0_tag_i.value = 0
    dut.in1_tag_i.value = 0
    dut.out_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    dut.in0_valid_i.value = 1
    dut.in1_valid_i.value = 1
    dut.in0_vector_i.value = 0b0101
    dut.in1_vector_i.value = 0b0110
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in0_completion_i.value = 1
    dut.in1_completion_i.value = 1
    dut.in0_tag_i.value = 7
    dut.in1_tag_i.value = 7
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in0_valid_i.value = 0
    dut.in1_valid_i.value = 0
    assert int(dut.out_valid_o.value) == 1
    assert int(dut.out_vector_o.value) == 0b0111
    assert int(dut.out_completion_o.value) == 0
    dut.out_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out_completion_o.value) == 1
    assert int(dut.out_tag_o.value) == 7
    assert int(dut.tag_mismatch_o.value) == 0
