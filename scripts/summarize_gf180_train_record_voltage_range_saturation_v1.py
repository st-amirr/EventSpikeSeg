"""Summarize the eight full-frame per-bank range saturation replays."""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def main():
    reports = [RESULTS / f"gf180_train_record_voltage_range_saturation_v1_record{i}.json" for i in range(8)]
    rows = [json.loads(path.read_text(encoding="utf8")) for path in reports]
    if not all(row.get("simulation_completed") and row.get("qat_or_quantized_reference_used") is False for row in rows):
        raise RuntimeError("incomplete or non-float replay report")
    output = {"simulation_completed": True, "frame_count": len(rows),
              "sequence_id": rows[0]["record"]["sequence_id"],
              "frame_indices": [row["record"]["frame_index"] for row in rows],
              "range_source": rows[0]["range_source"], "qat_or_quantized_reference_used": False,
              "modes": {}, "source_reports": {},
              "scope": "Eight contiguous full 440x640 training frames from one DSEC sequence. Each replay compares baseline epoch58 float inference to ideal candidate clipping or post-reset stored-state clipping at the existing per-8x8 capacitor rails. This is a range saturation sensitivity result, not analog circuit accuracy or independent-scene validation."}
    for mode in ("candidate_clip", "stored_state_clip"):
        output["modes"][mode] = {}
        for field in ("delta_present_class_mean_iou", "prediction_pixel_change_fraction"):
            output["modes"][mode][field] = stats([row["modes"][mode][field] for row in rows])
        output["modes"][mode]["baseline_present_class_mean_iou"] = stats([row["baseline"]["present_class_mean_iou"] for row in rows])
        output["modes"][mode]["replay_present_class_mean_iou"] = stats([row["modes"][mode]["present_class_mean_iou"] for row in rows])
        output["modes"][mode]["labeled_pixel_accuracy_delta"] = stats([
            row["modes"][mode]["labeled_pixel_accuracy"] - row["baseline"]["labeled_pixel_accuracy"] for row in rows])
        clipping = []
        clip_key = "candidate" if mode == "candidate_clip" else "stored_state"
        for row in rows:
            n = sum(x["clipped"] for x in row["clipping"][clip_key].values())
            total = sum(x["total"] for x in row["clipping"][clip_key].values())
            clipping.append(n / max(total, 1))
        output["modes"][mode]["state_values_clipped_fraction"] = stats(clipping)
    for path, row in zip(reports, rows):
        output["source_reports"][path.name] = digest(path)
    target = RESULTS / "gf180_train_record_voltage_range_saturation_v1_summary.json"
    target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"report": str(target), "frame_count": output["frame_count"], "modes": output["modes"]}, indent=2))


if __name__ == "__main__":
    main()
