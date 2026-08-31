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
                "ports": "1RW",
                "macro_required": True,
            }
        ],
    }
    catalog = {
        "catalog": "unit-test",
        "characterized": False,
        "macros": [
            {"name": "m32x1024", "ports": "1RW", "word_bits": 32, "depth": 1024},
            {"name": "m72x2048", "ports": "1RW", "word_bits": 72, "depth": 2048},
        ],
    }
    plan = module.plan_banking(manifest, catalog)
    bank = plan["banks"][0]
    assert bank["macro"] == "m72x2048"
    assert bank["width_tiles"] == 1
    assert bank["depth_tiles"] == 1
    assert bank["physical_instances"] == 2
    assert plan["PPA_eligible"] is False


def test_banking_requires_matching_catalog_port() -> None:
    path = ROOT / "scripts/plan_asic_sram_banking.py"
    spec = util.spec_from_file_location("asic_sram_banking_empty", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.plan_banking(
            {
                "format": "eventspikeseg-sram-manifest-v1",
                "banks": [{
                    "owner": "actor", "kind": "state", "word_bits": 8,
                    "depth": 8, "instances": 1, "total_bits": 64,
                    "ports": "1RW", "macro_required": True,
                }],
            },
            {"macros": [{"name": "dual", "ports": "1R1W", "word_bits": 8, "depth": 8}]},
        )
    except ValueError as error:
        assert "no 1RW macros" in str(error)
    else:
        raise AssertionError("planner accepted an incompatible macro port contract")


def test_banking_can_minimize_predictive_macro_area() -> None:
    path = ROOT / "scripts/plan_asic_sram_banking.py"
    spec = util.spec_from_file_location("asic_sram_banking_area", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = {
        "format": "eventspikeseg-sram-manifest-v1",
        "banks": [{
            "owner": "actor", "kind": "state", "word_bits": 64,
            "depth": 1024, "instances": 1, "total_bits": 65_536,
            "ports": "1RW", "macro_required": True,
        }],
    }
    catalog = {
        "catalog": "predictive", "characterized": True,
        "characterization_kind": "predictive_model",
        "research_PPA_eligible": True, "silicon_characterized": False,
        "selection_objective": "minimum_area",
        "macros": [
            {"name": "small", "ports": "1RW", "word_bits": 32, "depth": 256,
             "area_um2": 100.0, "leakage_uW": 2.0},
            {"name": "dense", "ports": "1RW", "word_bits": 128, "depth": 2048,
             "area_um2": 500.0, "leakage_uW": 5.0},
        ],
    }
    plan = module.plan_banking(manifest, catalog)
    assert plan["banks"][0]["macro"] == "dense"
    assert plan["totals"]["macro_area_um2"] == 500.0
    assert plan["totals"]["macro_leakage_uW"] == 5.0
    assert plan["research_PPA_eligible"] is True
    assert plan["silicon_characterized"] is False
    assert plan["PPA_eligible"] is True
