#!/usr/bin/env python3
"""Generate deterministic activity traces for exact 140k mechanism/readout leaves."""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path


PERIOD_PS = 5_000
MEM_WIDTH = 24
AGE_WIDTH = 6
AMPLITUDE_WIDTH = 19
ELAPSED_WIDTH = 24
INACTIVE_AGE = (1 << AGE_WIDTH) - 1
MAX_MEM = (1 << (MEM_WIDTH - 1)) - 1
MIN_MEM = -(1 << (MEM_WIDTH - 1))
MAX_VALUE = (1 << MEM_WIDTH) - 1
MAX_AMPLITUDE = (1 << AMPLITUDE_WIDTH) - 1


def packed(values: list[int], width: int) -> int:
    result = 0
    mask = (1 << width) - 1
    for channel, value in enumerate(values):
        result |= (value & mask) << (channel * width)
    return result


def unpacked(value: int, width: int, count: int, *, signed_values: bool = False) -> list[int]:
    mask = (1 << width) - 1
    values = [(value >> (channel * width)) & mask for channel in range(count)]
    return [signed(item, width) for item in values] if signed_values else values


def signed(value: int, width: int) -> int:
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def bits(value: int, width: int) -> str:
    return format(value & ((1 << width) - 1), f"0{width}b")


def write_vcd(
    path: Path,
    scope: str,
    signals: list[tuple[str, str, int]],
    samples: list[dict[str, int]],
) -> None:
    with path.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(f"$timescale 1ps $end\n$scope module {scope} $end\n")
        handle.write("$scope module dut $end\n")
        for code, name, width in signals:
            suffix = "" if width == 1 else f" [{width - 1}:0]"
            handle.write(f"$var wire {width} {code} {name}{suffix} $end\n")
        handle.write("$upscope $end\n$upscope $end\n$enddefinitions $end\n")
        previous: dict[str, int] = {}
        for stamp, values in enumerate(samples):
            handle.write(f"#{stamp * PERIOD_PS}\n")
            handle.write("0!\n")
            for code, name, width in signals:
                if name == "clk":
                    continue
                value = values[name]
                if previous.get(name) != value:
                    if width == 1:
                        handle.write(f"{value}{code}\n")
                    else:
                        handle.write(f"b{bits(value, width)} {code}\n")
                    previous[name] = value
            handle.write(f"#{stamp * PERIOD_PS + PERIOD_PS // 2}\n")
            handle.write("1!\n")


def mechanism_update(
    candidates: list[int],
    thresholds: list[int],
    update_mask: int,
    ages: list[int],
    amplitudes: list[int],
    elapsed: list[int],
    inhibition_strength: int,
    adaptation_strength: int,
    adaptation_duration: int,
    inhibition_enabled: bool,
    adaptation_enabled: bool,
) -> tuple[list[int], int, list[int], list[int], int, int]:
    penalty_sum = 0
    for channel, age in enumerate(ages):
        effective_age = age
        if age != INACTIVE_AGE and ((update_mask >> channel) & 1):
            effective_age += elapsed[channel]
        effective_age_q = effective_age << 16
        phase = 0
        if adaptation_enabled and age != INACTIVE_AGE and adaptation_duration:
            if effective_age_q <= adaptation_duration:
                phase = effective_age_q
            elif effective_age_q < 2 * adaptation_duration:
                phase = 2 * adaptation_duration - effective_age_q
        penalty_sum += 0 if adaptation_duration == 0 else (
            amplitudes[channel] * phase // adaptation_duration
        )
    shared_penalty = min(penalty_sum, MAX_VALUE)

    adjusted = [candidate - shared_penalty for candidate in candidates]
    mean_square = sum(abs(value) * abs(value) for value in adjusted) // len(adjusted)
    membrane_energy = min(math.isqrt(mean_square), MAX_VALUE)

    membranes: list[int] = []
    spikes = 0
    next_ages = list(ages)
    next_amplitudes = list(amplitudes)
    for channel, candidate in enumerate(candidates):
        threshold = min(thresholds[channel] + shared_penalty, MAX_MEM)
        spike = bool((update_mask >> channel) & 1) and candidate >= threshold
        if spike:
            spikes |= 1 << channel
        membrane = candidate - threshold if spike else candidate
        membranes.append(clamp(membrane, MIN_MEM, MAX_MEM))

        if adaptation_enabled and ((update_mask >> channel) & 1):
            effective_age = ages[channel] + elapsed[channel]
            effective_age_q = effective_age << 16
            if spike:
                next_ages[channel] = 0
                next_amplitudes[channel] = min(
                    (membrane_energy * adaptation_strength + (1 << 15)) >> 16,
                    MAX_AMPLITUDE,
                )
            elif ages[channel] != INACTIVE_AGE:
                if effective_age_q >= 2 * adaptation_duration:
                    next_ages[channel] = INACTIVE_AGE
                    next_amplitudes[channel] = 0
                else:
                    next_ages[channel] = effective_age & INACTIVE_AGE

    if inhibition_enabled and spikes:
        decrement = (membrane_energy * inhibition_strength + (1 << 15)) >> 16
        for channel in range(len(membranes)):
            if not ((spikes >> channel) & 1):
                membranes[channel] = clamp(
                    membranes[channel] - decrement, MIN_MEM, MAX_MEM
                )
    return (
        membranes,
        spikes,
        next_ages,
        next_amplitudes,
        shared_penalty,
        membrane_energy,
    )


def mechanism_samples(
    thresholds: list[int],
    channels: int,
    seed: int,
    inhibition_strength: int,
    adaptation_strength: int,
    adaptation_duration: int,
) -> tuple[list[dict[str, int]], dict[str, int]]:
    rng = random.Random(seed)
    samples: list[dict[str, int]] = []
    spike_count = 0
    active_adaptation_states = 0
    for sample in range(128):
        common = int(12_000 * math.sin(2 * math.pi * sample / 23))
        burst = 18_000 if sample % 17 in (0, 1, 2) else 0
        candidates = [
            clamp(
                thresholds[channel] - 12_000 + common + burst
                + rng.randint(-9_000, 9_000),
                MIN_MEM,
                MAX_MEM,
            )
            for channel in range(channels)
        ]
        update_mask = (1 << channels) - 1
        if adaptation_strength:
            ages = []
            amplitudes = []
            for channel in range(channels):
                active = (sample + channel) % 7 != 0
                age = (sample + 3 * channel) % 10 if active else INACTIVE_AGE
                ages.append(age)
                amplitudes.append(
                    0 if not active else 220 + ((sample * 29 + channel * 43) % 780)
                )
                active_adaptation_states += int(active)
        else:
            ages = [0] * channels
            amplitudes = [0] * channels
        elapsed = [1] * channels
        result = mechanism_update(
            candidates,
            thresholds,
            update_mask,
            ages,
            amplitudes,
            elapsed,
            inhibition_strength,
            adaptation_strength,
            adaptation_duration,
            bool(inhibition_strength),
            bool(adaptation_strength),
        )
        membranes, spikes, next_ages, next_amplitudes, penalty, energy = result
        spike_count += spikes.bit_count()
        samples.append(
            {
                "clk": 0,
                "candidates_i": packed(candidates, MEM_WIDTH),
                "update_mask_i": update_mask,
                "ages_i": packed(ages, AGE_WIDTH),
                "amplitudes_i": packed(amplitudes, AMPLITUDE_WIDTH),
                "elapsed_bins_i": packed(elapsed, ELAPSED_WIDTH),
                "membranes_o": packed(membranes, MEM_WIDTH),
                "spikes_o": spikes,
                "ages_o": packed(next_ages, AGE_WIDTH),
                "amplitudes_o": packed(next_amplitudes, AMPLITUDE_WIDTH),
                "shared_penalty_o": penalty,
                "membrane_energy_o": energy,
            }
        )
    return samples, {
        "samples": len(samples),
        "spikes": spike_count,
        "active_adaptation_input_states": active_adaptation_states,
    }


def decomposed_adaptation_samples(
    samples: list[dict[str, int]],
    thresholds: list[int],
    channels: int,
    adaptation_strength: int,
    adaptation_duration: int,
) -> dict[str, list[dict[str, int]]]:
    if channels not in (64, 128):
        raise ValueError(f"unsupported adaptation channel count: {channels}")
    traces = {
        "penalty_lane": [],
        "penalty_reduce64_direct": [],
        "penalty_reduce64_lower": [],
        "penalty_reduce64_upper": [],
        "square_lane": [],
        "energy_reduce64": [],
        "energy_reduce128": [],
        "commit_lane": [],
    }
    for sample in samples:
        candidates = unpacked(
            sample["candidates_i"], MEM_WIDTH, channels, signed_values=True
        )
        ages = unpacked(sample["ages_i"], AGE_WIDTH, channels)
        amplitudes = unpacked(sample["amplitudes_i"], AMPLITUDE_WIDTH, channels)
        elapsed = unpacked(sample["elapsed_bins_i"], ELAPSED_WIDTH, channels)
        membranes = unpacked(
            sample["membranes_o"], MEM_WIDTH, channels, signed_values=True
        )
        next_ages = unpacked(sample["ages_o"], AGE_WIDTH, channels)
        next_amplitudes = unpacked(sample["amplitudes_o"], AMPLITUDE_WIDTH, channels)
        update_mask = sample["update_mask_i"]
        shared_penalty = sample["shared_penalty_o"]
        energy = sample["membrane_energy_o"]
        penalties: list[int] = []
        squares: list[int] = []
        for channel in range(channels):
            update = (update_mask >> channel) & 1
            effective_age = ages[channel]
            if ages[channel] != INACTIVE_AGE and update:
                effective_age += elapsed[channel]
            effective_age_q = effective_age << 16
            phase = 0
            if ages[channel] != INACTIVE_AGE:
                if effective_age_q <= adaptation_duration:
                    phase = effective_age_q
                elif effective_age_q < 2 * adaptation_duration:
                    phase = 2 * adaptation_duration - effective_age_q
            penalty = min(
                amplitudes[channel] * phase // adaptation_duration, MAX_VALUE
            )
            square = abs(candidates[channel] - shared_penalty) ** 2
            penalties.append(penalty)
            squares.append(square)
            traces["penalty_lane"].append({
                "clk": 0, "update_i": update, "age_i": ages[channel],
                "amplitude_i": amplitudes[channel], "elapsed_bins_i": elapsed[channel],
                "adaptation_duration_i": adaptation_duration,
                "penalty_o": penalty,
            })
            traces["square_lane"].append({
                "clk": 0, "candidate_i": candidates[channel],
                "shared_penalty_i": shared_penalty, "square_o": square,
            })
            traces["commit_lane"].append({
                "clk": 0, "candidate_i": candidates[channel],
                "base_threshold_i": thresholds[channel], "update_i": update,
                "age_i": ages[channel], "amplitude_i": amplitudes[channel],
                "elapsed_bins_i": elapsed[channel],
                "shared_penalty_i": shared_penalty, "membrane_energy_i": energy,
                "adaptation_strength_i": adaptation_strength,
                "adaptation_duration_i": adaptation_duration,
                "membrane_o": membranes[channel],
                "spike_o": (sample["spikes_o"] >> channel) & 1,
                "age_o": next_ages[channel], "amplitude_o": next_amplitudes[channel],
            })
        if channels == 64:
            traces["penalty_reduce64_direct"].append({
                "clk": 0, "penalties_i": packed(penalties, MEM_WIDTH),
                "shared_penalty_o": shared_penalty,
            })
            traces["energy_reduce64"].append({
                "clk": 0, "squares_i": packed(squares, 2 * MEM_WIDTH),
                "membrane_energy_o": energy,
            })
        else:
            lower = [
                min(sum(penalties[:64]), MAX_VALUE),
                min(sum(penalties[64:]), MAX_VALUE),
            ]
            if min(sum(lower), MAX_VALUE) != shared_penalty:
                raise AssertionError("hierarchical 128-channel penalty mismatch")
            for half in range(2):
                traces["penalty_reduce64_lower"].append({
                    "clk": 0,
                    "penalties_i": packed(
                        penalties[half * 64:(half + 1) * 64], MEM_WIDTH
                    ),
                    "shared_penalty_o": lower[half],
                })
            traces["penalty_reduce64_upper"].append({
                "clk": 0,
                "penalties_i": packed(lower + [0] * 62, MEM_WIDTH),
                "shared_penalty_o": shared_penalty,
            })
            traces["energy_reduce128"].append({
                "clk": 0, "squares_i": packed(squares, 2 * MEM_WIDTH),
                "membrane_energy_o": energy,
            })
    return traces


def read_signed_mem(path: Path, width: int) -> list[int]:
    return [signed(int(line.strip(), 16), width) for line in path.read_text().splitlines() if line.strip()]


def readout_samples(weights: list[int]) -> tuple[list[dict[str, int]], dict[str, int]]:
    rng = random.Random(0x140C0DE)
    state = "COLLECT"
    bin_count = 0
    scores = [0] * 6
    frame_tag = 0
    samples: list[dict[str, int]] = []
    accepted_vectors = 0
    emitted_class = 0

    def outputs(inputs: dict[str, int]) -> dict[str, int]:
        prediction_class = max(range(6), key=lambda cls: (scores[cls], -cls))
        return inputs | {
            "in_ready_o": int(state == "COLLECT"),
            "prediction_valid_o": int(state == "EMIT"),
            "prediction_x_o": 0,
            "prediction_y_o": 0,
            "prediction_class_o": prediction_class,
            "frame_done_valid_o": int(state == "HOLD_DONE"),
            "frame_tag_o": frame_tag,
        }

    def cycle(inputs: dict[str, int]) -> None:
        nonlocal state, bin_count, scores, frame_tag, accepted_vectors, emitted_class
        complete = outputs({"clk": 0, **inputs})
        samples.append(complete)
        if inputs["reset"]:
            state = "COLLECT"
            bin_count = 0
            scores = [0] * 6
            frame_tag = 0
            return
        if state == "COLLECT" and inputs["in_valid_i"]:
            if inputs["in_completion_i"]:
                frame_tag = inputs["in_tag_i"]
                if bin_count + 1 >= 10:
                    state = "EMIT"
                else:
                    bin_count += 1
            else:
                accepted_vectors += 1
                vector = inputs["in_spike_vector_i"]
                for cls in range(6):
                    delta = sum(
                        weights[cls * 16 + channel]
                        for channel in range(16)
                        if (vector >> channel) & 1
                    )
                    scores[cls] = clamp(scores[cls] + delta, -(1 << 31), (1 << 31) - 1)
        elif state == "EMIT" and inputs["prediction_ready_i"]:
            emitted_class = max(range(6), key=lambda cls: (scores[cls], -cls))
            scores = [0] * 6
            state = "HOLD_DONE"
        elif state == "HOLD_DONE" and inputs["frame_done_ready_i"]:
            state = "COLLECT"
            bin_count = 0

    idle = {
        "reset": 0,
        "in_valid_i": 0,
        "in_spike_vector_i": 0,
        "in_completion_i": 0,
        "in_tag_i": 0,
        "prediction_ready_i": 0,
        "frame_done_ready_i": 0,
    }
    for _ in range(3):
        cycle(idle | {"reset": 1})
    cycle(idle)
    for bin_index in range(10):
        common_mask = 0
        for channel in range(16):
            probability = 0.12 + 0.06 * ((channel + bin_index) % 4)
            if rng.random() < probability:
                common_mask |= 1 << channel
        for event_index in range(3):
            correlated = common_mask
            correlated ^= 1 << ((bin_index * 3 + event_index * 5) % 16)
            if event_index == 2 and bin_index % 3:
                correlated &= ~(1 << ((bin_index + 7) % 16))
            cycle(idle | {"in_valid_i": 1, "in_spike_vector_i": correlated})
        cycle(
            idle
            | {
                "in_valid_i": 1,
                "in_completion_i": 1,
                "in_tag_i": bin_index + 1,
            }
        )
    cycle(idle)
    cycle(idle)
    cycle(idle | {"prediction_ready_i": 1})
    cycle(idle)
    cycle(idle | {"frame_done_ready_i": 1})
    cycle(idle)
    return samples, {
        "bins": 10,
        "accepted_spike_vectors": accepted_vectors,
        "prediction_stall_cycles": 2,
        "frame_done_stall_cycles": 1,
        "emitted_class": emitted_class,
        "cycles": len(samples),
    }


def power_tcl(design: str, scope: str, vcd_name: str) -> str:
    result = f"/workspace/artifacts/OpenROAD/results/asap7/{design}/checkpoint_exact"
    return f"""set platform /OpenROAD-flow-scripts/flow/platforms/asap7
foreach lib [glob $platform/lib/NLDM/*RVT*TT*.lib*] {{
  read_liberty $lib
}}
read_db {result}/6_final.odb
read_sdc {result}/6_final.sdc
read_spef {result}/6_final.spef
read_vcd -scope {scope}/dut /out/{vcd_name}
report_activity_annotation > /out/activity_annotation.rpt
report_power -digits 9 > /out/activity_power.rpt
puts "ACTIVITY_POWER_PASS"
"""


def write_case(
    output: Path,
    vcd_name: str,
    scope: str,
    signals: list[tuple[str, str, int]],
    samples: list[dict[str, int]],
    design: str,
    manifest: dict[str, object],
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    vcd = output / vcd_name
    write_vcd(vcd, scope, signals, samples)
    manifest |= {
        "model": "EventSpikeSeg140k",
        "checkpoint_epoch": 80,
        "checkpoint_seed": 17,
        "clock_period_ns": PERIOD_PS / 1000,
        "vcd_scope": f"{scope}/dut",
        "vcd_sha256": hashlib.sha256(vcd.read_bytes()).hexdigest(),
    }
    (output / "activity_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (output / "activity_power.tcl").write_text(
        power_tcl(design, scope, vcd_name), encoding="utf-8", newline="\n"
    )


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    params = repo / "artifacts/ASIC/parameters"
    model_spec = json.loads((repo / "artifacts/ASIC/model_spec.yaml").read_text())
    output_root = repo / "artifacts/ASIC/primitive_characterization"
    stem = json.loads((params / "02_stem.json").read_text())
    down2 = json.loads((params / "06_down2_standard.json").read_text())
    readout_weights = read_signed_mem(
        repo / "artifacts/ASIC/weights/25_head_synapse.mem", 24
    )
    if stem["inhibition_strength_q"] != [929] or len(stem["threshold_q"]) != 32:
        raise ValueError("unexpected epoch-80 stem mechanism constants")
    if down2["threshold_adaptation_strength_q"] != [875]:
        raise ValueError("unexpected epoch-80 down2 adaptation strength")
    if down2["adaptation_duration_q"] != [320026] or len(down2["threshold_q"]) != 64:
        raise ValueError("unexpected epoch-80 down2 adaptation constants")
    if len(readout_weights) != 96:
        raise ValueError("expected 6x16 readout weights")

    stem_samples, stem_stats = mechanism_samples(
        stem["threshold_q"], 32, 0x140532, 929, 0, 0
    )
    adaptation_profiles: list[dict[str, object]] = []
    decomposed = {
        key: [] for key in (
            "penalty_lane", "penalty_reduce64_direct",
            "penalty_reduce64_lower", "penalty_reduce64_upper",
            "square_lane", "energy_reduce64", "energy_reduce128", "commit_lane",
        )
    }
    down2_samples: list[dict[str, int]] | None = None
    down2_stats: dict[str, int] | None = None
    for layer in model_spec["layers"]:
        if not layer.get("logical_membrane_states"):
            continue
        actor_params = json.loads(
            (repo / "artifacts/ASIC" / layer["parameter_file"]).read_text()
        )
        if not actor_params.get("threshold_adaptation_enabled"):
            continue
        channels = int(layer["out_channels"])
        if channels not in (64, 128):
            raise ValueError(f"unexpected adaptation width for {layer['name']}: {channels}")
        strength = int(actor_params["threshold_adaptation_strength_q"][0])
        duration = int(actor_params["adaptation_duration_q"][0])
        thresholds = list(map(int, actor_params["threshold_q"]))
        if len(thresholds) != channels:
            raise ValueError(f"threshold count mismatch for {layer['name']}")
        actor_samples, actor_stats = mechanism_samples(
            thresholds, channels, 0x140D000 + int(layer["id"]), 0,
            strength, duration,
        )
        actor_traces = decomposed_adaptation_samples(
            actor_samples, thresholds, channels, strength, duration
        )
        h, w = map(int, layer["output_hw"])
        spatial_weight, remainder = divmod(h * w, 4_400)
        if remainder:
            raise ValueError(f"nonintegral spatial activity weight for {layer['name']}")
        for key, values in actor_traces.items():
            decomposed[key].extend(values * spatial_weight)
        adaptation_profiles.append({
            "actor": layer["name"],
            "channels": channels,
            "spatial_groups": h * w,
            "lane_instances": int(layer["logical_membrane_states"]),
            "pooled_trace_spatial_weight": spatial_weight,
            "adaptation_strength_q3_16": strength,
            "adaptation_duration_q5_16": duration,
            **actor_stats,
        })
        if layer["name"] == "down2.standard":
            down2_samples, down2_stats = actor_samples, actor_stats
    if down2_samples is None or down2_stats is None:
        raise ValueError("down2.standard adaptation profile missing")
    lane_instances = sum(
        int(profile["lane_instances"]) for profile in adaptation_profiles
    )
    spatial_groups = {
        width: sum(
            int(profile["spatial_groups"])
            for profile in adaptation_profiles
            if profile["channels"] == width
        )
        for width in (64, 128)
    }
    if (
        len(adaptation_profiles) != 15
        or lane_instances != 10_982_400
        or spatial_groups != {64: 92_400, 128: 39_600}
    ):
        raise ValueError("adaptation inventory no longer matches the 140k checkpoint")
    expected_trace_samples = {
        "penalty_lane": 319_488,
        "penalty_reduce64_direct": 2_688,
        "penalty_reduce64_lower": 2_304,
        "penalty_reduce64_upper": 1_152,
        "square_lane": 319_488,
        "energy_reduce64": 2_688,
        "energy_reduce128": 1_152,
        "commit_lane": 319_488,
    }
    if {key: len(values) for key, values in decomposed.items()} != expected_trace_samples:
        raise ValueError("population-weighted adaptation trace count mismatch")
    readout_trace, readout_stats = readout_samples(readout_weights)

    stem_signals = [
        ("!", "clk", 1), ('"', "candidates_i", 32 * 24),
        ("#", "update_mask_i", 32), ("$", "membranes_o", 32 * 24),
        ("%", "spikes_o", 32), ("&", "shared_penalty_o", 24),
        ("'", "membrane_energy_o", 24),
    ]
    down2_signals = [
        ("!", "clk", 1), ('"', "candidates_i", 64 * 24),
        ("#", "update_mask_i", 64), ("$", "ages_i", 64 * 6),
        ("%", "amplitudes_i", 64 * 19), ("&", "elapsed_bins_i", 64 * 24),
        ("'", "membranes_o", 64 * 24), ("(", "spikes_o", 64),
        (")", "ages_o", 64 * 6), ("*", "amplitudes_o", 64 * 19),
        ("+", "shared_penalty_o", 24), (",", "membrane_energy_o", 24),
    ]
    readout_signals = [
        ("!", "clk", 1), ('"', "reset", 1), ("#", "in_valid_i", 1),
        ("$", "in_ready_o", 1), ("%", "in_spike_vector_i", 16),
        ("&", "in_completion_i", 1), ("'", "in_tag_i", 24),
        ("(", "prediction_valid_o", 1), (")", "prediction_ready_i", 1),
        ("*", "prediction_x_o", 1), ("+", "prediction_y_o", 1),
        (",", "prediction_class_o", 3), ("-", "frame_done_valid_o", 1),
        (".", "frame_done_ready_i", 1), ("/", "frame_tag_o", 24),
    ]

    write_case(
        output_root / "stem_inhibition_32_checkpoint_exact",
        "stem_inhibition_32_activity.vcd", "inhibition140k_tb", stem_signals,
        stem_samples, "primitive_140k_stem_inhibition_32_pnr_top",
        {"source_actor": "stem", "inhibition_strength_q7_16": 929} | stem_stats,
    )
    penalty_reduce_signals = [
        ("!", "clk", 1), ('"', "penalties_i", 64 * 24),
        ("#", "shared_penalty_o", 24),
    ]
    decomposed_cases = [
        ("penalty_lane", "down2_adaptation_penalty_lane_checkpoint_exact",
         "down2_adaptation_penalty_lane_activity.vcd",
         "adaptation_penalty_lane_tb",
         "primitive_140k_down2_adaptation_penalty_lane_pnr_top",
         [("!", "clk", 1), ('"', "update_i", 1),
          ("#", "age_i", 6), ("$", "amplitude_i", 19),
          ("%", "elapsed_bins_i", 24), ("&", "adaptation_duration_i", 21),
          ("'", "penalty_o", 24)]),
        ("penalty_reduce64_direct",
         "down2_adaptation_penalty_reduce64_checkpoint_exact",
         "down2_adaptation_penalty_reduce64_activity.vcd",
         "adaptation_penalty_reduce64_direct_tb",
         "primitive_140k_down2_adaptation_penalty_reduce64_pnr_top",
         penalty_reduce_signals),
        ("penalty_reduce64_lower",
         "adaptation_penalty_reduce64_lower_checkpoint_exact",
         "adaptation_penalty_reduce64_lower_activity.vcd",
         "adaptation_penalty_reduce64_lower_tb",
         "primitive_140k_down2_adaptation_penalty_reduce64_pnr_top",
         penalty_reduce_signals),
        ("penalty_reduce64_upper",
         "adaptation_penalty_reduce64_upper_checkpoint_exact",
         "adaptation_penalty_reduce64_upper_activity.vcd",
         "adaptation_penalty_reduce64_upper_tb",
         "primitive_140k_down2_adaptation_penalty_reduce64_pnr_top",
         penalty_reduce_signals),
        ("square_lane", "down2_adaptation_square_lane_checkpoint_exact",
         "down2_adaptation_square_lane_activity.vcd", "adaptation_square_lane_tb",
         "primitive_140k_down2_adaptation_square_lane_pnr_top",
         [("!", "clk", 1), ('"', "candidate_i", 24),
          ("#", "shared_penalty_i", 24), ("$", "square_o", 48)]),
        ("energy_reduce64", "down2_adaptation_energy_reduce64_checkpoint_exact",
         "down2_adaptation_energy_reduce64_activity.vcd",
         "adaptation_energy_reduce64_tb",
         "primitive_140k_down2_adaptation_energy_reduce64_pnr_top",
         [("!", "clk", 1), ('"', "squares_i", 64 * 48),
          ("#", "membrane_energy_o", 24)]),
        ("energy_reduce128", "adaptation_energy_reduce128_checkpoint_exact",
         "adaptation_energy_reduce128_activity.vcd",
         "adaptation_energy_reduce128_tb",
         "primitive_140k_adaptation_energy_reduce128_pnr_top",
         [("!", "clk", 1), ('"', "squares_i", 128 * 48),
          ("#", "membrane_energy_o", 24)]),
        ("commit_lane", "down2_adaptation_commit_lane_checkpoint_exact",
         "down2_adaptation_commit_lane_activity.vcd", "adaptation_commit_lane_tb",
         "primitive_140k_down2_adaptation_commit_lane_pnr_top",
         [("!", "clk", 1), ('"', "candidate_i", 24),
          ("#", "base_threshold_i", 24), ("$", "update_i", 1),
          ("%", "age_i", 6), ("&", "amplitude_i", 19),
          ("'", "elapsed_bins_i", 24), ("(", "shared_penalty_i", 24),
          (")", "membrane_energy_i", 24), ("*", "membrane_o", 24),
          ("+", "spike_o", 1), (",", "age_o", 6), ("-", "amplitude_o", 19),
          (".", "adaptation_strength_i", 19),
          ("/", "adaptation_duration_i", 21)]),
    ]
    for block, directory, vcd_name, scope, design, signals in decomposed_cases:
        write_case(
            output_root / directory,
            vcd_name, scope,
            signals, decomposed[block], design,
            {
                "source_actors": [profile["actor"] for profile in adaptation_profiles],
                "actor_profiles": adaptation_profiles,
                "decomposition_block": block,
                "samples": len(decomposed[block]),
                "activity_scope": "full_model_population_weighted_all_adaptation_actors",
                "spatial_weight_unit_groups": 4_400,
            },
        )
    write_case(
        output_root / "down2_adaptation_64_checkpoint_exact",
        "down2_adaptation_64_activity.vcd", "adaptation140k_tb", down2_signals,
        down2_samples, "primitive_140k_down2_adaptation_64_pnr_top",
        {
            "source_actor": "down2.standard",
            "adaptation_strength_q3_16": 875,
            "adaptation_duration_q5_16": 320026,
        } | down2_stats,
    )
    write_case(
        output_root / "readout_1x1_checkpoint_exact",
        "readout_1x1_activity.vcd", "readout140k_tb", readout_signals,
        readout_trace, "primitive_140k_readout_1x1_pnr_top",
        {"source_actor": "head.synapse", "input_channels": 16, "class_count": 6}
        | readout_stats,
    )
    print(json.dumps({
        "stem": stem_stats,
        "adaptation_actor_profiles": adaptation_profiles,
        "adaptation_trace_samples": {
            key: len(values) for key, values in decomposed.items()
        },
        "down2": down2_stats,
        "readout": readout_stats,
    }, indent=2))


if __name__ == "__main__":
    main()
