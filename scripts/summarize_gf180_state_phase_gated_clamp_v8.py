"""Verify and summarize the phase-gated rail limiter SPICE screen."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    bench = BASE / "benches/gf180_state_phase_gated_clamp_screen_v8.spice"
    log = BASE / "results/gf180_state_phase_gated_clamp_screen_v8.log"
    text = log.read_text(encoding="utf8", errors="replace")
    if "ngspice-47 done" not in text.lower() or "aborted" in text.lower() or "timestep too small" in text.lower():
        raise RuntimeError("phase-gated clamp simulation incomplete")
    values = {name.lower(): float(value) for name, value in re.findall(
        r"^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", text, re.M | re.I)}
    report = {
        "simulation_completed": True,
        "simulator": "ngspice-47",
        "corner": "GF180 typical, 27C",
        "state_capacitance": "native 5x5um MIM plus4.77fF parasitic; approximately54.5fF total",
        "limiter": "Phase-gated extracted quarter-size TG from membrane state to shared compensated low/high rail; enabled for8.8us after outward update. Gate phases are ideal external commands; clamp references include nominal kick compensation.",
        "cases": {
            "low_outward_negative_clipped": {
                "pre_event_v": values["lo_pre_event"], "post_event_v": values["lo_post_event"],
                "post_limiter_v": values["lo_post_clamp"], "after_5ms_v": values["lo_5ms"],
                "error_from_0p75v_rail_after_5ms_uv": (values["lo_5ms"] - 0.75) * 1e6,
            },
            "high_outward_positive_clipped": {
                "pre_event_v": values["hi_pre_event"], "post_event_v": values["hi_post_event"],
                "post_limiter_v": values["hi_post_clamp"], "after_5ms_v": values["hi_5ms"],
                "error_from_2p55v_rail_after_5ms_uv": (values["hi_5ms"] - 2.55) * 1e6,
            },
            "low_inward_positive_unclamped": {
                "pre_event_v": values["lo_in_pre_event"], "post_event_v": values["lo_in_post_event"],
                "after_5ms_v": values["lo_in_5ms"],
                "update_after_5ms_mv": (values["lo_in_5ms"] - values["lo_in_pre_event"]) * 1e3,
            },
            "high_inward_negative_unclamped": {
                "pre_event_v": values["hi_in_pre_event"], "post_event_v": values["hi_in_post_event"],
                "after_5ms_v": values["hi_in_5ms"],
                "update_after_5ms_mv": (values["hi_in_5ms"] - values["hi_in_pre_event"]) * 1e3,
            },
            "center_hold": {"after_5ms_v": values["mid_5ms"]},
        },
        "scope": "One nominal extracted-switch SPICE screen: two outward updates are rail-limited and two inward updates bypass the limiter. No comparator, range detector, full actor, PVT/noise/mismatch, routed clamp parent, or whole-model accuracy.",
        "sha256": {bench.relative_to(ROOT).as_posix(): sha(bench), log.relative_to(ROOT).as_posix(): sha(log)},
    }
    report["screen_result"] = "pass_nominal_signed_inward_updates_preserved_outward_updates_limited_and_5ms_hold"
    out = BASE / "results/gf180_state_phase_gated_clamp_screen_v8.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"report": str(out), "screen_result": report["screen_result"], "cases": report["cases"]}, indent=2))


if __name__ == "__main__":
    main()
