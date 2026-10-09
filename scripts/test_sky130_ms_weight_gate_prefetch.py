"""Compare cold and precharged shared OTA gate programming at one bounded point."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
STEM = "sky130_ms_weight_gate_prefetch_ss0_n0p48"
SAMPLES_US = (9.9, 10.01, 10.05, 10.1, 10.2, 10.5, 11, 12, 13, 15, 18, 20)


def main() -> int:
    bench = OUT / "benches"
    results = OUT / "results"
    bench.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    lines = [
        "SKY130 SS 0C OTA weight-gate prefetch screen",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        ".temp 0",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"',
        '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
        "Vdd vdd 0 1.8", "Vbn vbnn 0 0.65", "Vbp vbpp 0 0.733",
        "Vcold coldin 0 PWL(0 0 10u 0 10.0001u 0.48 20.1u 0.48)",
        "Vwarm warmin 0 PWL(0 0.45 10u 0.45 10.0001u 0.48 20.1u 0.48)",
        "Xcold coldout coldin coldout vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
        "Xwarm warmout warmin warmout vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
        "Xcold_load vcm coldout 0 0 sky130_fd_pr__nfet_01v8 w=1 l=10",
        "Xwarm_load vcm warmout 0 0 sky130_fd_pr__nfet_01v8 w=1 l=10",
        "Vcm vcm 0 0.9",
        ".control", "set numdgt=15", "tran 0.5n 20.1u",
    ]
    for index, at in enumerate(SAMPLES_US):
        for branch in ("cold", "warm"):
            lines.append(f"meas tran {branch}_{index} find v({branch}out) at={at:g}u")
    lines += ["quit", ".endc", ".end"]
    deck = bench / f"{STEM}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = [
        "docker", "run", "--rm", "--network", "none", "--memory", "8g", "--cpus", "2",
        "--volume", f"{ROOT}:/workspace:ro",
        "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
        "--workdir", "/workspace/artifacts/analog_asic/benches",
        "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
        "120", "ngspice", "-b", deck.name,
    ]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (results / f"{STEM}.log").write_text(log, encoding="utf-8")
    found = {key: float(val) for key, val in re.findall(
        r"(?m)^\s*((?:cold|warm)_\d+)\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and len(found) == 2 * len(SAMPLES_US) and "Timestep too small" not in log
    rows = [{"time_us": at, "cold_output_v": found[f"cold_{i}"],
             "warm_output_v": found[f"warm_{i}"],
             "cold_error_mv": 1e3 * (found[f"cold_{i}"] - .48),
             "warm_error_mv": 1e3 * (found[f"warm_{i}"] - .48)}
            for i, at in enumerate(SAMPLES_US)] if complete else []
    report = {
        "test": "sky130_shared_weight_ota_gate_prefetch",
        "simulation_completed": complete,
        "return_code": run.returncode,
        "corner": "ss", "temperature_c": 0,
        "precharge_us": 10, "cold_initial_command_v": 0,
        "warm_initial_command_v": .45, "target_command_v": .48,
        "rows": rows,
        "scope": "Physical transistor OTA and injector NMOS gate load. Two ideal input commands, ideal bias/rail, no analog store or mux, no calibration, no noise/mismatch/extraction. Measures one gate-level transition only.",
    }
    (results / f"{STEM}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
