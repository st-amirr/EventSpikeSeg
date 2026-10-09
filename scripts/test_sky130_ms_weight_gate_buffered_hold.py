"""Screen a physical MIM-held weight driving a continuously biased shared OTA."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
STEM = "sky130_ms_weight_gate_buffered_hold_ss0_c10_n0p48"
SAMPLES_US = (9.9, 10.1, 20, 100, 1000, 2500, 5000)


def main() -> int:
    bench = OUT / "benches"
    results = OUT / "results"
    bench.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    lines = [
        "SKY130 SS 0C physical MIM weight store to loaded OTA gate",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        ".temp 0",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        '.include "../../../asic/analog/modules.spice"',
        '.include "../../../asic/analog/sky130_ms_plif.spice"',
        '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbn vbnn 0 0.65", "Vbp vbpp 0 0.733",
        "Vweight source 0 0.48",
        "Vsample sample 0 PWL(0 1.8 10u 1.8 10.0001u 0 5000.1u 0)",
        "Vsampleb sampleb 0 PWL(0 0 10u 0 10.0001u 1.8 5000.1u 1.8)",
        "Xstore held vcm membrane_mim w_um=10 l_um=10",
        "Xprogram source held sample sampleb vdd 0 transmission_gate",
        "Xbuffer buffered held buffered vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
        "Xload vcm buffered 0 0 sky130_fd_pr__nfet_01v8 w=1 l=10",
        ".control", "set numdgt=15", "tran 100n 5000.1u uic",
    ]
    for index, at in enumerate(SAMPLES_US):
        lines.append(f"meas tran hold_{index} find v(held) at={at:g}u")
        lines.append(f"meas tran output_{index} find v(buffered) at={at:g}u")
    for index, at in enumerate((20, 1000, 5000)):
        lines.append(f"meas tran supply_{index} find i(Vdd) at={at:g}u")
    lines += ["quit", ".endc", ".end"]
    deck = bench / f"{STEM}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
           "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (results / f"{STEM}.log").write_text(log, encoding="utf-8")
    found = {key: float(val) for key, val in re.findall(
        r"(?m)^\s*((?:hold|output|supply)_\d+)\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and len(found) == 2 * len(SAMPLES_US) + 3 and "Timestep too small" not in log
    rows = [{"time_us": at, "held_input_v": found[f"hold_{i}"],
             "loaded_output_v": found[f"output_{i}"]}
            for i, at in enumerate(SAMPLES_US)] if complete else []
    report = {"test": "sky130_physical_weight_mim_buffered_gate_hold",
              "simulation_completed": complete, "return_code": run.returncode,
              "corner": "ss", "temperature_c": 0,
              "store_cap_square_um": 10, "program_us": 10, "command_v": .48,
              "rows": rows,
              "supply_current_a": {str(at): found.get(f"supply_{i}")
                                   for i, at in enumerate((20, 1000, 5000))},
              "scope": "One physical MIM+TG sampled analog level driving a continuously biased transistor OTA and one injector NMOS gate load over 5ms. Ideal programming voltage, clocks and biases. No pulse event, buffer sleep/selection, replicated weight array, noise/mismatch/PVT spread, extracted parasitics or full-model schedule."}
    if complete:
        report["held_input_drift_mv_10p1_to_5000us"] = 1e3 * (rows[-1]["held_input_v"] - rows[1]["held_input_v"])
        report["output_drift_mv_20_to_5000us"] = 1e3 * (rows[-1]["loaded_output_v"] - rows[2]["loaded_output_v"])
        report["steady_output_error_mv"] = 1e3 * (rows[-1]["loaded_output_v"] - .48)
    (results / f"{STEM}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
