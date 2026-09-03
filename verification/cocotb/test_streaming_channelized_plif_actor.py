import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


def payload(channel: int, x: int, y: int) -> int:
    return x | (y << 10) | (channel << 19)


async def send_packet(dut, value: int, completion: int, tag: int):
    await FallingEdge(dut.clk)
    dut.in_payload.value = value
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
async def unified_stream_preserves_spikes_and_completion(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.reset.value = 0

    # Banked state implementations scrub each independent state SRAM after
    # reset.  Do not present stream traffic until every lane has completed
    # that initialization rendezvous.
    for _ in range(500):
        await RisingEdge(dut.clk)
        if int(dut.initialization_done_o.value):
            break
    else:
        raise AssertionError("stream actor state initialization did not complete")

    await send_packet(dut, payload(0, 2, 3), completion=0, tag=0)
    await send_packet(dut, 0, completion=1, tag=9)

    observed = []
    for _ in range(200):
        await RisingEdge(dut.clk)
        if int(dut.out_valid.value):
            observed.append(
                (
                    int(dut.out_completion.value),
                    int(dut.out_payload.value),
                    int(dut.out_bin_tag.value),
                )
            )
            if int(dut.out_completion.value):
                break
    else:
        raise AssertionError("stream actor did not emit completion")

    assert observed == [(0, payload(0, 2, 3), 9), (1, 0, 9)]
    assert int(dut.actor_error_o.value) == 0
