import cocotb
from cocotb.triggers import Timer


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


@cocotb.test()
async def a_spike_inhibits_only_nonspiking_retinotopic_peers(dut):
    dut.adjusted_candidates_i.value = pack_signed([3, 4, -4, 0], 16)
    dut.strength_i.value = 1 << 10
    dut.spikes_i.value = 0b0001
    await Timer(1, units="ns")
    # floor(sqrt((9+16+16+0)/4)) = 3
    result = unpack_signed(int(dut.inhibited_membranes_o.value), 4, 16)
    assert result == [3, 1, -7, -3], (
        result,
        int(dut.square_sum.value),
        int(dut.mean_square.value),
        int(dut.rms.value),
        int(dut.decrement.value),
    )

    dut.spikes_i.value = 0
    await Timer(1, units="ns")
    assert unpack_signed(int(dut.inhibited_membranes_o.value), 4, 16) == [3, 4, -4, 0]
