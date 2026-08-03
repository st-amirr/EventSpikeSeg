import cocotb
from cocotb.triggers import Timer


async def check(dut, ix, iy, kx, ky, expected) -> None:
    dut.input_x.value = ix
    dut.input_y.value = iy
    dut.kernel_x.value = kx
    dut.kernel_y.value = ky
    await Timer(1, units="ns")
    actual = (int(dut.valid.value), int(dut.output_x.value), int(dut.output_y.value))
    assert actual == expected


@cocotb.test()
async def stride_padding_and_border_addresses(dut) -> None:
    await check(dut, 0, 0, 1, 1, (1, 0, 0))
    await check(dut, 0, 0, 0, 0, (0, 0, 0))
    await check(dut, 239, 179, 2, 2, (1, 119, 89))
    await check(dut, 239, 179, 0, 0, (0, 0, 0))
