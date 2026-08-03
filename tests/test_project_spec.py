from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_hardware_and_framework_policy_is_frozen_in_yaml() -> None:
    specification = yaml.safe_load((ROOT / "project_spec.yaml").read_text())
    strategy = specification["custom_fpga_backend_strategy"]
    assert specification["document"]["version"] == "0.3.0"
    assert strategy["implementation_languages"]["hardware"] == "VHDL-2008 only"
    policy = strategy["framework_reuse_policy"]
    assert policy["candidate_framework"] == "Spiker+"
    assert "Do not add Spiker+ as a required dependency" in policy["current_evaluation"]["outcome"]


def test_rtl_tree_contains_vhdl_only() -> None:
    rtl_files = [path for path in (ROOT / "rtl").rglob("*") if path.is_file()]
    assert rtl_files
    assert all(path.suffix == ".vhd" for path in rtl_files)
