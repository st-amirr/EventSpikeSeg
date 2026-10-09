"""Apply SKY130's published 1-sigma Vth mismatch slope to a sensor pair.

The stock PDK annotations are Spectre ``vary`` directives and ngspice leaves
them at zero. This script clones the PDK TT model subcircuit twice, gives each
input device an independent +1/-1 sigma slope realization, and measures the
resulting open-loop input crossing. This is a deterministic +/-1 sigma pair,
not a Monte Carlo yield run.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches/diff_sensor_probe"
RESULTS = OUT / "results"
SWAP = "--swap" in sys.argv[1:]
TAG = "sky130_diff_sensor_vth_mismatch_1sigma_tt" + ("_swapped" if SWAP else "")
PDK_MODEL = (ROOT / "artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/"
             "sky130_fd_pr__nfet_01v8__tt.pm3.spice")


def make_variant(source: str, suffix: str, sigma: int) -> str:
    device = "sky130_fd_pr__nfet_01v8"
    slope = f"{device}__vth0_slope_spectre"
    variant = f"{device}__vth0_sigma_{suffix}"
    model = f"{device}__model"
    out_model = f"{device}__sigma_{suffix}__model"
    text = re.sub(rf"\.subckt\s+{re.escape(device)}\s+d g s b",
                  f".subckt nfet_vthsigma_{suffix} d g s b", source, count=1)
    text = text.replace(slope, variant)
    text = re.sub(rf"(\.param\s+{re.escape(variant)}\s*=\s*)0\.0\b",
                  rf"\g<1>{sigma}.0", text, count=1)
    text = text.replace(model, out_model)
    if f".subckt nfet_vthsigma_{suffix} d g s b" not in text:
        raise RuntimeError("Failed to rename the PDK input-device wrapper")
    if f"{variant} = {sigma}.0" not in text:
        raise RuntimeError("Failed to set the independent PDK mismatch variable")
    return text


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    source = PDK_MODEL.read_text(encoding="ascii")
    plus = make_variant(source, "plus", +1)
    minus = make_variant(source, "minus", -1)
    (BENCH / "nfet_vthsigma_plus.spice").write_text(plus, encoding="ascii")
    (BENCH / "nfet_vthsigma_minus.spice").write_text(minus, encoding="ascii")
    first_model, second_model = (("minus", "plus") if SWAP else ("plus", "minus"))
    first_sigma, second_sigma = ((-1, 1) if SWAP else (1, -1))
    deck = f'''* PDK 1-sigma threshold-mismatch pair, SKY130 TT/27C
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice"
.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
.include "/workspace/artifacts/analog_asic/benches/diff_sensor_probe/nfet_vthsigma_plus.spice"
.include "/workspace/artifacts/analog_asic/benches/diff_sensor_probe/nfet_vthsigma_minus.spice"
Vdd vdd 0 1.8
Vinp inp 0 0.8995
Vinn inn 0 0.9
Vtail tailbias 0 0.70
Xn1 outp inp tail 0 nfet_vthsigma_{first_model} w=10 l=1
Xn2 outn inn tail 0 nfet_vthsigma_{second_model} w=10 l=1
Xt tail tailbias 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2
Xp1 outp outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Xp2 outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Rlp outp 0 100k
Rln outn 0 100k
.control
set noaskquit
dc Vinp 0.8995 0.9005 0.5u
let vdiff = v(outn)-v(outp)
meas dc outdiff_0 FIND vdiff AT=0.9
meas dc outdiff_m30 FIND vdiff AT=0.899970
meas dc outdiff_p30 FIND vdiff AT=0.900030
meas dc outdiff_m100 FIND vdiff AT=0.899900
meas dc outdiff_p100 FIND vdiff AT=0.900100
quit
.endc
.end
'''
    path = BENCH / f"{TAG}.cir"
    path.write_text(deck, encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2",
               "-v", f"{ROOT}:/workspace", "-w",
               "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
               "--entrypoint", "ngspice", "eventspikeseg:analog-ngspice36", "-b",
               f"/workspace/{path.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=240, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{TAG}.log").write_text(log, encoding="utf-8")
    if proc.returncode or "ngspice-36 done" not in log:
        raise RuntimeError(f"PDK mismatch run failed:\n{log[-6000:]}")
    values = {k.lower(): float(v) for k, v in re.findall(
        r"^(outdiff_[a-z0-9]+)\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}
    required = ("outdiff_0", "outdiff_m30", "outdiff_p30", "outdiff_m100", "outdiff_p100")
    if any(key not in values for key in required):
        raise RuntimeError(f"Missing mismatch metrics; got {values}; log:\n{log[-4000:]}")
    gain = (values["outdiff_p30"] - values["outdiff_m30"]) / 60e-6
    report = {"test": "sky130_differential_sensor_PDK_vth_mismatch_sensitivity",
              "corner": "tt", "temperature_c": 27,
              "realization": {"input_1_vth_slope_sigma": first_sigma,
                              "input_2_vth_slope_sigma": second_sigma,
                              "coefficient_source": "SKY130 nfet_01v8 mismatch.corner.spice"},
              "output_diff_at_zero_input_diff_v": values["outdiff_0"],
              "local_gain_v_per_v": gain,
              "input_referred_zero_crossing_v": -values["outdiff_0"] / gain,
              "response_at_pm30uv_v": [values["outdiff_m30"], values["outdiff_p30"]],
              "response_at_pm100uv_v": [values["outdiff_m100"], values["outdiff_p100"]],
              "simulation_completed": True,
              "limitations": ["deterministic paired +/-1-sigma threshold slopes, not Monte Carlo",
                              "only input NFET Vth variation included",
                              "no correlated spatial variation or capacitor mismatch",
                              "open-loop DC only; no offset trim, noise or latch"]}
    (RESULTS / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
