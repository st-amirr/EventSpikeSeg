"""Measure comparator OTA input offset using SKY130's deterministic +/-1 sigma Vth pair."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from characterize_sky130_sensor_vth_mismatch import PDK_MODEL, make_variant

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches/diff_sensor_probe"
RESULTS = OUT / "results"
SWAP = "--swap" in sys.argv[1:]
TAG = "sky130_sc_ota_vth_offset_1sigma_tt" + ("_swapped" if SWAP else "")
ARGS = sys.argv[1:]
CENTER_MV = float(next((a.split("=", 1)[1] for a in ARGS if a.startswith("--center-mv=")), "0"))
SPAN_MV = float(next((a.split("=", 1)[1] for a in ARGS if a.startswith("--span-mv=")), "100"))
STEP_UV = float(next((a.split("=", 1)[1] for a in ARGS if a.startswith("--step-uv=")), "10"))
COMMON_MODE_V = float(next((a.split("=", 1)[1] for a in ARGS if a.startswith("--common-mode-v=")), "0.9"))
if CENTER_MV or SPAN_MV != 100 or STEP_UV != 10:
    TAG += f"_c{CENTER_MV:g}m_s{SPAN_MV:g}m_d{STEP_UV:g}u".replace(".", "p")
if COMMON_MODE_V != 0.9:
    TAG += f"_cm{COMMON_MODE_V:g}v".replace(".", "p")


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    source = PDK_MODEL.read_text(encoding="ascii")
    sigma_plus, sigma_minus = ((-1, 1) if SWAP else (1, -1))
    (BENCH / "nfet_vthsigma_plus.spice").write_text(make_variant(source, "plus", sigma_plus), encoding="ascii")
    (BENCH / "nfet_vthsigma_minus.spice").write_text(make_variant(source, "minus", sigma_minus), encoding="ascii")
    deck_text = f'''* SKY130 comparator OTA +/-1 sigma input NFET threshold realization
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice"
.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
.include "diff_sensor_probe/nfet_vthsigma_plus.spice"
.include "diff_sensor_probe/nfet_vthsigma_minus.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 {COMMON_MODE_V:g}
Vbn vbiasn 0 0.65
Vbp vbiasp 0 0.75
Vdelta delta 0 0
Binp inp 0 V={{v(vcm)+v(delta)*0.5}}
Binn inn 0 V={{v(vcm)-v(delta)*0.5}}
Xota inp inn out vbiasn vbiasp vdd 0 sky130_sc_ota_vthsigma win=0.5 wn3=2 wp3=27.8 cc=100f
Rout out vcm 1Meg
.subckt sky130_sc_ota_vthsigma inp inn out vbiasn vbiasp vdd vss
+ params: win=10 wload=20 wtail=4 wn3=20 wp3=20 cc=500f
Xn1 n1 inp ntail vss nfet_vthsigma_plus w={{win}} l=1
Xn2 n2 inn ntail vss nfet_vthsigma_minus w={{win}} l=1
Xntail ntail vbiasn vss vss sky130_fd_pr__nfet_01v8 w={{wtail}} l=2
Xp1 n1 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={{wload}} l=1
Xp2 n2 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={{wload}} l=1
Xn3 out n2 vss vss sky130_fd_pr__nfet_01v8 w={{wn3}} l=0.5
Xp3 out vbiasp vdd vdd sky130_fd_pr__pfet_01v8 w={{wp3}} l=0.5
Ccomp n2 out {{cc}}
.ends sky130_sc_ota_vthsigma
.control
set wr_singlescale
set wr_vecnames
dc Vdelta {CENTER_MV*1e-3-SPAN_MV*1e-3:g} {CENTER_MV*1e-3+SPAN_MV*1e-3:g} {STEP_UV:g}u
let outdiff=v(out)-v(vcm)
wrdata ../results/{TAG}.dat v(delta) outdiff
quit
.endc
.end
'''
    deck = OUT / "benches" / f"{TAG}.cir"
    deck.write_text(deck_text, encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
           "-w", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "ngspice",
           "eventspikeseg:analog-ngspice36", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=240, cwd=ROOT)
    log = run.stdout + run.stderr
    (RESULTS / f"{TAG}.log").write_text(log, encoding="utf-8")
    dat = RESULTS / f"{TAG}.dat"
    rows: list[tuple[float, float]] = []
    if dat.exists():
        for line in dat.read_text(encoding="ascii").splitlines()[1:]:
            try:
                _, delta, outdiff = map(float, line.split())
                rows.append((delta, outdiff))
            except ValueError:
                pass
    crossing = None
    if rows:
        crossing = min(rows, key=lambda p: abs(p[1]))[0]
    around = []
    if crossing is not None:
        nearest = sorted(rows, key=lambda p: abs(p[0] - crossing))[:21]
        if len(nearest) >= 2:
            nearest.sort()
            lo, hi = nearest[0], nearest[-1]
            gain = (hi[1] - lo[1]) / (hi[0] - lo[0]) if hi[0] != lo[0] else None
            around = [{"input_diff_v": x, "output_diff_v": y} for x, y in nearest]
        else:
            gain = None
    else:
        gain = None
    report = {"test": "sky130_sc_ota_comparator_input_offset_vth_mismatch",
              "corner": "tt", "temperature_c": 27,
              "input_device_width_um": 0.5,
              "realization_sigma_by_device": {"n1": sigma_plus, "n2": sigma_minus},
              "input_common_mode_v": COMMON_MODE_V, "bias_n_v": 0.65, "bias_p_v": 0.75,
              "sweep_range_v": [CENTER_MV*1e-3-SPAN_MV*1e-3, CENTER_MV*1e-3+SPAN_MV*1e-3], "sweep_step_v": STEP_UV*1e-6,
              "output_crossing_input_diff_v_coarse": crossing,
              "local_gain_v_per_v_coarse": gain,
              "points_near_crossing": around,
              "simulation_completed": run.returncode == 0 and len(rows) > 100,
              "return_code": run.returncode,
              "limitations": ["deterministic paired +/-1 sigma PDK Vth slopes, not Monte Carlo",
                              f"input sweep step {STEP_UV:g}uV; no trim-DAC implementation was characterized",
                              "schematic OTA, no switched sample, noise, layout or extraction"]}
    (RESULTS / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
