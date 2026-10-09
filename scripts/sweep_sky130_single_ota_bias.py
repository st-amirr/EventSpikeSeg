"""DC-sweep single-ended OTA-C bias to locate a non-railed state operating point."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/results/sky130_single_ota_bias_sweep"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    import sys
    arg = lambda key, default: next((v.split("=", 1)[1] for v in sys.argv[1:] if v.startswith(key + "=")), str(default))
    corner = arg("--corner", "tt").lower()
    temp = {"tt": 27, "ss": 0, "ff": 85}.get(corner)
    vbn = float(arg("--vbiasn", "0.65"))
    rdc = float(arg("--rdc-ohm", "1e12"))
    if temp is None:
        raise ValueError("corner must be tt, ss, or ff")
    OUT.mkdir(parents=True, exist_ok=True)
    dat_name = f"{corner}_vbiasn{vbn:g}_rdc{rdc:g}.dat".replace(".", "p")
    deck_name = f"{corner}_single_ota_bias_vbn{vbn:g}_rdc{rdc:g}.cir".replace(".", "p")
    deck = OUT / deck_name
    deck.write_text(f'''* Single-ended OTA-C operating-point PMOS load bias sweep
.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear
.temp {temp}
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.include "{MODEL}/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"
.subckt membrane_mim state vcm params: w_um=100 l_um=100
Xmim state vcm sky130_fd_pr__cap_mim_m3_2 w={{w_um}} l={{l_um}} mf=1
.ends membrane_mim
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vbn vbnp 0 {vbn:g}
Vbp vbpp 0 0.75
Xota sum vcm out vbnp vbpp vdd 0 sky130_sc_ota cc=5p
Xcfb out sum membrane_mim w_um=100 l_um=100 mf=1
Rdc out sum {rdc:g}
.control
set noaskquit
set numdgt=15
dc Vbp 0.3 1.4 0.01
wrdata /workspace/artifacts/analog_asic/results/sky130_single_ota_bias_sweep/{dat_name} v(vbpp) v(out) v(sum) v(xota.n1) v(xota.ntail) v(xota.n2)
quit
.endc
.end
''', encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2", "--volume", f"{ROOT}:/workspace",
           "--workdir", "/workspace/artifacts/analog_asic/results/sky130_single_ota_bias_sweep",
           "--entrypoint", "ngspice", IMAGE, "-b", deck_name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
    log = proc.stdout + proc.stderr
    report_stem = f"{corner}_vbiasn{vbn:g}_rdc{rdc:g}".replace(".", "p")
    (OUT / f"{report_stem}.log").write_text(log, encoding="utf-8")
    data_path = OUT / dat_name
    rows = []
    if data_path.exists():
        for line in data_path.read_text(encoding="ascii").splitlines()[1:]:
            try:
                vals = list(map(float, line.split()))
                # wrdata emits (sweep,value) pairs for each requested vector.
                rows.append({"vbiasp_v": vals[1], "out_v": vals[3], "sum_v": vals[5],
                             "n1_v": vals[7], "ntail_v": vals[9], "n2_v": vals[11]})
            except (ValueError, IndexError):
                continue
    nearest = min(rows, key=lambda row: abs(row["out_v"] - 0.9)) if rows else None
    nearest_both = min(rows, key=lambda row: abs(row["out_v"] - 0.9) + abs(row["sum_v"] - 0.9)) if rows else None
    report = {"test": "sky130_single_ended_ota_c_bias_dc_sweep", "simulation_completed": proc.returncode == 0 and len(rows) > 50,
              "corner": corner.upper(), "temperature_c": temp, "vbiasn_v": vbn, "rdc_ohm": rdc,
              "vbiasp_sweep_v": [0.3, 1.4, 0.01], "rows": rows,
              "closest_output_to_vcm": nearest,
              "closest_output_and_summing_node_to_vcm": nearest_both,
              "output_range_v": [min((r["out_v"] for r in rows), default=None), max((r["out_v"] for r in rows), default=None)],
              "deck": deck_name, "data": dat_name}
    (OUT / f"{report_stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
    return 0 if report["simulation_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
