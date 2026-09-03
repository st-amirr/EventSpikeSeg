from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_planner():
    spec = importlib.util.spec_from_file_location(
        "eventspikeseg_latency_lane_planner",
        ROOT / "scripts/plan_asic_latency_lanes.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_planner_adds_banks_without_claiming_measurement() -> None:
    planner = _load_planner()
    bounds = {
        "cycles_available_per_bin": 100,
        "target_utilization": 0.8,
        "completion_token_critical_path": ["input", "a", "b", "prediction"],
        "actors": {
            "a": {
                "commit_cycle_floor": 100,
                "profiled_maximum_bank_commit_cycle_floor": 100,
                "refined_channel_lane_count": 1,
                "refined_spatial_lane_count": 1,
            },
            "b": {
                "commit_cycle_floor": 60,
                "profiled_maximum_bank_commit_cycle_floor": 60,
                "refined_channel_lane_count": 1,
                "refined_spatial_lane_count": 1,
            },
        },
    }
    lane_config = {
        "actors": {
            "a": {"use_parallel_banked_state": True, "channel_lanes": 1, "spatial_lanes": 1},
            "b": {"use_parallel_banked_state": True, "channel_lanes": 1, "spatial_lanes": 1},
        }
    }
    model_spec = {
        "layers": [
            {"name": "a", "output_hw": [2, 2]},
            {"name": "b", "output_hw": [2, 2]},
        ]
    }

    result = planner.plan_latency_lanes(
        bounds, lane_config, model_spec, safety_factor=1.0
    )

    assert result["projection_is_measurement"] is False
    assert result["projected_completion_token_critical_path_cycle_floor"] <= 80
    assert sum(
        actor["channel_lanes"] * actor["spatial_lanes"]
        for actor in result["actors"].values()
    ) > 2


def test_planner_can_start_from_service_refined_lane_counts() -> None:
    planner = _load_planner()
    bounds = {
        "cycles_available_per_bin": 100,
        "target_utilization": 0.8,
        "completion_token_critical_path": ["input", "a", "prediction"],
        "actors": {
            "a": {
                "commit_cycle_floor": 40,
                "profiled_maximum_bank_commit_cycle_floor": 20,
                "refined_channel_lane_count": 1,
                "refined_spatial_lane_count": 2,
            }
        },
    }
    lane_config = {
        "actors": {
            "a": {"use_parallel_banked_state": True, "channel_lanes": 1, "spatial_lanes": 4}
        }
    }
    model_spec = {"layers": [{"name": "a", "output_hw": [2, 2]}]}

    result = planner.plan_latency_lanes(
        bounds,
        lane_config,
        model_spec,
        safety_factor=1.0,
        start_from_service_refinement=True,
    )

    assert result["actors"]["a"]["spatial_lanes"] == 2
    assert result["method"].startswith("service_refined")
