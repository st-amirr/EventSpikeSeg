"""Replay a checkpoint-derived actor trace and check every completed-bin vector."""

from __future__ import annotations

import json
import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


@cocotb.test()
async def exact_selected_coordinate_trace_matches(dut) -> None:
    trace = json.loads(Path(os.environ["EVENTSPIKESEG_ACTOR_TRACE"]).read_text())
    assert trace["actor"] == "enc3.pointwise"
    assert trace["scope"] == "single_coordinate_checkpoint_exact_integer_actor_trace"
    inputs = [int(value, 16) for value in trace["input_vectors_hex"]]
    expected = [int(value, 16) for value in trace["expected_output_vectors_hex"]]
    assert len(inputs) == len(expected) == int(trace["bins"])
    cocotb.start_soon(Clock(dut.clk, 5, units="ns").start())
    dut.reset.value = 1
    dut.presynaptic_valid_i.value = 0
    dut.presynaptic_spike_vector_i.value = 0
    dut.completion_valid_i.value = 0
    dut.completion_tag_i.value = 0
    dut.result_ready_i.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    for bin_index, (input_vector, expected_vector) in enumerate(
        zip(inputs, expected), start=1
    ):
        if input_vector:
            while not int(dut.presynaptic_ready_o.value):
                await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            dut.presynaptic_spike_vector_i.value = input_vector
            dut.presynaptic_valid_i.value = 1
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            dut.presynaptic_valid_i.value = 0
            dut.presynaptic_spike_vector_i.value = 0
        while not int(dut.completion_ready_o.value):
            await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        dut.completion_tag_i.value = bin_index
        dut.completion_valid_i.value = 1
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        dut.completion_valid_i.value = 0
        while not int(dut.result_valid_o.value):
            await RisingEdge(dut.clk)
        assert int(dut.completion_tag_o.value) == bin_index
        assert int(dut.spike_vector_o.value) == expected_vector
        assert int(dut.error_o.value) == 0
        dut.result_ready_i.value = 1
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        dut.result_ready_i.value = 0
