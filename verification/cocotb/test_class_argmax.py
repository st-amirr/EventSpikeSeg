import cocotb
from cocotb.triggers import Timer


def pack_signed(values: list[int], width: int = 24) -> int:
    mask = (1 << width) - 1
    return sum((value & mask) << (index * width) for index, value in enumerate(values))


@cocotb.test()
async def signed_scores_and_first_index_ties_match_pytorch(dut) -> None:
    dut.scores_i.value = pack_signed([-7, -3, -9, -3, -20, -20])
    await Timer(1, units="ns")
    assert int(dut.class_o.value) == 1

    dut.scores_i.value = pack_signed([0, 4, 2, 9, 3, 8])
    await Timer(1, units="ns")
    assert int(dut.class_o.value) == 3
