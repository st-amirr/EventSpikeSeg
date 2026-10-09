"""Bounded TT DC screen for a transistor-level NMOS differential state sensor.

This measures open-loop transfer only. State sources are ideal; there is no
physical latch, mismatch/noise analysis, feedback, or retained-state loading.
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
CORNER = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--corner=")), "tt")
TEMP = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--temp=")), "27"))
MISMATCH_PCT = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                           if arg.startswith("--input-mismatch-pct=")), "0"))
VCM = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                 if arg.startswith("--vcm=")), "0.9"))
if CORNER not in ("ss", "tt", "ff"):
    raise ValueError("--corner must be ss, tt or ff")
if not 0.6 <= VCM <= 1.2:
    raise ValueError("--vcm must be within the screened 0.6–1.2V state range")
TAG = f"sky130_diff_sensor_dc_{CORNER}_temp{TEMP}_mismatch{MISMATCH_PCT:g}pct"
if VCM != 0.9:
    TAG += f"_vcm{VCM:g}"

DECK = f'''* Open-loop differential state sensor: {CORNER.upper()}/{TEMP}C DC transfer
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice"
.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" {CORNER}
.temp {TEMP}
Vdd vdd 0 1.8
Vinp inp 0 {VCM-0.0005:.9g}
Vinn inn 0 {VCM:.9g}
Vtail tailbias 0 0.70
* NMOS input pair; PMOS current-mirror load; shared NMOS tail.
Xn1 outp inp tail 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xn2 outn inn tail 0 sky130_fd_pr__nfet_01v8 w={10*(1+MISMATCH_PCT/100):.6g} l=1
Xt tail tailbias 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2
Xp1 outp outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Xp2 outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Rlp outp 0 100k
Rln outn 0 100k
.control
set noaskquit
dc Vinp {VCM-0.0005:.9g} {VCM+0.0005:.9g} 0.5u
let vdiff = v(outn)-v(outp)
meas dc outdiff_m6 FIND vdiff AT={VCM-6e-6:.9g}
meas dc outdiff_m3 FIND vdiff AT={VCM-3e-6:.9g}
meas dc outdiff_0 FIND vdiff AT={VCM:.9g}
meas dc outdiff_p3 FIND vdiff AT={VCM+3e-6:.9g}
meas dc outdiff_p6 FIND vdiff AT={VCM+6e-6:.9g}
meas dc outdiff_m30 FIND vdiff AT={VCM-30e-6:.9g}
meas dc outdiff_p30 FIND vdiff AT={VCM+30e-6:.9g}
meas dc tail_v FIND v(tail) AT={VCM:.9g}
meas dc outp_v FIND v(outp) AT={VCM:.9g}
meas dc outn_v FIND v(outn) AT={VCM:.9g}
quit
.endc
.end
'''


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"{TAG}.cir"
    deck.write_text(DECK, encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
               "-v", f"{ROOT}:/workspace", "-w",
               "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
               "--entrypoint", "ngspice", "eventspikeseg:analog-ngspice36", "-b",
               f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=180, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{TAG}.log").write_text(log, encoding="utf-8")
    if proc.returncode or "ngspice-36 done" not in log:
        raise RuntimeError(f"Differential sensor DC screen failed:\n{log[-5000:]}")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"^(outdiff_[a-z0-9]+|tail_v|outp_v|outn_v)\s*=\s*([-+0-9.eE]+)",
        log, re.I | re.M)}
    required = ("outdiff_m6", "outdiff_m3", "outdiff_0", "outdiff_p3", "outdiff_p6",
                "outdiff_m30", "outdiff_p30", "tail_v", "outp_v", "outn_v")
    if any(key not in values for key in required):
        raise RuntimeError(f"Missing DC measurements {required}; got {values}; log:\n{log[-5000:]}")
    base = values["outdiff_0"]
    report = {"test": "sky130_nmos_differential_state_sensor_open_loop_dc",
              "corner": CORNER, "temperature_c": TEMP, "input_common_mode_v": VCM,
              "input_device_um": {"n1_w": 10, "n2_w": 10*(1+MISMATCH_PCT/100), "l": 1},
              "tail_device_um": {"w": 10, "l": 2},
              "tail_bias_v": 0.7, "tail_node_v": values["tail_v"],
              "outputs_at_zero_diff_v": {"outp": values["outp_v"], "outn": values["outn_v"]},
              "zero_diff_output_mismatch_v": base,
              "input_referred_offset_estimate_v": -base / ((values["outdiff_p3"] - values["outdiff_m3"]) / 6e-6),
              "input_device_width_perturbation_pct": MISMATCH_PCT,
              "differential_response": {
                  "minus_3uV_v": values["outdiff_m3"] - base,
                  "plus_3uV_v": values["outdiff_p3"] - base,
                  "minus_6uV_v": values["outdiff_m6"] - base,
                  "plus_6uV_v": values["outdiff_p6"] - base,
                  "minus_30uV_v": values["outdiff_m30"] - base,
                  "plus_30uV_v": values["outdiff_p30"] - base,
                  "local_gain_6uV_v_per_v": (values["outdiff_p3"] - values["outdiff_m3"]) / 6e-6,
                  "local_gain_60uV_v_per_v": (values["outdiff_p30"] - values["outdiff_m30"]) / 60e-6},
              "simulation_completed": True,
              "limitations": ["ideal input voltage sources", "no state capacitor loading",
                              "no mismatch or noise", "no latch, feedback or physical bias DAC",
                              "DC only; no retention or transient settling"]}
    (RESULTS / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
