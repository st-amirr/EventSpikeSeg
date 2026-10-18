"""Bind calibrated original-float membrane ranges to the existing 8x8 analog-bank selectors."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
EXPECTED = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    calibration_path = BASE / "results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json"
    selectors_path = BASE / "assembly/full25actor_permanent_analog_state_selectors_v1.json"
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    selectors = json.loads(selectors_path.read_text(encoding="utf-8"))
    assert calibration["checkpoint_sha256"] == selectors["checkpoint_sha256"] == EXPECTED
    assert calibration["simulation_completed"] and selectors["selector_map_construction_completed"]
    assert calibration["actor_count"] == 25 and calibration["settings"]["record_indices"] == "0,1,2,3,4,5,6,7"
    expected_state_count = 30_976_000
    assert sum(calibration["actor_state_counts"].values()) == expected_state_count

    membrane_planes = [plane for plane in selectors["planes"] if plane["state_kind"] == "membrane"]
    assert len(membrane_planes) == 25 and len({p["actor"] for p in membrane_planes}) == 25
    entries = []
    value_count = 0
    total_active = 0
    for plane in membrane_planes:
        name = plane["actor"]
        channels, height, width = plane["shape_chw"]
        tile_h, tile_w = plane["spatial_tile_hw"]
        assert (tile_h, tile_w) == (8, 8)
        ty, tx = plane["tile_grid_yx"]
        assert (ty, tx) == ((height + 7) // 8, (width + 7) // 8)
        ranges = calibration["state_tile8_ranges"][name]
        assert len(ranges) == 1 and len(ranges[0]) == channels
        assert all(len(c) == ty for c in ranges[0])
        assert all(len(row) == tx for c in ranges[0] for row in c)
        flat = [float(value) for channel in ranges[0] for row in channel for value in row]
        assert len(flat) == channels * ty * tx and all(value > 0 for value in flat)
        entries.append({
            "actor": name,
            "logical_state_interval": [plane["logical_start"], plane["logical_end_exclusive"]],
            "shape_chw": plane["shape_chw"],
            "tile_hw": [8, 8],
            "tile_grid_yx": [ty, tx],
            "channels": channels,
            "scale_count": len(flat),
            "bank_selector_expression": plane["selector_expression"],
            "scale_index_expression": "scale_index=c*(tile_grid_yx[0]*tile_grid_yx[1])+tile_y*tile_grid_yx[1]+tile_x",
            "range_layout": "channel-major, then tile_y, then tile_x",
            "range_abs_model_units": flat,
        })
        value_count += len(flat)
        total_active += plane["active_state_count"]

    assert total_active == expected_state_count
    assert value_count == 490_240
    assert value_count == sum(len(values[0]) * len(values[0][0]) * len(values[0][0][0]) for values in calibration["state_tile8_ranges"].values())
    out = BASE / "assembly/membrane_voltage_scale_manifest_v1.json"
    assert not out.exists(), f"preserve existing manifest: {out}"
    report = {
        "manifest_completed": True,
        "checkpoint_sha256": EXPECTED,
        "calibration_records": calibration["settings"]["record_indices"],
        "guard_policy": {"range_margin": calibration["settings"]["range_margin"], "threshold_floor_multiple": calibration["settings"]["threshold_floor_multiple"]},
        "actor_count": len(entries),
        "active_membrane_states": total_active,
        "scale_count": value_count,
        "states_per_scale_max": 64,
        "storage_bank_selector_source": selectors_path.relative_to(ROOT).as_posix(),
        "continuous_mapping_contract": "Vmem=VCM+scale_v_per_model_unit*model_state; scale_v_per_model_unit=usable_signed_voltage_half_swing_v/range_abs_model_units. The physical usable half-swing and implementation of shared scale/reference delivery remain parameters to characterize; no voltage endpoints are assumed here.",
        "actors": entries,
        "scope": "Maps the existing 8x8 spatial membrane ranges onto the exact permanent state selectors. One analog scale serves the maximum 64 membrane cells in each (actor,channel,tile_y,tile_x) bank; categorical bank addressing remains unchanged and all membrane identities are retained. Software calibration only: this manifest does not add scale hardware, establish physical voltage limits, or claim analog accuracy, mismatch/noise/PVT, unseen-scene headroom, 5ms service, or full-chip acceptance.",
        "sha256": {path.relative_to(ROOT).as_posix(): sha(path) for path in [Path(__file__), calibration_path, selectors_path]},
    }
    out.write_text(json.dumps(report, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": out.relative_to(ROOT).as_posix(), "actor_count": len(entries), "active_membrane_states": total_active, "shared_scale_count": value_count, "max_membranes_per_scale": 64, "usable_voltage_span_set": False}, indent=2))

if __name__ == "__main__":
    main()
