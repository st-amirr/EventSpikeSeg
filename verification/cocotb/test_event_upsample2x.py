import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


def payload(channel: int, y: int, x: int) -> int:
    return x | (y << 10) | (channel << 19)


async def reset_dut(dut):
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def send(dut, value: int, *, completion: int, tag: int):
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
async def data_expands_four_times_but_completion_once(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send(dut, payload(6, 4, 3), completion=0, tag=2)

    outputs = []
    for _ in range(4):
        await Timer(1, units="ns")
        assert int(dut.out_valid.value) == 1
        value = int(dut.out_payload.value)
        outputs.append(
            ((value >> 19) & 0x7F, (value >> 10) & 0x1FF, value & 0x3FF)
        )
        dut.out_ready.value = 1
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        dut.out_ready.value = 0
    assert outputs == [(6, 8, 6), (6, 8, 7), (6, 9, 6), (6, 9, 7)]
    assert int(dut.coordinate_overflow_o.value) == 0

    await send(dut, payload(0, 0, 0), completion=1, tag=3)
    await Timer(1, units="ns")
    assert int(dut.out_valid.value) == 1
    assert int(dut.out_completion.value) == 1
    assert int(dut.out_bin_tag.value) == 3
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.out_valid.value) == 0
