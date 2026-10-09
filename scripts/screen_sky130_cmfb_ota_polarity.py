"""Measure shared OTA common-mode controller DC polarity across SKY130 corners."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/results/sky130_cmfb_ota_polarity"
IMAGE = "eventspikeseg:analog-ngspice36"
CASES = [("tt", 27), ("ss", 0), ("ff", 85)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for corner, temp in CASES:
        for polarity in ("sense_high_inp", "sense_high_inn"):
            inp, inn = ("vsense", "vcm") if polarity.endswith("inp") else ("vcm", "vsense")
            deck = OUT / f"{corner}_{polarity}.cir"
            deck.write_text(f'''* CMFB OTA control polarity sweep, SKY130 {corner}
.option scale=1u reltol=1e-4 abstol=1e-15 vntol=1e-8
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.include "/workspace/asic/analog/modules.spice"
.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vsense vsense 0 0.9
Vbn vbiasn 0 0.65
Vref vbiasp_ref 0 0.75
Cout vbiasp 0 10p
Rleak vbiasp vbiasp_ref 100Meg
Xtest {inp} {inn} vbiasp vbiasn vbiasp_ref vdd 0 sky130_sc_ota wn3=4 wp3=20 cc=5p
.temp {temp}
.dc Vsense 0.8 1.0 0.01
.control
set noaskquit
run
print v(vbiasp)
quit
.endc
.end
''', encoding="ascii")
            proc = subprocess.run(
                ["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
                 "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models", "--entrypoint",
                 "ngspice", IMAGE, "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"],
                capture_output=True, text=True, timeout=120, cwd=ROOT)
            log = proc.stdout + proc.stderr
            (OUT / f"{corner}_{polarity}.log").write_text(log, encoding="utf-8")
            rows = [(float(x), float(y)) for x, y in re.findall(
                r"(?m)^\d+\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)", log)]
            if proc.returncode or len(rows) != 21 or "ngspice-36 done" not in log:
                raise RuntimeError(f"{corner}/{polarity}: {log[-2000:]}")
            results.append({"corner": corner.upper(), "temperature_c": temp,
                            "polarity": polarity,
                            "gate_v_at_sense_0p89": rows[9][1],
                            "gate_v_at_sense_0p90": rows[10][1],
                            "gate_v_at_sense_0p91": rows[11][1],
                            "gate_v_at_sense_1p00": rows[20][1]})
    report = {"test": "sky130_cmfb_ota_dc_polarity", "completed": True,
              "sweep_v": [0.8, 1.0, 0.01], "results": results,
              "scope": "DC sign/range only; does not qualify closed-loop stability, offset, noise, events, layout, or state accuracy."}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
