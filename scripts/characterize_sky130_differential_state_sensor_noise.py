"""Small-signal noise estimate for the SKY130 differential sensor schematic."""
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
FMAX = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--fmax-hz=")), "1Meg")
CORNER = next((arg.split("=", 1)[1].lower() for arg in sys.argv[1:] if arg.startswith("--corner=")), "tt")
TEMP = {"ss": 0, "tt": 27, "ff": 85}.get(CORNER)
if TEMP is None:
    raise ValueError("--corner must be ss, tt or ff")
if FMAX not in ("1k", "10k", "100k", "1Meg"):
    raise ValueError("--fmax-hz must be 1k, 10k, 100k or 1Meg")
SIZE = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--input-size-scale=")), "1"))
INPUT_W_UM = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--input-w-um=")), "10"))
if not 0.42 <= INPUT_W_UM <= 10:
    raise ValueError("--input-w-um must be within 0.42..10")
if SIZE < 1 or SIZE > 100:
    raise ValueError("input-size scale must be within 1..100")
if not SIZE.is_integer():
    raise ValueError("parallel input-device count must be an integer")
NPAIR = int(SIZE)
TAG = f"sky130_diff_sensor_noise_{CORNER}_{FMAX.lower()}_size{SIZE:g}"
if INPUT_W_UM != 10:
    TAG += f"_inputw{INPUT_W_UM:g}um"
DECK = f'''* Differential state sensor small-signal noise at TT/27C
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice"
.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" {CORNER}
.temp {TEMP}
Vdd vdd 0 1.8
Vinp inp 0 dc 0.9 ac 1
Vinn inn 0 dc 0.9
Vtail tailbias 0 0.70
{chr(10).join(f'Xn1_{i} outp inp tail 0 sky130_fd_pr__nfet_01v8 w={INPUT_W_UM:g} l=1' for i in range(NPAIR))}
{chr(10).join(f'Xn2_{i} outn inn tail 0 sky130_fd_pr__nfet_01v8 w={INPUT_W_UM:g} l=1' for i in range(NPAIR))}
Xt tail tailbias 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2
{chr(10).join(f'Xp1_{i} outp outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1' for i in range(NPAIR))}
{chr(10).join(f'Xp2_{i} outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1' for i in range(NPAIR))}
Rlp outp 0 100k
Rln outn 0 100k
.control
set noaskquit
noise v(outn,outp) Vinp dec 20 10 {FMAX}
print onoise_total
print inoise_total
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
        raise RuntimeError(f"Noise analysis failed:\n{log[-5000:]}")
    def measured(pattern: str) -> float:
        match = re.search(pattern, log, re.I | re.M)
        if not match:
            raise RuntimeError(f"Missing noise result {pattern!r}:\n{log[-5000:]}")
        return float(match.group(1))
    report = {"test": "sky130_differential_sensor_open_loop_noise",
              "corner": CORNER, "temperature_c": TEMP,
              "parallel_input_and_load_devices_per_side": NPAIR,
              "input_device_width_um": INPUT_W_UM,
              "frequency_span_hz": [10, {"1k": 1e3, "10k": 1e4, "100k": 1e5, "1Meg": 1e6}[FMAX]], "points_per_decade": 20,
              "integrated_output_noise_v_rms": measured(r"onoise_total\s*=\s*([-+0-9.eE]+)"),
              "integrated_input_noise_v_rms": measured(r"inoise_total\s*=\s*([-+0-9.eE]+)"),
              "simulation_completed": True,
              "limitations": [f"small-signal noise over an illustrative 10Hz-{FMAX} span",
                              "not a switched latch or sampled-noise analysis",
                              "no mismatch/statistical variation", "no state feedback or trim"]}
    (RESULTS / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
