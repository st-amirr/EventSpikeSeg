from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_planner():
    spec = importlib.util.spec_from_file_location(
        "eventspikeseg_resident_tile_planner",
        ROOT / "scripts/plan_asic_resident_tiles.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tile_plan_preserves_every_resident_state_bit(tmp_path: Path) -> None:
    parameter_file = tmp_path / "actor_parameters.json"
    parameter_file.write_text(
        json.dumps({"threshold_adaptation_enabled": True}), encoding="utf-8"
    )
    model_spec = tmp_path / "model_spec.yaml"
    model_spec.write_text(
        json.dumps(
            {
                "artifact_root": ".",
                "checkpoint": {"epoch": 40},
                "graph": {"actor_topological_order": ["actor"]},
                "layers": [
                    {
                        "name": "actor",
                        "in_channels": 2,
                        "out_channels": 3,
                        "input_hw": [3, 5],
                        "output_hw": [3, 5],
                        "kernel": [3, 3],
                        "stride": [1, 1],
                        "padding": [1, 1],
                        "dilation": [1, 1],
                        "weight_count": 7,
                        "parameter_file": parameter_file.name,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = _load_planner().plan_tiles(model_spec, tile_width=4, tile_height=2)
    actor = result["actors"][0]
    assert actor["tile_grid"] == [2, 2]
    assert actor["tile_count"] == 4
    assert actor["tile_shape_counts"] == {"2x4": 1, "2x1": 1, "1x4": 1, "1x1": 1}
    assert actor["logical_plifs"] == 45
    assert actor["resident_state_bits"] == 45 * (24 + 16 + 16 + 16)
    assert actor["receptive_halo_shape_counts"] == {
        "3x5": 1,
        "3x2": 1,
        "2x5": 1,
        "2x2": 1,
    }
    assert actor["receptive_halo_input_bits"] == 2 * (15 + 6 + 10 + 4)
    assert actor["full_bitmap_broadcast_input_bits"] == 2 * 3 * 5 * 4
    assert result["totals"]["input_wiring_reduction_fraction"] == 1 - 70 / 120
    assert result["totals"]["static_weight_bits"] == 56
