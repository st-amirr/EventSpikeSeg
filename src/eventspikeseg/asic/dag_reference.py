"""Sparse bit-exact integer oracle for the exported EventSpikeSeg140k ASIC DAG.

The oracle executes one completed 5 ms bin at a time.  It is intentionally an
event graph rather than a dense PyTorch model: convolution is presynaptic
scatter, joins use the exported routing contract, and persistent PLIF state is
owned by each actor.  Its arithmetic mirrors the synthesizable SystemVerilog.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .contracts import BIN_TAG_MODULUS
from .fixed_point import ASIC_FORMATS, round_shift_ties_away
from .integer_reference import IntegerPLIF, NeuronState


@dataclass(frozen=True, order=True)
class SpikeEvent:
    """One packed-stream data event, without its completion token."""

    channel: int
    y: int
    x: int


@dataclass(frozen=True)
class Prediction:
    """One dense semantic output emitted at a prediction-window boundary."""

    bin_tag: int
    classes: np.ndarray


def _sat(value: int, bits: int) -> int:
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    return min(max(int(value), minimum), maximum)


def _scalar(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, list):
        return int(value[0]) if value else 0
    return int(value)


class IntegerDAGReference:
    """Execute an exported model specification using RTL-equivalent integers."""

    def __init__(self, model_spec: str | Path) -> None:
        self.model_spec_path = Path(model_spec)
        self.export_dir = self.model_spec_path.parent
        self.spec = json.loads(self.model_spec_path.read_text(encoding="utf-8"))
        self.graph = self.spec["graph"]
        if self.graph.get("actor_count") != 25 or self.graph.get("linear_pipeline") is not False:
            raise ValueError("integer DAG reference requires the exact 25-actor graph")
        self.layers = {str(layer["name"]): layer for layer in self.spec["layers"]}
        self.actors = set(self.graph["actor_topological_order"])
        self.node_kinds = {
            str(node["name"]): str(node["kind"]) for node in self.graph["nodes"]
        }
        self.incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in self.graph["edges"]:
            self.incoming[str(edge["destination"])].append(dict(edge))

        archive = np.load(self.export_dir / "quantized_weights.npz", allow_pickle=False)
        self.weights = {name: archive[name].astype(np.int64) for name in archive.files}
        self.parameters: dict[str, dict[str, Any]] = {}
        for name in self.actors:
            layer = self.layers[name]
            self.parameters[name] = json.loads(
                (self.export_dir / str(layer["parameter_file"])).read_text(
                    encoding="utf-8"
                )
            )

        self.states: dict[str, dict[SpikeEvent, NeuronState]] = {
            name: {} for name in self.actors
        }
        self.class_scores: dict[tuple[int, int], list[int]] = {}
        self.prediction_bin_count = 0
        self.prediction_bins = int(
            self.spec["timing_contract"]["prediction_bins_default"]
        )
        self.plif = IntegerPLIF()
        self.last_trace: dict[str, dict[str, list[tuple[int, ...]]]] = {}

    def reset(self) -> None:
        """Clear sequence state, including the temporal class-current window."""

        for state in self.states.values():
            state.clear()
        self.class_scores.clear()
        self.prediction_bin_count = 0
        self.last_trace = {}

    @staticmethod
    def _edge_events(
        edge: dict[str, Any], streams: dict[str, list[SpikeEvent]]
    ) -> list[SpikeEvent]:
        events = streams[str(edge["source"])]
        offset = int(edge.get("channel_offset", 0))
        if offset:
            return [SpikeEvent(event.channel + offset, event.y, event.x) for event in events]
        return list(events)

    def _route_node(
        self, name: str, streams: dict[str, list[SpikeEvent]]
    ) -> list[SpikeEvent]:
        inputs = [self._edge_events(edge, streams) for edge in self.incoming[name]]
        kind = self.node_kinds[name]
        if kind == "nearest_event_fanout_2x":
            result: list[SpikeEvent] = []
            for event in inputs[0]:
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    result.append(
                        SpikeEvent(event.channel, event.y * 2 + dy, event.x * 2 + dx)
                    )
            return result
        if kind == "binary_residual_or":
            # RTL input 0 has arbitration priority. Dict insertion retains that order.
            return list(dict.fromkeys(event for group in inputs for event in group))
        if kind in {"channel_concat", "multiplicity_preserving_sum"}:
            return [event for group in inputs for event in group]
        raise ValueError(f"unsupported integer-reference route node {name!r}: {kind}")

    def _scatter(
        self, name: str, events: list[SpikeEvent]
    ) -> tuple[dict[SpikeEvent, int], list[tuple[int, ...]]]:
        layer = self.layers[name]
        weights = self.weights[name]
        input_channels = int(layer["in_channels"])
        output_channels = int(layer["out_channels"])
        groups = int(layer["groups"])
        input_h, input_w = (int(v) for v in layer["input_hw"])
        output_h, output_w = (int(v) for v in layer["output_hw"])
        kernel_h, kernel_w = (int(v) for v in layer["kernel"])
        stride_y, stride_x = (int(v) for v in layer["stride"])
        pad_y, pad_x = (int(v) for v in layer["padding"])
        dilation_y, dilation_x = (int(v) for v in layer["dilation"])
        inputs_per_group = input_channels // groups
        outputs_per_group = output_channels // groups
        current_min = ASIC_FORMATS["current"].minimum
        current_max = ASIC_FORMATS["current"].maximum
        currents: dict[SpikeEvent, int] = {}
        contributions: list[tuple[int, ...]] = []

        for event in events:
            if not (0 <= event.channel < input_channels):
                raise ValueError(f"{name}: input channel out of range: {event}")
            if not (0 <= event.x < input_w and 0 <= event.y < input_h):
                raise ValueError(f"{name}: input coordinate out of range: {event}")
            group = event.channel // inputs_per_group
            input_local = event.channel % inputs_per_group
            first_output = group * outputs_per_group
            for output_channel in range(first_output, first_output + outputs_per_group):
                for kernel_y in range(kernel_h):
                    numerator_y = event.y + pad_y - kernel_y * dilation_y
                    if numerator_y < 0 or numerator_y % stride_y:
                        continue
                    output_y = numerator_y // stride_y
                    if output_y >= output_h:
                        continue
                    for kernel_x in range(kernel_w):
                        numerator_x = event.x + pad_x - kernel_x * dilation_x
                        if numerator_x < 0 or numerator_x % stride_x:
                            continue
                        output_x = numerator_x // stride_x
                        if output_x >= output_w:
                            continue
                        weight = int(
                            weights[output_channel, input_local, kernel_y, kernel_x]
                        )
                        if weight == 0:
                            continue
                        destination = SpikeEvent(output_channel, output_y, output_x)
                        updated = min(
                            max(currents.get(destination, 0) + weight, current_min),
                            current_max,
                        )
                        currents[destination] = updated
                        contributions.append(
                            (
                                event.channel,
                                event.y,
                                event.x,
                                output_channel,
                                output_y,
                                output_x,
                                weight,
                            )
                        )
        return currents, contributions

    def _ordinary_commit(
        self, name: str, bin_tag: int, currents: dict[SpikeEvent, int]
    ) -> tuple[list[SpikeEvent], list[tuple[int, ...]]]:
        parameters = self.parameters[name]
        betas = [int(value) for value in parameters["beta_q"]]
        thresholds = [int(value) for value in parameters["threshold_q"]]
        states = self.states[name]
        spikes: list[SpikeEvent] = []
        membranes: list[tuple[int, ...]] = []
        for destination, current in currents.items():
            previous = states.get(destination, NeuronState())
            updated, result = self.plif.touch_state(
                previous,
                current_bin_tag=bin_tag,
                current_q=current,
                beta_q=betas[destination.channel],
                threshold_q=thresholds[destination.channel],
            )
            if updated.membrane == 0:
                states.pop(destination, None)
            else:
                states[destination] = updated
            membranes.append(
                (
                    destination.channel,
                    destination.y,
                    destination.x,
                    result.candidate,
                    result.membrane,
                    result.spike,
                )
            )
            if result.spike:
                spikes.append(destination)
        return spikes, membranes

    def _mechanism_commit(
        self, name: str, bin_tag: int, currents: dict[SpikeEvent, int]
    ) -> tuple[list[SpikeEvent], list[tuple[int, ...]]]:
        layer = self.layers[name]
        parameters = self.parameters[name]
        channels = int(layer["out_channels"])
        betas = [int(value) for value in parameters["beta_q"]]
        thresholds = [int(value) for value in parameters["threshold_q"]]
        inhibition = bool(parameters.get("inhibition_enabled", False))
        adaptation = bool(parameters.get("threshold_adaptation_enabled", False))
        inhibition_strength = _scalar(parameters.get("inhibition_strength_q"))
        adaptation_strength = _scalar(parameters.get("threshold_adaptation_strength_q"))
        adaptation_duration = _scalar(parameters.get("adaptation_duration_q"))
        states = self.states[name]
        touched_by_spatial: dict[tuple[int, int], set[int]] = defaultdict(set)
        for destination in currents:
            touched_by_spatial[(destination.y, destination.x)].add(destination.channel)

        spikes: list[SpikeEvent] = []
        membranes: list[tuple[int, ...]] = []
        for (y, x), touched_channels in touched_by_spatial.items():
            update_channels = set(range(channels)) if inhibition else touched_channels
            previous = [states.get(SpikeEvent(channel, y, x), NeuronState()) for channel in range(channels)]
            elapsed = [
                self.plif.elapsed_bins(bin_tag, state.last_bin_tag)
                if channel in update_channels
                else 0
                for channel, state in enumerate(previous)
            ]
            candidates: list[int] = []
            for channel, state in enumerate(previous):
                if channel not in update_channels:
                    candidates.append(state.membrane)
                    continue
                retention = self.plif.retention_for_bins(betas[channel], elapsed[channel])
                leaked = round_shift_ties_away(
                    state.membrane * retention,
                    ASIC_FORMATS["beta"].fractional_bits,
                )
                current = currents.get(SpikeEvent(channel, y, x), 0)
                candidates.append(ASIC_FORMATS["membrane"].saturate(leaked + current))

            penalty_sum = 0
            for channel, state in enumerate(previous):
                effective_age = state.adaptation_age
                if effective_age >= 0 and channel in update_channels:
                    effective_age += elapsed[channel] << 10
                phase = 0
                if adaptation and state.adaptation_age >= 0 and adaptation_duration:
                    if effective_age <= adaptation_duration:
                        phase = effective_age
                    elif effective_age < 2 * adaptation_duration:
                        phase = 2 * adaptation_duration - effective_age
                if adaptation_duration:
                    penalty_sum += state.adaptation_amplitude * phase // adaptation_duration
            shared_penalty = min(penalty_sum, 0xFFFF) & 0x7FFF
            adjusted = [candidate - shared_penalty for candidate in candidates]
            energy = math.isqrt(sum(abs(value) ** 2 for value in adjusted) // channels)
            energy = min(energy, 0xFFFF)

            output_membranes = list(candidates)
            channel_spikes = [False] * channels
            new_ages = [state.adaptation_age for state in previous]
            new_amplitudes = [state.adaptation_amplitude for state in previous]
            for channel in range(channels):
                threshold = _sat(thresholds[channel] + shared_penalty, 16)
                if channel in update_channels and candidates[channel] >= threshold:
                    channel_spikes[channel] = True
                    output_membranes[channel] = _sat(candidates[channel] - threshold, 16)
                if adaptation and channel in update_channels:
                    effective_age = previous[channel].adaptation_age + (elapsed[channel] << 10)
                    if channel_spikes[channel]:
                        new_ages[channel] = 0
                        new_amplitudes[channel] = min(
                            (energy * adaptation_strength + 512) >> 10, 0xFFFF
                        )
                    elif previous[channel].adaptation_age >= 0:
                        if effective_age >= 2 * adaptation_duration:
                            new_ages[channel] = -1
                            new_amplitudes[channel] = 0
                        else:
                            new_ages[channel] = effective_age & 0xFFFF

            if inhibition and any(channel_spikes):
                decrement = (energy * inhibition_strength + 512) >> 10
                for channel in range(channels):
                    if not channel_spikes[channel]:
                        output_membranes[channel] = _sat(
                            output_membranes[channel] - decrement, 16
                        )

            for channel in update_channels:
                destination = SpikeEvent(channel, y, x)
                state = NeuronState(
                    membrane=output_membranes[channel],
                    adaptation_age=new_ages[channel],
                    adaptation_amplitude=new_amplitudes[channel],
                    last_bin_tag=bin_tag % BIN_TAG_MODULUS,
                )
                if state.membrane == 0 and not state.adaptation_active:
                    states.pop(destination, None)
                else:
                    states[destination] = state
                membranes.append(
                    (
                        channel,
                        y,
                        x,
                        candidates[channel],
                        output_membranes[channel],
                        int(channel_spikes[channel]),
                    )
                )
                if channel_spikes[channel]:
                    spikes.append(destination)
        return spikes, membranes

    def _actor(
        self, name: str, bin_tag: int, events: list[SpikeEvent]
    ) -> list[SpikeEvent]:
        currents, contributions = self._scatter(name, events)
        parameters = self.parameters[name]
        mechanism = bool(parameters.get("inhibition_enabled", False)) or bool(
            parameters.get("threshold_adaptation_enabled", False)
        )
        if mechanism:
            spikes, membranes = self._mechanism_commit(name, bin_tag, currents)
        else:
            spikes, membranes = self._ordinary_commit(name, bin_tag, currents)
        self.last_trace[name] = {
            "contributions": contributions,
            "currents": [
                (event.channel, event.y, event.x, current)
                for event, current in currents.items()
            ],
            "membranes": membranes,
            "spikes": [(event.channel, event.y, event.x) for event in spikes],
        }
        return spikes

    def _readout(self, events: list[SpikeEvent], bin_tag: int) -> Prediction | None:
        layer = self.layers[str(self.graph["current_readout"])]
        weights = self.weights[str(self.graph["current_readout"])]
        class_count = int(layer["out_channels"])
        output_h, output_w = (int(value) for value in layer["output_hw"])
        for event in events:
            scores = self.class_scores.setdefault((event.y, event.x), [0] * class_count)
            for class_index in range(class_count):
                scores[class_index] = _sat(
                    scores[class_index] + int(weights[class_index, event.channel, 0, 0]),
                    24,
                )
        self.prediction_bin_count += 1
        if self.prediction_bin_count < self.prediction_bins:
            return None
        classes = np.zeros((output_h, output_w), dtype=np.uint8)
        for (y, x), scores in self.class_scores.items():
            classes[y, x] = int(np.argmax(np.asarray(scores, dtype=np.int64)))
        self.class_scores.clear()
        self.prediction_bin_count = 0
        return Prediction(bin_tag=bin_tag, classes=classes)

    def process_bin(
        self, events: list[SpikeEvent], *, bin_tag: int
    ) -> Prediction | None:
        """Process data events followed by one same-tag completion token."""

        if not 0 <= int(bin_tag) < BIN_TAG_MODULUS:
            raise ValueError("bin_tag must fit the exported 24-bit contract")
        input_h, input_w = (int(value) for value in self.spec["input_size"])
        input_channels = int(self.spec["input_channels"])
        for event in events:
            if not (
                0 <= event.channel < input_channels
                and 0 <= event.y < input_h
                and 0 <= event.x < input_w
            ):
                raise ValueError(f"input event is outside the exported geometry: {event}")

        streams: dict[str, list[SpikeEvent]] = {"input": list(events)}
        self.last_trace = {}
        readout_name = str(self.graph["current_readout"])
        for name in self.graph["node_topological_order"]:
            if name in {"input", "prediction"}:
                continue
            if name in self.actors:
                incoming = self.incoming[name]
                if len(incoming) != 1:
                    raise ValueError(f"actor {name} does not have exactly one input")
                actor_events = self._edge_events(incoming[0], streams)
                streams[name] = self._actor(name, int(bin_tag), actor_events)
            elif name == readout_name:
                incoming = self.incoming[name]
                readout_events = self._edge_events(incoming[0], streams)
                streams[name] = readout_events
            else:
                streams[name] = self._route_node(name, streams)
        return self._readout(streams[readout_name], int(bin_tag))

    def state_profile(self) -> dict[str, int]:
        """Return live sparse entries per actor for capacity profiling."""

        return {name: len(states) for name, states in self.states.items()}
