from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from eventspikeseg.asic.dag_reference import (
    IntegerDAGReference,
    SpikeEvent,
    write_golden_artifacts,
)
from eventspikeseg.asic.topology import eventspikeseg140k_graph_contract

_LAYERS = (
    ("detail_stem", 2, 8, 1, 3, 1, "native", "native"),
    ("detail1.standard", 8, 8, 1, 3, 1, "native", "native"),
    ("stem", 2, 32, 1, 5, 2, "native", "half"),
    ("enc1.standard", 32, 32, 1, 3, 1, "half", "half"),
    ("enc1_extra.depthwise", 32, 32, 32, 3, 1, "half", "half"),
    ("enc1_extra.pointwise", 32, 32, 1, 1, 1, "half", "half"),
    ("down2.standard", 32, 64, 1, 3, 2, "half", "quarter"),
    ("enc2.depthwise", 64, 64, 64, 3, 1, "quarter", "quarter"),
    ("enc2.pointwise", 64, 64, 1, 1, 1, "quarter", "quarter"),
    ("enc2_extra.depthwise", 64, 64, 64, 3, 1, "quarter", "quarter"),
    ("enc2_extra.pointwise", 64, 64, 1, 1, 1, "quarter", "quarter"),
    ("down3.depthwise", 64, 64, 64, 3, 2, "quarter", "eighth"),
    ("down3.pointwise", 64, 128, 1, 1, 1, "eighth", "eighth"),
    ("enc3.depthwise", 128, 128, 128, 3, 1, "eighth", "eighth"),
    ("enc3.pointwise", 128, 128, 1, 1, 1, "eighth", "eighth"),
    ("enc3_extra.depthwise", 128, 128, 128, 3, 1, "eighth", "eighth"),
    ("enc3_extra.pointwise", 128, 128, 1, 1, 1, "eighth", "eighth"),
    ("context1.depthwise", 128, 128, 128, 3, 1, "eighth", "eighth"),
    ("context1.pointwise", 128, 128, 1, 1, 1, "eighth", "eighth"),
    ("context2.depthwise", 128, 128, 128, 3, 1, "eighth", "eighth"),
    ("context2.pointwise", 128, 128, 1, 1, 1, "eighth", "eighth"),
    ("project3", 128, 64, 1, 1, 1, "eighth", "eighth"),
    ("decoder2_fuse", 128, 64, 1, 1, 1, "quarter", "quarter"),
    ("project2", 64, 32, 1, 1, 1, "quarter", "quarter"),
    ("final_fuse.standard", 40, 16, 1, 3, 1, "native", "native"),
)


def _write_reference_fixture(path: Path) -> Path:
    graph = eventspikeseg140k_graph_contract()
    shapes = {"native": [8, 8], "half": [4, 4], "quarter": [2, 2], "eighth": [1, 1]}
    layers = []
    weights: dict[str, np.ndarray] = {}
    for index, (
        name,
        inputs,
        outputs,
        groups,
        kernel,
        stride,
        input_tier,
        output_tier,
    ) in enumerate(_LAYERS):
        inputs_per_group = inputs // groups
        array = np.zeros((outputs, inputs_per_group, kernel, kernel), dtype=np.int8)
        # Keep one complete channel-0 signal path. Concat routes require their
        # statically assigned channel offsets to be represented explicitly.
        input_channel = 0
        if name == "decoder2_fuse":
            array[0, 64, 0, 0] = 1
        elif name == "final_fuse.standard":
            array[0, 32, kernel // 2, kernel // 2] = 1
        array[0, input_channel % inputs_per_group, kernel // 2, kernel // 2] = 1
        weights[name] = array
        safe = name.replace(".", "_")
        parameter_file = f"{index:02d}_{safe}.json"
        (path / parameter_file).write_text(
            json.dumps(
                {
                    "beta_q": [32767] * outputs,
                    "threshold_q": [1] * outputs,
                    "inhibition_enabled": False,
                    "threshold_adaptation_enabled": False,
                    "inhibition_strength_q": None,
                    "threshold_adaptation_strength_q": None,
                    "adaptation_duration_q": None,
                }
            ),
            encoding="utf-8",
        )
        padding = kernel // 2
        layers.append(
            {
                "name": name,
                "input_hw": shapes[input_tier],
                "output_hw": shapes[output_tier],
                "in_channels": inputs,
                "out_channels": outputs,
                "groups": groups,
                "kernel": [kernel, kernel],
                "stride": [stride, stride],
                "padding": [padding, padding],
                "dilation": [1, 1],
                "parameter_file": parameter_file,
            }
        )
    readout = np.zeros((2, 16, 1, 1), dtype=np.int8)
    readout[0, 0, 0, 0] = -1
    readout[1, 0, 0, 0] = 1
    weights[graph["current_readout"]] = readout
    layers.append(
        {
            "name": graph["current_readout"],
            "input_hw": shapes["native"],
            "output_hw": shapes["native"],
            "in_channels": 16,
            "out_channels": 2,
            "groups": 1,
            "kernel": [1, 1],
            "stride": [1, 1],
            "padding": [0, 0],
            "dilation": [1, 1],
        }
    )
    np.savez_compressed(path / "quantized_weights.npz", **weights)
    model_spec = path / "model_spec.yaml"
    model_spec.write_text(
        json.dumps(
            {
                "input_size": shapes["native"],
                "input_channels": 2,
                "timing_contract": {"prediction_bins_default": 2},
                "graph": graph,
                "layers": layers,
            }
        ),
        encoding="utf-8",
    )
    return model_spec


def test_sparse_integer_reference_executes_complete_25_actor_dag(tmp_path: Path) -> None:
    reference = IntegerDAGReference(_write_reference_fixture(tmp_path))
    event = SpikeEvent(channel=0, y=4, x=4)
    assert reference.process_bin([event], bin_tag=1) is None
    prediction = reference.process_bin([event], bin_tag=2)
    assert prediction is not None
    assert prediction.bin_tag == 2
    assert prediction.classes.shape == (8, 8)
    assert 1 in prediction.classes
    assert set(reference.last_trace) == set(reference.graph["actor_topological_order"])
    # The project2+x1 merge preserves coincident events, so final fusion sees
    # repeated semantic events instead of residual-style binary deduplication.
    final_currents = reference.last_trace["final_fuse.standard"]["currents"]
    assert any(current > 1 for *_address, current in final_currents)


def test_sparse_integer_reference_rejects_invalid_ingress(tmp_path: Path) -> None:
    reference = IntegerDAGReference(_write_reference_fixture(tmp_path))
    with pytest.raises(ValueError, match="outside the exported geometry"):
        reference.process_bin([SpikeEvent(channel=2, y=0, x=0)], bin_tag=1)


def test_sparse_integer_reference_reset_clears_persistent_state(tmp_path: Path) -> None:
    reference = IntegerDAGReference(_write_reference_fixture(tmp_path))
    reference.process_bin([SpikeEvent(channel=0, y=4, x=4)], bin_tag=1)
    reference.reset()
    assert sum(reference.state_profile().values()) == 0
    assert reference.prediction_bin_count == 0


def test_integer_reference_writes_pickle_free_golden_contract(tmp_path: Path) -> None:
    model_spec = _write_reference_fixture(tmp_path)
    profile = write_golden_artifacts(
        model_spec,
        [[SpikeEvent(0, 4, 4)], [SpikeEvent(0, 4, 4)]],
    )
    assert profile["bins"] == 2
    assert profile["predictions"] == 1
    expected = {
        "golden_input_samples.npz",
        "golden_layer_currents.npz",
        "golden_layer_membranes.npz",
        "golden_layer_spikes.npz",
        "golden_semantic_outputs.npz",
    }
    assert expected <= {path.name for path in tmp_path.iterdir()}
    with np.load(tmp_path / "golden_semantic_outputs.npz", allow_pickle=False) as data:
        assert data["classes"].shape == (1, 8, 8)
        assert data["bin_tags"].tolist() == [2]
