"""Bounded DC operating-point and polarity screen for the SKY130 SC OTA."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

DECK = r"""* SKY130 TT OTA open-loop input-polarity and output-range screen
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / "sky130_sc_ota_open_loop.cir"
    grid = []
    for iw, (wn, wp, delta) in enumerate(((2, 27.8, 0.0), (2, 27.8, 0.001), (2, 27.8, -0.001))):
            name = f"d{iw}"
            grid += [f"Vbn_{name} vbnn_{name} 0 0.65", f"Vbp_{name} vbpp_{name} 0 0.75",
                     f"Vinp_{name} inp_{name} 0 {0.9 + delta:.6f}", f"Vinn_{name} inn_{name} 0 0.900000",
                     f"Rload_{name} out_{name} vcm 1Meg",
                     f"Xota_{name} inp_{name} inn_{name} out_{name} vbnn_{name} vbpp_{name} vdd 0 sky130_sc_ota wn3={wn} wp3={wp}"]
    outputs = " ".join(f"v(out_d{i})" for i in range(3))
    deck.write_text(DECK + "\n".join(grid) + f"\n.control\nop\nprint {outputs}\nquit\n.endc\n.end\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "30", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=40)
    log = run.stdout + run.stderr
    (RES / "sky130_sc_ota_open_loop.log").write_text(log, encoding="utf-8")
    report = {"test": "sky130_tt_ota_open_loop_input_polarity_and_output_range", "simulation_completed": run.returncode == 0,
              "return_code": run.returncode, "scope": "schematic TT only; input deltas 0 and +/-1mV at 0.9V common mode; tuned second-stage wn3=2um, wp3=27.8um; 1Meg output load"}
    (RES / "sky130_sc_ota_open_loop.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(log)
    print(json.dumps(report))
    return 0 if run.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
