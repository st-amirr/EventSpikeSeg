import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

SCORE_WIDTH = 24
CONTRIBUTION_WIDTH = 8
CLASS_COUNT = 6


def pack_signed(values: list[int], width: int) -> int:
    mask = (1 << width) - 1
    return sum((value & mask) << (index * width) for index, value in enumerate(values))


def unpack_signed(value: int, count: int, width: int) -> list[int]:
    mask = (1 << width) - 1
    sign = 1 << (width - 1)
    result = []
    for index in range(count):
        item = (value >> (index * width)) & mask
        result.append(item - (1 << width) if item & sign else item)
    return result


async def tick(dut) -> None:
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def update(
    dut, scores: list[int], contributions: list[int], flush: bool
) -> tuple[list[int], int, int, int]:
    assert int(dut.in_ready.value) == 1
    dut.scores_i.value = pack_signed(scores, SCORE_WIDTH)
    dut.contributions_i.value = pack_signed(contributions, CONTRIBUTION_WIDTH)
    dut.prediction_flush_i.value = int(flush)
    dut.in_valid.value = 1
    await tick(dut)
    dut.in_valid.value = 0
    assert int(dut.out_valid.value) == 1
    result = (
        unpack_signed(int(dut.scores_o.value), CLASS_COUNT, SCORE_WIDTH),
        int(dut.state_live_o.value),
        int(dut.prediction_valid_o.value),
        int(dut.class_o.value),
    )
    await tick(dut)
    return result


@cocotb.test()
async def accumulates_signed_weights_then_flushes_prediction(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    await tick(dut)
    dut.reset.value = 0

    first, live, prediction, winner = await update(
        dut,
        [0] * CLASS_COUNT,
        [5, -2, 7, 0, 1, 3],
        False,
    )
    assert first == [5, -2, 7, 0, 1, 3]
    assert (live, prediction, winner) == (1, 0, 2)

    cleared, live, prediction, winner = await update(
        dut,
        first,
        [2, 10, -1, 0, 0, 0],
        True,
    )
    assert cleared == [0] * CLASS_COUNT
    assert (live, prediction, winner) == (0, 1, 1)


@cocotb.test()
async def saturates_and_preserves_first_index_on_tie(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    await tick(dut)
    dut.reset.value = 0

    maximum = (1 << 23) - 1
    scores = [maximum, maximum, -10] + [0] * 3
    updated, _, prediction, winner = await update(
        dut, scores, [127, 127, -128] + [0] * 3, True
    )
    assert updated == [0] * CLASS_COUNT
    assert prediction == 1
    assert winner == 0
