from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_active_residual_profile_covers_all_joins_but_is_non_bounding() -> None:
    path = ROOT / "scripts/profile_asic_residual_occupancy.py"
    spec = util.spec_from_file_location("asic_residual_occupancy", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.profile_residual_occupancy(
        ROOT / "artifacts/asic_export_v4_6class/model_spec.yaml",
        ROOT / "artifacts/asic_export_v4_6class/golden_input_samples.npz",
    )
    assert len(report["joins"]) == 9
    assert report["scope"] == "observed_fixture_only_not_a_safe_native_capacity_bound"
    assert all(join["bins_observed"] == 10 for join in report["joins"])
