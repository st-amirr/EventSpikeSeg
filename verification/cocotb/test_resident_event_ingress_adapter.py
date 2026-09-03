import cocotb
from cocotb.triggers import Timer


def payload(x: int, y: int, channel: int) -> int:
    return x | (y << 10) | (channel << 19)


@cocotb.test()
async def raw_event_becomes_one_local_one_hot_pulse(dut) -> None:
    dut.in_valid_i.value = 1
    dut.in_payload_i.value = payload(2, 1, 1)
    dut.in_completion_i.value = 0
    dut.in_tag_i.value = 4
    dut.out_ready_i.value = 1
    await Timer(1, units="ns")
    assert int(dut.in_ready_o.value) == 1
    assert int(dut.out_valid_o.value) == 1
    assert int(dut.out_spike_vector_o.value) == 1 << (12 + 4 + 2)
    assert int(dut.coordinate_error_o.value) == 0

    dut.in_completion_i.value = 1
    await Timer(1, units="ns")
    assert int(dut.out_spike_vector_o.value) == 0
    assert int(dut.out_completion_o.value) == 1
    assert int(dut.out_tag_o.value) == 4

    dut.in_completion_i.value = 0
    dut.in_payload_i.value = payload(4, 0, 0)
    await Timer(1, units="ns")
    assert int(dut.coordinate_error_o.value) == 1
