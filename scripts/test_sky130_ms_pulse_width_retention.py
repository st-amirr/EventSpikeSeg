"""Bounded 5ms hold check for the SKY130 pulse-duration PLIF channel."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
COMMON = """.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
"""


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 pulse-duration PLIF 5ms retention", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbias vbias 0 0.65",
             "Vcap capture 0 0", "Vcapb capture_b 0 1.8",
             "Vreset reset 0 0", "Vresetb reset_b 0 1.8",
             "Vleak leak_en 0 0", "Vleakb leak_enb 0 1.8",
             "Vpref pgr 0 1.8", "Vnref ngr 0 0",
             "Xref ref snapref spikeref capture capture_b reset reset_b leak_en leak_enb pgr ngr vbias vdd 0 vcm analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100",
             "Vppg ppg 0 PWL(0 1.8 0.099u 1.8 0.1u 1.0 1u 1.0 1.001u 1.8 5.1m 1.8)",
             "Vpng png 0 0",
             "Xpos pstate snapp spikep capture capture_b reset reset_b leak_en leak_enb ppg png vbias vdd 0 vcm analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100",
             "Vnpg npg 0 1.8",
             "Vnng nng 0 PWL(0 0 0.099u 0 0.1u 0.525 1u 0.525 1.001u 0 5.1m 0)",
             "Xneg nstate snapn spiken capture capture_b reset reset_b leak_en leak_enb npg nng vbias vdd 0 vcm analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100",
             ".control", "tran 1u 5.1m uic",
             "meas tran ref_post find v(ref) at=2u", "meas tran ref_end find v(ref) at=5m",
             "meas tran pos_post find v(pstate) at=2u", "meas tran pos_end find v(pstate) at=5m",
             "meas tran neg_post find v(nstate) at=2u", "meas tran neg_end find v(nstate) at=5m",
             "quit", ".endc", ".end"]
    name = "sky130_ms_pulse_width_retention"
    (BENCH / f"{name}.cir").write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", f"{name}.cir"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    log = proc.stdout + proc.stderr
    (RES / f"{name}.log").write_text(log, encoding="utf-8")
    values = {key: float(value) for key, value in re.findall(
        r"^(ref_post|ref_end|pos_post|pos_end|neg_post|neg_end)\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}
    complete = proc.returncode == 0 and len(values) == 6
    rows = {}
    for prefix in ("ref", "pos", "neg"):
        post, end = values.get(f"{prefix}_post"), values.get(f"{prefix}_end")
        rows[prefix] = {
            "post_pulse_v": post,
            "end_5ms_v": end,
            "hold_drift_v": end - post if post is not None and end is not None else None,
        }
    limit_v = 0.003
    drift_pass = complete and all(abs(rows[p]["hold_drift_v"]) <= limit_v for p in rows)
    report = {
        "test": "sky130_tt_pulse_duration_channel_5ms_hold",
        "simulation_completed": complete,
        "exit_code": proc.returncode,
        "hold_interval_s": 0.004998,
        "state_after_pulse_and_hold": rows,
        "max_abs_hold_drift_limit_v": limit_v,
        "hold_pass": bool(drift_pass),
        "scope": "TT transient, three single PLIF channel variants with SKY130 PDK MIM model; one 0.9us pulse per sign; leak/capture disabled; no extracted parasitics or mismatch.",
    }
    (RES / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if drift_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
