from __future__ import annotations

import os
from pathlib import Path

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge


async def _send(dut, *, payload: int, completion: int, bin_tag: int) -> None:
    while not int(dut.input_ready.value):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.input_payload.value = payload
    dut.input_completion.value = completion
    dut.input_bin_tag.value = bin_tag
    dut.input_valid.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.input_valid.value = 0
    dut.input_completion.value = 0


@cocotb.test()
async def epoch35_integer_golden_replay_matches_semantic_output(dut) -> None:
    replay = Path(os.environ["EVENTSPIKESEG_REPLAY_DIR"])
    inputs = np.load(replay / "golden_input_samples.npz")["events"]
    semantic = np.load(replay / "golden_semantic_outputs.npz")
    expected_tag = int(semantic["bin_tags"][0])
    expected = semantic["classes"][0]

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.input_valid.value = 0
    dut.input_completion.value = 0
    dut.prediction_ready.value = 1
    dut.frame_done_ready.value = 1
    for _ in range(4):
        await RisingEdge(dut.clk)
    dut.reset.value = 0

    for bin_tag in range(1, 11):
        for row in inputs[inputs[:, 0] == bin_tag]:
            _, channel, y, x = (int(value) for value in row)
            payload = x | (y << 10) | (channel << 19)
            await _send(dut, payload=payload, completion=0, bin_tag=bin_tag)
        await _send(dut, payload=0, completion=1, bin_tag=bin_tag)

    observed = np.full(expected.shape, 255, dtype=np.uint8)
    frame_tag = None
    for _ in range(5_000_000):
        await RisingEdge(dut.clk)
        if int(dut.prediction_valid.value):
            x = int(dut.prediction_x_o.value)
            y = int(dut.prediction_y_o.value)
            observed[y, x] = int(dut.prediction_class_o.value)
        if int(dut.frame_done_valid.value):
            frame_tag = int(dut.frame_bin_tag_o.value)
            break
    else:
        raise AssertionError("exported DAG replay did not complete within 5,000,000 cycles")

    assert int(dut.fault_o.value) == 0
    assert frame_tag == expected_tag
    np.testing.assert_array_equal(observed, expected)
