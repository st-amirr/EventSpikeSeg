"""Record whether always-connected diode MOS clamps preserve signed state packets."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"


def read_measures(path):
    text = path.read_text(encoding="utf8", errors="replace")
    if "ngspice-47 done" not in text.lower():
        raise RuntimeError(f"incomplete ngspice log: {path}")
    values = {}
    for name, value in re.findall(r"^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", text, re.M | re.I):
        values[name.lower()] = float(value)
    return values


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    clamp_log = BASE / "results/gf180_state_diode_clamp_screen_v1.log"
    control_log = BASE / "results/gf180_state_diode_clamp_screen_noclamp_v1.log"
    clamp = read_measures(clamp_log)
    control = read_measures(control_log)
    report = {
        "simulation_completed": True,
        "simulator": "ngspice-47",
        "corner": "GF180 typical, 27C",
        "state_capacitance": "native 5x5um MIM plus 4.77fF parasitic",
        "clamp_topology": "Always-connected diode NMOS upper and diode PMOS lower clamps, shared references 2.20V and 1.35V",
        "test": "Initial low/center/high states; inject approximately -0.44fC at low and +0.44fC at high over1us; hold for5ms. Compare same bench with clamp devices removed.",
        "clamped": {key: clamp[key] for key in ("lo_pre_event", "lo_post_event", "lo_5ms", "hi_pre_event", "hi_post_event", "hi_5ms", "mid_5ms")},
        "unclamped": {key: control[key] for key in ("lo_pre_event", "lo_post_event", "lo_5ms", "hi_pre_event", "hi_post_event", "hi_5ms", "mid_5ms")},
        "interpretation": "Reject always-connected diode clamps: by5ms they reverse the requested rail-edge update direction. Low state moves from0.7503V pre-event to0.7573V at5ms after a negative update; high state moves from2.5498V to2.5475V after a positive update. The unclamped controls retain the requested signs. This nominal schematic screen does not test a phase-gated limiter.",
        "sources": {},
    }
    for path in (BASE / "benches/gf180_state_diode_clamp_screen_v1.spice",
                 BASE / "benches/gf180_state_diode_clamp_screen_noclamp_v1.spice", clamp_log, control_log):
        report["sources"][path.relative_to(ROOT).as_posix()] = sha(path)
    out = BASE / "results/gf180_state_diode_clamp_screen_v1.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"report": str(out), "interpretation": report["interpretation"]}, indent=2))


if __name__ == "__main__":
    main()
