import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut) -> None:
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


@cocotb.test()
async def schedules_all_actors_and_marks_prediction_window(dut) -> None:
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.bin_valid_i.value = 0
    dut.bin_buffer_i.value = 0
    dut.actor_advance_i.value = 0
    await tick(dut)
    dut.reset.value = 0

    for bin_index in range(10):
        assert int(dut.bin_ready_o.value) == 1
        dut.bin_valid_i.value = 1
        dut.bin_buffer_i.value = bin_index & 1
        await tick(dut)
        dut.bin_valid_i.value = 0
        assert int(dut.active_o.value) == 1
        assert int(dut.active_buffer_o.value) == (bin_index & 1)

        for actor_index in range(25):
            assert int(dut.actor_index_o.value) == actor_index
            dut.actor_advance_i.value = 1
            await tick(dut)
        dut.actor_advance_i.value = 0

        assert int(dut.bin_done_o.value) == 1
        assert int(dut.bin_cycles_o.value) == 25
        assert int(dut.current_bin_tag_o.value) == bin_index + 1
        assert int(dut.prediction_due_o.value) == int(bin_index == 9)
        assert int(dut.hard_deadline_miss_o.value) == 0
        assert int(dut.target_budget_miss_o.value) == 0
        await tick(dut)
