from __future__ import annotations

import json
import os
from pathlib import Path

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb.utils import get_sim_time


def _cycle() -> int:
    return int(round(float(get_sim_time(units="ns")) / 10.0))


async def _send(dut, *, payload: int, completion: int, bin_tag: int) -> None:
    await FallingEdge(dut.clk)
    dut.input_payload.value = payload
    dut.input_completion.value = completion
    dut.input_bin_tag.value = bin_tag
    dut.input_valid.value = 1
    await Timer(1, units="ns")
    while not int(dut.input_ready.value):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
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
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    await Timer(1, units="ns")

    initialization_cycles = 0
    while not int(dut.input_ready.value):
        await RisingEdge(dut.clk)
        initialization_cycles += 1
        await Timer(1, units="ns")

    inference_start = _cycle()
    ingress_cycles_by_bin = []
    for bin_tag in range(1, 11):
        bin_start = _cycle()
        for row in inputs[inputs[:, 0] == bin_tag]:
            _, channel, y, x = (int(value) for value in row)
            payload = x | (y << 10) | (channel << 19)
            await _send(dut, payload=payload, completion=0, bin_tag=bin_tag)
        await _send(dut, payload=0, completion=1, bin_tag=bin_tag)
        ingress_cycles_by_bin.append(_cycle() - bin_start)

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

    total_cycles = _cycle() - inference_start
    average_cycles_per_bin = total_cycles / 10
    budget_cycles_per_bin = 500_000  # 100 MHz * 5 ms
    utilization = average_cycles_per_bin / budget_cycles_per_bin
    clock_mhz = 100
    metrics = {
        "schema_version": "1.0.0",
        "scope": "reduced_8x8_SRAM_integrated_RTL_not_native_resolution_PPA",
        "clock_mhz": clock_mhz,
        "semantic_bin_us": 5000,
        "bins": 10,
        "initialization_cycles_excluded_from_steady_state": initialization_cycles,
        "initialization_latency_us": initialization_cycles / clock_mhz,
        "steady_state_cycles_to_frame_done": total_cycles,
        "steady_state_latency_us": total_cycles / clock_mhz,
        "average_cycles_per_bin": average_cycles_per_bin,
        "average_latency_us_per_bin": average_cycles_per_bin / clock_mhz,
        "ingress_cycles_by_bin": ingress_cycles_by_bin,
        "maximum_ingress_cycles_per_bin": max(ingress_cycles_by_bin),
        "utilization_at_100MHz": utilization,
        "headroom_at_100MHz": (1.0 / utilization) if utilization else None,
        "native_resolution_claim": False,
        "power_claim": False,
    }
    metrics_path = Path(
        os.environ.get("EVENTSPIKESEG_RTL_METRICS", replay / "rtl_metrics.json")
    )
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
