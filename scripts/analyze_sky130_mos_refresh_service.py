"""Conditional refresh-service arithmetic from the bounded SKY130 MOS hold probe."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "artifacts/analog_asic/results"
STATE_COUNT = 30_976_000
VCM_V = 0.9
HOLD_S = 5e-3
ERROR_PROBES_V = (3e-6, 100e-6, 1e-3)
SERVICE_PROBES_S = (0.1e-6, 1e-6, 5e-6)


def main() -> int:
    source = json.loads((RES / "sky130_mos_state_cap_boundary.json").read_text(encoding="utf-8"))
    if not source["all_simulations_completed"] or source["logical_state_count"] != STATE_COUNT:
        raise RuntimeError("MOS storage screen incomplete or wrong inventory")
    rows = []
    for case in source["results"]:
        bias = case["program_v"]
        if bias == VCM_V:
            continue
        initial_offset = bias - VCM_V
        drift = case["mos"]["no_pulse_hold_drift_v"]
        retained_fraction = (initial_offset + drift) / initial_offset
        if not 0 < retained_fraction < 1:
            raise RuntimeError("observed off-center drift is not toward VCM")
        tau_s = -HOLD_S / math.log(retained_fraction)
        error_rows = []
        for error_v in ERROR_PROBES_V:
            interval_s = -tau_s * math.log(1 - error_v / abs(initial_offset))
            services_per_s = STATE_COUNT / interval_s
            error_rows.append({
                "illustrative_abs_error_limit_uv": error_v * 1e6,
                "inferred_refresh_interval_us": interval_s * 1e6,
                "required_state_visits_per_s": services_per_s,
                "parallel_channel_lower_bounds": {
                    f"{service_s * 1e6:g}us_per_state":
                    math.ceil(services_per_s * service_s)
                    for service_s in SERVICE_PROBES_S
                },
            })
        rows.append({
            "program_v": bias,
            "observed_no_pulse_5ms_drift_mv": drift * 1e3,
            "inferred_single_pole_tau_s": tau_s,
            "error_probes": error_rows,
        })
    report = {
        "source": "sky130_mos_state_cap_boundary.json",
        "scope": "Conditional one-pole interpolation of nominal TT physical-TG MOS-gate drift toward 0.9V. Full state inventory visited every inferred interval. Channel bounds count only cell service, not readout/ADC/programmer, routing, power, event service, actor dependencies, PVT, noise or layout. Error probes are illustrative and are not model acceptance limits. Refresh copies a measured state and does not undo unknown noise or reconstruct a lost original value.",
        "logical_state_count": STATE_COUNT,
        "model_qualified": False,
        "refresh_circuit_implemented": False,
        "rows": rows,
    }
    (RES / "sky130_mos_refresh_service_boundary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
