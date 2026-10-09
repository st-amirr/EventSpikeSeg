"""Carry one full-float MOS-geometry fan-in across fast SPICE segments."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/test_sky130_geometry_weighted_sequence.py"
OUT = ROOT / "artifacts/analog_asic"
RES = OUT / "results"


def main() -> int:
    order = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--order=")), "shuffle")
    chunk_size = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--chunk-size=")), "40"))
    initial_vp = initial_vn = 0.9
    common = [a for a in sys.argv[1:] if not a.startswith(("--order=", "--chunk-size="))]
    if chunk_size <= 0:
        raise ValueError("chunk size must be positive")
    rows = []
    total = 370
    for offset in range(0, total, chunk_size):
        count = min(chunk_size, total-offset)
        cmd = [sys.executable, str(SCRIPT), *common, f"--order={order}",
               f"--event-offset={offset}", f"--event-count={count}",
               f"--initial-vp={initial_vp:.12g}", f"--initial-vn={initial_vn:.12g}"]
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=270, cwd=ROOT)
        if run.returncode not in (0,):
            raise RuntimeError(f"segment {offset}:{offset+count} failed ({run.returncode}):\n{run.stdout}\n{run.stderr}")
        report = json.loads(run.stdout)
        if not report.get("simulation_completed"):
            raise RuntimeError(f"segment {offset}:{offset+count} did not complete: {run.stdout}")
        initial_vp, initial_vn = report["final_vp_v"], report["final_vn_v"]
        rows.append({"offset": offset, "count": count,
                     "ideal_segment_sum_v": report["segment_float_target_v"],
                     "measured_segment_change_v": report["measured_event_sum_v"],
                     "segment_error_v": report["measured_event_sum_v"]-report["segment_float_target_v"],
                     "state_start_vp_v": report.get("initial_vp_v", 0.9),
                     "state_end_vp_v": initial_vp, "state_end_vn_v": initial_vn,
                     "common_mode_v": (initial_vp+initial_vn)/2,
                     "source_report": next(RES.glob(f"sky130_geometry_weighted_sequence_n370_*_ord{order}_*seg{offset}-{offset+count}.json")).name})
        print(json.dumps(rows[-1]), flush=True)
    ideal = sum(row["ideal_segment_sum_v"] for row in rows)
    final_diff = rows[-1]["state_end_vp_v"]-rows[-1]["state_end_vn_v"]
    measured = final_diff
    result = {"simulation_completed": True, "mos_corner": "ss", "temperature_c": 0,
              "qat_or_quantized_reference_used": False, "event_order": order,
              "segment_count": len(rows), "events": sum(row["count"] for row in rows),
              "segment_reports": rows, "geometry_calibration": "measured SS/0C fixed-gate transfer, widths 0.5–64x",
              "ideal_full_float_event_sum_v": ideal, "measured_final_differential_v": measured,
              "final_error_v": measured-ideal,
              "relative_error": (measured-ideal)/max(abs(ideal),1e-30),
              "final_common_mode_v": (rows[-1]["state_end_vp_v"]+rows[-1]["state_end_vn_v"])/2,
              "scope": "One max-fanin final-fusion site from the original epoch58 float checkpoint, split into contiguous 40-event simulator segments with actual MOS models and custom geometry widths. Membrane states are carried between chunks; only the current segment's active synapse devices are instantiated. Other synapse off-leakage, extracted routing, mismatch/noise, physical PCell geometry, 5ms retention, PLIF threshold/reset/beta and population service are absent."}
    path=RES/f"sky130_geometry_weighted_sequence_segmented_{order}_c{chunk_size}.json"
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
