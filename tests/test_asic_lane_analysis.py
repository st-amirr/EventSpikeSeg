from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_analyzer():
    spec = importlib.util.spec_from_file_location(
        "eventspikeseg_lane_analyzer", ROOT / "scripts/analyze_asic_native_profile.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_profiled_bank_floor_conserves_activity_and_reports_imbalance(
    tmp_path: Path,
) -> None:
    analyzer = _load_analyzer()
    parameter_file = tmp_path / "actor.json"
    parameter_file.write_text(
        json.dumps(
            {
                "inhibition_enabled": False,
                "threshold_adaptation_enabled": False,
            }
        ),
        encoding="utf-8",
    )
    model_spec = tmp_path / "model_spec.json"
    model_spec.write_text(
        json.dumps(
            {
                "artifact_root": ".",
                "graph": {
                    "actor_topological_order": ["actor"],
                    "node_topological_order": ["input", "actor", "prediction"],
                    "edges": [
                        {"source": "input", "destination": "actor"},
                        {"source": "actor", "destination": "prediction"},
                    ],
                    "nodes": [
                        {"name": "input", "kind": "event_input"},
                        {"name": "actor", "kind": "plif_actor"},
                        {"name": "prediction", "kind": "semantic_output"},
                    ],
                },
                "layers": [
                    {
                        "name": "actor",
                        "out_channels": 2,
                        "output_hw": [1, 4],
                        "parameter_file": parameter_file.name,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    profile = tmp_path / "profile.json"
    profile.write_text(
        json.dumps(
            {
                "bins_profiled": 1,
                "scope": "synthetic",
                "actor_synaptic_contributions": {"actor": 10},
                "maximum_touched_queue_entries_by_actor": {"actor": 4},
                "actor_output_spikes": {"actor": 1},
                "actor_input_events": {"actor": 3},
                "input_events": 3,
                "maximum_residual_events_by_join": {},
                    "bank_activity": {
                        "actor": {
                            "channel_lanes": 2,
                            "spatial_lanes": 1,
                            "synaptic_contributions": [6, 4],
                        "maximum_touched_entries": [2, 2],
                        "output_spikes": [1, 0],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = analyzer.analyze(
        profile, model_spec, clock_mhz=1.0, bin_us=100.0, target_utilization=0.8
    )

    actor = result["actors"]["actor"]
    assert actor["serial_actor_cycle_floor"] == 63
    assert actor["profiled_maximum_bank_collection_cycle_floor"] == 18
    assert actor["profiled_maximum_bank_commit_cycle_floor"] == 17
    assert actor["profiled_channel_lane_count"] == 2
    assert actor["profiled_spatial_lane_count"] == 1
    assert actor["profiled_maximum_bank_cycle_floor"] == 35
    assert actor["profiled_maximum_bank_utilization_floor"] == 0.35
    assert actor["profiled_bank_cycle_imbalance"] == 35 / 31.5
    assert result["profiled_banked_realtime_floor_pass"] is True
    assert result["profiled_banked_target_floor_pass"] is True
    assert result["completion_token_critical_path_cycle_floor"] == 17
    assert result["completion_token_critical_path_target_floor_pass"] is True
    assert result["completion_token_critical_path"] == [
        "input",
        "actor",
        "prediction",
    ]
    assert result["generated_FIFO_count"] == 1
    assert result["edge_traffic"][0]["total_packets"] == 4
    assert result["edge_traffic"][1]["generated_FIFO_present"] is False
    assert result["edge_traffic_occupancy_available"] is False
    assert result["scalar_edge_serialization_cycle_floor"] == 4
    assert result["scalar_edge_realtime_floor_pass"] is True
    assert result["edge_lanes_required_floor_for_target"] == 1
    assert result["maximum_independent_cycle_floor"] == 35
    assert result["minimum_clock_mhz_floor_for_target"] == 0.4375
    assert result["combined_timed_schedule_available"] is False
