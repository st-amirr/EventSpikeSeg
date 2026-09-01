from __future__ import annotations

import json
import os
import re
from collections import Counter
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


def _signal_stem(actor_name: str) -> str:
    return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", actor_name)


def _signed(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)


def _destination(destination: int, width: int, height: int) -> tuple[int, int, int]:
    spatial_count = width * height
    channel, spatial = divmod(destination, spatial_count)
    y, x = divmod(spatial, width)
    return channel, y, x


async def _capture_actor_spikes(dut, actor_name: str, rows: list[tuple[int, ...]]) -> None:
    """Capture each accepted actor-output spike without adding RTL debug ports."""

    stem = _signal_stem(actor_name)
    valid = getattr(dut, f"{stem}_valid")
    ready = getattr(dut, f"{stem}_ready")
    payload = getattr(dut, f"{stem}_payload")
    completion = getattr(dut, f"{stem}_completion")
    bin_tag = getattr(dut, f"{stem}_bin_tag")
    while True:
        await FallingEdge(dut.clk)
        if (
            not int(dut.reset.value)
            and int(valid.value)
            and int(ready.value)
            and not int(completion.value)
        ):
            packed = int(payload.value)
            rows.append(
                (
                    int(bin_tag.value),
                    (packed >> 19) & 0x1FFF,
                    (packed >> 10) & 0x1FF,
                    packed & 0x3FF,
                )
            )


async def _capture_actor_commits(
    dut,
    actor_name: str,
    *,
    width: int,
    height: int,
    mechanism: bool,
    adaptation: bool,
    current_rows: list[tuple[int, ...]],
    membrane_rows: list[tuple[int, ...]],
) -> None:
    """Observe actor commit internals used by the synthesized state machines."""

    wrapper = getattr(dut, f"actor_{_signal_stem(actor_name)[2:]}")
    actor = wrapper.actor
    neuron = (
        actor.mechanism_state.neuron_array
        if mechanism
        else actor.simple_state.neuron_array
    )
    while True:
        await FallingEdge(dut.clk)
        if int(dut.reset.value):
            continue
        state = int(neuron.state_reg.value)
        if not mechanism:
            # asynchronous_plif_actor COMMIT_WRITE
            if state == 7 and int(neuron.state_write_ready.value):
                channel, y, x = _destination(
                    int(neuron.destination_reg.value), width, height
                )
                current_rows.append(
                    (
                        int(neuron.epoch_tag_reg.value),
                        channel,
                        y,
                        x,
                        _signed(int(neuron.plif_current_in.value), 24),
                    )
                )
                membrane_rows.append(
                    (
                        int(neuron.epoch_tag_reg.value),
                        channel,
                        y,
                        x,
                        _signed(int(neuron.plif_candidate.value), 16),
                        _signed(int(neuron.result_membrane_reg.value), 16),
                        int(neuron.result_spike_reg.value),
                        -1,
                        0,
                    )
                )
            continue

        channel = int(neuron.group_channel_reg.value)
        spatial = int(neuron.spatial_reg.value)
        y, x = divmod(spatial, width)
        # retinotopic actor GROUP_READ_WAIT: capture only genuinely touched currents.
        if state == 7 and int(neuron.state_read_response_valid.value):
            packed_state = int(neuron.state_read_data.value)
            age_width = 16 if adaptation else 1
            amplitude_width = 16 if adaptation else 1
            touched_bit = 24 + 16 + 24 + age_width + amplitude_width + 1
            if (packed_state >> touched_bit) & 1:
                current_rows.append(
                    (
                        int(neuron.epoch_tag_reg.value),
                        channel,
                        y,
                        x,
                        _signed(packed_state, 24),
                    )
                )
        # retinotopic actor GROUP_WRITE: capture each channel selected for commit.
        if (
            state == 10
            and int(neuron.state_write_ready.value)
            and ((int(neuron.update_mask_reg.value) >> channel) & 1)
        ):
            candidates = int(neuron.candidates.value)
            membranes = int(neuron.result_membranes_reg.value)
            ages = int(neuron.result_ages_reg.value) if adaptation else 0
            amplitudes = int(neuron.result_amplitudes_reg.value) if adaptation else 0
            age = (ages >> (channel * 16)) & 0xFFFF if adaptation else 0xFFFF
            membrane_rows.append(
                (
                    int(neuron.epoch_tag_reg.value),
                    channel,
                    y,
                    x,
                    _signed(candidates >> (channel * 16), 16),
                    _signed(membranes >> (channel * 16), 16),
                    (int(neuron.spike_pending_reg.value) >> channel) & 1,
                    -1 if age == 0xFFFF else age,
                    (amplitudes >> (channel * 16)) & 0xFFFF,
                )
            )


@cocotb.test()
async def epoch35_integer_golden_replay_matches_semantic_output(dut) -> None:
    replay = Path(os.environ["EVENTSPIKESEG_REPLAY_DIR"])
    inputs = np.load(replay / "golden_input_samples.npz")["events"]
    spike_archive = np.load(replay / "golden_layer_spikes.npz")
    actor_names = [str(value) for value in spike_archive["actor_names"]]
    expected_spikes = spike_archive["spikes"]
    expected_currents = np.load(replay / "golden_layer_currents.npz")["currents"]
    expected_membranes = np.load(replay / "golden_layer_membranes.npz")["membranes"]
    spec = json.loads((replay / "model_spec.yaml").read_text(encoding="utf-8"))
    export_dir = (replay / str(spec.get("artifact_root", "."))).resolve()
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    semantic = np.load(replay / "golden_semantic_outputs.npz")
    expected_tag = int(semantic["bin_tags"][0])
    expected = semantic["classes"][0]

    observed_spikes = {name: [] for name in actor_names}
    observed_currents = {name: [] for name in actor_names}
    observed_membranes = {name: [] for name in actor_names}
    adaptation_actors: set[str] = set()
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    monitors = [
        cocotb.start_soon(_capture_actor_spikes(dut, name, observed_spikes[name]))
        for name in actor_names
    ]
    for name in actor_names:
        layer = layers[name]
        parameters = json.loads(
            (export_dir / str(layer["parameter_file"])).read_text(encoding="utf-8")
        )
        inhibition = bool(parameters.get("inhibition_enabled", False))
        adaptation = bool(parameters.get("threshold_adaptation_enabled", False))
        if adaptation:
            adaptation_actors.add(name)
        height, width = (int(value) for value in layer["output_hw"])
        monitors.append(
            cocotb.start_soon(
                _capture_actor_commits(
                    dut,
                    name,
                    width=width,
                    height=height,
                    mechanism=inhibition or adaptation,
                    adaptation=adaptation,
                    current_rows=observed_currents[name],
                    membrane_rows=observed_membranes[name],
                )
            )
        )
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
    for _ in range(2):
        await RisingEdge(dut.clk)
    for monitor in monitors:
        monitor.kill()

    compared_spike_rows = 0
    compared_current_rows = 0
    compared_membrane_rows = 0
    compared_adaptation_rows = 0
    for actor_id, actor_name in enumerate(actor_names):
        expected_actor = [
            tuple(int(value) for value in row[[0, 2, 3, 4]])
            for row in expected_spikes[expected_spikes[:, 1] == actor_id]
        ]
        assert Counter(observed_spikes[actor_name]) == Counter(expected_actor), (
            f"per-actor spike trace mismatch for {actor_name}: "
            f"observed={len(observed_spikes[actor_name])}, expected={len(expected_actor)}"
        )
        compared_spike_rows += len(expected_actor)
        expected_actor_currents = [
            tuple(int(value) for value in row[[0, 2, 3, 4, 5]])
            for row in expected_currents[expected_currents[:, 1] == actor_id]
        ]
        assert Counter(observed_currents[actor_name]) == Counter(expected_actor_currents), (
            f"per-actor current trace mismatch for {actor_name}: "
            f"observed={len(observed_currents[actor_name])}, "
            f"expected={len(expected_actor_currents)}"
        )
        compared_current_rows += len(expected_actor_currents)
        expected_actor_membranes = [
            tuple(int(value) for value in row[[0, 2, 3, 4, 5, 6, 7, 8, 9]])
            for row in expected_membranes[expected_membranes[:, 1] == actor_id]
        ]
        assert Counter(observed_membranes[actor_name]) == Counter(
            expected_actor_membranes
        ), (
            f"per-actor membrane trace mismatch for {actor_name}: "
            f"observed={len(observed_membranes[actor_name])}, "
            f"expected={len(expected_actor_membranes)}"
        )
        compared_membrane_rows += len(expected_actor_membranes)
        if actor_name in adaptation_actors:
            compared_adaptation_rows += len(expected_actor_membranes)

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
        "per_actor_spike_trace_actors_compared": len(actor_names),
        "per_actor_spike_trace_rows_compared": compared_spike_rows,
        "per_actor_spike_trace_exact_match": True,
        "per_actor_current_trace_rows_compared": compared_current_rows,
        "per_actor_current_trace_exact_match": True,
        "per_actor_membrane_trace_rows_compared": compared_membrane_rows,
        "per_actor_membrane_trace_exact_match": True,
        "per_actor_adaptation_trace_rows_compared": compared_adaptation_rows,
        "per_actor_adaptation_trace_exact_match": True,
        "utilization_at_100MHz": utilization,
        "headroom_at_100MHz": (1.0 / utilization) if utilization else None,
        "native_resolution_claim": False,
        "power_claim": False,
    }
    metrics_path = Path(
        os.environ.get("EVENTSPIKESEG_RTL_METRICS", replay / "rtl_metrics.json")
    )
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
