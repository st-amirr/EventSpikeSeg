"""Measure physical OTA settling while driving the direct injector MOS gates."""

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
TIMES_US = (0.9, 1.01, 1.05, 1.10, 1.20, 1.50, 2.0, 3.0,
            5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 15.0, 20.0)


def main() -> int:
    stem = "sky130_ms_weight_gate_ota_buffer_settle_ss0_f0p8"
    lines = ["SKY130 SS 0C analog gate OTA buffer transient with injector gate loads",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9", ".temp 0",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"',
             '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbn vbnn 0 0.65", "Vbp vbpp 0 0.733",
             "Vpin pin 0 PWL(0 1.8 1u 1.8 1.0001u 0.936 20.1u 0.936)",
             "Vnin nin 0 PWL(0 0 1u 0 1.0001u 0.48 20.1u 0.48)",
             "Xbuf_p pg pin pg vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
             "Xbuf_n ng nin ng vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
             "Xp_load vcm pg vdd vdd sky130_fd_pr__pfet_01v8 w=1.5 l=10",
             "Xn_load vcm ng 0 0 sky130_fd_pr__nfet_01v8 w=1 l=10",
             ".control", "set numdgt=15", "tran 0.2n 20.1u"]
    for index, at in enumerate(TIMES_US):
        lines += [f"meas tran p_{index} find v(pg) at={at:g}u",
                  f"meas tran n_{index} find v(ng) at={at:g}u"]
    lines += ["meas tran pre_vdd_current find i(Vdd) at=0.9u",
              "meas tran post_vdd_current find i(Vdd) at=5u",
              "quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    found = {name: float(value) for name, value in re.findall(
        r"(?m)^\s*((?:p|n)_\d+|(?:pre|post)_vdd_current)\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and len(found) == 2 * len(TIMES_US) + 2 and "Timestep too small" not in log
    rows = []
    if complete:
        for index, at in enumerate(TIMES_US):
            rows.append({"time_us": at, "p_gate_v": found[f"p_{index}"],
                         "n_gate_v": found[f"n_{index}"],
                         "p_error_from_command_mv": (found[f"p_{index}"] - .936) * 1e3,
                         "n_error_from_command_mv": (found[f"n_{index}"] - .48) * 1e3})
    report = {"test": "sky130_weight_gate_ota_buffer_step_settling",
              "simulation_completed": complete, "corner": "ss", "temperature_c": 0,
              "n_bias_v": .65, "p_bias_v": .733, "commanded_p_gate_v": .936,
              "commanded_n_gate_v": .48, "rows": rows,
              "supply_current_a": {key: found.get(key) for key in ("pre_vdd_current", "post_vdd_current")},
              "scope": "Two existing SKY130 transistor OTAs in unity feedback, driving p/n injector MOS gate loads. Ideal input step from off rails to selected gate levels, ideal bias and supply. Drain loads tied to ideal VCM; no analog weight MIM/mux, event switching, bias generator, noise, mismatch, extracted parasitics or network service."}
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
