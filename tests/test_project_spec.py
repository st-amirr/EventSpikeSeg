from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_hardware_and_framework_policy_is_frozen_in_yaml() -> None:
    specification = yaml.safe_load((ROOT / "project_spec.yaml").read_text())
    strategy = specification["custom_fpga_backend_strategy"]
    assert specification["document"]["version"] == "0.5.1"
    assert strategy["implementation_languages"]["hardware"] == "VHDL-2008 only"
    policy = strategy["framework_reuse_policy"]
    assert policy["candidate_framework"] == "Spiker+"
    assert "Do not add Spiker+ as a required dependency" in policy["current_evaluation"]["outcome"]
    assert specification["model"]["layers"][2]["convolution"]["stride"] == [1, 1]
    attention = specification["model"]["pixel_attention_head"]
    assert attention["output_shape_chw"] == [1, 90, 120]
    roi_policy = specification["model"]["tracking_head"]["roi_policy"]
    assert roi_policy["enabled_after_acquisition"] is False
    classifier = specification["model"]["classification_head"]
    assert classifier["analog_readout_allowed"] is False
    assert "LIF output neurons" in classifier["classifier"]


def test_hybrid_memory_policy_preserves_bram_for_deep_state() -> None:
    specification = yaml.safe_load((ROOT / "project_spec.yaml").read_text())
    policy = specification["custom_fpga_backend_strategy"]["memory_mapping_policy"]
    assert "Conv1 membrane state" in policy["bram_default_candidates"]
    assert "Pixel-attention membrane state" in policy["lutram_default_candidates"]
    assert "Class-neuron membrane state" in policy["register_default_candidates"]
    assert policy["status"] == "documented_for_future_implementation_not_yet_synthesized"


def test_rtl_tree_contains_vhdl_only() -> None:
    rtl_files = [path for path in (ROOT / "rtl").rglob("*") if path.is_file()]
    assert rtl_files
    assert all(path.suffix == ".vhd" for path in rtl_files)
