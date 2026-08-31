import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


async def reset_dut(dut):
    dut.reset.value = 1
    dut.in0_valid.value = 0
    dut.in1_valid.value = 0
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def send(dut, lane: int, *, payload: int = 0, completion: int = 0, tag: int = 1):
    valid = dut.in0_valid if lane == 0 else dut.in1_valid
    ready = dut.in0_ready if lane == 0 else dut.in1_ready
    payload_signal = dut.in0_payload if lane == 0 else dut.in1_payload
    completion_signal = dut.in0_completion if lane == 0 else dut.in1_completion
    tag_signal = dut.in0_bin_tag if lane == 0 else dut.in1_bin_tag
    await FallingEdge(dut.clk)
    payload_signal.value = payload
    completion_signal.value = completion
    tag_signal.value = tag
    valid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(ready.value):
            break
    await FallingEdge(dut.clk)
    valid.value = 0


@cocotb.test()
async def forwards_multiplicity_and_rendezvous_waits_for_same_bin(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    await send(dut, 0, payload=7, tag=3)
    await send(dut, 1, payload=7, tag=3)
    await send(dut, 0, completion=1, tag=3)
    for _ in range(3):
        await RisingEdge(dut.clk)
        assert int(dut.out_completion.value) == 0

    await send(dut, 1, completion=1, tag=3)
    for _ in range(5):
        await RisingEdge(dut.clk)
        if int(dut.out_valid.value) and int(dut.out_completion.value):
            assert int(dut.out_bin_tag.value) == 3
            break
    else:
        raise AssertionError("join did not emit rendezvous completion")
    assert int(dut.tag_mismatch_o.value) == 0


@cocotb.test()
async def mismatched_completion_tags_are_reported(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send(dut, 0, completion=1, tag=4)
    await send(dut, 1, completion=1, tag=5)
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.tag_mismatch_o.value) == 1
    assert int(dut.out_valid.value) == 0
