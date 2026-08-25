import cocotb
from cocotb.triggers import Timer


COORD_WIDTH = 10
WEIGHT_WIDTH = 8
TAP_COUNT = 9


def pack_signed(values: list[int], width: int) -> int:
    mask = (1 << width) - 1
    return sum((value & mask) << (index * width) for index, value in enumerate(values))


def unpack(packed: int, width: int, count: int) -> list[int]:
    mask = (1 << width) - 1
    return [(packed >> (index * width)) & mask for index in range(count)]


@cocotb.test()
async def parallel_3x3_scatter_uses_presynaptic_address_equation(dut):
    weights = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    dut.input_valid.value = 1
    dut.input_x.value = 5
    dut.input_y.value = 6
    dut.weights_i.value = pack_signed(weights, WEIGHT_WIDTH)
    await Timer(1, units="ns")

    assert int(dut.tap_valid_o.value) == (1 << TAP_COUNT) - 1
    xs = unpack(int(dut.tap_x_o.value), COORD_WIDTH, TAP_COUNT)
    ys = unpack(int(dut.tap_y_o.value), COORD_WIDTH, TAP_COUNT)
    emitted_weights = unpack(int(dut.tap_weight_o.value), WEIGHT_WIDTH, TAP_COUNT)

    assert xs == [6, 5, 4, 6, 5, 4, 6, 5, 4]
    assert ys == [7, 7, 7, 6, 6, 6, 5, 5, 5]
    assert emitted_weights == weights


@cocotb.test()
async def border_and_zero_weight_taps_are_suppressed(dut):
    weights = [1, 2, 3, 4, 0, 6, 7, 8, 9]
    dut.input_valid.value = 1
    dut.input_x.value = 0
    dut.input_y.value = 0
    dut.weights_i.value = pack_signed(weights, WEIGHT_WIDTH)
    await Timer(1, units="ns")

    # At (0,0), only kx<=1 and ky<=1 are in bounds. The centre tap is zero.
    expected_valid = (1 << 0) | (1 << 1) | (1 << 3)
    assert int(dut.tap_valid_o.value) == expected_valid
