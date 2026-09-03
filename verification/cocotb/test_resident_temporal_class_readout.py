import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def send(dut, vector: int, completion: bool, tag: int) -> None:
    await FallingEdge(dut.clk)
    dut.in_spike_vector_i.value = vector
    dut.in_completion_i.value = completion
    dut.in_tag_i.value = tag
    dut.in_valid_i.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.in_ready_o.value):
            break
    await FallingEdge(dut.clk)
    dut.in_valid_i.value = 0


@cocotb.test()
async def class_scores_remain_local_across_prediction_bins(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid_i.value = 0
    dut.in_spike_vector_i.value = 0
    dut.in_completion_i.value = 0
    dut.in_tag_i.value = 0
    dut.prediction_ready_i.value = 1
    dut.frame_done_ready_i.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    # Channel-major: channel 0 spikes at pixel 0, channel 1 at pixel 1.
    for tag in (1, 2):
        await send(dut, 0b1001, False, tag)
        await send(dut, 0, True, tag)

    predictions = []
    for _ in range(10):
        await RisingEdge(dut.clk)
        if int(dut.prediction_valid_o.value):
            predictions.append(
                (
                    int(dut.prediction_x_o.value),
                    int(dut.prediction_class_o.value),
                )
            )
        if int(dut.frame_done_valid_o.value):
            break
    assert predictions == [(0, 0), (1, 1)]
    assert int(dut.frame_tag_o.value) == 2
