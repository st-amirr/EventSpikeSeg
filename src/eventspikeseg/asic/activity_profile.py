"""Native DSEC activity profiling for the exported integer actor DAG."""

from __future__ import annotations

import ctypes
import gc
import hashlib
import json
import os
import pickle
import time
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any

import h5py
import hdf5plugin  # noqa: F401 - registers DSEC's HDF5 compression filters
import numpy as np
import torch

from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records

from .activity_trace import build_pointwise_actor_trace, write_actor_trace
from .contracts import BIN_TAG_MODULUS
from .dag_reference import IntegerDAGReference, SpikeEvent

CHECKPOINT_IDENTITY_FIELDS = (
    "architecture",
    "dataset",
    "epoch",
    "seed",
    "temporal_protocol_version",
    "training_strategy_version",
)


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


def _validate_export_checkpoint(
    spec: dict[str, Any], checkpoint: dict[str, Any]
) -> dict[str, Any]:
    exported = spec.get("checkpoint")
    if not isinstance(exported, dict):
        raise ValueError("model specification lacks checkpoint provenance")
    current = {field: checkpoint.get(field) for field in CHECKPOINT_IDENTITY_FIELDS}
    expected = {field: exported.get(field) for field in CHECKPOINT_IDENTITY_FIELDS}
    if current != expected:
        raise ValueError(
            "ASIC export checkpoint provenance does not match the supplied checkpoint: "
            f"exported={expected}, supplied={current}; regenerate artifacts/ASIC"
        )
    return current


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
    checkpoint_identity = _validate_export_checkpoint(spec, checkpoint)
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
    reference = IntegerDAGReference(model_spec, capture_trace=False)
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
    actor_input_events = {name: 0 for name in actor_names}
    actor_synaptic_contributions = {name: 0 for name in actor_names}

    try:
        for record_offset, record in enumerate(records):
            scheduled, _ = dataset._schedule_events(record)
            for clock in range(10):
                events = counted_events(scheduled[clock].numpy())
                input_events_per_bin.append(len(events))
                bin_tag = (record_offset * 10 + clock + 1) % BIN_TAG_MODULUS
                reference.process_bin(events, bin_tag=bin_tag)
                for name in actor_names:
                    activity = reference.last_actor_activity[name]
                    actor_input_events[name] += activity["input_events"]
                    actor_synaptic_contributions[name] += activity[
                        "synaptic_contributions"
                    ]
                    actor_spikes[name] += activity["output_spikes"]
                    touched = activity["touched_entries"]
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
        "checkpoint_identity": checkpoint_identity,
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
        "actor_input_events": actor_input_events,
        "actor_synaptic_contributions": actor_synaptic_contributions,
        "set_conflicts": "not_applicable_to_current_direct_indexed_state_SRAM",
        "cycle_latency_available": False,
        "power_activity_available": False,
        "capacity_claim": complete_sequence,
    }


def _event_file_bins(
    event_path: Path,
    *,
    start_ms: int,
    duration_ms: int,
    rectify_path: Path | None,
) -> tuple[list[list[SpikeEvent]], str]:
    if start_ms < 0 or duration_ms <= 0 or duration_ms % 5:
        raise ValueError("start_ms must be non-negative and duration_ms a positive multiple of 5")
    rectify: np.ndarray | None = None
    if rectify_path is not None:
        with h5py.File(rectify_path, "r") as handle:
            rectify = np.asarray(handle["rectify_map"][()], dtype=np.float32)
        if rectify.ndim != 3 or rectify.shape[2] != 2:
            raise ValueError(f"invalid DSEC rectify map shape: {rectify.shape}")

    result: list[list[SpikeEvent]] = []
    with h5py.File(event_path, "r") as handle:
        milliseconds = handle["ms_to_idx"]
        end_ms = start_ms + duration_ms
        if end_ms >= len(milliseconds):
            raise ValueError(
                f"requested event interval ends at {end_ms} ms, "
                f"but the file index covers only {len(milliseconds) - 1} ms"
            )
        for bin_start_ms in range(start_ms, end_ms, 5):
            start_index = int(milliseconds[bin_start_ms])
            end_index = int(milliseconds[bin_start_ms + 5])
            x = np.asarray(handle["events/x"][start_index:end_index], dtype=np.int64)
            y = np.asarray(handle["events/y"][start_index:end_index], dtype=np.int64)
            polarity = np.asarray(
                handle["events/p"][start_index:end_index], dtype=np.int64
            )
            sensor_valid = (
                (x >= 0)
                & (x < 640)
                & (y >= 0)
                & (y < 480)
                & ((polarity == 0) | (polarity == 1))
            )
            x = x[sensor_valid]
            y = y[sensor_valid]
            polarity = polarity[sensor_valid]
            if rectify is not None:
                xy_rect = rectify[y, x]
                x_native = xy_rect[:, 0]
                y_native = xy_rect[:, 1]
                native_valid = (
                    np.isfinite(x_native)
                    & np.isfinite(y_native)
                    & (x_native >= 0.0)
                    & (x_native < 640.0)
                    & (y_native >= 0.0)
                    & (y_native < 440.0)
                )
                x = np.floor(x_native[native_valid]).astype(np.int64)
                y = np.floor(y_native[native_valid]).astype(np.int64)
                polarity = polarity[native_valid]
            else:
                native_valid = y < 440
                x = x[native_valid]
                y = y[native_valid]
                polarity = polarity[native_valid]
            result.append(
                [
                    SpikeEvent(int(channel), int(event_y), int(event_x))
                    for channel, event_y, event_x in zip(polarity, y, x)
                ]
            )
    preprocessing = (
        "official_rectify_map_then_native_440x640_crop"
        if rectify_path is not None
        else "unrectified_sensor_coordinates_cropped_to_y_0_439_sample_only"
    )
    return result, preprocessing


def profile_native_event_sample(
    *,
    model_spec: Path,
    checkpoint_path: Path,
    event_path: Path,
    start_ms: int = 0,
    duration_ms: int = 50,
    rectify_path: Path | None = None,
    lane_config_path: Path | None = None,
    report_progress: bool = False,
    workers: int = 1,
    resume_checkpoint_path: Path | None = None,
    prediction_output_path: Path | None = None,
    actor_trace_name: str | None = None,
    actor_trace_output_path: Path | None = None,
) -> dict[str, Any]:
    """Run a real-event interval through the full native integer actor DAG."""

    spec = json.loads(model_spec.read_text(encoding="utf-8"))
    if spec.get("input_size") != [440, 640]:
        raise ValueError("native DSEC profiling requires the 440x640 export")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    checkpoint_identity = _validate_export_checkpoint(spec, checkpoint)
    bins, preprocessing = _event_file_bins(
        event_path,
        start_ms=start_ms,
        duration_ms=duration_ms,
        rectify_path=rectify_path,
    )
    lane_document: dict[str, Any] | None = None
    lane_config: dict[str, dict[str, Any]] | None = None
    if lane_config_path is not None:
        lane_document = json.loads(lane_config_path.read_text(encoding="utf-8"))
        lane_config = {
            str(name): dict(values)
            for name, values in dict(lane_document.get("actors", {})).items()
        }
    if (actor_trace_name is None) != (actor_trace_output_path is None):
        raise ValueError("actor trace name and output path must be supplied together")
    reference = IntegerDAGReference(
        model_spec,
        capture_trace=False,
        event_trace_actors=(() if actor_trace_name is None else (actor_trace_name,)),
        lane_config=lane_config,
        workers=workers,
    )
    actor_names: Sequence[str] = reference.graph["actor_topological_order"]
    residual_names = {
        name
        for name, contract in reference.graph["join_nodes"].items()
        if contract["kind"] == "binary_residual_or"
    }
    maximum_live = {name: 0 for name in actor_names}
    maximum_touched = {name: 0 for name in actor_names}
    maximum_residual = {name: 0 for name in sorted(residual_names)}
    actor_spikes = {name: 0 for name in actor_names}
    actor_input_events = {name: 0 for name in actor_names}
    actor_synaptic_contributions = {name: 0 for name in actor_names}
    bank_contributions: dict[str, list[int]] = {}
    maximum_bank_touched: dict[str, list[int]] = {}
    bank_spikes: dict[str, list[int]] = {}
    maximum_isolated_collection_cycles: dict[str, int] = {}
    if lane_config is not None:
        for name in actor_names:
            config = lane_config[name]
            lane_count = int(config["channel_lanes"]) * int(config["spatial_lanes"])
            bank_contributions[name] = [0] * lane_count
            maximum_bank_touched[name] = [0] * lane_count
            bank_spikes[name] = [0] * lane_count
            maximum_isolated_collection_cycles[name] = 0
    host_seconds_per_bin: list[float] = []
    prediction_emitted = False
    final_prediction: np.ndarray | None = None
    actor_event_bins: list[dict[str, list[tuple[int, int, int]]]] = []
    first_bin = 0
    resume_identity = {
        "model_spec_sha256": _sha256(model_spec),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "event_file_sha256": _sha256(event_path),
        "start_ms": int(start_ms),
        "duration_ms": int(duration_ms),
        "rectify_map": str(rectify_path) if rectify_path is not None else None,
        "lane_config": str(lane_config_path) if lane_config_path is not None else None,
        "actor_trace": actor_trace_name,
    }
    if resume_checkpoint_path is not None and resume_checkpoint_path.exists():
        with resume_checkpoint_path.open("rb") as stream:
            saved = pickle.load(stream)
        if saved.get("identity") != resume_identity:
            raise ValueError("native simulation resume checkpoint belongs to another run")
        first_bin = int(saved["completed_bins"])
        if not 0 <= first_bin <= len(bins):
            raise ValueError("native simulation resume checkpoint has invalid bin count")
        reference.states = saved["states"]
        reference.class_scores = saved["class_scores"]
        reference.prediction_bin_count = int(saved["prediction_bin_count"])
        maximum_live = saved["maximum_live"]
        maximum_touched = saved["maximum_touched"]
        maximum_residual = saved["maximum_residual"]
        actor_spikes = saved["actor_spikes"]
        actor_input_events = saved["actor_input_events"]
        actor_synaptic_contributions = saved["actor_synaptic_contributions"]
        bank_contributions = saved["bank_contributions"]
        maximum_bank_touched = saved["maximum_bank_touched"]
        bank_spikes = saved["bank_spikes"]
        maximum_isolated_collection_cycles = saved[
            "maximum_isolated_collection_cycles"
        ]
        host_seconds_per_bin = saved["host_seconds_per_bin"]
        prediction_emitted = bool(saved["prediction_emitted"])
        final_prediction = saved.get("final_prediction")
        actor_event_bins = saved.get("actor_event_bins", [])
        del saved
        gc.collect()
        with suppress(OSError):
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        if report_progress:
            print(
                f"resuming exact native simulation after {first_bin}/{len(bins)} bins",
                flush=True,
            )

    for offset in range(first_bin, len(bins)):
        events = bins[offset]
        started = time.perf_counter()
        last_actor_finished = started

        def actor_progress(
            name: str,
            actor_index: int,
            actor_count: int,
            output_spikes: int,
            bin_number: int = offset + 1,
        ) -> None:
            nonlocal last_actor_finished
            now = time.perf_counter()
            print(
                f"bin {bin_number}/{len(bins)} actor {actor_index}/{actor_count} "
                f"{name}: {output_spikes} output spikes, "
                f"{now - last_actor_finished:.3f} s",
                flush=True,
            )
            last_actor_finished = now

        prediction = reference.process_bin(
            events,
            bin_tag=offset + 1,
            progress_callback=actor_progress if report_progress else None,
        )
        host_seconds_per_bin.append(time.perf_counter() - started)
        prediction_emitted |= prediction is not None
        if actor_trace_name is not None:
            actor_event_bins.append(reference.last_actor_event_trace[actor_trace_name])
        if prediction is not None:
            final_prediction = prediction.classes.copy()
        for name in actor_names:
            activity = reference.last_actor_activity[name]
            actor_input_events[name] += activity["input_events"]
            actor_synaptic_contributions[name] += activity[
                "synaptic_contributions"
            ]
            actor_spikes[name] += activity["output_spikes"]
            maximum_touched[name] = max(
                maximum_touched[name], activity["touched_entries"]
            )
            if lane_config is not None:
                maximum_isolated_collection_cycles[name] = max(
                    maximum_isolated_collection_cycles[name],
                    int(activity["isolated_saturated_collection_cycles"]),
                )
                bank_activity = reference.last_actor_bank_activity[name]
                for lane, count in enumerate(
                    bank_activity["synaptic_contributions"]
                ):
                    bank_contributions[name][lane] += count
                for lane, count in enumerate(bank_activity["touched_entries"]):
                    maximum_bank_touched[name][lane] = max(
                        maximum_bank_touched[name][lane], count
                    )
                for lane, count in enumerate(bank_activity["output_spikes"]):
                    bank_spikes[name][lane] += count
        for name in residual_names:
            maximum_residual[name] = max(
                maximum_residual[name], reference.last_route_event_counts[name]
            )
        for name, count in reference.state_profile().items():
            maximum_live[name] = max(maximum_live[name], count)
        if resume_checkpoint_path is not None:
            saved = {
                "identity": resume_identity,
                "completed_bins": offset + 1,
                "states": reference.states,
                "class_scores": reference.class_scores,
                "prediction_bin_count": reference.prediction_bin_count,
                "maximum_live": maximum_live,
                "maximum_touched": maximum_touched,
                "maximum_residual": maximum_residual,
                "actor_spikes": actor_spikes,
                "actor_input_events": actor_input_events,
                "actor_synaptic_contributions": actor_synaptic_contributions,
                "bank_contributions": bank_contributions,
                "maximum_bank_touched": maximum_bank_touched,
                "bank_spikes": bank_spikes,
                "maximum_isolated_collection_cycles": (
                    maximum_isolated_collection_cycles
                ),
                "host_seconds_per_bin": host_seconds_per_bin,
                "prediction_emitted": prediction_emitted,
                "final_prediction": final_prediction,
                "actor_event_bins": actor_event_bins,
            }
            resume_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = resume_checkpoint_path.with_suffix(
                resume_checkpoint_path.suffix + ".tmp"
            )
            with temporary.open("wb") as stream:
                pickle.dump(saved, stream, protocol=pickle.HIGHEST_PROTOCOL)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, resume_checkpoint_path)
            if report_progress:
                print(
                    f"saved exact state after bin {offset + 1}/{len(bins)}: "
                    f"{resume_checkpoint_path}",
                    flush=True,
                )

    event_counts = np.asarray([len(events) for events in bins], dtype=np.int64)
    result = {
        "schema_version": "1.0.0",
        "scope": (
            f"real_event_interval_full_{len(actor_names)}_actor_"
            "native_440x640_integer_DAG"
        ),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "checkpoint_identity": checkpoint_identity,
        "model_spec_sha256": _sha256(model_spec),
        "event_file_sha256": _sha256(event_path),
        "event_file": str(event_path),
        "start_ms": start_ms,
        "duration_ms": duration_ms,
        "bins_profiled": len(bins),
        "simulation_workers": int(workers),
        "spatial_preprocessing": preprocessing,
        "input_events_per_bin": event_counts.tolist(),
        "input_events": int(event_counts.sum()),
        "maximum_input_events_per_bin": int(event_counts.max(initial=0)),
        "host_seconds_per_bin": host_seconds_per_bin,
        "host_seconds_total": float(sum(host_seconds_per_bin)),
        "prediction_emitted": prediction_emitted,
        "maximum_live_state_entries_by_actor": maximum_live,
        "maximum_touched_queue_entries_by_actor": maximum_touched,
        "maximum_residual_events_by_join": maximum_residual,
        "actor_output_spikes": actor_spikes,
        "actor_input_events": actor_input_events,
        "actor_synaptic_contributions": actor_synaptic_contributions,
        "cycle_latency_available": False,
        "power_activity_available": False,
        "capacity_claim": False,
        "article_limit": (
            "short sample cannot establish full-sequence capacity or publication-grade "
            "activity power"
            if rectify_path is not None
            else "short sample and unrectified coordinates cannot establish full-sequence "
            "capacity or publication-grade activity power"
        ),
    }
    if final_prediction is not None:
        prediction_bytes = final_prediction.tobytes(order="C")
        result["prediction_shape"] = list(final_prediction.shape)
        result["prediction_sha256"] = hashlib.sha256(prediction_bytes).hexdigest()
        values, counts = np.unique(final_prediction, return_counts=True)
        result["prediction_class_histogram"] = {
            str(int(value)): int(count) for value, count in zip(values, counts)
        }
        if prediction_output_path is not None:
            prediction_output_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(prediction_output_path, final_prediction, allow_pickle=False)
            result["prediction_output"] = str(prediction_output_path)
    if lane_config_path is not None:
        result["lane_config_sha256"] = _sha256(lane_config_path)
        result["bank_activity"] = {
            name: {
                "channel_lanes": int(lane_config[name]["channel_lanes"]),
                "spatial_lanes": int(lane_config[name]["spatial_lanes"]),
                "synaptic_contributions": bank_contributions[name],
                "maximum_touched_entries": maximum_bank_touched[name],
                "output_spikes": bank_spikes[name],
            }
            for name in actor_names
        }
        result["maximum_isolated_saturated_collection_cycles_by_actor"] = (
            maximum_isolated_collection_cycles
        )
    if actor_trace_name is not None and actor_trace_output_path is not None:
        trace = build_pointwise_actor_trace(
            actor_name=actor_trace_name,
            layer=reference.layers[actor_trace_name],
            bins=actor_event_bins,
            checkpoint_sha256=result["checkpoint_sha256"],
            model_spec_sha256=result["model_spec_sha256"],
            event_file_sha256=result["event_file_sha256"],
        )
        write_actor_trace(actor_trace_output_path, trace)
        result["actor_event_trace"] = {
            "actor": actor_trace_name,
            "path": str(actor_trace_output_path),
            "trace_payload_sha256": trace["trace_payload_sha256"],
            "scope": trace["scope"],
        }
    return result
