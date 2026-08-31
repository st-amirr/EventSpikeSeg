import cocotb
from cocotb.triggers import Timer


def signed16(value: int) -> int:
    return value & 0xFFFF


@cocotb.test()
async def shared_energy_inhibits_only_nonspiking_peers(dut):
    dut.candidates_i.value = (signed16(6) << 16) | signed16(12)
    dut.base_thresholds_i.value = (10 << 16) | 10
    dut.update_mask_i.value = 0b11
    dut.ages_i.value = 0xFFFFFFFF
    dut.amplitudes_i.value = 0
    dut.elapsed_bins_i.value = (1 << 24) | 1
    dut.inhibition_enabled_i.value = 1
    dut.adaptation_enabled_i.value = 0
    dut.inhibition_strength_i.value = 1 << 10
    dut.adaptation_strength_i.value = 0
    dut.adaptation_duration_i.value = 0
    await Timer(1, units="ns")
    assert int(dut.spikes_o.value) == 0b01
    assert int(dut.membrane_energy_o.value) == 9
    assert int(dut.membranes_o.value) == (signed16(-3) << 16) | signed16(2)


@cocotb.test()
async def triangular_processes_sum_before_all_channel_thresholds(dut):
    dut.candidates_i.value = (signed16(5) << 16) | signed16(25)
    dut.base_thresholds_i.value = (10 << 16) | 10
    dut.update_mask_i.value = 0b11
    dut.ages_i.value = (0xFFFF << 16) | (1 << 10)
    dut.amplitudes_i.value = 20
    dut.elapsed_bins_i.value = 0
    dut.inhibition_enabled_i.value = 0
    dut.adaptation_enabled_i.value = 1
    dut.inhibition_strength_i.value = 0
    dut.adaptation_strength_i.value = 1 << 10
    dut.adaptation_duration_i.value = 2 << 10
    await Timer(1, units="ns")
    assert int(dut.shared_penalty_o.value) == 10
    assert int(dut.spikes_o.value) == 0b01
    assert int(dut.membranes_o.value) == (signed16(5) << 16) | signed16(5)
    assert int(dut.ages_o.value) & 0xFFFF == 0
    assert int(dut.amplitudes_o.value) & 0xFFFF == 11
