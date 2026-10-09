"""Measure read loading of a transistor sensor on the extracted MOS state pair."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RESULTS = OUT / "results"
PAIR = "mos_gate_state_pair_100x10_nf10"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
PDK = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A"
TAG = "sky130_mos_pair_sensor_loading_tt_30uv_5ms"

DECK = f'''* PEX MOS state-pair hold with and without the differential input sensor
.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2 gmin=1e-12
.temp 27
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../layout/sky130_mos_gate_state_pair_100x10_nf10/{PAIR}.spice"
.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
.subckt transmission_gate_pex a b en enb vdd vss
Xpex a b en enb vdd vss sky130_transmission_gate_raw
.ends transmission_gate_pex
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vinitp initp 0 0.900015
Vinitn initn 0 0.899985
Vinitrp initrp 0 0.9
Vinitrn initrn 0 0.9
Vinitup initup 0 0.900015
Vinitun initun 0 0.899985
Von on 0 PWL(0 1.8 0.9u 1.8 1u 0 5.1m 0)
Voff off 0 PWL(0 0 0.9u 0 1u 1.8 5.1m 1.8)
Xswp initp statep on off vdd 0 transmission_gate_pex
Xswn initn staten on off vdd 0 transmission_gate_pex
Xswpr initrp refp on off vdd 0 transmission_gate_pex
Xswnr initrn refn on off vdd 0 transmission_gate_pex
Xswup initup unloadedp on off vdd 0 transmission_gate_pex
Xswun initun unloadedn on off vdd 0 transmission_gate_pex
Xstate statep staten vcm 0 {PAIR}
Xreference refp refn vcm 0 {PAIR}
Xunloaded unloadedp unloadedn vcm 0 {PAIR}
Vtail tailbias 0 0.70
Xn1 outp statep tail 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xn2 outn staten tail 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xt tail tailbias 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2
Xp1 outp outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Xp2 outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Vtailr tailbiasr 0 0.70
Xrn1 refoutp refp tailr 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xrn2 refoutn refn tailr 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xrt tailr tailbiasr 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2
Xrp1 refoutp refoutp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Xrp2 refoutn refoutp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Rrlp refoutp 0 100k
Rrln refoutn 0 100k
Rlp outp 0 100k
Rln outn 0 100k
.control
set numdgt=15
tran 5u 5.1m 0 5u
let state_diff=v(statep)-v(staten)
let ref_diff=v(refp)-v(refn)
let unloaded_diff=v(unloadedp)-v(unloadedn)
let sense_diff=v(outn)-v(outp)
let zero_sense_diff=v(refoutn)-v(refoutp)
meas tran state_start find state_diff at=1.1u
meas tran state_end find state_diff at=5m
meas tran ref_start find ref_diff at=1.1u
meas tran ref_end find ref_diff at=5m
meas tran unloaded_start find unloaded_diff at=1.1u
meas tran unloaded_end find unloaded_diff at=5m
meas tran sense_start find sense_diff at=1.1u
meas tran sense_end find sense_diff at=5m
meas tran zero_sense_start find zero_sense_diff at=1.1u
meas tran zero_sense_end find zero_sense_diff at=5m
quit
.endc
.end
'''


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"{TAG}.cir"
    deck.write_text(DECK, encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "300", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=330)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{TAG}.log").write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(state_start|state_end|ref_start|ref_end|unloaded_start|unloaded_end|sense_start|sense_end|zero_sense_start|zero_sense_end)\s*=\s*([-+0-9.eE]+)", log)}
    required = {"state_start", "state_end", "ref_start", "ref_end", "unloaded_start", "unloaded_end", "sense_start", "sense_end",
                "zero_sense_start", "zero_sense_end"}
    if proc.returncode or "ngspice-36 done" not in log or set(values) != required:
        raise RuntimeError(f"MOS pair sensor-load simulation failed:\n{log[-5000:]}")
    state_drift = values["state_end"] - values["state_start"]
    ref_drift = values["unloaded_end"] - values["unloaded_start"]
    report = {"test": TAG, "corner": "tt", "temperature_c": 27,
              "state_storage_layout": PAIR, "state_differential_initial_v": 30e-6,
              "access_and_reference_switches": "extracted-layout SKY130 TG PEX",
              "sensor": "10/1um NMOS differential pair, 10/2um tail, 20/1um PMOS mirror, ideal 0.7V tail bias",
              "simulation_completed": True,
              "state_diff_start_v": values["state_start"], "state_diff_end_v": values["state_end"],
              "state_drift_with_sensor_v": state_drift,
              "reference_diff_start_v": values["ref_start"], "reference_diff_end_v": values["ref_end"],
              "state_drift_without_sensor_v": ref_drift,
              "excess_sensor_read_disturbance_v": state_drift-ref_drift,
              "zero_state_reference_differential_start_v": values["ref_start"],
              "zero_state_reference_differential_end_v": values["ref_end"],
              "sensor_output_start_v": values["sense_start"], "sensor_output_end_v": values["sense_end"],
              "zero_state_sensor_output_start_v": values["zero_sense_start"],
              "zero_state_sensor_output_end_v": values["zero_sense_end"],
              "30uv_state_minus_zero_state_sensor_output_v": values["sense_start"]-values["zero_sense_start"],
              "limitations": ["one nominal TT state point", "ideal initialization and tail bias",
                              "no latch, offset trim, mismatch or transient noise",
                              "TG PEX includes capacitance but not extracted wire resistance",
                              "no full-float or full-population service"]}
    (RESULTS / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
