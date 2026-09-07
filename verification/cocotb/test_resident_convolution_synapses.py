import cocotb
from cocotb.triggers import Timer


def signed_words(value: int, width: int, count: int) -> list[int]:
    mask = (1 << width) - 1
    words = []
    for index in range(count):
        word = (value >> (index * width)) & mask
        words.append(word - (1 << width) if word & (1 << (width - 1)) else word)
    return words


@cocotb.test()
async def bitmap_spikes_drive_static_grouped_synapses_in_parallel(dut) -> None:
    # Two input channels, two output channels, depthwise 1x1 weights +3 and -2.
    # Channel-major input bitmap: c0 pixels 0,1 and c1 pixel 0 spike.
    dut.spike_vector_i.value = 0b010011
    await Timer(1, units="ns")
    assert signed_words(int(dut.current_delta_o.value), 32, 8) == [3, 3, 0, 0, -2, 0, 0, 0]
