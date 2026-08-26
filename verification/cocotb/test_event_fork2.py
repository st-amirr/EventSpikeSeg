import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


async def reset_dut(dut):
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.out0_ready.value = 0
    dut.out1_ready.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def send_packet(dut, payload: int, completion: int, tag: int):
    while not int(dut.in_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_payload.value = payload
    dut.in_completion.value = completion
    dut.in_bin_tag.value = tag
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.in_valid.value = 0


@cocotb.test()
async def multicast_waits_for_both_branches_independently(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send_packet(dut, 0x1234, 0, 9)

    assert int(dut.out0_valid.value) == 1
    assert int(dut.out1_valid.value) == 1
    assert int(dut.in_ready.value) == 0
    assert int(dut.out0_payload.value) == 0x1234
    assert int(dut.out1_payload.value) == 0x1234

    dut.out0_ready.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.out0_valid.value) == 0
    assert int(dut.out1_valid.value) == 1
    assert int(dut.in_ready.value) == 0

    dut.out1_ready.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.out1_valid.value) == 0
    assert int(dut.in_ready.value) == 1

    await send_packet(dut, 0, 1, 10)
    assert int(dut.out0_completion.value) == 1
    assert int(dut.out1_completion.value) == 1
    assert int(dut.out0_bin_tag.value) == 10
    assert int(dut.out1_bin_tag.value) == 10
