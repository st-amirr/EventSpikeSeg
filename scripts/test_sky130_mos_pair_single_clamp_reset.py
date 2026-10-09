"""Compare shared one-switch first-touch reset with independent rail clamps."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
PAIR_LAYOUT = "sky130_mos_gate_state_pair_100x10_nf10"
PAIR = PAIR_LAYOUT.removeprefix("sky130_")
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
PDK = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A"


def run(corner: str, temp: int) -> dict[str, object]:
    tag = f"sky130_mos_pair_single_clamp_simul_reset_{corner}_temp{temp}"
    deck_path = OUT / "benches" / f"{tag}.cir"
    deck_path.parent.mkdir(parents=True, exist_ok=True)
    deck = f'''* First-touch zero-state reset using shared rail bridge and one TG clamp
.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2 gmin=1e-12
.temp {temp}
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../layout/{PAIR_LAYOUT}/{PAIR}.spice"
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
Vrst rst 0 PWL(0 0 10u 0 10.01u 1.8 100u 1.8 100.01u 0 5.1m 0)
Vrstb rstb 0 PWL(0 1.8 10u 1.8 10.01u 0 100u 0 100.01u 1.8 5.1m 1.8)
Vshare share 0 PWL(0 0 10u 0 10.01u 1.8 100u 1.8 100.01u 0 5.1m 0)
Vshareb shareb 0 PWL(0 1.8 10u 1.8 10.01u 0 100u 0 100.01u 1.8 5.1m 1.8)
Xwsp initp sp wr wrb vdd 0 tgpex
Xwsn initn sn wr wrb vdd 0 tgpex
* One common reset switch drives both rails while the bridge remains closed.
Xcl_shared sp vcm rst rstb vdd 0 tgpex
Xbridge sp sn share shareb vdd 0 tgpex
Xshared sp sn vcm 0 {PAIR}
* Reference case: one independent reset switch per rail, no bridge.
Xwrp initp rp wr wrb vdd 0 tgpex
Xwrn initn rn wr wrb vdd 0 tgpex
Xclp rp vcm rst rstb vdd 0 tgpex
Xcln rn vcm rst rstb vdd 0 tgpex
Xindependent rp rn vcm 0 {PAIR}
.control
set numdgt=15
tran 1u 5.1m 0 1u
let dshared=v(sp)-v(sn)
let dind=v(rp)-v(rn)
meas tran shared_before find dshared at=5u
meas tran ind_before find dind at=5u
meas tran shared_clamp_hold find dshared at=90u
meas tran ind_clamped find dind at=90u
meas tran shared_after_bridge find dshared at=105u
meas tran ind_after_clamp find dind at=125u
meas tran shared_after_clamp find dshared at=125u
meas tran shared_5ms find dshared at=5m
meas tran ind_5ms find dind at=5m
quit
.endc
.end
'''
    deck_path.write_text(deck, encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck_path.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=135)
    log = proc.stdout + proc.stderr
    result_path = OUT / "results" / f"{tag}.log"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(log, encoding="utf-8")
    names = ("shared_before", "ind_before", "shared_clamp_hold", "ind_clamped",
             "shared_after_bridge", "ind_after_clamp", "shared_after_clamp", "shared_5ms", "ind_5ms")
    vals = {k.lower(): float(v) for k, v in re.findall(
        rf"(?im)^\s*({'|'.join(names)})\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(vals) != set(names):
        raise RuntimeError(f"single-clamp reset transient failed {corner}/{temp}:\n{log[-4000:]}")
    return {"test": tag, "corner": corner, "temperature_c": temp,
            "state_pair_layout": PAIR_LAYOUT, "access_reset_switches": "extracted TG PEX; wire-R not extracted",
            "reset_window_us": [10.01, 100.0], "shared_bridge_release_us": 100.01,
            "sequence": "short rails, clamp one rail through one TG, open bridge and common clamp on matched edges",
            "comparison": "two independent rail TG clamps, no bridge",
            "simulation_completed": True, "measurements_v": vals,
            "limitations": ["deterministic transient; no thermal transient noise or mismatch",
                            "ideal clock edges and VCM supply", "first-touch zero reset only; cannot preserve nonzero subtractive-reset residual",
                            "event injector and sensor absent"]}


def main() -> int:
    rows = [run(corner, temp) for corner, temp in (("tt", 27), ("ss", 0), ("ff", 85))]
    report = {"test": "sky130_mos_pair_single_clamp_first_touch_reset", "rows": rows}
    path = OUT / "results" / "sky130_mos_pair_single_clamp_reset.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
