import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def reset_dut(dut):
    dut.reset.value = 1
    dut.presynaptic_valid.value = 0
    dut.epoch_end_valid.value = 0
    dut.spike_ready.value = 1
    # Hold completion so the test cannot miss a one-cycle ready/valid transfer.
    dut.epoch_done_ready.value = 0
    dut.beta_i.value = 1 << 15
    dut.threshold_i.value = 100
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def send_presynaptic_spike(dut, x: int, y: int):
    while not int(dut.presynaptic_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_x.value = x
    dut.presynaptic_y.value = y
    dut.presynaptic_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.presynaptic_valid.value = 0


@cocotb.test()
async def static_kernel_scatter_accumulates_in_actor_local_membranes(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Each of the nine static 3x3 taps contributes 20 to its own destination.
    # Five identical presynaptic spikes therefore make all nine PLIFs reach 100.
    for _ in range(5):
        await send_presynaptic_spike(dut, 5, 6)

    while not int(dut.epoch_end_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.epoch_tag_i.value = 4
    dut.epoch_end_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.epoch_end_valid.value = 0

    spikes = []
    for _ in range(300):
        await RisingEdge(dut.clk)
        if int(dut.spike_valid.value):
            spikes.append(int(dut.spike_destination_o.value))
        if int(dut.epoch_done_valid.value):
            break
    else:
        raise AssertionError(
            "integrated actor did not finish epoch: "
            f"state={int(dut.neuron_array.state_reg.value)} "
            f"pending={int(dut.pending_valid_reg.value):x} "
            f"touched={int(dut.neuron_array.touched_count_reg.value)} "
            f"commit={int(dut.neuron_array.commit_index_reg.value)}"
        )

    assert spikes == [118, 117, 116, 102, 101, 100, 86, 85, 84]
    assert int(dut.epoch_tag_o.value) == 4
    dut.epoch_done_ready.value = 1
    await RisingEdge(dut.clk)
