"""Bounded SKY130 OTA differential sensitivity near a measured packet size."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

HEADER = r"""* SKY130 TT open-loop OTA differential sensitivity at 0.9V common mode
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
    arg = lambda k, d: next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith(k + '=')), str(d))
    common_mode = float(arg('--common-mode-v', 0.9))
    bias_n = float(arg('--bias-n-v', 0.65))
    bias_p = float(arg('--bias-p-v', 0.75))
    input_width_um = float(arg('--input-width-um', 10))
    temperature_c = float(arg('--temperature-c', 27))
    corner = arg('--mos-corner', 'tt')
    if corner not in ('tt', 'ss', 'ff'):
        raise ValueError('MOS corner must be tt, ss or ff')
    deltas_uv = tuple(float(v) for v in arg('--deltas-uv', '0,64,-64,250,-250,500,-500').split(','))
    deltas = tuple(v * 1e-6 for v in deltas_uv)
    tag = ('cm' + str(common_mode).replace('.', 'p') + '_u' + '-'.join(str(v).replace('.', 'p').replace('-', 'm') for v in deltas_uv)
           + f'_bn{bias_n:g}_bp{bias_p:g}_win{input_width_um:g}_mos{corner}_temp{temperature_c:g}'.replace('.', 'p'))
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"sky130_sc_ota_diff_sensitivity_{tag}.cir"
    devices: list[str] = []
    outputs: list[str] = []
    for index, delta in enumerate(deltas):
        name = f"d{index}"
        devices += [
            f"Vbn_{name} vbnn_{name} 0 {bias_n:g}",
            f"Vbp_{name} vbpp_{name} 0 {bias_p:g}",
            f"Vinp_{name} inp_{name} 0 {common_mode + delta:.12f}",
            f"Vinn_{name} inn_{name} 0 {common_mode:.12f}",
            f"Rload_{name} out_{name} vcm 1Meg",
            f"Xota_{name} inp_{name} inn_{name} out_{name} vbnn_{name} vbpp_{name} vdd 0 sky130_sc_ota win={input_width_um:g} wn3=2 wp3=27.8 cc=100f",
        ]
        outputs.append(f"v(out_{name})")
    header = HEADER.replace('__tt.corner.spice', f'__{corner}.corner.spice')
    header = header.replace('Vdd vdd 0 1.8', f'.temp {temperature_c:g}\nVdd vdd 0 1.8')
    deck.write_text(header + "\n".join(devices) + "\n.control\nop\nprint " + " ".join(outputs) + "\nquit\n.endc\n.end\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "30", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=40)
    log = run.stdout + run.stderr
    (RES / f"sky130_sc_ota_diff_sensitivity_{tag}.log").write_text(log, encoding="utf-8")
    parsed = {int(i): float(v) for i, v in re.findall(r"v\(out_d(\d+)\)\s*=\s*([+\-0-9.eE]+)", log)}
    baseline = parsed.get(0)
    rows = []
    for index, delta in enumerate(deltas):
        voltage = parsed.get(index)
        rows.append({
            "input_diff_v": delta,
            "output_v": voltage,
            "output_change_from_zero_v": None if voltage is None or baseline is None else voltage - baseline,
            "incremental_gain_v_per_v": None if voltage is None or baseline is None or not delta else (voltage - baseline) / delta,
        })
    report = {
        "test": "sky130_tt_ota_open_loop_differential_sensitivity",
        "simulation_completed": run.returncode == 0 and len(parsed) == len(deltas),
        "return_code": run.returncode,
        "common_mode_v": common_mode,
        "bias_n_v": bias_n,
        "bias_p_v": bias_p,
        "ota_input_width_um": input_width_um,
        "temperature_c": temperature_c,
        "mos_corner": corner,
        "scope": "DC schematic OTA with selected MOS process corner/temperature and ideal fixed bias; typical passive R/C, 1Meg output load; no transient sampling, noise, mismatch, complete PVT, or physical layout",
        "points": rows,
    }
    (RES / f"sky130_sc_ota_diff_sensitivity_{tag}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
