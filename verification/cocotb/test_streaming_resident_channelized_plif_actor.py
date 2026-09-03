import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
async def stream_emits_bitmap_before_matching_completion(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid_i.value = 0
    dut.in_spike_vector_i.value = 0
    dut.in_completion_i.value = 0
    dut.in_tag_i.value = 0
    # Hold the output while presenting the completion. This makes the first
    # packet visible to this sequential monitor; the interface may otherwise
    # legally complete its data handshake on the same edge that result_valid
    # rises.
    dut.out_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    dut.in_valid_i.value = 1
    dut.in_spike_vector_i.value = 0b11
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_completion_i.value = 1
    dut.in_tag_i.value = 5
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_valid_i.value = 0
    dut.in_completion_i.value = 0
    dut.out_ready_i.value = 1

    await Timer(1, units="ns")
    packets = [
        (
            int(dut.out_completion_o.value),
            int(dut.out_spike_vector_o.value),
            int(dut.out_tag_o.value),
        )
    ]
    for _ in range(8):
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        if int(dut.out_valid_o.value):
            packets.append(
                (
                    int(dut.out_completion_o.value),
                    int(dut.out_spike_vector_o.value),
                    int(dut.out_tag_o.value),
                )
            )
        if len(packets) == 2:
            break
    assert packets == [(0, 0b11, 5), (1, 0b11, 5)]
    assert int(dut.error_o.value) == 0
