"""Check loading of a differential MOS sensor on an extracted MIM state pair."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches/diff_sensor_probe"
RESULTS = OUT / "results"
TAG = "sky130_diff_sensor_mim_hold_5ms"
CAP_CELL = "membrane_state_mim_m3_2_w30_l30_m12"

DECK = f'''* Differential MOS sense-pair loading on extracted MIM storage
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice"
.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
.include "/workspace/artifacts/analog_asic/benches/mim_large_probe/{CAP_CELL}.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vinitp initp 0 0.900015
Vinitn initn 0 0.899985
Vinitpr initpr 0 0.900015
Vinitnr initnr 0 0.899985
Ven en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)
Venb enb 0 PWL(0 0 0.9u 0 1u 1.8 5.01m 1.8)
Xcap_p statep vcm {CAP_CELL}
Xcap_n staten vcm {CAP_CELL}
Xcap_rp refp vcm {CAP_CELL}
Xcap_rn refn vcm {CAP_CELL}
Xinitpn initp en statep 0 sky130_fd_pr__nfet_01v8 w=2 l=0.15
Xinitpp initp enb statep vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15
Xinitnn initn en staten 0 sky130_fd_pr__nfet_01v8 w=2 l=0.15
Xinitnp initn enb staten vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15
Xinitrpn initpr en refp 0 sky130_fd_pr__nfet_01v8 w=2 l=0.15
Xinitrpp initpr enb refp vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15
Xinitrnn initnr en refn 0 sky130_fd_pr__nfet_01v8 w=2 l=0.15
Xinitrnp initnr enb refn vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15
Vtail tailbias 0 0.70
Xn1 outp statep tail 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xn2 outn staten tail 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xt tail tailbias 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2
Xp1 outp outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Xp2 outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Rlp outp 0 100k
Rln outn 0 100k
.control
set noaskquit
tran 10u 5m
let sens_diff = v(statep)-v(staten)
let ref_diff = v(refp)-v(refn)
let sense_out = v(outn)-v(outp)
meas tran sens_diff_start FIND sens_diff AT=2u
meas tran sens_diff_end FIND sens_diff AT=5m
meas tran ref_diff_start FIND ref_diff AT=2u
meas tran ref_diff_end FIND ref_diff AT=5m
meas tran sense_out_start FIND sense_out AT=2u
meas tran sense_out_end FIND sense_out AT=5m
quit
.endc
.end
'''


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"{TAG}.cir"
    deck.write_text(DECK, encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2",
               "-v", f"{ROOT}:/workspace", "-w",
               "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
               "--entrypoint", "ngspice", "eventspikeseg:analog-ngspice36", "-b",
               f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=300, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{TAG}.log").write_text(log, encoding="utf-8")
    if proc.returncode or "ngspice-36 done" not in log:
        raise RuntimeError(f"Sensor/storage transient failed:\n{log[-5000:]}")
    values = {k.lower(): float(v) for k, v in re.findall(
        r"^(sens_diff_start|sens_diff_end|ref_diff_start|ref_diff_end|sense_out_start|sense_out_end)\s*=\s*([-+0-9.eE]+)",
        log, re.I | re.M)}
    required = ("sens_diff_start", "sens_diff_end", "ref_diff_start", "ref_diff_end",
                "sense_out_start", "sense_out_end")
    if any(k not in values for k in required):
        raise RuntimeError(f"Missing hold metrics {required}; got {values}; log:\n{log[-5000:]}")
    s_delta = values["sens_diff_end"] - values["sens_diff_start"]
    r_delta = values["ref_diff_end"] - values["ref_diff_start"]
    report = {"test": "sky130_differential_pair_state_loading", "corner": "tt",
              "temperature_c": 27, "state_storage": "two extracted 12x30x30um M3_2 banks",
              "initial_differential_v": 30e-6, "simulation_completed": True,
              "sensor_state_differential_start_v": values["sens_diff_start"],
              "sensor_state_differential_end_v": values["sens_diff_end"],
              "sensor_state_drift_v": s_delta,
              "unloaded_reference_differential_start_v": values["ref_diff_start"],
              "unloaded_reference_differential_end_v": values["ref_diff_end"],
              "unloaded_reference_drift_v": r_delta,
              "excess_drift_due_to_sensor_v": s_delta - r_delta,
              "sensor_output_differential_start_v": values["sense_out_start"],
              "sensor_output_differential_end_v": values["sense_out_end"],
              "limitations": ["ideal 30uV programmed starting differential",
                              "nominal TT only; no mismatch or noise",
                              "sensor is open-loop and has no latch or bias feedback",
                              "switches are schematic-only, not extracted layout"]}
    (RESULTS / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
