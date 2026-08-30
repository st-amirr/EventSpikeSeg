from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_active_touch_profile_is_explicitly_non_bounding() -> None:
    path = ROOT / "scripts/profile_asic_touch_occupancy.py"
    spec = util.spec_from_file_location("asic_touch_occupancy", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.profile_touch_occupancy(
        ROOT / "artifacts/asic_export_v4_6class/model_spec.yaml",
        ROOT / "artifacts/asic_export_v4_6class/golden_layer_currents.npz",
    )
    assert len(report["actors"]) == 25
    assert report["scope"] == "observed_fixture_only_not_a_safe_native_capacity_bound"
    assert report["global_max_observed"] > 0
    assert all(
        actor["observed_max_per_bin"] <= actor["logical_capacity"]
        for actor in report["actors"]
    )
