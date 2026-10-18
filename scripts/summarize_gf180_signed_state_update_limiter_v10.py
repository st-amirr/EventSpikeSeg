"""Aggregate extracted layout and endpoint clamp screens for parent v10."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
CELL = "gf180_signed_state_update_limiter_v10"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    layout = BASE / "layout" / CELL
    qpath = layout / "qualification.json"
    qualification = json.loads(qpath.read_text())
    assert qualification["magic_drc_count"] == 0
    assert qualification["lvs_unique"]
    assert qualification["gds_roundtrip_drc_count"] == 0
    assert qualification["gds_roundtrip_lvs_unique"]
    assert qualification["range_limiter"]["control_is_external"]

    cases = []
    input_hashes = {qpath.relative_to(ROOT).as_posix(): sha(qpath)}
    for tag, endpoint in (("lo", 0.75), ("hi", 2.55)):
        source = BASE / "results" / f"gf180_signed_state_update_limiter_v{22 if tag == 'lo' else 21}.json"
        result = json.loads(source.read_text())
        assert result["simulation_completed"] and result["cell"] == CELL
        assert len(result["cases"]) == 1 and result["cases"][0]["case"] == tag
        case = result["cases"][0]
        cases.append({
            "case": tag,
            "initial_v": case["initial_v"],
            "packet_delta_mv": case["packet_delta_mv"],
            "compensated_rail_reference_v": case["rail_reference_v"],
            "after_limiter_v": case["post_limiter"],
            "after_5ms_v": case["5ms"],
            "nominal_endpoint_v": endpoint,
            "endpoint_error_after_5ms_uv": (case["5ms"] - endpoint) * 1e6,
            "error_from_compensated_reference_after_5ms_uv": (case["5ms"] - case["rail_reference_v"]) * 1e6,
            "bench_scope": result["scope"],
        })
        input_hashes[source.relative_to(ROOT).as_posix()] = sha(source)

    report = {
        "cell": CELL,
        "layout_qualification": {
            "drc_errors": qualification["magic_drc_count"],
            "lvs_unique": qualification["lvs_unique"],
            "gds_roundtrip_drc_errors": qualification["gds_roundtrip_drc_count"],
            "gds_roundtrip_lvs_unique": qualification["gds_roundtrip_lvs_unique"],
            "bbox_um": qualification["bbox_um"],
        },
        "corner": "GF180 typical, 27C",
        "cases": cases,
        "scope": "Combined extracted parent/limiter transient at low and high endpoints, with ideal 0.44fC packet current and externally timed limiter controls. Both cases simulate a 5ms post-event hold. No physical range comparator, analog weight-to-packet mapper, inward-update sequence, PVT/noise/mismatch, full PLIF recurrence, or full-chip approval is included. This large pin-exposed parent is an integration test vehicle, not the final compact reusable macro.",
        "source_sha256": input_hashes,
    }
    out = BASE / "results" / f"{CELL}_combined_extracted_screen.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(out), "cases": cases, "layout": report["layout_qualification"]}, indent=2))


if __name__ == "__main__":
    main()
