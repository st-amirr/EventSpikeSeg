import cocotb
from cocotb.triggers import Timer


def payload(channel: int, y: int, x: int) -> int:
    return x | (y << 10) | (channel << 19)


@cocotb.test()
async def remaps_only_data_channel_and_preserves_token(dut):
    dut.out_ready.value = 1
    dut.in_valid.value = 1
    dut.in_completion.value = 0
    dut.in_bin_tag.value = 12
    dut.in_payload.value = payload(3, 17, 29)
    await Timer(1, units="ns")
    value = int(dut.out_payload.value)
    assert value & 0x3FF == 29
    assert (value >> 10) & 0x1FF == 17
    assert (value >> 19) & 0x7F == 67
    assert int(dut.channel_overflow_o.value) == 0

    original = payload(5, 2, 1)
    dut.in_completion.value = 1
    dut.in_payload.value = original
    await Timer(1, units="ns")
    assert int(dut.out_payload.value) == original
    assert int(dut.out_completion.value) == 1
    assert int(dut.out_bin_tag.value) == 12
