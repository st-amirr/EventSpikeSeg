"""Compare independent and shared-bridge precharge on the extracted MOS pair."""
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
TAG = "sky130_mos_pair_correlated_reset_clamp_last_ss0"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"

DECK = f'''* Common-mode shared reset bridge compared with two independent reset TGs
.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2 gmin=1e-12
.temp 0
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../layout/sky130_mos_gate_state_pair_100x10_nf10/{PAIR}.spice"
.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
.subckt tgpex a b en enb vdd vss
Xraw a b en enb vdd vss sky130_transmission_gate_raw
.ends tgpex
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vinitp initp 0 0.95
Vinitn initn 0 0.85
Vwr wr 0 PWL(0 1.8 0.99u 1.8 1u 0 5.1m 0)
Vwrb wrb 0 PWL(0 0 0.99u 0 1u 1.8 5.1m 1.8)
* Shared-reset candidate: both rails shorted while a common VCM clamp is on.
Vrst rst 0 PWL(0 0 10u 0 10.01u 1.8 120u 1.8 120.01u 0 5.1m 0)
Vrstb rstb 0 PWL(0 1.8 10u 1.8 10.01u 0 120u 0 120.01u 1.8 5.1m 1.8)
Vshare share 0 PWL(0 0 10u 0 10.01u 1.8 100u 1.8 100.01u 0 5.1m 0)
Vshareb shareb 0 PWL(0 1.8 10u 1.8 10.01u 0 100u 0 100.01u 1.8 5.1m 1.8)
Xwsp initp sp wr wrb vdd 0 tgpex
Xwsn initn sn wr wrb vdd 0 tgpex
Xclsp sp vcm rst rstb vdd 0 tgpex
Xclsn sn vcm rst rstb vdd 0 tgpex
Xbridge sp sn share shareb vdd 0 tgpex
Xshared sp sn vcm 0 {PAIR}
* Reference: separate reset TGs, no inter-rail equalization switch.
Xwrp initp rp wr wrb vdd 0 tgpex
Xwrn initn rn wr wrb vdd 0 tgpex
Xclr_p rp vcm rst rstb vdd 0 tgpex
Xclr_n rn vcm rst rstb vdd 0 tgpex
Xindependent rp rn vcm 0 {PAIR}
.control
set numdgt=15
tran 5u 5.1m 0 5u
let dshared=v(sp)-v(sn)
let dind=v(rp)-v(rn)
meas tran shared_before find dshared at=5u
meas tran ind_before find dind at=5u
meas tran shared_clamped find dshared at=109u
meas tran ind_clamped find dind at=109u
meas tran shared_after find dshared at=115u
meas tran ind_after find dind at=125u
meas tran shared_5ms find dshared at=5m
meas tran ind_5ms find dind at=5m
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
    names = ("shared_before", "ind_before", "shared_clamped", "ind_clamped", "shared_after",
             "ind_after", "shared_5ms", "ind_5ms")
    values = {k.lower(): float(v) for k, v in re.findall(
        rf"(?im)^\s*({'|'.join(names)})\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(values) != set(names):
        raise RuntimeError(f"MOS shared reset simulation failed:\n{log[-5000:]}")
    shared_kick = values["shared_after"]
    ind_kick = values["ind_after"]
    report = {"test": TAG, "corner": "ss", "temperature_c": 0,
              "state_storage_layout": PAIR,
              "reset_sequence": "short state rails; clamp both to VCM; release bridge while clamps remain on; then release VCM TGs",
              "comparison": "two independent VCM reset TGs without rail bridge",
              "access_switches": "extracted-layout SKY130 TG capacitance PEX, no extracted wire resistance",
              "simulation_completed": True,
              "measurements_v": values,
              "differential_residual_after_reset_v": {"shared_bridge": shared_kick, "independent": ind_kick},
              "shared_bridge_improvement_ratio": abs(ind_kick/shared_kick) if shared_kick else None,
              "limitations": ["deterministic transistor transient; no transient noise or mismatch",
                              "ideal VCM and reset timing", "event injector and state sensor absent",
                              "does not establish achievable common-mode reset-noise correlation"]}
    (RESULTS / f"{TAG}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

