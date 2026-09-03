import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def two_tiles_commit_as_one_actor_transaction(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.presynaptic_valid_i.value = 0
    dut.presynaptic_spike_vector_i.value = 0
    dut.completion_valid_i.value = 0
    dut.completion_tag_i.value = 0
    dut.result_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    # A spike at global x=1 contributes through a 3-tap kernel to output
    # x=0,1,2. Output x=2 belongs to the second tile, proving its locally
    # cropped input halo includes the neighboring tile's boundary pixel.
    dut.presynaptic_spike_vector_i.value = 0b0010
    dut.presynaptic_valid_i.value = 1
    await Timer(1, units="ns")
    assert int(dut.presynaptic_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid_i.value = 0
    dut.completion_valid_i.value = 1
    dut.completion_tag_i.value = 7
    await Timer(1, units="ns")
    assert int(dut.completion_ready_o.value) == 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

    assert int(dut.result_valid_o.value) == 1
    assert int(dut.spike_vector_o.value) == 0b0111
    assert int(dut.completion_tag_o.value) == 7
    assert int(dut.error_o.value) == 0

    dut.result_ready_i.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    assert int(dut.result_valid_o.value) == 0
