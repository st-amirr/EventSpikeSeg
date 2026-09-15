import json

import pytest

from eventspikeseg.asic.activity_trace import (
    apply_resident_ordinary_expectations,
    build_actor_trace,
    build_pointwise_actor_trace,
    validate_trace_payload,
    write_actor_trace,
)


def _layer() -> dict:
    return {
        "kernel": [1, 1], "stride": [1, 1], "padding": [0, 0],
        "dilation": [1, 1], "input_hw": [10, 10], "output_hw": [10, 10],
        "in_channels": 4, "out_channels": 3,
    }


def test_pointwise_trace_selects_stable_busiest_coordinate_and_encodes_vectors(tmp_path) -> None:
    bins = [
        {"inputs": [(0, 4, 5), (2, 4, 5), (1, 8, 9)], "outputs": [(1, 4, 5)]},
        {"inputs": [(1, 4, 5), (3, 8, 9)], "outputs": [(0, 4, 5), (2, 4, 5)]},
    ]
    trace = build_pointwise_actor_trace(
        actor_name="enc3.pointwise",
        layer=_layer(),
        bins=bins,
        checkpoint_sha256="checkpoint",
        model_spec_sha256="model",
        event_file_sha256="events",
    )
    assert trace["coordinate_yx"] == [4, 5]
    assert trace["input_vectors_hex"] == ["5", "2"]
    assert trace["expected_output_vectors_hex"] == ["2", "5"]
    assert trace["selected_input_spikes"] == 3
    assert trace["selected_output_spikes"] == 3
    output = tmp_path / "trace.json"
    write_actor_trace(output, trace)
    assert json.loads(output.read_text()) == trace
    validate_trace_payload(trace)
    trace["input_vectors_hex"][0] = "0"
    with pytest.raises(ValueError, match="payload digest mismatch"):
        validate_trace_payload(trace)


def test_pointwise_trace_rejects_bitmap_multiplicity_loss() -> None:
    bins = [{"inputs": [(1, 2, 3), (1, 2, 3)], "outputs": []}]
    with pytest.raises(ValueError, match="duplicate presynaptic"):
        build_pointwise_actor_trace(
            actor_name="enc3.pointwise",
            layer=_layer(),
            bins=bins,
            checkpoint_sha256="checkpoint",
            model_spec_sha256="model",
            event_file_sha256="events",
        )


def test_activity_trace_rejects_non_pointwise_actor() -> None:
    layer = _layer() | {"kernel": [3, 3]}
    with pytest.raises(ValueError, match="pointwise"):
        build_pointwise_actor_trace(
            actor_name="enc3.depthwise",
            layer=layer,
            bins=[],
            checkpoint_sha256="checkpoint",
            model_spec_sha256="model",
            event_file_sha256="events",
        )


def test_depthwise_trace_encodes_channel_major_three_by_three_halo() -> None:
    layer = {
        "kernel": [3, 3], "stride": [1, 1], "padding": [1, 1],
        "dilation": [1, 1], "input_hw": [5, 5], "output_hw": [5, 5],
        "in_channels": 2, "out_channels": 2,
    }
    bins = [{
        "inputs": [(0, 1, 1), (0, 2, 2), (1, 3, 3)],
        "outputs": [(1, 2, 2)],
    }]
    trace = build_actor_trace(
        actor_name="enc1.depthwise", layer=layer, bins=bins,
        checkpoint_sha256="checkpoint", model_spec_sha256="model",
        event_file_sha256="events",
    )
    assert trace["coordinate_yx"] == [2, 2]
    assert trace["input_vector_bits"] == 18
    # Channel 0 halo bits 0 and 4; channel 1 bottom-right is bit 17.
    assert int(trace["input_vectors_hex"][0], 16) == (1 << 0) | (1 << 4) | (1 << 17)
    assert trace["expected_output_vectors_hex"] == ["2"]
    validate_trace_payload(trace)


def test_resident_expectations_commit_idle_residual_every_bin() -> None:
    layer = {
        "kernel": [1, 1], "stride": [1, 1], "padding": [0, 0],
        "dilation": [1, 1], "input_hw": [1, 1], "output_hw": [1, 1],
        "in_channels": 1, "out_channels": 1, "groups": 1,
    }
    trace = build_actor_trace(
        actor_name="fixture", layer=layer,
        bins=[
            {"inputs": [(0, 0, 0)], "outputs": [(0, 0, 0)]},
            {"inputs": [], "outputs": []},
            {"inputs": [], "outputs": []},
        ],
        checkpoint_sha256="checkpoint", model_spec_sha256="model",
        event_file_sha256="events",
    )
    apply_resident_ordinary_expectations(
        trace,
        layer=layer,
        weights=[[[[3 * 65536]]]],
        parameters={
            "beta_q": [1 << 23], "threshold_q": [65536],
            "inhibition_enabled": False,
            "threshold_adaptation_enabled": False,
        },
    )
    assert trace["input_vectors_hex"] == ["1", "0", "0"]
    assert trace["expected_output_vectors_hex"] == ["1", "1", "1"]
    assert trace["expectation_semantics"] == "resident_all_destinations_commit_every_bin"
    validate_trace_payload(trace)
