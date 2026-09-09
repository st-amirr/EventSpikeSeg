import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


@cocotb.test()
async def qk_completion_rendezvous_gates_v_by_head_and_location(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_q_valid_i.value = 0
    dut.in_k_valid_i.value = 0
    dut.in_v_valid_i.value = 0
    dut.in_q_completion_i.value = 0
    dut.in_k_completion_i.value = 0
    dut.in_v_completion_i.value = 0
    dut.in_q_vector_i.value = 0
    dut.in_k_vector_i.value = 0
    dut.in_v_vector_i.value = 0
    dut.in_q_tag_i.value = 0
    dut.in_k_tag_i.value = 0
    dut.in_v_tag_i.value = 0
    dut.out_ready_i.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    # Channel-major [2 channels x 2 locations]. Location 0 has two Q/K
    # coincidences and passes threshold 2; location 1 has one and is suppressed.
    dut.in_q_vector_i.value = 0b0111
    dut.in_k_vector_i.value = 0b0111
    dut.in_v_vector_i.value = 0xF
    dut.in_q_valid_i.value = 1
    dut.in_k_valid_i.value = 1
    dut.in_v_valid_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

    dut.in_q_completion_i.value = 1
    dut.in_k_completion_i.value = 1
    dut.in_v_completion_i.value = 1
    dut.in_q_tag_i.value = 9
    dut.in_k_tag_i.value = 9
    dut.in_v_tag_i.value = 9
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_q_valid_i.value = 0
    dut.in_k_valid_i.value = 0
    dut.in_v_valid_i.value = 0

    assert int(dut.out_valid_o.value) == 1
    assert int(dut.out_completion_o.value) == 0
    assert int(dut.out_v_vector_o.value) == 0x5
    assert int(dut.out_tag_o.value) == 9
    assert int(dut.tag_mismatch_o.value) == 0

    dut.out_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out_valid_o.value) == 1
    assert int(dut.out_completion_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.out_valid_o.value) == 0
