import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def clock_edge(dut) -> None:
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def send(
    dut,
    *,
    membrane: int,
    current: int,
    beta: int,
    threshold: int,
    elapsed_bins: int = 1,
) -> tuple[int, int, int]:
    dut.membrane_i.value = membrane
    dut.current_i.value = current
    dut.beta_i.value = beta
    dut.threshold_i.value = threshold
    dut.elapsed_bins_i.value = elapsed_bins
    dut.in_valid.value = 1
    dut.out_ready.value = 1
    assert int(dut.in_ready.value) == 1
    await clock_edge(dut)
    dut.in_valid.value = 0
    while not int(dut.out_valid.value):
        await clock_edge(dut)
    assert int(dut.out_valid.value) == 1
    result = (
        dut.candidate_o.value.signed_integer,
        dut.membrane_o.value.signed_integer,
        int(dut.spike_o.value),
    )
    # Complete the ready/valid transfer before starting the next transaction.
    await clock_edge(dut)
    return result


@cocotb.test()
async def plif_matches_integer_reference_order_and_saturation(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    dut.reset.value = 1
    await clock_edge(dut)
    dut.reset.value = 0

    # beta=.75, V=.5, I=.25, threshold=.5 in the exported formats.
    assert await send(
        dut, membrane=512, current=256, beta=24_576, threshold=512
    ) == (640, 128, 1)

    # Negative product rounding and no spike.
    assert await send(
        dut, membrane=-513, current=0, beta=16_384, threshold=512
    ) == (-257, -257, 0)

    # Current accumulation saturates before threshold/reset.
    assert await send(
        dut, membrane=32_000, current=8_000_000, beta=32_768, threshold=512
    ) == (32_767, 32_255, 1)

    # Two exact beta applications: .75**2 * .5 + .25 = .53125.
    assert await send(
        dut,
        membrane=512,
        current=256,
        beta=24_576,
        threshold=512,
        elapsed_bins=2,
    ) == (544, 32, 1)


@cocotb.test()
async def plif_holds_output_under_backpressure(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    dut.reset.value = 1
    await clock_edge(dut)
    dut.reset.value = 0

    dut.membrane_i.value = 0
    dut.current_i.value = 700
    dut.beta_i.value = 32_768
    dut.threshold_i.value = 512
    dut.elapsed_bins_i.value = 0
    dut.in_valid.value = 1
    await clock_edge(dut)
    dut.in_valid.value = 0
    while not int(dut.out_valid.value):
        await clock_edge(dut)
    assert int(dut.out_valid.value) == 1
    assert int(dut.in_ready.value) == 0
    held = (
        dut.candidate_o.value.signed_integer,
        dut.membrane_o.value.signed_integer,
        int(dut.spike_o.value),
    )

    dut.current_i.value = -900
    await clock_edge(dut)
    assert (
        dut.candidate_o.value.signed_integer,
        dut.membrane_o.value.signed_integer,
        int(dut.spike_o.value),
    ) == held

    dut.out_ready.value = 1
    dut.in_valid.value = 0
    await clock_edge(dut)
    assert int(dut.out_valid.value) == 0
