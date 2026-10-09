"""Bounded physical two-TG isolation screen for a sampled SKY130 MOS state."""
from __future__ import annotations

import json
import re
import subprocess

from screen_sky130_mos_state_cap import BENCH, HEADER, OUT, RESULTS, ROOT

BIAS_V = (0.6, 1.2)
MID_MIM_SIDES_UM = (None, 1.0, 2.2, 5.0, 10.0)


def deck(bias: float) -> str:
    lines = [HEADER, f"Vprogram src 0 {bias}",
             "Von on 0 PWL(0 1.8 1u 1.8 1.001u 0 5.01m 0)",
             "Voff off 0 PWL(0 0 1u 0 1.001u 1.8 5.01m 1.8)"]
    cases = {"single": None}
    cases.update({f"stack_{'none' if side is None else str(side).replace('.', 'p')}": side
                  for side in MID_MIM_SIDES_UM})
    for name, side in cases.items():
        if name == "single":
            lines.append(f"Xsw_{name} src state_{name} on off vdd 0 transmission_gate")
        else:
            lines.extend((f"Xsw1_{name} src mid_{name} on off vdd 0 transmission_gate",
                          f"Xsw2_{name} mid_{name} state_{name} on off vdd 0 transmission_gate"))
            if side is not None:
                lines.append(f"Xmidcap_{name} mid_{name} 0 sky130_fd_pr__cap_mim_m3_2 w={side} l={side} mf=1")
        for finger in range(10):
            lines.append(f"Xstatecap_{name}_{finger} 0 state_{name} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1")
    lines.extend((".control", "tran 1u 5.01m 0 1u"))
    for name in cases:
        lines.extend((f"meas tran {name}_start find v(state_{name}) at=2u",
                      f"meas tran {name}_end find v(state_{name}) at=5m"))
        if name != "single":
            lines.extend((f"meas tran {name}_mid_start find v(mid_{name}) at=2u",
                          f"meas tran {name}_mid_end find v(mid_{name}) at=5m"))
    lines.extend(("quit", ".endc", ".end"))
    return "\n".join(lines) + "\n"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for bias in BIAS_V:
        tag = f"sky130_mos_stacked_isolation_{str(bias).replace('.', 'p')}v"
        (BENCH / f"{tag}.cir").write_text(deck(bias), encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro",
               "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
               "--workdir", "/workspace/artifacts/analog_asic/benches",
               "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
               "120", "ngspice", "-b", f"{tag}.cir"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        log = proc.stdout + proc.stderr
        (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
        values = {name.lower(): float(value) for name, value in re.findall(
            r"^((?:single|stack_(?:none|1p0|2p2|5p0|10p0))_(?:(?:mid_)?(?:start|end)))\s*=\s*([-+0-9.eE]+)",
            log, re.I | re.M)}
        cases = {}
        for name in ("single", "stack_none", "stack_1p0", "stack_2p2", "stack_5p0", "stack_10p0"):
            start, end = values.get(f"{name}_start"), values.get(f"{name}_end")
            cases[name] = {"start_v": start, "end_v": end,
                           "hold_drift_v": end - start if start is not None and end is not None else None,
                           "program_error_v": start - bias if start is not None else None}
            if name != "single":
                mid_start, mid_end = values.get(f"{name}_mid_start"), values.get(f"{name}_mid_end")
                cases[name]["mid_start_v"] = mid_start
                cases[name]["mid_end_v"] = mid_end
                cases[name]["mid_hold_drift_v"] = (
                    mid_end - mid_start if mid_start is not None and mid_end is not None else None)
        rows.append({"program_v": bias, "simulation_completed": proc.returncode == 0 and len(values) == 22,
                     "exit_code": proc.returncode, "cases": cases})
    report = {
        "scope": "SKY130 TT nominal 100um2 MOS gate state, single TG versus two series TGs with intermediate floating node or 1/2.2/5/10um MIM hold capacitor. Both switches on during initial sampling and off for 5ms. No signed events, noise, mismatch, extraction or layout.",
        "all_simulations_completed": all(row["simulation_completed"] for row in rows),
        "results": rows,
    }
    (RESULTS / "sky130_mos_stacked_isolation_boundary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_simulations_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
