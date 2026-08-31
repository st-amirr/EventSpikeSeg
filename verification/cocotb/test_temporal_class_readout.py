import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


def payload(channel: int, x: int, y: int) -> int:
    return x | (y << 10) | (channel << 19)


async def send_packet(dut, value: int, completion: int, tag: int):
    while not int(dut.in_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_payload.value = value
    dut.in_completion.value = completion
    dut.in_bin_tag.value = tag
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_valid.value = 0


@cocotb.test()
async def signed_currents_accumulate_then_dense_frame_flushes(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.prediction_ready.value = 1
    dut.frame_done_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.reset.value = 0

    await send_packet(dut, payload(1, 1, 0), completion=0, tag=0)
    await send_packet(dut, payload(0, 0, 1), completion=0, tag=0)
    await send_packet(dut, 0, completion=1, tag=1)
    for _ in range(3):
        await RisingEdge(dut.clk)
        assert int(dut.prediction_valid.value) == 0

    await send_packet(dut, payload(1, 1, 0), completion=0, tag=0)
    await send_packet(dut, 0, completion=1, tag=2)

    predictions = []
    frame_tag = None
    for _ in range(40):
        await RisingEdge(dut.clk)
        if int(dut.prediction_valid.value):
            predictions.append(
                (
                    int(dut.prediction_x_o.value),
                    int(dut.prediction_y_o.value),
                    int(dut.prediction_class_o.value),
                )
            )
        if int(dut.frame_done_valid.value):
            frame_tag = int(dut.frame_bin_tag_o.value)
            break
    assert predictions == [(0, 0, 0), (1, 0, 1), (0, 1, 0), (1, 1, 0)]
    assert frame_tag == 2
    assert int(dut.address_error_o.value) == 0
