from __future__ import annotations

import json

import pytest
import torch

from eventspikeseg.fpga import (
    EVENTSPIKESEG140K_INFERENCE_STAGES,
    FPGA_FORMATS,
    NEXYS_VIDEO_XC7A200T,
    IntegerPLIF,
    LiveStateProfile,
    SparseStateStore,
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

    assert len(EVENTSPIKESEG140K_INFERENCE_STAGES) == 37
    assert manifest["model"] == "EventSpikeSeg140k"
    assert manifest["registered_parameters"] == 140_589
    assert manifest["executed_inference_parameters"] == 134_807
    assert manifest["executed_convolution_weights"] == 127_456
    assert manifest["logical_membrane_states"] == 72_843_333
    assert manifest["base_skeleton_membrane_states"] == 17_251_429
    assert manifest["canonical_addition_membrane_states"] == 55_591_904
    assert "refine2" in manifest["deployment_excludes"]
    assert "aux_head" in manifest["deployment_excludes"]
    assert manifest["hardware_topology"]["cross_layer_compute_sharing"] is False
    assert manifest["target"]["device"] == "XC7A200T-1SBG484C"
    assert manifest["dense_state_memory_budget"]["required_over_available"] == pytest.approx(
        293.2093785673516
    )

    model_spec = json.loads((tmp_path / "model_spec.yaml").read_text(encoding="utf-8"))
    assert [layer["name"] for layer in model_spec["layers"]] == list(
        EVENTSPIKESEG140K_INFERENCE_STAGES
    )
    assert model_spec["layer_order"] == list(EVENTSPIKESEG140K_INFERENCE_STAGES)
    assert model_spec["layers"][11]["input_hw"] == [241, 351]
    assert model_spec["layers"][11]["output_hw"] == [121, 176]
    stem_parameters = json.loads(
        (tmp_path / model_spec["layers"][0]["parameter_file"]).read_text()
    )
    assert stem_parameters["inhibition_strength_q"] is not None
    assert "inhibition_strength" not in stem_parameters
    rom_lines = (tmp_path / model_spec["layers"][0]["weight_rom"]).read_text().splitlines()
    assert len(rom_lines) == model_spec["layers"][0]["weight_count"]
    assert all(len(value) == 2 for value in rom_lines)


def test_export_rejects_xl() -> None:
    with pytest.raises(TypeError, match="frozen to EventSpikeSeg140k"):
        export_model(EventSpikeSegXL(class_count=11, input_channels=2), "unused")


def test_checkpoint_export_rejects_non_140k_before_loading_weights(tmp_path) -> None:
    checkpoint = tmp_path / "xl.pt"
    torch.save({"architecture": "EventSpikeSegXL"}, checkpoint)
    with pytest.raises(ValueError, match="must be EventSpikeSeg140k"):
        export_checkpoint(checkpoint, tmp_path / "export")


def test_integer_plif_lazy_decay_and_soft_reset() -> None:
    plif = IntegerPLIF()
    beta_q = int(FPGA_FORMATS["beta"].quantize(0.75))
    retention_q = plif.retention_for_delta(beta_q, 5_000)
    result = plif.step(
        membrane_q=512,
        current_q=256,
        retention_q=retention_q,
        threshold_q=512,
    )
    assert retention_q == 24_576
    assert result.candidate == 640
    assert result.spike == 1
    assert result.membrane == 128


def test_sparse_state_store_zero_default_reclaim_and_profile() -> None:
    store = SparseStateStore()
    address = (3, 7, 11, 13)
    assert store.read(address) == NeuronState()

    store.write(address, NeuronState(membrane=9, last_timestamp_us=100))
    assert len(store) == 1
    assert store.read(address).membrane == 9

    store.write(address, NeuronState(membrane=0, last_timestamp_us=200))
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
    assert budget["state_mib"] == pytest.approx(470.308988571167)
    assert budget["missing_mib"] == pytest.approx(468.704984664917)
    assert budget["percent_missing"] == pytest.approx(99.65894787522022)


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
    assert summary["state_budget_bytes"] == 1_133_984
    assert summary["current_entries_sum"] == 0
