"""SKY130 MS PLIF: Q7.16 weight-DAC transfer + beta↔leak phase mapping.

Docker ngspice only. Declared approximations:
  - weight ≈ binary-weighted MOS current gated by spike pulse
  - beta ≈ exp(-t_leak/tau); digital PLIF candidate = beta*mem + I
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

VDD, VCM, SCALE = 1.8, 0.9, 0.2
# Export beta range ~0.32..0.975; smoke a few points inside that band.
BETAS = (0.35, 0.60, 0.90)
BETA_ERR_LIM = 0.12  # schematic smoke; not accuracy gate


COMMON = f""".option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
"""


def docker_ngspice(name: str, timeout_s: int = 120) -> tuple[int, str]:
    cmd = [
        "docker",
        "run",
        "--rm",
        "--memory",
        "2g",
        "--cpus",
        "2",
        "--volume",
        f"{ROOT}:/workspace:ro",
        "--volume",
        f"{OUT}:/workspace/artifacts/analog_asic",
        "--workdir",
        "/workspace/artifacts/analog_asic/benches",
        "--entrypoint",
        "timeout",
        "eventspikeseg:analog-ngspice36",
        str(timeout_s),
        "ngspice",
        "-b",
        f"{name}.cir",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 30)
    (RES / f"{name}.log").write_text(r.stdout + r.stderr)
    return r.returncode, r.stdout + r.stderr


def load_rows(name: str) -> list[list[float]]:
    p = RES / f"{name}.dat"
    if not p.is_file():
        return []
    return [
        [float(x) for x in line.split()]
        for line in p.read_text().splitlines()[1:]
        if line.strip()
    ]


def nearest(rows: list[list[float]], t: float) -> list[float]:
    return min(rows, key=lambda r: abs(r[0] - t))


def complete(rows: list[list[float]], end: float, log: str) -> bool:
    return (
        bool(rows)
        and rows[-1][0] >= end * 0.999
        and "timestep too small" not in log.lower()
        and "aborted" not in log.lower()
        and all(math.isfinite(x) for r in rows for x in r)
    )


def write_tau_cal_bench() -> str:
    """Fixed leak window to estimate tau from residual attenuation."""
    name = "ms_plif_beta_tau_cal"
    t_leak = 5e-6
    (BENCH / f"{name}.cir").write_text(
        f"""SKY130 MS PLIF beta tau calibration (5us leak)
{COMMON}
Vdd vdd 0 {VDD}
Vcm vcm 0 {VCM}
Vbias bias 0 0.65
Vibp ibias_p 0 1.2
Vibn ibias_n 0 0.4
Vrst reset 0 PWL(0 {VDD} 0.4u {VDD} 0.401u 0 40u 0)
Vrstb reset_b 0 PWL(0 0 0.4u 0 0.401u {VDD} 40u {VDD})
Vpp pulse_pos 0 PWL(0 {VDD} 1u {VDD} 1.001u 0 2u 0 2.001u {VDD} 40u {VDD})
Vpn pulse_neg 0 0
Vle leak_en 0 PWL(0 0 5u 0 5.001u {VDD} {5e-6 + t_leak} {VDD} {5e-6 + t_leak + 1e-9} 0 40u 0)
Vleb leak_enb 0 PWL(0 {VDD} 5u {VDD} 5.001u 0 {5e-6 + t_leak} 0 {5e-6 + t_leak + 1e-9} {VDD} 40u {VDD})
Vcap capture 0 0
Vcapb capture_b 0 {VDD}
Xplif state snapshot spike capture capture_b reset reset_b leak_en leak_enb
+ pulse_pos pulse_neg ibias_p ibias_n bias vdd 0 vcm analog_plif_channel
+ theta=0.4 scale={SCALE} w_um=100 l_um=100
.control
set wr_singlescale
set wr_vecnames
tran 20n 40u
wrdata ../results/{name}.dat v(state) v(leak_en)
quit
.endc
.end
"""
    )
    return name


def write_beta_bench(beta: float, t_leak: float) -> str:
    name = f"ms_plif_beta_{beta:.2f}".replace(".", "p")
    t_end = 5e-6 + t_leak + 10e-6
    (BENCH / f"{name}.cir").write_text(
        f"""SKY130 MS PLIF beta={beta} t_leak={t_leak}
{COMMON}
Vdd vdd 0 {VDD}
Vcm vcm 0 {VCM}
Vbias bias 0 0.65
Vibp ibias_p 0 1.2
Vibn ibias_n 0 0.4
Vrst reset 0 PWL(0 {VDD} 0.4u {VDD} 0.401u 0 {t_end} 0)
Vrstb reset_b 0 PWL(0 0 0.4u 0 0.401u {VDD} {t_end} {VDD})
Vpp pulse_pos 0 PWL(0 {VDD} 1u {VDD} 1.001u 0 2u 0 2.001u {VDD} {t_end} {VDD})
Vpn pulse_neg 0 0
Vle leak_en 0 PWL(0 0 5u 0 5.001u {VDD} {5e-6 + t_leak} {VDD} {5e-6 + t_leak + 1e-9} 0 {t_end} 0)
Vleb leak_enb 0 PWL(0 {VDD} 5u {VDD} 5.001u 0 {5e-6 + t_leak} 0 {5e-6 + t_leak + 1e-9} {VDD} {t_end} {VDD})
Vcap capture 0 0
Vcapb capture_b 0 {VDD}
Xplif state snapshot spike capture capture_b reset reset_b leak_en leak_enb
+ pulse_pos pulse_neg ibias_p ibias_n bias vdd 0 vcm analog_plif_channel
+ theta=0.4 scale={SCALE} w_um=100 l_um=100
.control
set wr_singlescale
set wr_vecnames
tran 20n {t_end}
wrdata ../results/{name}.dat v(state)
quit
.endc
.end
"""
    )
    return name


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)

    dac_run = subprocess.run(
        [sys.executable, str(ROOT / "scripts/test_sky130_ms_weight_dac_q716.py")],
        capture_output=True, text=True, timeout=240,
    )
    dac_report_path = RES / "sky130_weight_q716_dac_screen.json"
    dac_report = json.loads(dac_report_path.read_text()) if dac_report_path.is_file() else {}
    mono = bool(dac_run.returncode == 0 and dac_report.get("monotonic_pass"))
    weight_rows = [{
        "bench": "sky130_weight_q716_dac_screen",
        "simulation_completed": bool(dac_report.get("screen_pass")),
        "monotonic_pass": bool(dac_report.get("monotonic_pass")),
        "coarse_transfer_pass": bool(dac_report.get("coarse_transfer_pass")),
        "analog_q716_precision_qualified": False,
        "injection_current_tested": False,
    }]

    # Tau calibration
    tau_name = write_tau_cal_bench()
    (RES / f"{tau_name}.dat").unlink(missing_ok=True)
    rc, log = docker_ngspice(tau_name, 90)
    rows = load_rows(tau_name)
    tau_ok = rc == 0 and complete(rows, 40e-6, log)
    tau_s = None
    tau_entry: dict = {"bench": tau_name, "simulation_completed": tau_ok, "exit_code": rc}
    if tau_ok:
        pre = nearest(rows, 4.5e-6)[1]
        post = nearest(rows, 10.5e-6)[1]
        amp0 = pre - VCM
        amp1 = post - VCM
        ratio = amp1 / amp0 if abs(amp0) > 1e-4 else float("nan")
        t_cal = 5e-6
        if ratio > 0 and ratio < 1:
            tau_s = -t_cal / math.log(ratio)
        tau_entry.update(
            pre_v=pre,
            post_v=post,
            residual_ratio=ratio,
            t_leak_s=t_cal,
            tau_s=tau_s,
        )
    print(json.dumps(tau_entry))

    beta_rows: list[dict] = []
    beta_pass = True
    if tau_s and tau_s > 0:
        for beta in BETAS:
            t_leak = -tau_s * math.log(beta)
            name = write_beta_bench(beta, t_leak)
            (RES / f"{name}.dat").unlink(missing_ok=True)
            rc, log = docker_ngspice(name, 120)
            rows = load_rows(name)
            end = 5e-6 + t_leak + 10e-6
            ok = rc == 0 and complete(rows, end, log)
            entry = {
                "bench": name,
                "target_beta": beta,
                "t_leak_s": t_leak,
                "simulation_completed": ok,
                "exit_code": rc,
            }
            if ok:
                pre = nearest(rows, 4.5e-6)[1]
                post = nearest(rows, 5e-6 + t_leak + 0.5e-6)[1]
                amp0 = pre - VCM
                amp1 = post - VCM
                measured = amp1 / amp0 if abs(amp0) > 1e-4 else float("nan")
                err = abs(measured - beta)
                entry.update(
                    pre_v=pre,
                    post_v=post,
                    measured_beta=measured,
                    abs_error=err,
                    beta_pass=err <= BETA_ERR_LIM,
                )
                beta_pass = beta_pass and entry["beta_pass"]
            else:
                beta_pass = False
                for line in log.splitlines():
                    if "error" in line.lower() or "undefined" in line.lower():
                        entry["failure_hint"] = line.strip()
                        break
            print(json.dumps(entry))
            beta_rows.append(entry)
    else:
        beta_pass = False

    summary = {
        "architecture": "sky130_ms_weight_dac_and_beta_leak_mapping",
        "mapping_notes": {
            "weight": "23-bit Q7.16 magnitude R-2R voltage transfer only; MOS injection current not tested here",
            "beta": "t_leak = -tau_nom * ln(beta); attenuates (V-vcm) toward vcm",
            "limitation": "schematic smoke; not mismatch/extracted/layout PPA",
        },
        "weight_results": weight_rows,
        "weight_monotonic_pass": mono,
        "tau_calibration": tau_entry,
        "beta_results": beta_rows,
        "beta_mapping_pass": beta_pass,
        "screen_pass": mono and beta_pass and bool(tau_s),
    }
    out = RES / "sky130_ms_weight_beta_screen.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print("weight_monotonic_pass", mono)
    print("beta_mapping_pass", beta_pass)
    print("screen_pass", summary["screen_pass"])
    print("wrote", out)
    return 0 if summary["screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
