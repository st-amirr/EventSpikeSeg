from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


def _integer(signal) -> int:
    return int(signal.value)


async def _transfer(dut, *, payload: int, completion: bool, bin_tag: int) -> None:
    dut.input_payload.value = payload
    dut.input_completion.value = int(completion)
    dut.input_bin_tag.value = bin_tag
    dut.input_valid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if _integer(dut.input_ready):
            break
    dut.input_valid.value = 0
    dut.input_completion.value = 0


async def _drive_golden_input(dut, rows: np.ndarray) -> None:
    tags = list(dict.fromkeys(int(row[0]) for row in rows))
    for tag in tags:
        for _, channel, y, x in rows[rows[:, 0] == tag]:
            payload = int(x) | (int(y) << 10) | (int(channel) << 19)
            await _transfer(dut, payload=payload, completion=False, bin_tag=tag)
        await _transfer(dut, payload=0, completion=True, bin_tag=tag)


@cocotb.test()
async def replay_integer_golden_through_generated_dag(dut) -> None:
    replay_dir = Path(os.environ["ASIC_REPLAY_DIR"])
    with np.load(replay_dir / "golden_input_samples.npz", allow_pickle=False) as archive:
        input_rows = archive["events"]
    with np.load(replay_dir / "golden_layer_spikes.npz", allow_pickle=False) as archive:
        expected_spikes = Counter(tuple(int(value) for value in row) for row in archive["spikes"])
        actor_count = len(archive["actor_names"])
    with np.load(replay_dir / "golden_semantic_outputs.npz", allow_pickle=False) as archive:
        expected_classes = archive["classes"][0]
        expected_frame_tag = int(archive["bin_tags"][0])

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.reset.value = 1
    dut.input_valid.value = 0
    dut.input_payload.value = 0
    dut.input_completion.value = 0
    dut.input_bin_tag.value = 0
    dut.prediction_ready.value = 1
    dut.frame_done_ready.value = 1
    for _ in range(4):
        await RisingEdge(dut.clk)
    dut.reset.value = 0

    driver = cocotb.start_soon(_drive_golden_input(dut, input_rows))
    observed_spikes: Counter[tuple[int, ...]] = Counter()
    completion_counts = Counter()
    observed_classes: dict[tuple[int, int], int] = {}
    frame_tag = None
    timeout_cycles = int(os.environ.get("ASIC_REPLAY_TIMEOUT_CYCLES", "2000000"))
    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk)
        assert not _integer(dut.fault_o), "generated DAG asserted a routing/state fault"
        valid = _integer(dut.actor_trace_valid_o)
        ready = _integer(dut.actor_trace_ready_o)
        completion = _integer(dut.actor_trace_completion_o)
        payloads = _integer(dut.actor_trace_payload_o)
        tags = _integer(dut.actor_trace_bin_tag_o)
        transfers = valid & ready
        for actor_id in range(actor_count):
            if not (transfers >> actor_id) & 1:
                continue
            bin_tag = (tags >> (actor_id * 24)) & 0xFFFFFF
            if (completion >> actor_id) & 1:
                completion_counts[(bin_tag, actor_id)] += 1
                continue
            payload = (payloads >> (actor_id * 32)) & 0xFFFFFFFF
            x = payload & 0x3FF
            y = (payload >> 10) & 0x1FF
            channel = (payload >> 19) & 0x7F
            observed_spikes[(bin_tag, actor_id, channel, y, x)] += 1
        if _integer(dut.prediction_valid) and _integer(dut.prediction_ready):
            coordinate = (_integer(dut.prediction_y_o), _integer(dut.prediction_x_o))
            assert coordinate not in observed_classes
            observed_classes[coordinate] = _integer(dut.prediction_class_o)
        if _integer(dut.frame_done_valid):
            frame_tag = _integer(dut.frame_bin_tag_o)
            break
    else:
        raise AssertionError(f"RTL replay exceeded {timeout_cycles} cycles")

    await driver
    assert observed_spikes == expected_spikes
    expected_completions = Counter(
        (tag, actor_id)
        for tag in dict.fromkeys(int(row[0]) for row in input_rows)
        for actor_id in range(actor_count)
    )
    assert completion_counts == expected_completions
    assert frame_tag == expected_frame_tag
    assert len(observed_classes) == expected_classes.size
    for (y, x), class_index in observed_classes.items():
        assert class_index == int(expected_classes[y, x])
