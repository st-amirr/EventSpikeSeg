from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_banking_selects_minimum_allocated_bits_and_gates_PPA() -> None:
    path = ROOT / "scripts/plan_asic_sram_banking.py"
    spec = util.spec_from_file_location("asic_sram_banking", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = {
        "format": "eventspikeseg-sram-manifest-v1",
        "banks": [
            {
                "owner": "actor",
                "kind": "state",
                "word_bits": 66,
                "depth": 1500,
                "instances": 2,
                "total_bits": 198_000,
                "ports": "1R1W",
                "macro_required": True,
            }
        ],
    }
    catalog = {
        "catalog": "unit-test",
        "characterized": False,
        "macros": [
            {"name": "m32x1024", "ports": "1R1W", "word_bits": 32, "depth": 1024},
            {"name": "m72x2048", "ports": "1R1W", "word_bits": 72, "depth": 2048},
        ],
    }
    plan = module.plan_banking(manifest, catalog)
    bank = plan["banks"][0]
    assert bank["macro"] == "m72x2048"
    assert bank["width_tiles"] == 1
    assert bank["depth_tiles"] == 1
    assert bank["physical_instances"] == 2
    assert plan["PPA_eligible"] is False


def test_banking_requires_1R1W_catalog_entry() -> None:
    path = ROOT / "scripts/plan_asic_sram_banking.py"
    spec = util.spec_from_file_location("asic_sram_banking_empty", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.plan_banking(
            {"format": "eventspikeseg-sram-manifest-v1", "banks": []},
            {"macros": [{"name": "single", "ports": "1RW", "word_bits": 8, "depth": 8}]},
        )
    except ValueError as error:
        assert "no 1R1W macros" in str(error)
    else:
        raise AssertionError("planner accepted an incompatible macro port contract")
