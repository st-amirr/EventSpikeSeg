#!/usr/bin/env python3
"""Capture a checkpoint-exact actor trace while executing only its DAG prefix."""

from __future__ import annotations

import argparse
import json
import os
import pickle
from pathlib import Path
from typing import Any

import torch

from eventspikeseg.asic.activity_profile import (
    _event_file_bins,
    _sha256,
    _validate_export_checkpoint,
)
from eventspikeseg.asic.activity_trace import (
    apply_resident_ordinary_expectations,
    build_actor_trace,
    write_actor_trace,
)
from eventspikeseg.asic.dag_reference import IntegerDAGReference


def _identity(
    model_spec: Path, checkpoint: Path, event_file: Path, actor: str, duration_ms: int
) -> dict[str, Any]:
    return {
        "model_spec_sha256": _sha256(model_spec),
        "checkpoint_sha256": _sha256(checkpoint),
        "event_file_sha256": _sha256(event_file),
        "start_ms": 0,
        "duration_ms": duration_ms,
        "actor": actor,
        "execution": "integer_DAG_prefix_through_selected_actor",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=Path("artifacts/ASIC_XL"))
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--event-file", type=Path, required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--duration-ms", type=int, default=50)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--resume-checkpoint", type=Path)
    parser.add_argument("--trace-output", type=Path, required=True)
    parser.add_argument("--profile-output", type=Path, required=True)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")

    model_spec = args.export / "model_spec.yaml"
    spec = json.loads(model_spec.read_text(encoding="utf-8"))
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    checkpoint_identity = _validate_export_checkpoint(spec, checkpoint)
    del checkpoint
    bins, preprocessing = _event_file_bins(
        args.event_file, start_ms=0, duration_ms=args.duration_ms, rectify_path=None
    )
    identity = _identity(
        model_spec, args.checkpoint, args.event_file, args.actor, args.duration_ms
    )
    reference = IntegerDAGReference(
        model_spec,
        capture_trace=False,
        event_trace_actors=(args.actor,),
        workers=args.workers,
    )
    actor_bins: list[dict[str, list[tuple[int, int, int]]]] = []
    first_bin = 0
    if args.resume_checkpoint is not None and args.resume_checkpoint.exists():
        with args.resume_checkpoint.open("rb") as stream:
            saved = pickle.load(stream)
        if saved.get("identity") != identity:
            raise ValueError("actor-prefix resume checkpoint belongs to another run")
        first_bin = int(saved["completed_bins"])
        actor_bins = saved["actor_event_bins"]
        reference.states = saved["states"]
        print(f"resuming actor-prefix replay after {first_bin}/{len(bins)} bins", flush=True)

    actor_order = [str(name) for name in reference.graph["actor_topological_order"]]
    for offset in range(first_bin, len(bins)):
        def progress(
            name: str,
            index: int,
            count: int,
            outputs: int,
            bin_number: int = offset + 1,
        ) -> None:
            print(
                f"bin {bin_number}/{len(bins)} actor {index}/{count} "
                f"{name}: {outputs} output spikes",
                flush=True,
            )

        reference.process_bin(
            bins[offset],
            bin_tag=offset + 1,
            progress_callback=progress,
            stop_after_actor=args.actor,
        )
        actor_bins.append(reference.last_actor_event_trace[args.actor])
        if args.resume_checkpoint is not None:
            saved = {
                "identity": identity,
                "completed_bins": offset + 1,
                "states": reference.states,
                "actor_event_bins": actor_bins,
            }
            args.resume_checkpoint.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.resume_checkpoint.with_suffix(
                args.resume_checkpoint.suffix + ".tmp"
            )
            with temporary.open("wb") as stream:
                pickle.dump(saved, stream, protocol=pickle.HIGHEST_PROTOCOL)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, args.resume_checkpoint)

    layer = reference.layers[args.actor]
    trace = build_actor_trace(
        actor_name=args.actor,
        layer=layer,
        bins=actor_bins,
        checkpoint_sha256=identity["checkpoint_sha256"],
        model_spec_sha256=identity["model_spec_sha256"],
        event_file_sha256=identity["event_file_sha256"],
    )
    parameters = reference.parameters[args.actor]
    if not parameters.get("inhibition_enabled") and not parameters.get(
        "threshold_adaptation_enabled"
    ):
        apply_resident_ordinary_expectations(
            trace,
            layer=layer,
            weights=reference.weights[args.actor],
            parameters=parameters,
        )
    write_actor_trace(args.trace_output, trace)
    profile = {
        "schema_version": "1.0.0",
        "scope": "real_event_interval_integer_DAG_prefix_actor_trace",
        **identity,
        "checkpoint_identity": checkpoint_identity,
        "bins_profiled": len(bins),
        "bin_duration_ms": 5,
        "preprocessing": preprocessing,
        "simulation_workers": args.workers,
        "actors_executed_per_bin": len(reference.last_actor_activity),
        "total_actor_count": len(actor_order),
        "trace_output": str(args.trace_output),
        "trace_payload_sha256": trace["trace_payload_sha256"],
    }
    args.profile_output.parent.mkdir(parents=True, exist_ok=True)
    args.profile_output.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(profile, indent=2), flush=True)


if __name__ == "__main__":
    main()
