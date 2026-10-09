"""Locate deterministic error growth in one actual mixed-weight analog fan-in."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
STEM = ("sky130_ms_first_touch_float_fanin_ss0_high_cancellation_stage_continuous_"
        "geometry_mapw42p2657n_bankedmap_durationfloor_piecewise1_prefix40_slot55n_shuffleonly")


def main() -> int:
    deck = json.loads((RES / f"{STEM}_deck.json").read_text(encoding="utf-8"))
    log = (RES / f"{STEM}.log").read_text(encoding="utf-8", errors="replace")
    if (deck["qat_or_quantized_reference_used"] or not deck["piecewise_first_range"] or
            deck["event_orders"] != ["shuffle"] or deck["prefix_measure_step"] != 40 or
            "ngspice-36 done" not in log or "Timestep too small" in log):
        raise RuntimeError("invalid mixed-weight prefix physical run")
    measured = {name: float(value) for name, value in re.findall(
        r"(?m)^(prefix_(?:ref|shuffle)_\d+)\s*=\s*([-+\d.eE]+)", log)}
    rows = []
    for count in deck["prefix_measure_counts"]:
        ref = measured[f"prefix_ref_{count}"]
        physical = measured[f"prefix_shuffle_{count}"] - ref
        ideal = deck["ideal_prefix_sums_v_by_order"]["shuffle"][str(count)]
        rows.append({"event_count": count, "ideal_sum_uv": ideal * 1e6,
                     "physical_sum_uv": physical * 1e6,
                     "error_uv": (physical - ideal) * 1e6})
    report = {"test": "sky130_first_piecewise_range_mixed_weight_prefix_error",
              "checkpoint_sha256": deck["checkpoint_sha256"],
              "qat_or_quantized_reference_used": False,
              "source_deck": deck["deck"], "event_slot_ns": deck["period_ns"],
              "rows": rows,
              "scope": "One shuffled322-event original-float high-cancellation site, ideal first-segment target, physical SS/0C shared MOS/TG/MIM bank and ideal effective gate commands. Prefix readings are taken 5ns after each selected pulse ends and before the next event, relative to a matched no-event branch. They differ in sampling time from the final post-train measurement and can retain transient settlement. No state-aware correction, physical DAC, noise/mismatch, beta/reset/readout, 5ms hold or layout."}
    (RES / "sky130_piecewise_first_range_highcancel_prefix40.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
