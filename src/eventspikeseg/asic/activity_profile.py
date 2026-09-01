"""Native DSEC activity profiling for the exported integer actor DAG."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch

from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records

from .contracts import BIN_TAG_MODULUS
from .dag_reference import IntegerDAGReference, SpikeEvent


def counted_events(counts: np.ndarray) -> list[SpikeEvent]:
    """Expand one integer [2,H,W] count plane without losing multiplicity."""

    if counts.ndim != 3 or counts.shape[0] != 2:
        raise ValueError("DSEC bin counts must have shape [2,H,W]")
    if np.any(counts < 0) or np.any(counts != np.floor(counts)):
        raise ValueError("DSEC event counts must be non-negative integers")
    events: list[SpikeEvent] = []
    for channel, y, x in np.argwhere(counts > 0):
        events.extend(
            [SpikeEvent(int(channel), int(y), int(x))]
            * int(counts[channel, y, x])
        )
    return events


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _checkpoint_records(checkpoint: dict[str, Any]) -> tuple[str, set[tuple[str, int]]]:
    protocol = checkpoint.get("temporal_protocol")
    if not isinstance(protocol, dict):
        raise ValueError("checkpoint lacks its temporal protocol")
    sequences = protocol.get("validation_sequences")
    record_ids = protocol.get("validation_record_ids")
    if not isinstance(sequences, list) or len(sequences) != 1:
        raise ValueError("native profile requires one complete validation sequence")
    if not isinstance(record_ids, list) or not record_ids:
        raise ValueError("checkpoint lacks validation record membership")
    return str(sequences[0]), {(str(name), int(index)) for name, index in record_ids}


def profile_native_dsec(
    *,
    model_spec: Path,
    checkpoint_path: Path,
    dataset_root: Path,
    maximum_records: int = 0,
) -> dict[str, Any]:
    """Profile the checkpoint's held-out sequence through the native integer DAG."""

    spec = json.loads(model_spec.read_text(encoding="utf-8"))
    if spec.get("input_size") != [440, 640]:
        raise ValueError("native DSEC profiling requires the 440x640 export")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    sequence, required_ids = _checkpoint_records(checkpoint)
    discovered = discover_dsec_records(dataset_root, "train")
    records = [
        record
        for record in discovered
        if (record.sequence_id, record.frame_index) in required_ids
    ]
    found_ids = {(record.sequence_id, record.frame_index) for record in records}
    if found_ids != required_ids:
        missing = sorted(required_ids - found_ids)
        raise ValueError(f"dataset is missing {len(missing)} checkpoint validation records")
    records.sort(key=lambda record: record.frame_index)
    complete_sequence = maximum_records <= 0
    if maximum_records > 0:
        records = records[:maximum_records]

    dataset = DSECRawEventDataset(
        dataset_root,
        split="train",
        output_size=(440, 640),
        internal_updates=10,
        class_count=6,
        records=records,
    )
    reference = IntegerDAGReference(model_spec)
    actor_names: Sequence[str] = reference.graph["actor_topological_order"]
    residual_names = {
        name
        for name, contract in reference.graph["join_nodes"].items()
        if contract["kind"] == "binary_residual_or"
    }
    maximum_live = {name: 0 for name in actor_names}
    maximum_touched = {name: 0 for name in actor_names}
    maximum_residual = {name: 0 for name in sorted(residual_names)}
    input_events_per_bin: list[int] = []
    actor_spikes = {name: 0 for name in actor_names}

    try:
        for record_offset, record in enumerate(records):
            scheduled, _ = dataset._schedule_events(record)
            for clock in range(10):
                events = counted_events(scheduled[clock].numpy())
                input_events_per_bin.append(len(events))
                bin_tag = (record_offset * 10 + clock + 1) % BIN_TAG_MODULUS
                reference.process_bin(events, bin_tag=bin_tag)
                for name in actor_names:
                    trace = reference.last_trace[name]
                    actor_spikes[name] += len(trace["spikes"])
                    parameters = reference.parameters[name]
                    mechanism = bool(parameters["inhibition_enabled"]) or bool(
                        parameters["threshold_adaptation_enabled"]
                    )
                    touched = (
                        len({(y, x) for _channel, y, x, _current in trace["currents"]})
                        if mechanism
                        else len(trace["currents"])
                    )
                    maximum_touched[name] = max(maximum_touched[name], touched)
                for name in residual_names:
                    maximum_residual[name] = max(
                        maximum_residual[name], reference.last_route_event_counts[name]
                    )
                for name, count in reference.state_profile().items():
                    maximum_live[name] = max(maximum_live[name], count)
    finally:
        dataset.close()

    event_array = np.asarray(input_events_per_bin, dtype=np.int64)
    return {
        "schema_version": "1.0.0",
        "scope": (
            "complete_checkpoint_validation_sequence_native_integer_activity"
            if complete_sequence
            else "partial_checkpoint_validation_sequence_native_integer_activity"
        ),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "model_spec_sha256": _sha256(model_spec),
        "sequence": sequence,
        "records_profiled": len(records),
        "complete_checkpoint_sequence": complete_sequence,
        "bins_profiled": len(input_events_per_bin),
        "input_events": int(event_array.sum()),
        "maximum_input_events_per_bin": int(event_array.max(initial=0)),
        "p99_input_events_per_bin": float(np.percentile(event_array, 99)),
        "maximum_live_state_entries_by_actor": maximum_live,
        "maximum_touched_queue_entries_by_actor": maximum_touched,
        "maximum_residual_events_by_join": maximum_residual,
        "actor_output_spikes": actor_spikes,
        "set_conflicts": "not_applicable_to_current_direct_indexed_state_SRAM",
        "cycle_latency_available": False,
        "power_activity_available": False,
        "capacity_claim": complete_sequence,
    }
