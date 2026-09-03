import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


async def push(dut, payload: int, completion: int, tag: int) -> None:
    await FallingEdge(dut.clk)
    dut.in_payload.value = payload
    dut.in_completion.value = completion
    dut.in_bin_tag.value = tag
    dut.in_valid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.in_ready.value):
            break
    await FallingEdge(dut.clk)
    dut.in_valid.value = 0


@cocotb.test()
async def fifo_preserves_packet_order_and_backpressure(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0

    await push(dut, 0x11, 0, 7)
    await push(dut, 0x22, 0, 7)
    await push(dut, 0, 1, 7)
    await push(dut, 0x33, 0, 8)
    assert int(dut.occupancy_o.value) == 4
    assert int(dut.in_ready.value) == 0

    # A full FIFO must pop and replace its head in one clock when the consumer
    # is ready, without introducing a full-queue bubble.
    dut.in_payload.value = 0x44
    dut.in_completion.value = 0
    dut.in_bin_tag.value = 8
    dut.in_valid.value = 1
    dut.out_ready.value = 1
    await Timer(1, units="ns")
    assert int(dut.in_ready.value) == 1
    observed = [
        (
            int(dut.out_payload.value),
            int(dut.out_completion.value),
            int(dut.out_bin_tag.value),
        )
    ]
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_valid.value = 0
    for _ in range(8):
        if int(dut.out_valid.value):
            observed.append(
                (
                    int(dut.out_payload.value),
                    int(dut.out_completion.value),
                    int(dut.out_bin_tag.value),
                )
            )
        await RisingEdge(dut.clk)
        if len(observed) == 5:
            await FallingEdge(dut.clk)
            break
        await FallingEdge(dut.clk)
    assert observed == [
        (0x11, 0, 7),
        (0x22, 0, 7),
        (0, 1, 7),
        (0x33, 0, 8),
        (0x44, 0, 8),
    ]
    assert int(dut.occupancy_o.value) == 0
