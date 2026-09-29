"""Aggregate bounded physical analog weight-store and event-routing screens."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
PLIF_WEIGHTS = 143728


def load(stem: str) -> dict:
    row = json.loads((RES / f"{stem}.json").read_text(encoding="utf-8"))
    if not row["simulation_completed"]:
        raise RuntimeError(f"incomplete gate-hold result: {stem}")
    return row


def main() -> int:
    direct = []
    for cap, hold, program in ((10, 0, 1), (10, 5000, 1), (20, 5000, 1),
                               (50, 5000, 1), (100, 5000, 10)):
        stem = f"sky130_ms_weight_gate_hold_ss0_c{cap}_h{hold}_f0p8_w40p253"
        if program != 1:
            stem += f"_prog{program}"
        row = load(stem)
        direct.append({"cap_square_um": cap, "hold_us": hold, "program_us": program,
                       "source_result": f"{stem}.json",
                       "p_gate_drift_mv": row["stored_p_gate_drift_v"] * 1e3,
                       "n_gate_drift_mv": row["stored_n_gate_drift_v"] * 1e3,
                       "held_over_direct_event_charge": row["held_event_step_v"] / row["direct_event_step_v"],
                       "bare_two_cap_all_plif_weight_area_mm2": 2 * PLIF_WEIGHTS * cap ** 2 / 1e6})
    steered = []
    for cap, hold, idle in ((10, 0, "rails"), (10, 5000, "rails"),
                            (10, 0, "vcm"), (10, 100, "vcm"),
                            (10, 500, "vcm"), (10, 1000, "vcm"),
                            (10, 5000, "vcm"), (20, 5000, "vcm"),
                            (50, 5000, "vcm"), (100, 5000, "vcm")):
        stem = f"sky130_ms_weight_gate_steered_hold_ss0_c{cap}_h{hold}_prog10_f0p5_w40p253"
        if idle == "vcm":
            stem += "_idlecm"
        row = load(stem)
        steered.append({"cap_square_um": cap, "hold_us": hold, "idle_clamp": idle,
                        "source_result": f"{stem}.json",
                        "p_gate_drift_mv": row["stored_p_gate_drift_v"] * 1e3,
                        "n_gate_drift_mv": row["stored_n_gate_drift_v"] * 1e3,
                        "neutral_switching_step_uv": row["neutral_switching_step_v"] * 1e6,
                        "ideal_gate_minus_neutral_step_uv": row["ideal_gate_minus_neutral_step_v"] * 1e6,
                        "held_gate_minus_neutral_step_uv": row["held_gate_minus_neutral_step_v"] * 1e6,
                        "held_gate_minus_neutral_relative_error":
                            row["held_gate_minus_neutral_step_v"] / row["ideal_gate_minus_neutral_step_v"] - 1,
                        "bare_two_cap_all_plif_weight_area_mm2": 2 * PLIF_WEIGHTS * cap ** 2 / 1e6})
    report = {"test": "sky130_physical_analog_weight_gate_storage_boundary",
              "simulation_completed": True, "checkpoint_float_plif_weight_count": PLIF_WEIGHTS,
              "direct_gate_mux": direct, "steered_drain": steered,
              "selected_weight_store_qualified": False,
              "scope": "Deterministic SS/0C one-event physical SKY130 MIM/TG/MOS screens. Area is bare two-cap geometry for 143728 folded PLIF weights, excluding 96 head weights, storage switching, current sources, routing and calibration. No thermal noise, mismatch, across-weight/fanin replay, refresh implementation, gate-reference generation, beta/reset/readout, extraction or full chip."}
    path = RES / "sky130_ms_weight_gate_storage_boundary.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"direct": direct, "steered": steered}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
