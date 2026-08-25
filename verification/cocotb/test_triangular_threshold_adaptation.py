import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def update(dut, *, elapsed: int, spike: int, energy: int = 100):
    dut.elapsed_bins_i.value = elapsed
    dut.spike_i.value = spike
    dut.membrane_energy_i.value = energy
    dut.update_valid.value = 1
    await RisingEdge(dut.clk)
    dut.update_valid.value = 0
    await Timer(1, units="ns")


@cocotb.test()
async def latest_spike_starts_one_local_inverted_v_process(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.update_valid.value = 0
    dut.strength_i.value = 1 << 9  # 0.5 in Q5.10
    dut.duration_i.value = 4
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    await update(dut, elapsed=1, spike=1)
    assert int(dut.penalty_o.value) == 0
    await update(dut, elapsed=1, spike=0)
    assert int(dut.penalty_o.value) == 12
    await update(dut, elapsed=3, spike=0)
    assert int(dut.penalty_o.value) == 50
    await update(dut, elapsed=4, spike=0)
    assert int(dut.penalty_o.value) == 0
    assert int(dut.active_o.value) == 0
