"""Aggregate the corrected four-record original-float low-tail sensitivity screen."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
EXPECTED = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    files = sorted((BASE / "results").glob("gf180_float_weight_lowtail_sensitivity_v2_record[0-3]_src*.json"))
    reports = [json.loads(path.read_text()) for path in files]
    assert len(reports) == 4
    assert [report["record"]["validation_record_index"] for report in reports] == [0, 1, 2, 3]
    assert all(report["simulation_completed"] and report["checkpoint_sha256"] == EXPECTED for report in reports)
    replay_script = ROOT / "scripts/replay_gf180_float_weight_lowtail_sensitivity_v2.py"
    assert all(report["sha256"][replay_script.relative_to(ROOT).as_posix()] == sha(replay_script) for report in reports)
    deltas = [report["lowtail_analog_gain_sensitivity"]["mean_iou_delta"] for report in reports]
    pixel_changes = [report["lowtail_analog_gain_sensitivity"]["pixel_change_fraction"] for report in reports]
    rows = []
    for report, path in zip(reports, files):
        delta = report["lowtail_analog_gain_sensitivity"]["mean_iou_delta"]
        rows.append(
            {
                "report": path.relative_to(ROOT).as_posix(),
                "record": report["record"],
                "baseline_mean_iou": report["baseline"]["mean_iou"],
                "perturbed_mean_iou": report["lowtail_analog_gain_sensitivity"]["mean_iou"],
                "mean_iou_delta": delta,
                "pixel_change_fraction": report["lowtail_analog_gain_sensitivity"]["pixel_change_fraction"],
                "weights_perturbed": report["weights_perturbed"],
                "report_sha256": sha(path),
            }
        )
    output = {
        "simulation_completed": True,
        "checkpoint_sha256": EXPECTED,
        "checkpoint_epoch": 58,
        "record_count": len(rows),
        "actor_count": 25,
        "update_count": 10,
        "normalized_cut": 0.001,
        "continuous_lowtail_gain": reports[0]["continuous_lowtail_gain"],
        "effective_actor_weights_perturbed": reports[0]["weights_perturbed"],
        "record_results": rows,
        "mean_iou_delta_average": sum(deltas) / len(deltas),
        "mean_iou_delta_min": min(deltas),
        "mean_iou_delta_max": max(deltas),
        "pixel_change_fraction_average": sum(pixel_changes) / len(pixel_changes),
        "qat_or_quantized_reference_used": False,
        "scope": "Four full-frame validation-listed records; only the measured +29.1% q0.1 transfer error was extrapolated continuously to effective per-tensor weights below0.1%. No coefficients were zeroed or quantized. One-record-per-scene-subset sensitivity only; no measured low-current transfer below q0.1, noise/PVT, full validation-set accuracy, addressed analog storage, physical service, or acceptance.",
        "original_float_accuracy_accepted": False,
        "full_5ms_population_service_accepted": False,
        "full_chip_accepted": False,
        "sha256": {path.relative_to(ROOT).as_posix(): sha(path) for path in [Path(__file__), replay_script, *files]},
    }
    dest = BASE / "results/gf180_float_weight_lowtail_sensitivity_4record_summary_v1.json"
    dest.write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            {
                "report": dest.relative_to(ROOT).as_posix(),
                "record_count": len(rows),
                "mean_iou_delta_average": output["mean_iou_delta_average"],
                "mean_iou_delta_range": [min(deltas), max(deltas)],
                "pixel_change_fraction_average": output["pixel_change_fraction_average"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
