from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_active_sram_manifest_has_exact_logical_capacity() -> None:
    path = ROOT / "scripts/generate_asic_sram_manifest.py"
    spec = util.spec_from_file_location("asic_sram_manifest", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = module.generate_manifest(
        ROOT / "artifacts/asic_export_v4_6class/model_spec.yaml"
    )
    assert manifest["totals"]["total_bits"] == 3_070_478_400
    assert manifest["totals"]["bank_entries"] == 100
    assert {bank["ports"] for bank in manifest["banks"]} == {"1RW"}
    assert not any(bank["simultaneous_read_write"] for bank in manifest["banks"])
    assert sum(
        bank["total_bits"]
        for bank in manifest["banks"]
        if bank["kind"].startswith("residual_")
    ) == 252_313_600
    assert sum(
        bank["total_bits"]
        for bank in manifest["banks"]
        if bank["kind"] == "temporal_score"
    ) == 40_550_400
