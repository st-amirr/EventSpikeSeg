#!/usr/bin/env python3
"""Create deterministic epoch-provenanced reduced-geometry ASIC golden replay data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from generate_asic_top import generate_top

from eventspikeseg.asic.dag_reference import IntegerDAGReference, SpikeEvent

REPLAY_SHAPES = {
    (440, 640): [8, 8],
    (220, 320): [4, 4],
    (110, 160): [2, 2],
    (55, 80): [1, 1],
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _scaled_spec(source: Path, destination: Path) -> dict[str, object]:
    spec = json.loads(source.read_text(encoding="utf-8"))
    source_export = source.parent
    spec["artifact_root"] = os.path.relpath(
        source_export.resolve(), destination.resolve()
    )
    spec["input_size"] = REPLAY_SHAPES[tuple(spec["input_size"])]
    spec["spatial_shapes"] = {
        tier: REPLAY_SHAPES[tuple(shape)] for tier, shape in spec["spatial_shapes"].items()
    }
    logical_states = 0
    adaptation_states = 0
    for layer in spec["layers"]:
        layer["input_hw"] = REPLAY_SHAPES[tuple(layer["input_hw"])]
        layer["output_hw"] = REPLAY_SHAPES[tuple(layer["output_hw"])]
        states = int(layer["out_channels"]) * int(layer["output_hw"][0]) * int(
            layer["output_hw"][1]
        )
        layer["logical_membrane_states"] = 0 if layer["name"] == "head.synapse" else states
        logical_states += int(layer["logical_membrane_states"])
        parameter_file = layer.get("parameter_file")
        if parameter_file:
            parameters = json.loads(
                (source_export / parameter_file).read_text(encoding="utf-8")
            )
            if parameters["threshold_adaptation_enabled"]:
                adaptation_states += int(layer["logical_membrane_states"])

    spec["logical_membrane_states"] = logical_states
    spec["base_skeleton_membrane_states"] = 0
    spec["canonical_addition_membrane_states"] = 0
    state_capacity = spec["state_capacity"]
    state_capacity.update(
        {
            "logical_membranes": logical_states,
            "adaptation_enabled_neurons": adaptation_states,
            "membrane_bytes_int16": logical_states * 2,
            "last_bin_tag_bytes_24": logical_states * 3,
            "adaptation_bytes_two_int16": adaptation_states * 4,
            "dense_exact_state_bytes": logical_states * 5 + adaptation_states * 4,
            "dense_exact_state_mib": (logical_states * 5 + adaptation_states * 4) / 2**20,
        }
    )
    spec["replay_geometry"] = {
        "purpose": "tractable_bit_exact_RTL_equivalence_not_native_resolution_PPA",
        "native_input_hw": [440, 640],
        "replay_input_hw": [8, 8],
        "weights_and_neuron_parameters": "unchanged_from_source_export",
    }
    return spec


def _input_events(count: int) -> list[tuple[int, SpikeEvent]]:
    if count <= 0:
        raise ValueError("input event count must be positive")
    rng = np.random.default_rng(17)
    result: list[tuple[int, SpikeEvent]] = []
    for index in range(count):
        bin_tag = 1 + (index * 10 // count)
        result.append(
            (
                bin_tag,
                SpikeEvent(
                    channel=int(rng.integers(0, 2)),
                    y=int(rng.integers(0, 8)),
                    x=int(rng.integers(0, 8)),
                ),
            )
        )
    return result


def prepare_replay(
    source_export: Path, output: Path, *, input_event_count: int = 160
) -> dict[str, object]:
    """Prepare one deterministic ten-bin replay from the active export."""

    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing replay directory: {output}")
    output.mkdir(parents=True)

    source_spec = source_export / "model_spec.yaml"
    replay_spec = output / "model_spec.yaml"
    replay_spec.write_text(
        json.dumps(_scaled_spec(source_spec, output), indent=2) + "\n", encoding="utf-8"
    )
    generate_top(
        replay_spec,
        output / "eventspikeseg140k_replay_top.sv",
        module_name="eventspikeseg140k_replay_top",
        architecture="legacy_sram",
    )

    reference = IntegerDAGReference(replay_spec)
    indexed_actors = list(reference.graph["actor_topological_order"])
    actor_ids = {name: index for index, name in enumerate(indexed_actors)}
    events = _input_events(input_event_count)
    input_rows = np.asarray(
        [(tag, event.channel, event.y, event.x) for tag, event in events], dtype=np.int64
    )
    current_rows: list[tuple[int, ...]] = []
    membrane_rows: list[tuple[int, ...]] = []
    spike_rows: list[tuple[int, ...]] = []
    prediction_tags: list[int] = []
    predictions: list[np.ndarray] = []
    maximum_live_by_actor = {name: 0 for name in indexed_actors}
    maximum_touched_queue_by_actor = {name: 0 for name in indexed_actors}
    residual_joins = {
        name
        for name, contract in reference.graph["join_nodes"].items()
        if contract["kind"] == "binary_residual_or"
    }
    maximum_residual_events_by_join = {name: 0 for name in sorted(residual_joins)}

    for bin_tag in range(1, 11):
        bin_events = [event for tag, event in events if tag == bin_tag]
        prediction = reference.process_bin(bin_events, bin_tag=bin_tag)
        for name in indexed_actors:
            actor_id = actor_ids[name]
            trace = reference.last_trace[name]
            current_rows.extend(
                (bin_tag, actor_id, channel, y, x, current)
                for channel, y, x, current in trace["currents"]
            )
            membrane_rows.extend(
                (
                    bin_tag,
                    actor_id,
                    channel,
                    y,
                    x,
                    candidate,
                    membrane,
                    spike,
                    adaptation_age,
                    adaptation_amplitude,
                )
                for (
                    channel,
                    y,
                    x,
                    candidate,
                    membrane,
                    spike,
                    adaptation_age,
                    adaptation_amplitude,
                ) in trace["membranes"]
            )
            spike_rows.extend(
                (bin_tag, actor_id, channel, y, x)
                for channel, y, x in trace["spikes"]
            )
            parameters = reference.parameters[name]
            retinotopic_queue = bool(parameters["inhibition_enabled"]) or bool(
                parameters["threshold_adaptation_enabled"]
            )
            if retinotopic_queue:
                touched_queue_entries = len(
                    {(y, x) for _channel, y, x, _current in trace["currents"]}
                )
            else:
                touched_queue_entries = len(trace["currents"])
            maximum_touched_queue_by_actor[name] = max(
                maximum_touched_queue_by_actor[name], touched_queue_entries
            )
        for name in residual_joins:
            maximum_residual_events_by_join[name] = max(
                maximum_residual_events_by_join[name],
                reference.last_route_event_counts[name],
            )
        for name, count in reference.state_profile().items():
            maximum_live_by_actor[name] = max(maximum_live_by_actor[name], count)
        if prediction is not None:
            prediction_tags.append(prediction.bin_tag)
            predictions.append(prediction.classes)

    actor_names = np.asarray(indexed_actors)
    np.savez(
        output / "golden_input_samples.npz",
        events=input_rows,
        columns=np.asarray(["bin_tag", "channel", "y", "x"]),
    )
    np.savez(
        output / "golden_layer_currents.npz",
        currents=np.asarray(current_rows, dtype=np.int64).reshape(-1, 6),
        columns=np.asarray(["bin_tag", "actor_id", "channel", "y", "x", "current_q"]),
        actor_names=actor_names,
    )
    np.savez(
        output / "golden_layer_membranes.npz",
        membranes=np.asarray(membrane_rows, dtype=np.int64).reshape(-1, 10),
        columns=np.asarray(
            [
                "bin_tag",
                "actor_id",
                "channel",
                "y",
                "x",
                "candidate_q",
                "membrane_q",
                "spike",
                "adaptation_age_q",
                "adaptation_amplitude_q",
            ]
        ),
        actor_names=actor_names,
    )
    np.savez(
        output / "golden_layer_spikes.npz",
        spikes=np.asarray(spike_rows, dtype=np.int64).reshape(-1, 5),
        columns=np.asarray(["bin_tag", "actor_id", "channel", "y", "x"]),
        actor_names=actor_names,
    )
    np.savez(
        output / "golden_semantic_outputs.npz",
        bin_tags=np.asarray(prediction_tags, dtype=np.uint32),
        classes=np.asarray(predictions, dtype=np.uint8),
    )

    artifacts = {
        name: _sha256(output / name)
        for name in (
            "model_spec.yaml",
            "eventspikeseg140k_replay_top.sv",
            "golden_input_samples.npz",
            "golden_layer_currents.npz",
            "golden_layer_membranes.npz",
            "golden_layer_spikes.npz",
            "golden_semantic_outputs.npz",
        )
    }
    profile: dict[str, object] = {
        "source_model_spec_sha256": _sha256(source_spec),
        "checkpoint": json.loads(source_spec.read_text(encoding="utf-8"))["checkpoint"],
        "bins": 10,
        "input_events": len(input_rows),
        "current_rows": len(current_rows),
        "membrane_rows": len(membrane_rows),
        "spike_rows": len(spike_rows),
        "predictions": len(predictions),
        "logical_membrane_states": json.loads(replay_spec.read_text(encoding="utf-8"))[
            "logical_membrane_states"
        ],
        "final_live_state_entries": sum(reference.state_profile().values()),
        "maximum_live_state_entries_by_actor": maximum_live_by_actor,
        "maximum_touched_queue_entries_by_actor": maximum_touched_queue_by_actor,
        "maximum_residual_events_by_join": maximum_residual_events_by_join,
        "fixture_observed_maximum_touched_queue_entries": max(
            maximum_touched_queue_by_actor.values()
        ),
        "fixture_observed_maximum_residual_events": max(
            maximum_residual_events_by_join.values()
        ),
        "occupancy_scope": "observed_reduced_fixture_only_not_a_safe_native_capacity_bound",
        "artifact_sha256": artifacts,
        "scope": "reduced_8x8_bit_exact_equivalence_not_native_resolution_PPA",
    }
    (output / "replay_profile.json").write_text(
        json.dumps(profile, indent=2) + "\n", encoding="utf-8"
    )
    return profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--input-events", type=int, default=160)
    args = parser.parse_args()
    profile = prepare_replay(
        args.export, args.output, input_event_count=args.input_events
    )
    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
