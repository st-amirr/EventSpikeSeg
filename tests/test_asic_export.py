from __future__ import annotations

import json

import h5py
import numpy as np
import pytest
import torch

from eventspikeseg.asic import (
    ASIC_FORMATS,
    BIN_TAG_WIDTH,
    DENSE_EXACT_STATE_BYTES,
    EVENTSPIKESEG140K_ACTORS,
    EVENTSPIKESEG140K_EDGES,
    EVENTSPIKESEG140K_INFERENCE_STAGES,
    EVENTSPIKESEG140K_JOIN_NODES,
    EVENTSPIKESEGXL_ACTORS,
    ActorLocalStateStore,
    IntegerPLIF,
    NeuronState,
    build_sram_manifest,
    eventspikeseg140k_graph_contract,
    eventspikesegxl_graph_contract,
    export_checkpoint,
    export_model,
    state_capacity_contract,
    validate_eventspikeseg140k_topology,
    validate_eventspikesegxl_topology,
)
from eventspikeseg.asic.activity_profile import (
    CHECKPOINT_IDENTITY_FIELDS,
    _event_file_bins,
    _validate_export_checkpoint,
    counted_events,
)
from eventspikeseg.asic.dag_reference import SpikeEvent
from eventspikeseg.model import EventSpikeSeg140k, EventSpikeSegXL


def test_frozen_140k_asic_graph_contract(tmp_path) -> None:
    model = EventSpikeSeg140k(class_count=6, input_channels=2)
    manifest = export_model(model, tmp_path)

    assert len(EVENTSPIKESEG140K_INFERENCE_STAGES) == 25
    assert manifest["schema_version"] == "2.2.0"
    assert manifest["class_count"] == 6
    assert manifest["registered_parameters"] == 149_835
    assert manifest["executed_inference_parameters"] == 149_423
    assert manifest["executed_convolution_weights"] == 143_824
    assert manifest["logical_membrane_states"] == 30_976_000
    assert manifest["hardware_topology"]["cross_layer_compute_sharing"] is False
    assert manifest["hardware_topology"]["runtime_layer_reconfiguration"] is False
    assert manifest["hardware_topology"]["state_ownership"] == "actor_local_direct_indexed_SRAM"
    assert manifest["hardware_topology"]["graph_kind"] == "static_directed_acyclic_actor_graph"
    assert manifest["hardware_topology"]["linear_pipeline"] is False
    assert (
        manifest["layer_order_semantics"]
        == "deterministic_topological_export_order_not_runtime_chain"
    )
    assert manifest["graph"]["linear_pipeline"] is False
    assert manifest["timing_contract"]["schedule"] == "autonomous_static_actor_graph"
    assert manifest["timing_contract"]["global_actor_scheduler"] is False
    assert manifest["timing_contract"]["last_bin_tag_width_bits"] == 0
    assert BIN_TAG_WIDTH == 24  # completion-token tag, not per-neuron state
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
    beta_lines = (tmp_path / model_spec["layers"][2]["beta_rom"]).read_text().splitlines()
    threshold_lines = (tmp_path / model_spec["layers"][2]["threshold_rom"]).read_text().splitlines()
    assert len(beta_lines) == model_spec["layers"][2]["out_channels"]
    assert len(threshold_lines) == model_spec["layers"][2]["out_channels"]
    assert all(len(word) == 6 for word in beta_lines + threshold_lines)


def test_xl_asic_graph_contract(tmp_path) -> None:
    manifest = export_model(EventSpikeSegXL(class_count=11, input_channels=2), tmp_path)
    assert len(EVENTSPIKESEGXL_ACTORS) == 44
    assert manifest["model"] == "EventSpikeSegXL"
    assert manifest["class_count"] == 11
    assert manifest["registered_parameters"] == 979_179
    assert manifest["executed_inference_parameters"] == 968_831
    assert manifest["executed_convolution_weights"] == 959_824
    assert manifest["logical_membrane_states"] == 78_707_200
    assert manifest["state_capacity"]["adaptation_enabled_neurons"] == 15_910_400
    assert manifest["spike_attention"]["heads"] == 4
    assert manifest["layers"][-1]["in_channels"] == 24
    assert manifest["layers"][-1]["out_channels"] == 11
    validate_eventspikesegxl_topology()
    assert eventspikesegxl_graph_contract()["actor_count"] == 44


def test_export_rejects_legacy_eleven_class_140k() -> None:
    with pytest.raises(ValueError, match="2 inputs and 6 classes"):
        export_model(EventSpikeSeg140k(class_count=11, input_channels=2), "unused")


def test_checkpoint_export_rejects_unknown_architecture_before_loading_weights(tmp_path) -> None:
    checkpoint = tmp_path / "xl.pt"
    torch.save({"architecture": "UnknownNet"}, checkpoint)
    with pytest.raises(ValueError, match="EventSpikeSeg140k or EventSpikeSegXL"):
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
    assert result.retention_q == 4_718_592
    assert result.candidate == 544
    assert result.spike == 1
    assert result.membrane == 32


def test_combined_accumulator_matches_one_bin_plif_and_prepares_next_leak() -> None:
    plif = IntegerPLIF()
    beta_q = int(ASIC_FORMATS["beta"].quantize(0.75))
    leaked = plif.leak_membrane_for_bins(512, beta_q, 1)
    conventional = plif.step(
        membrane_q=512,
        current_q=256,
        beta_q=beta_q,
        threshold_q=512,
    )
    combined = plif.commit_combined_accumulator(
        accumulator_q=leaked + 256,
        beta_q=beta_q,
        threshold_q=512,
    )
    assert (combined.candidate, combined.spike, combined.membrane) == (
        conventional.candidate,
        conventional.spike,
        conventional.membrane,
    )
    assert combined.next_accumulator == plif.leak_membrane_for_bins(combined.membrane, beta_q, 1)


def test_compact_adaptation_formats_cover_configured_limits() -> None:
    assert ASIC_FORMATS["adaptation_age"].maximum == 63
    assert ASIC_FORMATS["weight"].bits == 24
    assert ASIC_FORMATS["weight"].fractional_bits == 16
    assert ASIC_FORMATS["current"].bits == 32
    assert ASIC_FORMATS["adaptation_amplitude"].maximum >= 6 * (1 << 16)
    assert ASIC_FORMATS["adaptation_duration"].maximum >= 16 * (1 << 16)


def test_native_activity_event_expansion_preserves_count_multiplicity() -> None:
    counts = np.zeros((2, 3, 4), dtype=np.float32)
    counts[0, 1, 2] = 3
    counts[1, 2, 0] = 1
    events = counted_events(counts)
    assert events.count(SpikeEvent(0, 1, 2)) == 3
    assert events.count(SpikeEvent(1, 2, 0)) == 1


def test_native_event_file_short_sample_preserves_geometry_and_multiplicity(
    tmp_path,
) -> None:
    event_path = tmp_path / "events.h5"
    with h5py.File(event_path, "w") as handle:
        events = handle.create_group("events")
        events.create_dataset("x", data=np.asarray([2, 2, 3, 4], dtype=np.uint16))
        events.create_dataset("y", data=np.asarray([1, 1, 439, 440], dtype=np.uint16))
        events.create_dataset("p", data=np.asarray([0, 0, 1, 1], dtype=np.uint8))
        events.create_dataset("t", data=np.asarray([0, 1, 2, 3], dtype=np.uint32))
        handle.create_dataset("ms_to_idx", data=np.asarray([0, 4, 4, 4, 4, 4], dtype=np.uint64))
        handle.create_dataset("t_offset", data=np.int64(0))

    bins, preprocessing = _event_file_bins(event_path, start_ms=0, duration_ms=5, rectify_path=None)

    assert preprocessing.startswith("unrectified_sensor_coordinates")
    assert bins == [[SpikeEvent(0, 1, 2), SpikeEvent(0, 1, 2), SpikeEvent(1, 439, 3)]]


def test_native_profile_rejects_stale_checkpoint_export() -> None:
    identity = {field: f"value-{field}" for field in CHECKPOINT_IDENTITY_FIELDS}
    assert _validate_export_checkpoint({"checkpoint": identity}, identity) == identity
    stale = dict(identity)
    stale["epoch"] = "different"
    with pytest.raises(ValueError, match="regenerate artifacts/ASIC"):
        _validate_export_checkpoint({"checkpoint": stale}, identity)


def test_integer_plif_rounds_membrane_after_each_lazy_decay_step() -> None:
    plif = IntegerPLIF()
    result = plif.step(
        membrane_q=-200,
        current_q=0,
        beta_q=int(ASIC_FORMATS["beta"].quantize(30_000 / 32_768)),
        threshold_q=512,
        elapsed_bins=3,
    )
    # Per-step membrane rounding gives -154. Applying one rounded beta**3
    # coefficient would incorrectly give -153.
    assert result.candidate == -154
    assert result.membrane == -154
    assert result.spike == 0


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
    assert capacity["weight_bytes_int24"] == 431_472
    assert capacity["logical_membranes"] == 30_976_000
    assert capacity["dense_exact_state_mib"] == pytest.approx(150.8941650390625)
    assert capacity["adaptation_age_bits_per_enabled_neuron"] == 6
    assert capacity["adaptation_amplitude_bits_per_enabled_neuron"] == 19
    assert capacity["full_chip_PPA_gate"] == "characterized_actor_local_SRAM_macros_required"


def test_sram_manifest_derives_exact_actor_local_storage(tmp_path) -> None:
    export_model(EventSpikeSeg140k(class_count=6, input_channels=2), tmp_path)
    manifest = build_sram_manifest(tmp_path, maximum_bank_depth=65_536)

    assert manifest["memory_contract"]["port"] == "synchronous_single_port_1RW"
    assert manifest["memory_contract"]["runtime_reconfiguration"] is False
    assert manifest["memory_contract"]["events_accepted_during_initialization"] is False
    assert manifest["totals"]["actor_count"] == 25
    assert manifest["totals"]["logical_neurons"] == 30_976_000
    assert manifest["totals"]["persistent_state_bytes"] == 158_224_000
    assert manifest["totals"]["collection_current_bytes"] == 0
    assert manifest["totals"]["touched_bitmap_bytes"] == 0
    assert manifest["totals"]["direct_index_exact_bytes_excluding_queue"] == 158_224_000
    assert manifest["totals"]["weight_rom_bytes"] == 431_472
    assert manifest["totals"]["parallel_bank_scrub_cycles"] == 0
    assert manifest["totals"]["parallel_bank_scrub_time_us_at_200MHz"] == 0
    assert manifest["totals"]["rtl_sram_bytes_excluding_weight_rom"] == 163_295_104
    assert manifest["totals"]["rtl_state_bank_count"] == 487
    assert manifest["totals"]["rtl_queue_bank_count"] == 0
    assert manifest["totals"]["rtl_retinotopic_marker_bank_count"] == 0
    assert manifest["totals"]["rtl_readout_bank_count"] == 5
    assert manifest["shared_state"]["residual_unions"]["count"] == 9
    assert sum(actor["adaptation_enabled"] for actor in manifest["actors"]) == 15
    assert all(actor["banking"]["maximum_bank_depth"] == 65_536 for actor in manifest["actors"])
    assert manifest["physical_status"]["area_power_latency_available"] is False


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
