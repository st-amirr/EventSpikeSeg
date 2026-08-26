from __future__ import annotations

import json

import pytest
import torch

from eventspikeseg.asic import (
    ASIC_FORMATS,
    BIN_TAG_WIDTH,
    DENSE_EXACT_STATE_BYTES,
    EVENTSPIKESEG140K_ACTORS,
    EVENTSPIKESEG140K_EDGES,
    EVENTSPIKESEG140K_JOIN_NODES,
    EVENTSPIKESEG140K_INFERENCE_STAGES,
    ActorLocalStateStore,
    IntegerPLIF,
    NeuronState,
    eventspikeseg140k_graph_contract,
    export_checkpoint,
    export_model,
    state_capacity_contract,
    validate_eventspikeseg140k_topology,
)
from eventspikeseg.model import EventSpikeSeg140k, EventSpikeSegXL


def test_frozen_140k_asic_graph_contract(tmp_path) -> None:
    model = EventSpikeSeg140k(class_count=11, input_channels=2)
    manifest = export_model(model, tmp_path)

    assert len(EVENTSPIKESEG140K_INFERENCE_STAGES) == 25
    assert manifest["schema_version"] == "2.1.0"
    assert manifest["registered_parameters"] == 150_245
    assert manifest["executed_inference_parameters"] == 149_503
    assert manifest["executed_convolution_weights"] == 143_904
    assert manifest["logical_membrane_states"] == 30_976_000
    assert manifest["hardware_topology"]["cross_layer_compute_sharing"] is False
    assert manifest["hardware_topology"]["runtime_layer_reconfiguration"] is False
    assert manifest["hardware_topology"]["state_ownership"] == "actor_local_direct_indexed_SRAM"
    assert manifest["hardware_topology"]["graph_kind"] == "static_directed_acyclic_actor_graph"
    assert manifest["hardware_topology"]["linear_pipeline"] is False
    assert manifest["layer_order_semantics"] == "deterministic_topological_export_order_not_runtime_chain"
    assert manifest["graph"]["linear_pipeline"] is False
    assert manifest["timing_contract"]["schedule"] == "autonomous_static_actor_graph"
    assert manifest["timing_contract"]["global_actor_scheduler"] is False
    assert manifest["timing_contract"]["last_bin_tag_width_bits"] == BIN_TAG_WIDTH == 24
    assert manifest["open_PPA_target"]["platform"] == "ASAP7"
    assert manifest["open_PPA_target"]["manufacturable"] is False
    assert manifest["manufacturable_target_gate"]["maximum_process_nm"] == 28
    assert manifest["state_capacity"]["dense_exact_state_bytes"] == DENSE_EXACT_STATE_BYTES

    model_spec = json.loads((tmp_path / "model_spec.yaml").read_text(encoding="utf-8"))
    assert [layer["name"] for layer in model_spec["layers"][:-1]] == list(
        EVENTSPIKESEG140K_INFERENCE_STAGES
    )
    assert model_spec["layers"][-1]["name"] == "head.synapse"
    assert model_spec["layers"][2]["input_hw"] == [440, 640]
    assert model_spec["layers"][2]["output_hw"] == [220, 320]
    rom_lines = (tmp_path / model_spec["layers"][2]["weight_rom"]).read_text().splitlines()
    assert len(rom_lines) == model_spec["layers"][2]["weight_count"]


def test_export_rejects_xl() -> None:
    with pytest.raises(TypeError, match="frozen to EventSpikeSeg140k"):
        export_model(EventSpikeSegXL(class_count=11, input_channels=2), "unused")


def test_checkpoint_export_rejects_non_140k_before_loading_weights(tmp_path) -> None:
    checkpoint = tmp_path / "xl.pt"
    torch.save({"architecture": "EventSpikeSegXL"}, checkpoint)
    with pytest.raises(ValueError, match="must be EventSpikeSeg140k"):
        export_checkpoint(checkpoint, tmp_path / "export")


def test_integer_plif_lazy_decay_and_subtractive_reset() -> None:
    plif = IntegerPLIF()
    beta_q = int(ASIC_FORMATS["beta"].quantize(0.75))
    result = plif.step(
        membrane_q=512,
        current_q=256,
        beta_q=beta_q,
        threshold_q=512,
        elapsed_bins=2,
    )
    assert result.retention_q == 18_432
    assert result.candidate == 544
    assert result.spike == 1
    assert result.membrane == 32


def test_actor_local_state_zero_default_reclaim_and_tag() -> None:
    store = ActorLocalStateStore()
    address = (3, 7, 11)
    assert store.read(address) == NeuronState()
    store.write(address, NeuronState(membrane=9, last_bin_tag=12))
    assert store.read(address).last_bin_tag == 12
    store.write(address, NeuronState(membrane=0))
    assert len(store) == 0
    assert store.profile()["reclaims"] == 1


def test_triangular_adaptation_age_advances_by_elapsed_bins() -> None:
    assert IntegerPLIF.triangular_age_increment(0) == 0
    assert IntegerPLIF.triangular_age_increment(7) == 7


def test_state_capacity_is_model_scale_not_parameter_scale() -> None:
    capacity = state_capacity_contract()
    assert capacity["weight_bytes_int8"] == 143_904
    assert capacity["logical_membranes"] == 30_976_000
    assert capacity["dense_exact_state_mib"] == pytest.approx(189.599609375)
    assert capacity["full_chip_PPA_gate"] == "characterized_actor_local_SRAM_macros_required"


def test_140k_asic_topology_is_real_dag_not_linear_chain() -> None:
    validate_eventspikeseg140k_topology()
    graph = eventspikeseg140k_graph_contract()
    assert tuple(EVENTSPIKESEG140K_ACTORS) == tuple(EVENTSPIKESEG140K_INFERENCE_STAGES)
    assert graph["actor_count"] == 25
    assert graph["linear_pipeline"] is False

    edges = {(edge["source"], edge["destination"]): edge for edge in EVENTSPIKESEG140K_EDGES}
    # Input is an actual fork, not actor0 of a linear chain.
    assert ("input", "detail_stem") in edges
    assert ("input", "stem") in edges
    # x1 and x2 each fan out into a deeper encoder path and a later decoder skip.
    assert ("enc1_extra.residual_or", "down2.standard") in edges
    assert ("enc1_extra.residual_or", "semantic_half.multiplicity_sum") in edges
    assert ("enc2_extra.residual_or", "down3.depthwise") in edges
    assert ("enc2_extra.residual_or", "decoder2.concat") in edges
    # Decoder concatenation and final concatenation use fixed channel offsets.
    assert edges[("project3.upsample2x", "decoder2.concat")]["channel_offset"] == 0
    assert edges[("enc2_extra.residual_or", "decoder2.concat")]["channel_offset"] == 64
    assert edges[("semantic_native.upsample2x", "final.concat")]["channel_offset"] == 0
    assert edges[("detail1.residual_or", "final.concat")]["channel_offset"] == 32
    # Residual and decoder skip merges intentionally have different data semantics.
    assert EVENTSPIKESEG140K_JOIN_NODES["enc1.residual_or"]["data_rule"] == (
        "deduplicate_equal_binary_spike_addresses"
    )
    assert EVENTSPIKESEG140K_JOIN_NODES["semantic_half.multiplicity_sum"]["data_rule"] == (
        "forward_coincident_events_without_deduplication"
    )
    assert all(
        spec["completion_rule"] == "wait_for_all_inputs_same_bin"
        for spec in EVENTSPIKESEG140K_JOIN_NODES.values()
    )
