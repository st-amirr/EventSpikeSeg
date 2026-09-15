#!/usr/bin/env python3
"""Validate the checkpoint-bound inputs to the XL full-chip physical flow."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


EXPECTED_ACTORS = 44
EXPECTED_TILES = 49_610
EXPECTED_PLIFS = 78_707_200
EXPECTED_STATE_BITS = 2_916_390_400


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_report(export: Path) -> dict[str, object]:
    model = export / "model_spec.yaml"
    top = export / "generated_eventspikesegxl_dag_top.sv"
    plan_path = export / "resident_tile_plan.json"
    summary_path = export / "partitioned_synthesis_1x1" / "summary.tsv"
    for path in (model, top, plan_path, summary_path):
        if not path.is_file():
            raise ValueError(f"required input is missing: {path}")

    model_data = json.loads(model.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    top_text = top.read_text(encoding="utf-8")
    with summary_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))

    actor_order = model_data.get("graph", {}).get("actor_topological_order", [])
    totals = plan.get("totals", {})
    failures = [row for row in rows if row.get("status") != "PASS"]
    checks = {
        "model_architecture": model_data.get("checkpoint", {}).get("architecture")
        == "EventSpikeSegXL",
        "model_actor_count": len(actor_order) == EXPECTED_ACTORS,
        "generated_top_actor_count": top_text.count(
            "streaming_resident_channelized_plif_actor #("
        )
        == EXPECTED_ACTORS,
        "generated_top_tiled_readout": top_text.count(
            "tiled_resident_temporal_class_readout #("
        )
        == 1,
        "tile_plan_actor_count": totals.get("actor_count") == EXPECTED_ACTORS,
        "tile_count": totals.get("tile_count") == EXPECTED_TILES,
        "logical_plifs": totals.get("logical_plifs") == EXPECTED_PLIFS,
        "resident_state_bits": totals.get("resident_state_bits") == EXPECTED_STATE_BITS,
        "model_plan_digest": plan.get("model_spec_sha256") == sha256(model),
        "partition_count": len(rows) == EXPECTED_ACTORS + 1,
        "partition_status": not failures,
    }
    return {
        "schema_version": "1.0.0",
        "stage": "full_structural_elaboration_preflight",
        "ready": all(checks.values()),
        "checks": checks,
        "inventory": {
            "actors": len(actor_order),
            "resident_tiles": totals.get("tile_count"),
            "logical_plifs": totals.get("logical_plifs"),
            "resident_state_bits": totals.get("resident_state_bits"),
            "partition_rows": len(rows),
            "partition_failures": failures,
        },
        "digests": {
            "model_spec_sha256": sha256(model),
            "generated_top_sha256": sha256(top),
            "resident_tile_plan_sha256": sha256(plan_path),
            "partition_summary_sha256": sha256(summary_path),
        },
        "claim_boundary": (
            "This preflight authorizes full structural elaboration only. Full-chip PPA "
            "requires successful complete placement, routing, extracted timing, and "
            "representative-activity power for the native resident graph."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_report(args.export)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(args.output)
    print(text, end="")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
