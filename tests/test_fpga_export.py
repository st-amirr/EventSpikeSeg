from __future__ import annotations

import json

import pytest
import torch

from eventspikeseg.fpga import (
    ARTIX7_XC7A200T,
    BIN_TAG_WIDTH,
    BIN_US,
    DEFAULT_TARGET_UTILIZATION,
    EVENTSPIKESEG140K_INFERENCE_STAGES,
    FPGA_FORMATS,
    NEXYS_VIDEO_XC7A200T,
    STEPS_PER_RECORD,
    FixedTimeRuntime,
    IntegerPLIF,
    LiveStateProfile,
    RuntimeTiming,
    SparseStateStore,
    StreamingBinRuntime,
    export_checkpoint,
    export_model,
    live_state_mask,
    memory_budget,
)
from eventspikeseg.fpga.integer_reference import NeuronState
from eventspikeseg.model import EventSpikeSeg140k, EventSpikeSegXL


def test_frozen_140k_inference_graph_contract(tmp_path) -> None:
    model = EventSpikeSeg140k(class_count=11, input_channels=2)
    manifest = export_model(model, tmp_path)

    assert len(EVENTSPIKESEG140K_INFERENCE_STAGES) == 25
    assert manifest["model"] == "EventSpikeSeg140k"
    assert manifest["registered_parameters"] == 150_245
    assert manifest["executed_inference_parameters"] == 149_503
    assert manifest["executed_convolution_weights"] == 143_904
    assert manifest["logical_membrane_states"] == 30_976_000
    assert manifest["base_skeleton_membrane_states"] == 10_700_800
    assert manifest["canonical_addition_membrane_states"] == 20_275_200
    assert "refine2" in manifest["deployment_excludes"]
    assert "aux_head" in manifest["deployment_excludes"]
    assert manifest["hardware_topology"]["cross_layer_compute_sharing"] is False
    assert manifest["target"]["device"] == "XC7A200T-1SBG484C"
    assert manifest["target"]["family"] == "AMD/Xilinx Artix-7"
    assert ARTIX7_XC7A200T is NEXYS_VIDEO_XC7A200T
    assert manifest["timing_contract"]["bin_us"] == 5_000
    assert manifest["timing_contract"]["prediction_bins_default"] == 10
    assert manifest["timing_contract"]["schedule"] == "bin_major_end_to_end"
    assert manifest["timing_contract"]["double_buffered_input"] is True
    assert manifest["timing_contract"]["per_neuron_timestamp_required"] is False
    assert manifest["timing_contract"]["per_neuron_last_bin_tag_required"] is True
    assert manifest["timing_contract"]["last_bin_tag_width_bits"] == BIN_TAG_WIDTH == 24
    assert manifest["hardware_topology"]["event_flow"] == "streaming_5ms_bin_ready_valid"
    assert manifest["hardware_topology"]["state_record_timestamp_field"] is False
    assert manifest["hardware_topology"]["state_record_last_bin_tag_bits"] == 24
    assert manifest["dense_state_memory_budget"]["required_over_available"] == pytest.approx(
        118.20395738203958
    )

    model_spec = json.loads((tmp_path / "model_spec.yaml").read_text(encoding="utf-8"))
    assert [layer["name"] for layer in model_spec["layers"][:-1]] == list(
        EVENTSPIKESEG140K_INFERENCE_STAGES
    )
    assert model_spec["layers"][-1]["name"] == "head.synapse"
    assert model_spec["layer_order"][-1] == "head.synapse"
    assert model_spec["layers"][2]["input_hw"] == [440, 640]
    assert model_spec["layers"][2]["output_hw"] == [220, 320]
    stem_parameters = json.loads(
        (tmp_path / model_spec["layers"][2]["parameter_file"]).read_text()
    )
    assert stem_parameters["inhibition_strength_q"] is not None
    assert "inhibition_strength" not in stem_parameters
    rom_lines = (tmp_path / model_spec["layers"][2]["weight_rom"]).read_text().splitlines()
    assert len(rom_lines) == model_spec["layers"][2]["weight_count"]
    assert all(len(value) == 2 for value in rom_lines)


def test_export_rejects_xl() -> None:
    with pytest.raises(TypeError, match="frozen to EventSpikeSeg140k"):
        export_model(EventSpikeSegXL(class_count=11, input_channels=2), "unused")


def test_checkpoint_export_rejects_non_140k_before_loading_weights(tmp_path) -> None:
    checkpoint = tmp_path / "xl.pt"
    torch.save({"architecture": "EventSpikeSegXL"}, checkpoint)
    with pytest.raises(ValueError, match="must be EventSpikeSeg140k"):
        export_checkpoint(checkpoint, tmp_path / "export")


def test_integer_plif_lazy_bin_decay_and_soft_reset() -> None:
    plif = IntegerPLIF()
    beta_q = int(FPGA_FORMATS["beta"].quantize(0.75))
    assert plif.retention_for_bins(beta_q, 2) == 18_432
    result = plif.step(
        membrane_q=512,
        current_q=256,
        beta_q=beta_q,
        threshold_q=512,
        elapsed_bins=2,
    )
    assert beta_q == 24_576
    assert result.retention_q == 18_432
    assert result.candidate == 544
    assert result.spike == 1
    assert result.membrane == 32


def test_integer_plif_touch_refreshes_compact_last_bin_tag() -> None:
    plif = IntegerPLIF()
    beta_q = int(FPGA_FORMATS["beta"].quantize(0.75))
    state, result = plif.touch_state(
        NeuronState(membrane=512, last_bin_tag=4),
        current_bin_tag=7,
        current_q=256,
        beta_q=beta_q,
        threshold_q=512,
    )
    assert result.elapsed_bins == 3
    assert state.last_bin_tag == 7
    assert result.candidate == 472
    assert result.spike == 0


def test_sparse_state_store_zero_default_reclaim_and_profile() -> None:
    store = SparseStateStore()
    address = (3, 7, 11, 13)
    assert store.read(address) == NeuronState()

    store.write(address, NeuronState(membrane=9, last_bin_tag=12))
    assert len(store) == 1
    assert store.read(address).membrane == 9
    assert store.read(address).last_bin_tag == 12

    store.write(address, NeuronState(membrane=0))
    assert len(store) == 0
    assert store.profile() == {
        "live_entries": 0,
        "high_watermark": 1,
        "touches": 2,
        "reclaims": 1,
    }


def test_sparse_state_does_not_reclaim_active_adaptation() -> None:
    store = SparseStateStore()
    address = (1, 2, 3, 4)
    store.write(address, NeuronState(membrane=0, adaptation_age=0))
    assert len(store) == 1


def test_artix7_memory_shortfall_uses_binary_units() -> None:
    budget = memory_budget(NEXYS_VIDEO_XC7A200T.bram_kibits)
    assert NEXYS_VIDEO_XC7A200T.bram_mib == pytest.approx(1.60400390625)
    assert budget["state_mib"] == pytest.approx(189.599609375)
    assert budget["missing_mib"] == pytest.approx(187.99560546875)
    assert budget["percent_missing"] == pytest.approx(99.15400463559104)


def test_live_state_mask_reclaims_quantized_zero_and_expired_adaptation() -> None:
    membrane = torch.tensor([[[[0.0001, 0.0020, 0.0]]]])
    age = torch.tensor([[[[0.0, 3.0, 1.0]]]])
    amplitude = torch.tensor([[[[0.0001, 1.0, 1.0]]]])
    duration = torch.tensor([1.0])
    assert live_state_mask(
        membrane,
        adaptation_age=age,
        adaptation_amplitude=amplitude,
        adaptation_duration=duration,
    ).flatten().tolist() == [False, True, True]


def test_empty_live_state_profile_fits_reserved_bram() -> None:
    summary = LiveStateProfile().summary()
    assert summary["fits_on_chip_bram"] is True
    assert summary["state_budget_bytes"] == 1_117_536
    assert summary["current_entries_sum"] == 0


def test_streaming_runtime_uses_bin_major_end_to_end_order() -> None:
    runtime = StreamingBinRuntime()
    events = runtime.schedule_bin_events(
        [
            (1_005_000, 0, 5, 6),
            (1_009_999, 1, 7, 8, 2),
        ],
        bin_index=1,
        stream_start_us=1_000_000,
    )
    assert [event.bin_index for event in events] == [1, 1]
    assert [event.multiplicity for event in events] == [1, 2]
    schedule = list(runtime.actor_schedule(["a", "b", "c"], bin_index=7))
    assert [(item.actor_name, item.bin_index) for item in schedule] == [
        ("a", 7), ("b", 7), ("c", 7)
    ]
    assert runtime.prediction_due(9) is False
    assert runtime.prediction_due(10) is True


def test_runtime_utilization_and_headroom_contract() -> None:
    timing = RuntimeTiming(clock_hz=100_000_000)
    assert BIN_US == 5_000
    assert pytest.approx(0.8) == DEFAULT_TARGET_UTILIZATION
    assert timing.hard_cycle_budget == 500_000
    assert timing.target_cycle_budget == 400_000
    assert timing.prediction_period_us == 50_000
    assert timing.prediction_rate_hz == pytest.approx(20.0)
    target = timing.report(400_000)
    assert target["utilization"] == pytest.approx(0.8)
    assert target["throughput_headroom"] == pytest.approx(1.25)
    assert target["hard_realtime_met"] is True
    assert target["target_utilization_met"] is True
    late = timing.report(500_001)
    assert late["hard_realtime_met"] is False


def test_fixed_time_record_helper_still_partitions_training_window() -> None:
    slices = FixedTimeRuntime.schedule_input_events(
        [
            (1_000_000, 0, 1, 2),
            (1_004_999, 1, 3, 4, 2),
            (1_005_000, 0, 5, 6),
            (1_049_999, 1, 7, 8),
        ],
        record_start_us=1_000_000,
    )
    assert len(slices) == STEPS_PER_RECORD == 10
    assert [event.multiplicity for event in slices[0]] == [1, 2]
    assert len(slices[1]) == 1
    assert len(slices[9]) == 1


def test_fixed_time_runtime_rejects_event_outside_record() -> None:
    with pytest.raises(ValueError, match="outside the 50 ms record"):
        FixedTimeRuntime.slice_for_timestamp(50_000, record_start_us=0)
