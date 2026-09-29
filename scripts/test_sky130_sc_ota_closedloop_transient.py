"""Transient settling check for the SKY130 xhigh-poly closed-loop differential OTA."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

HEADER = r"""* SKY130 TT OTA closed-loop small-signal transient settling
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / "sky130_sc_ota_closedloop_transient.cir"
    devices = []
    vectors = []
    for tag, rgain, rfb, l_gain, l_feedback in (("g10", 10, 90, 6.74, 60.97), ("g30", 10, 290, 6.74, 196.73)):
        devices += [
            f"Vbn_{tag} vbnn_{tag} 0 0.65",
            f"Vbp_{tag} vbpp_{tag} 0 0.75",
            f"Vsignal_{tag} signal_{tag} 0 PWL(0 0.9 0.99u 0.9 1.09u 0.900064 2m 0.900064)",
            f"Xgain_{tag} vcm inp_{tag} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={l_gain:g}",
            f"Xfeedback_{tag} out_{tag} inp_{tag} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={l_feedback:g}",
            f"Rload_{tag} out_{tag} vcm 1Meg",
            f"Xota_{tag} inp_{tag} signal_{tag} out_{tag} vbnn_{tag} vbpp_{tag} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
        ]
        vectors.append(f"v(out_{tag})")
    data = RES / "sky130_sc_ota_closedloop_transient.dat"
    lines = HEADER + "\n".join(devices) + f"\n.control\nset wr_singlescale\nset wr_vecnames\ntran 100n 2m\nwrdata ../results/{data.name} {' '.join(vectors)}\nquit\n.endc\n.end\n"
    deck.write_text(lines, encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "30", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=40)
    (RES / "sky130_sc_ota_closedloop_transient.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(value) for value in line.split()])
            except ValueError:
                continue
    results = {}
    if rows:
        final = {"gain10": rows[-1][1], "gain30": rows[-1][2]}
        for idx, tag in ((1, "gain10"), (2, "gain30")):
            target = final[tag]
            tolerance = max(abs(target - 0.9) * 0.01, 1e-9)
            settling_time = None
            for j, row in enumerate(rows):
                if all(abs(future[idx] - target) <= tolerance for future in rows[j:]):
                    settling_time = row[0]
                    break
            results[tag] = {
                "final_output_v": target,
                "final_step_mv": (target - 0.9) * 1e3,
                "settling_tolerance_mv": tolerance * 1e3,
                "settling_time_s_1pct": settling_time,
            }
    report = {
        "test": "sky130_tt_ota_closedloop_small_signal_transient_settling",
        "simulation_completed": run.returncode == 0 and len(rows) > 10,
        "return_code": run.returncode,
        "scope": "TT schematic with xhigh-poly resistor model, idealized 1Meg load and OTA compensation capacitor; 64uV step at 1us; no noise, mismatch, extraction or large-signal recovery",
        "sample_count": len(rows),
        "settling": results,
    }
    (RES / "sky130_sc_ota_closedloop_transient.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
