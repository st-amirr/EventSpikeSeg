import cocotb
from cocotb.triggers import Timer


def signed_words(value: int, width: int, count: int) -> list[int]:
    mask = (1 << width) - 1
    result = []
    for index in range(count):
        word = (value >> (index * width)) & mask
        result.append(word - (1 << width) if word & (1 << (width - 1)) else word)
    return result


@cocotb.test()
async def spatial_tile_only_forms_its_local_destination_currents(dut) -> None:
    # This two-bit physical input tile represents global x=2,3. The actor
    # still owns global output x=2,3 and must translate before indexing it.
    dut.spike_vector_i.value = 0b11
    await Timer(1, units="ns")
    assert signed_words(int(dut.current_delta_o.value), 32, 2) == [3, 3]
