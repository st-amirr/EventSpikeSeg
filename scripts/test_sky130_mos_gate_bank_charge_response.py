"""Verify nonlinear transient charge response of the extracted MOS gate-bank netlist."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_mos_gate_bank_100x10_nf10"
BENCH = OUT / "charge_response_40fC.cir"
CELL = "mos_gate_bank_100x10_nf10"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    lines = ["* Nonlinear charge-response check, matched capacitor node references",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
             ".temp 27",
             f'.include "{MODEL}/models/parameters/invariant.spice"',
             f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
             f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
             f'.include "/workspace/artifacts/analog_asic/layout/{OUT.name}/{CELL}.spice"']
    for tag in ("large_pos", "large_neg"):
        lines += [f"Xcap_{tag} state_{tag} 0 0 {CELL}",
                  (f"Bdrive_{tag} 0 state_{tag} I={{time>=3u && time<3.04u ? 1u : 0}}" if tag.endswith("pos")
                   else f"Bdrive_{tag} state_{tag} 0 I={{time>=3u && time<3.04u ? 1u : 0}}")]
    for tag in ("small_pos", "small_neg"):
        lines += [f"Xcap_{tag}_{i} 0 state_{tag} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1" for i in range(10)]
        lines.append(f"Bdrive_{tag} {'0 state_' + tag if tag.endswith('pos') else 'state_' + tag + ' 0'} I={{time>=3u && time<3.04u ? 1u : 0}}")
    lines += [".ic " + " ".join(f"v(state_{tag})=0.9" for tag in
                                 ("large_pos", "large_neg", "small_pos", "small_neg")),
              ".control", "set numdgt=15", "tran 0.5n 3.1u 0 0.5n uic"]
    for tag in ("large_pos", "large_neg", "small_pos", "small_neg"):
        lines += [f"let delta_{tag}=v(state_{tag})-0.9",
                  f"meas tran {tag} find delta_{tag} at=3.066u"]
    lines += ["quit", ".endc", ".end", ""]
    BENCH.write_text("\n".join(lines), encoding="ascii")
    proc = subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w", "/workspace",
                           "--entrypoint", "ngspice", IMAGE, "-b", f"/workspace/artifacts/analog_asic/layout/{OUT.name}/{BENCH.name}"],
                          capture_output=True, text=True, timeout=150, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUT / "charge_response.log").write_text(log, encoding="utf-8")
    vals = {name.lower(): float(value) for name, value in re.findall(
        r"(?im)^\s*(large_pos|large_neg|small_pos|small_neg)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or len(vals) != 4:
        raise RuntimeError(f"MOS gate bank charge-response test failed:\n{log[-4000:]}")
    report = {"test": "sky130_mos_gate_bank_nonlinear_charge_response",
              "corner": "tt", "temperature_c": 27,
              "injected_charge_each_case_c": 40e-15,
              "large_bank_ac_capacitance_f": 74.8442682833e-12,
              "small_bank_ac_capacitance_f": 0.7732041249539075e-12,
              "state_voltage_delta_v": vals,
              "large_to_small_abs_delta_ratio": abs(vals["large_pos"]/vals["small_pos"]),
              "simulation_completed": True,
              "limitations": ["ideal current source and initial voltage", "TT only",
                              "no actual pulse injector, switch, sampled noise or retention"]}
    (OUT / "charge_response.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
