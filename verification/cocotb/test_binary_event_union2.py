import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


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
async def residual_union_deduplicates_then_emits_one_completion(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    await send(dut, 0, payload=10, tag=8)
    await send(dut, 0, payload=11, tag=8)
    await send(dut, 1, payload=10, tag=8)
    await send(dut, 1, payload=12, tag=8)
    await send(dut, 0, completion=1, tag=8)
    await send(dut, 1, completion=1, tag=8)

    events = []
    for _ in range(30):
        await RisingEdge(dut.clk)
        if int(dut.out_valid.value):
            if int(dut.out_completion.value):
                assert int(dut.out_bin_tag.value) == 8
                break
            events.append(int(dut.out_payload.value))
    else:
        raise AssertionError("union did not emit completion")

    assert events == [10, 11, 12]
    assert int(dut.overflow_o.value) == 0
    assert int(dut.tag_mismatch_o.value) == 0


@cocotb.test()
async def mismatched_tags_fail_closed_without_downstream_completion(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    await send(dut, 0, completion=1, tag=2)
    await send(dut, 1, completion=1, tag=3)
    for _ in range(5):
        await RisingEdge(dut.clk)
        assert not (
            int(dut.out_valid.value) and int(dut.out_completion.value)
        )
    assert int(dut.tag_mismatch_o.value) == 1
