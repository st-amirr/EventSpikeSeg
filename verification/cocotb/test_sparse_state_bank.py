import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut) -> None:
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def request(
    dut,
    *,
    address: int,
    write: bool = False,
    live: bool = False,
    membrane: int = 0,
    timestamp: int = 0,
    age: int = 0,
    amplitude: int = 0,
) -> tuple[bool, bool, int, int, int, int]:
    dut.request_valid.value = 1
    dut.write_enable.value = int(write)
    dut.address_i.value = address
    dut.state_live_i.value = int(live)
    dut.membrane_i.value = membrane
    dut.last_timestamp_i.value = timestamp
    dut.adaptation_age_i.value = age
    dut.adaptation_amplitude_i.value = amplitude
    await tick(dut)
    dut.request_valid.value = 0
    result = (
        bool(dut.found_o.value),
        bool(dut.overflow_o.value),
        dut.membrane_o.value.signed_integer,
        dut.last_timestamp_o.value.integer,
        dut.adaptation_age_o.value.signed_integer,
        dut.adaptation_amplitude_o.value.signed_integer,
    )
    await tick(dut)
    return result


@cocotb.test()
async def zero_default_update_reclaim_and_no_eviction(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.request_valid.value = 0
    dut.response_ready.value = 1
    dut.write_enable.value = 0
    dut.state_live_i.value = 0
    dut.address_i.value = 0
    dut.membrane_i.value = 0
    dut.last_timestamp_i.value = 0
    dut.adaptation_age_i.value = 0
    dut.adaptation_amplitude_i.value = 0
    await tick(dut)
    dut.reset.value = 0

    assert await request(dut, address=3) == (False, False, 0, 0, 0, 0)

    await request(
        dut,
        address=3,
        write=True,
        live=True,
        membrane=17,
        timestamp=5000,
        age=2,
        amplitude=4,
    )
    assert dut.live_entry_count_o.value.integer == 1
    assert await request(dut, address=3) == (True, False, 17, 5000, 2, 4)

    await request(
        dut,
        address=3,
        write=True,
        live=True,
        membrane=23,
        timestamp=7000,
    )
    assert dut.live_entry_count_o.value.integer == 1
    assert (await request(dut, address=3))[2:4] == (23, 7000)

    await request(dut, address=3, write=True, live=False)
    assert dut.live_entry_count_o.value.integer == 0
    assert await request(dut, address=3) == (False, False, 0, 0, 0, 0)

    # Default geometry is two ways and eight sets. These addresses collide.
    await request(dut, address=1, write=True, live=True, membrane=11)
    await request(dut, address=9, write=True, live=True, membrane=19)
    result = await request(dut, address=17, write=True, live=True, membrane=27)
    assert result[1] is True
    assert dut.live_entry_count_o.value.integer == 2
    assert (await request(dut, address=1))[2] == 11
    assert (await request(dut, address=9))[2] == 19
    assert (await request(dut, address=17))[0] is False
