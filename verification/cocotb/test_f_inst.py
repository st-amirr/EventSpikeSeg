import cocotb
from cocotb.triggers import Timer


def packed(values: list[int], width: int = 16) -> int:
    mask = (1 << width) - 1
    return sum((value & mask) << (index * width) for index, value in enumerate(values))


@cocotb.test()
async def selects_maximum_and_lowest_tie(dut) -> None:
    dut.candidates.value = packed([8, 11, 9, 10])
    dut.candidate_mask.value = 0b1111
    await Timer(1, units="ns")
    assert int(dut.winners.value) == 0b0010
    dut.candidates.value = packed([12, 12, 3, 2])
    await Timer(1, units="ns")
    assert int(dut.winners.value) == 0b0001
    dut.candidate_mask.value = 0
    await Timer(1, units="ns")
    assert int(dut.winners.value) == 0
