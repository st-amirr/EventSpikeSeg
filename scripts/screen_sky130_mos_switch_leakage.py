"""Isolate off-switch leakage from SKY130 MOS-gate storage capacitance."""
from __future__ import annotations

import json
import re
import subprocess

from screen_sky130_mos_state_cap import BENCH, HEADER, OUT, RESULTS, ROOT


def deck(bias: float) -> str:
    lines = [HEADER, "Vsrc src 0 0.9", "Voff_n gn 0 0", "Voff_p gp 0 1.8"]
    for kind in ("bare", "n_only", "p_only", "tg", "n_body", "p_body", "tg_body"):
        lines.append(f".ic v(state_{kind})={bias}")
        for finger in range(10):
            lines.append(f"Xcap_{kind}_{finger} 0 state_{kind} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1")
        if kind in ("n_only", "tg", "n_body", "tg_body"):
            body = f"state_{kind}" if kind in ("n_body", "tg_body") else "0"
            lines.append(f"Xsw_n_{kind} src gn state_{kind} {body} sky130_fd_pr__nfet_01v8 w=1 l=0.15")
        if kind in ("p_only", "tg", "p_body", "tg_body"):
            body = f"state_{kind}" if kind in ("p_body", "tg_body") else "vdd"
            lines.append(f"Xsw_p_{kind} src gp state_{kind} {body} sky130_fd_pr__pfet_01v8 w=1 l=0.15")
    lines.extend((".control", "tran 1u 5m uic"))
    for kind in ("bare", "n_only", "p_only", "tg", "n_body", "p_body", "tg_body"):
        lines.extend((f"meas tran {kind}_start find v(state_{kind}) at=2u",
                      f"meas tran {kind}_end find v(state_{kind}) at=5m"))
    lines.extend(("quit", ".endc", ".end"))
    return "\n".join(lines) + "\n"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for bias in (0.6, 1.2):
        tag = f"sky130_mos_switch_leakage_{str(bias).replace('.', 'p')}v"
        (BENCH / f"{tag}.cir").write_text(deck(bias), encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro",
               "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
               "--workdir", "/workspace/artifacts/analog_asic/benches",
               "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
               "120", "ngspice", "-b", f"{tag}.cir"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        log = proc.stdout + proc.stderr
        (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
        values = {name.lower(): float(value) for name, value in re.findall(
            r"^((?:bare|n_only|p_only|tg|n_body|p_body|tg_body)_(?:start|end))\s*=\s*([-+0-9.eE]+)",
            log, re.I | re.M)}
        cases = {}
        for kind in ("bare", "n_only", "p_only", "tg", "n_body", "p_body", "tg_body"):
            start, end = values.get(f"{kind}_start"), values.get(f"{kind}_end")
            cases[kind] = {"start_v": start, "end_v": end,
                           "hold_drift_v": end - start if start is not None and end is not None else None}
            if kind in ("p_body", "tg_body") and bias == 0.6:
                cases[kind]["within_documented_VBS_range"] = False
                cases[kind]["model_range_note"] = "PFET body 0.6V versus 0.9V source gives VBS=-0.3V, below documented -0.1V limit"
            elif kind in ("n_body", "tg_body") and bias == 1.2:
                cases[kind]["within_documented_VBS_range"] = None
                cases[kind]["model_range_note"] = "NFET body/source bias starts at the documented +0.3V boundary; not a robust in-range operating point"
            else:
                cases[kind]["within_documented_VBS_range"] = True
        rows.append({"initial_state_v": bias, "simulation_completed": proc.returncode == 0 and len(values) == 14,
                     "exit_code": proc.returncode, "cases": cases})
    report = {
        "scope": "SKY130 TT nominal 100um2 MOS gate state; ideal .ic initializes stored voltage; bare cap, off NFET/PFET/TG, and schematic body-to-state variants to 0.9V. UIC transient to 5ms. PFET body-tracking at 0.6V violates documented VBS range and NFET body-tracking at 1.2V begins at its boundary; these cases cannot qualify or reject a legal cell. Other body cases lack isolated-well layout. No noise/mismatch/extraction.",
        "all_simulations_completed": all(row["simulation_completed"] for row in rows),
        "results": rows,
    }
    (RESULTS / "sky130_mos_switch_leakage_boundary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_simulations_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
