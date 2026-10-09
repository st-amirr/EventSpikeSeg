"""Collect explicit numerical-conductance screens without accepting a state cell."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"


def main() -> None:
    rows = []
    for pattern in ("gf180_schematic_tg_*_gmin*.json",
                    "sky130_diode_isolated_mim_state_*_gmin*.json",
                    "sky130_min_mim_pair_pex_tg_hold_*_gmin*.json",
                    "sky130_diode_event_time_*_gmin*.json",
                    "sky130_body_tied_tg_pex_hold_*_gmin*.json",
                    "sky130_body_tied_tg_event_time_*_gmin*.json"):
        for path in sorted(RESULTS.glob(pattern)):
            report = json.loads(path.read_text(encoding="utf-8"))
            rows.append({"path": path.relative_to(ROOT).as_posix(),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "gmin_siemens_requested": report.get("gmin_siemens_requested"),
                         "simulation_completed": report["simulation_completed"],
                         "initialization_pass": report.get("initialization_pass"),
                         "equal_charge_serialization_verified": report.get("serialized_pulse_charge_checked")
                             if report["test"] == "sky130_extracted_diode_state_equal_charge_event_time" else None,
                         "results": report.get("rows", report.get("rows_mv", report.get("cases", report.get("hold", {
                             key: report[key] for key in ("early_final_increment_mv", "late_final_increment_mv",
                                                         "early_to_late_final_ratio") if key in report}))))})
    out = RESULTS / "analog_state_gmin_audit.json"
    out.write_text(json.dumps({
        "test": "analog_state_numerical_conductance_audit",
        "decision": "Reopen default-GMIN retention rejection; no cell accepted",
        "physical_state_accepted": False,
        "rows": rows,
        "limitations": "Explicit GMIN changes simulator stabilization, not PDK model cards. Low-GMIN completion alone is not convergence proof or measured silicon leakage. Remaining common-mode/state-dependent drift, initialization, addressability, noise/mismatch, read/write disturbance, actual events, area, task fidelity and 5ms population service remain open. GF180 capacitors/geometry are schematic assumptions; SKY130 reduced MIM and well proxies retain their diagnostic limitations. Historical default runs remain preserved and must not be treated as physical leakage evidence without numerical sensitivity checks."
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "reports": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
