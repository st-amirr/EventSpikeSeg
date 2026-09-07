from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_generator():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "eventspikeseg_resident_tile_pnr_generator",
        ROOT / "scripts/generate_resident_tile_pnr_top.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pnr_tile_uses_exported_nonzero_parameters(tmp_path: Path) -> None:
    (tmp_path / "weights.mem").write_text("01\nfe\n", encoding="utf-8")
    (tmp_path / "beta.mem").write_text("7fff\n", encoding="utf-8")
    (tmp_path / "threshold.mem").write_text("0005\n", encoding="utf-8")
    (tmp_path / "parameters.json").write_text(
        json.dumps(
            {
                "inhibition_enabled": False,
                "threshold_adaptation_enabled": False,
                "inhibition_strength_q": None,
                "threshold_adaptation_strength_q": None,
                "adaptation_duration_q": None,
            }
        ),
        encoding="utf-8",
    )
    model_spec = tmp_path / "model_spec.yaml"
    model_spec.write_text(
        json.dumps(
            {
                "artifact_root": ".",
                "graph": {"actor_topological_order": ["actor"]},
                "layers": [
                    {
                        "name": "actor",
                        "in_channels": 2,
                        "out_channels": 1,
                        "groups": 1,
                        "kernel": [1, 1],
                        "stride": [1, 1],
                        "padding": [0, 0],
                        "dilation": [1, 1],
                        "weight_count": 2,
                        "weight_rom": "weights.mem",
                        "beta_rom": "beta.mem",
                        "threshold_rom": "threshold.mem",
                        "parameter_file": "parameters.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "tile.sv"
    _load_generator().generate_tile_top(
        model_spec, output, actor_name="actor", tile_width=2, tile_height=2
    )
    text = output.read_text(encoding="utf-8")
    assert ".KERNEL_WEIGHTS(48'h0000fe000001)" in text
    assert ".CHANNEL_BETAS(24'h007fff)" in text
    assert ".CHANNEL_THRESHOLDS(24'h000005)" in text
    assert "input logic [7:0] presynaptic_spike_vector_i" in text


def test_pnr_multi_tile_top_uses_production_halo_wrapper(tmp_path: Path) -> None:
    (tmp_path / "weights.mem").write_text("01\n01\n01\n", encoding="utf-8")
    (tmp_path / "beta.mem").write_text("7fff\n", encoding="utf-8")
    (tmp_path / "threshold.mem").write_text("0001\n", encoding="utf-8")
    (tmp_path / "parameters.json").write_text(
        json.dumps(
            {
                "inhibition_enabled": False,
                "threshold_adaptation_enabled": False,
                "inhibition_strength_q": None,
                "threshold_adaptation_strength_q": None,
                "adaptation_duration_q": None,
            }
        ),
        encoding="utf-8",
    )
    model_spec = tmp_path / "model_spec.yaml"
    model_spec.write_text(
        json.dumps(
            {
                "artifact_root": ".",
                "graph": {"actor_topological_order": ["actor"]},
                "layers": [
                    {
                        "name": "actor",
                        "in_channels": 1,
                        "out_channels": 1,
                        "groups": 1,
                        "kernel": [1, 3],
                        "stride": [1, 1],
                        "padding": [0, 1],
                        "dilation": [1, 1],
                        "weight_count": 3,
                        "weight_rom": "weights.mem",
                        "beta_rom": "beta.mem",
                        "threshold_rom": "threshold.mem",
                        "parameter_file": "parameters.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "two_tiles.sv"
    _load_generator().generate_tile_top(
        model_spec,
        output,
        actor_name="actor",
        tile_width=2,
        tile_height=1,
        tile_columns=2,
    )
    text = output.read_text(encoding="utf-8")
    assert "tiled_resident_channelized_plif_actor" in text
    assert ".OUTPUT_WIDTH(4), .OUTPUT_HEIGHT(1)" in text
    assert ".TILE_WIDTH(2), .TILE_HEIGHT(1)" in text
    assert ".PAD_X(1), .PAD_Y(0)" in text
    assert "input logic [3:0] presynaptic_spike_vector_i" in text
