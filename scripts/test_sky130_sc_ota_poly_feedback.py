"""Check the gain-10 OTA feedback with SKY130 xhigh-poly resistor devices."""
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

HEADER = r"""* SKY130 TT OTA feedback using PDK xhigh-poly resistor devices
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    corner = next((arg.split("=", 1)[1].lower() for arg in sys.argv[1:] if arg.startswith("--corner=")), "tt")
    resistor_corner = next((arg.split("=", 1)[1].lower() for arg in sys.argv[1:] if arg.startswith("--rescorner=")), "typical")
    if corner not in {"tt", "ss", "ff"}:
        raise ValueError("corner must be tt, ss, or ff")
    if resistor_corner not in {"typical", "high", "low"}:
        raise ValueError("rescorner must be typical, high, or low")
    deltas = (0.0, 64e-6, -64e-6, 250e-6, -250e-6, 500e-6, -500e-6)
    # For 1.41um xhigh-poly, nominal sheet resistance is 2kOhm/square.
    # These lengths include an approximate 0.0592um end correction.
    configs = {"gain10": (6.74, 60.97), "gain30": (6.74, 196.73)}
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    suffix = corner if resistor_corner == "typical" else f"{corner}_r{resistor_corner}"
    deck = BENCH / f"sky130_sc_ota_poly_feedback_{suffix}.cir"
    devices: list[str] = []
    outputs: list[str] = []
    mapping: list[tuple[int, float, str]] = []
    index = 0
    for tag, (lg, lf) in configs.items():
        for delta in deltas:
            name = f"d{index}"
            devices += [
                f"Vbn_{name} vbnn_{name} 0 0.65",
                f"Vbp_{name} vbpp_{name} 0 0.75",
                f"Vsignal_{name} signal_{name} 0 {0.9 + delta:.9f}",
                f"Xgain_{name} vcm inp_{name} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={lg:g}",
                f"Xfeedback_{name} out_{name} inp_{name} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={lf:g}",
                f"Rload_{name} out_{name} vcm 1Meg",
                f"Xota_{name} inp_{name} signal_{name} out_{name} vbnn_{name} vbpp_{name} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
            ]
            outputs.append(f"v(out_{name})")
            mapping.append((index, delta, tag))
            index += 1
    corner_header = HEADER.replace("__tt.corner.spice", f"__{corner}.corner.spice")
    if resistor_corner != "typical":
        corner_header = corner_header.replace("res_typical__cap_typical__lin.spice", f"res_{resistor_corner}__cap_{resistor_corner}__lin.spice")
    deck.write_text(corner_header + "\n".join(devices) + "\n.control\nop\nprint " + " ".join(outputs) + "\nquit\n.endc\n.end\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "30", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=40)
    log = run.stdout + run.stderr
    (RES / f"sky130_sc_ota_poly_feedback_{suffix}.log").write_text(log, encoding="utf-8")
    parsed = {int(i): float(v) for i, v in re.findall(r"v\(out_d(\d+)\)\s*=\s*([+\-0-9.eE]+)", log)}
    grouped: dict[str, list[dict[str, float | None]]] = {tag: [] for tag in configs}
    for index, delta, tag in mapping:
        grouped[tag].append({"input_diff_v": delta, "output_v": parsed.get(index)})
    for tag, points in grouped.items():
        base = points[0]["output_v"]
        nominal_gain = int(tag.removeprefix("gain"))
        for point in points:
            output = point["output_v"]
            delta = point["input_diff_v"]
            point["output_change_from_zero_v"] = None if output is None or base is None else output - base
            point["target_gain_change_v"] = nominal_gain * delta
    report = {
        "test": "sky130_tt_ota_xhigh_poly_feedback_gain_screen",
        "simulation_completed": run.returncode == 0 and len(parsed) == len(mapping),
        "return_code": run.returncode,
        "process_corner": corner,
        "resistor_corner": resistor_corner,
        "scope": f"SKY130 {corner.upper()} MOS schematic with xhigh-poly resistor devices, w=1.41um; gain10 lengths 6.74/60.97um; gain30 lengths 6.74/196.73um; resistor corner {resistor_corner}; no mismatch/layout extraction",
        "feedback_gain_sweeps": grouped,
    }
    (RES / f"sky130_sc_ota_poly_feedback_{suffix}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
