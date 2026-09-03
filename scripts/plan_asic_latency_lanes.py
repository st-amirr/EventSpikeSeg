#!/usr/bin/env python3
"""Propose extra spatial banks for the completion-token latency target.

The planner is intentionally not a result generator.  It extrapolates existing
per-bank commit imbalance, writes a candidate manifest, and requires an exact
native reprofile before the candidate can be accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan_latency_lanes(
    bounds: dict[str, Any],
    lane_config: dict[str, Any],
    model_spec: dict[str, Any],
    *,
    safety_factor: float = 1.1,
    start_from_service_refinement: bool = False,
) -> dict[str, Any]:
    if safety_factor < 1.0:
        raise ValueError("safety_factor must be at least 1.0")
    target_cycles = math.floor(
        float(bounds["cycles_available_per_bin"])
        * float(bounds["target_utilization"])
    )
    critical_nodes = set(bounds["completion_token_critical_path"])
    actor_bounds = bounds["actors"]
    layers = {str(layer["name"]): layer for layer in model_spec["layers"]}
    actors = {
        str(name): dict(config)
        for name, config in dict(lane_config["actors"]).items()
    }
    if start_from_service_refinement:
        for name, config in actors.items():
            actor = actor_bounds[name]
            config["channel_lanes"] = int(actor["refined_channel_lane_count"])
            config["spatial_lanes"] = int(actor["refined_spatial_lane_count"])

    work: dict[str, dict[str, float | int]] = {}
    for name, config in actors.items():
        actor = actor_bounds[name]
        total_commit = int(actor["commit_cycle_floor"])
        if name not in critical_nodes or total_commit == 0:
            continue
        channel_lanes = int(config["channel_lanes"])
        spatial_lanes = int(config["spatial_lanes"])
        physical_lanes = channel_lanes * spatial_lanes
        observed_maximum = int(actor["profiled_maximum_bank_commit_cycle_floor"])
        mean = total_commit / physical_lanes
        observed_imbalance = observed_maximum / mean if mean else 1.0
        output_h, output_w = (int(value) for value in layers[name]["output_hw"])
        work[name] = {
            "total_commit": total_commit,
            "channel_lanes": channel_lanes,
            "spatial_lanes": spatial_lanes,
            "maximum_spatial_lanes": output_h * output_w,
            "observed_imbalance": max(1.0, observed_imbalance),
        }

    def projected_cycles(item: dict[str, float | int], spatial_lanes: int) -> int:
        return math.ceil(
            int(item["total_commit"])
            * float(item["observed_imbalance"])
            * safety_factor
            / (int(item["channel_lanes"]) * spatial_lanes)
        )

    def projected_total() -> int:
        return sum(
            projected_cycles(item, int(item["spatial_lanes"]))
            for item in work.values()
        )

    while projected_total() > target_cycles:
        best: tuple[float, str] | None = None
        for name, item in work.items():
            spatial_lanes = int(item["spatial_lanes"])
            if spatial_lanes >= int(item["maximum_spatial_lanes"]):
                continue
            reduction = projected_cycles(item, spatial_lanes) - projected_cycles(
                item, spatial_lanes + 1
            )
            added_physical_lanes = int(item["channel_lanes"])
            score = reduction / added_physical_lanes
            if best is None or score > best[0]:
                best = (score, name)
        if best is None or best[0] <= 0:
            raise ValueError("latency target cannot be reached with legal spatial banking")
        work[best[1]]["spatial_lanes"] = int(work[best[1]]["spatial_lanes"]) + 1

    per_actor_projection: dict[str, dict[str, Any]] = {}
    for name, item in work.items():
        proposed_spatial = int(item["spatial_lanes"])
        actors[name]["spatial_lanes"] = proposed_spatial
        per_actor_projection[name] = {
            "proposed_spatial_lanes": proposed_spatial,
            "proposed_physical_lanes": (
                int(item["channel_lanes"]) * proposed_spatial
            ),
            "projected_commit_cycle_floor": projected_cycles(
                item, proposed_spatial
            ),
            "observed_commit_imbalance_factor": item["observed_imbalance"],
        }

    return {
        "schema_version": "1.0.0",
        "status": "latency_candidate_requires_exact_native_reprofile",
        "method": (
            "service_refined_then_greedy_spatial_commit_bank_addition"
            if start_from_service_refinement
            else "greedy_spatial_bank_addition_using_observed_commit_imbalance"
        ),
        "safety_factor": safety_factor,
        "target_completion_token_cycles": target_cycles,
        "projected_completion_token_critical_path_cycle_floor": projected_total(),
        "projection_is_measurement": False,
        "acceptance_requirement": (
            "rerun the exact native event profile with this manifest and accept only "
            "the remeasured completion-token critical-path result"
        ),
        "per_actor_projection": per_actor_projection,
        "actors": actors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bounds", type=Path, required=True)
    parser.add_argument("--lane-config", type=Path, required=True)
    parser.add_argument("--model-spec", type=Path, required=True)
    parser.add_argument("--safety-factor", type=float, default=1.1)
    parser.add_argument("--start-from-service-refinement", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bounds = json.loads(args.bounds.read_text(encoding="utf-8"))
    lane_config = json.loads(args.lane_config.read_text(encoding="utf-8"))
    model_spec = json.loads(args.model_spec.read_text(encoding="utf-8"))
    result = plan_latency_lanes(
        bounds,
        lane_config,
        model_spec,
        safety_factor=args.safety_factor,
        start_from_service_refinement=args.start_from_service_refinement,
    )
    result["source_bounds_sha256"] = _sha256(args.bounds)
    result["source_lane_config_sha256"] = _sha256(args.lane_config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
