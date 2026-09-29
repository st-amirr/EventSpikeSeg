"""Screen a continuously connected SKY130 OTA on a 20um differential MIM state pair."""
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


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deltas_uv = (0.0, 0.1, -0.1, 1.0, -1.0, 3.0, -3.0, 6.0, -6.0)
    cm = 0.918
    physical_init = '--physical-init' in sys.argv[1:]
    tag = 'tg_init' if physical_init else 'ic_init'
    lines = [
        "SKY130 TT differential MIM state with continuously connected OTA input",
        ".option scale=1u",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        '.include "../../../asic/analog/modules.spice"',
        '.include "../../../asic/analog/sky130_ms_plif.spice"',
        '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbn vbnn 0 0.65", "Vbp vbpp 0 0.75",
    ]
    for i, delta_uv in enumerate(deltas_uv):
        delta = delta_uv * 1e-6
        vp, vn = f"vp{i}", f"vn{i}"
        lines += [
            f"Xmem_p{i} {vp} vcm membrane_mim w_um=20 l_um=20",
            f"Xmem_n{i} {vn} vcm membrane_mim w_um=20 l_um=20",
            f"Rload{i} out{i} vcm 1Meg",
            f"Xota{i} {vp} {vn} out{i} vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
        ]
        if physical_init:
            lines += [
                f"Vinitp{i} initp{i} 0 {cm + delta/2:.12f}",
                f"Vinitn{i} initn{i} 0 {cm - delta/2:.12f}",
                f"Vinit_en{i} init_en{i} 0 PWL(0 1.8 20u 1.8 20.0001u 0 5m 0)",
                f"Vinit_enb{i} init_enb{i} 0 PWL(0 0 20u 0 20.0001u 1.8 5m 1.8)",
                f"Xinitp{i} initp{i} {vp} init_en{i} init_enb{i} vdd 0 transmission_gate",
                f"Xinitn{i} initn{i} {vn} init_en{i} init_enb{i} vdd 0 transmission_gate",
            ]
        else:
            lines += [f".ic v({vp})={cm + delta/2:.12f}",
                      f".ic v({vn})={cm - delta/2:.12f}",
                      f".ic v(xmem_p{i}.xmim.a)={cm + delta/2:.12f}",
                      f".ic v(xmem_n{i}.xmim.a)={cm - delta/2:.12f}"]
    lines += [".control", "set numdgt=15", "tran 50n 5m uic"]
    for i in range(len(deltas_uv)):
        lines += [
            f"let diff{i}=v(vp{i})-v(vn{i})",
            f"meas tran initial_diff{i} find diff{i} at=1n",
            f"meas tran us1_diff{i} find diff{i} at=1u",
            f"meas tran us10_diff{i} find diff{i} at=10u",
            f"meas tran preoff_diff{i} find diff{i} at=19.9u",
            f"meas tran postoff_diff{i} find diff{i} at=20.1u",
            f"meas tran start_diff{i} find diff{i} at=100u",
            f"meas tran end_diff{i} find diff{i} at=4.9m",
            f"meas tran start_out{i} find v(out{i}) at=100u",
            f"meas tran end_out{i} find v(out{i}) at=4.9m",
        ]
    lines += ["quit", ".endc", ".end"]
    deck = BENCH / f"sky130_ms_diff_ota_state_hold_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "180", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=195)
    log = run.stdout + run.stderr
    (RES / f"sky130_ms_diff_ota_state_hold_{tag}.log").write_text(log, encoding="utf-8")
    found = {(phase, metric, int(i)): float(v) for phase, metric, i, v in re.findall(
        r"(?im)^\s*(initial|us1|us10|preoff|postoff|start|end)_(diff|out)(\d+)\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and len(found) == 9 * len(deltas_uv)
    rows = []
    if complete:
        for i, delta_uv in enumerate(deltas_uv):
            rows.append({"initial_differential_uv": delta_uv,
                         "at_1ns_differential_uv": found["initial", "diff", i] * 1e6,
                         "at_1us_differential_uv": found["us1", "diff", i] * 1e6,
                         "at_10us_differential_uv": found["us10", "diff", i] * 1e6,
                         "before_tg_disconnect_differential_uv": found["preoff", "diff", i] * 1e6,
                         "after_tg_disconnect_differential_uv": found["postoff", "diff", i] * 1e6,
                         "start_differential_uv": found["start", "diff", i] * 1e6,
                         "end_differential_uv": found["end", "diff", i] * 1e6,
                         "start_output_v": found["start", "out", i],
                         "end_output_v": found["end", "out", i],
                         "end_output_relative_to_zero_v": found["end", "out", i] - found["end", "out", 0]})
    report = {"test": "sky130_tt_20um_diff_mim_continuous_ota_state_hold",
              "simulation_completed": complete, "return_code": run.returncode,
              "initial_common_mode_v": cm, "hold_ms": 5.0, "physical_tg_initialization": physical_init, "cases": rows,
              "scope": "Nominal SKY130 TT schematic; direct continuously connected OTA gate load on both 20um MIM states, ideal OTA bias, and either .ic or 20us physical TG initialization. No threshold DAC/comparator decision, noise, mismatch, PVT, extraction or full network."}
    path = RES / f"sky130_ms_diff_ota_state_hold_{tag}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
