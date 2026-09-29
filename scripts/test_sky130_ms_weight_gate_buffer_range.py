"""Bound the existing transistor OTA as a unity weight-gate buffer."""

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VALUES = (0.30, 0.48, 0.72, 0.936, 1.08, 1.26, 1.50)
BIAS_P = (0.733, 0.750)


def main() -> int:
    stem = "sky130_ms_weight_gate_unity_buffer_ss0"
    lines = ["SKY130 SS 0C analog weight gate OTA follower DC range",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9", ".temp 0",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"',
             '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
             "Vdd vdd 0 1.8", "Vbn vbnn 0 0.65"]
    names = []
    for bi, bias in enumerate(BIAS_P):
        lines.append(f"Vbp{bi} vbpp{bi} 0 {bias:g}")
        for vi, value in enumerate(VALUES):
            name = f"b{bi}v{vi}"
            names.append(name)
            lines += [f"Vin_{name} in_{name} 0 {value:g}",
                      f"Xota_{name} out_{name} in_{name} out_{name} vbnn vbpp{bi} vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f"]
    lines += [".control", "set numdgt=15", "op"]
    for name in names:
        lines.append(f"print v(out_{name})")
    lines += ["print i(Vdd)", "quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    found = {name: float(value) for name, value in re.findall(
        r"(?im)^\s*v\(out_(b\dv\d)\)\s*=\s*([-+0-9.eE]+)", log)}
    current = re.search(r"(?im)^\s*i\(vdd\)\s*=\s*([-+0-9.eE]+)", log)
    complete = run.returncode == 0 and len(found) == len(names) and current is not None
    rows = []
    if complete:
        for bi, bias in enumerate(BIAS_P):
            for vi, value in enumerate(VALUES):
                output = found[f"b{bi}v{vi}"]
                rows.append({"p_bias_v": bias, "input_v": value, "output_v": output,
                             "follower_error_mv": (output - value) * 1e3})
    report = {"test": "sky130_ota_analog_weight_gate_unity_range", "simulation_completed": complete,
              "corner": "ss", "temperature_c": 0, "n_bias_v": 0.65,
              "rows": rows, "total_supply_current_a_for_14_instances": float(current.group(1)) if current else None,
              "scope": "Existing SKY130 two-stage OTA in DC unity feedback at selected SS/0C and two ideal bias settings. No physical weight MIM, mux, gate load, transient settling, output swing under current load, noise, mismatch, bias generator, PVT, extraction or area."}
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
