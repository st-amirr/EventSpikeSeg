"""Screen gate-pulse-duration charge injection on SKY130 TT.

This is an analog-state candidate, not a Q7.16 accuracy claim. The weight is
represented by the pulse duration; the membrane remains a physical capacitor.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
WIDTHS_US = (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 4.0)
VDD = 1.8
VCM = 0.9

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
    lines = ["SKY130 TT analog PLIF pulse-duration injection screen", COMMON,
             f"Vdd vdd 0 {VDD}", f"Vcm vcm 0 {VCM}", "Vcap capture 0 0", "Vcapb capture_b 0 1.8",
             "Vreset reset 0 0", "Vresetb reset_b 0 1.8", "Vleak leak_en 0 0", "Vleakb leak_enb 0 1.8",
             "Vbias vbias 0 0.65"]
    lines += ["Vpref pgbref 0 1.8", "Vnref ngbref 0 0",
              "Xref pmemref snapref spikeref capture capture_b reset reset_b leak_en leak_enb pgbref ngbref vbias vdd 0 vcm analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100",
              "Vpref2 pgbref2 0 1.8",
              "Vnref2 ngbref2 0 0", "Xref2 nmemref snapref2 spikeref2 capture capture_b reset reset_b leak_en leak_enb pgbref2 ngbref2 vbias vdd 0 vcm analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100"]
    for pol in ("p", "n"):
        for i, width in enumerate(WIDTHS_US):
            pulse_scale = 7.0 if pol == "p" else 1.0
            stop = 0.1 + width * pulse_scale
            if pol == "p":
                lines += [f"Vpg{i} pgb{i} 0 PWL(0 1.8 0.099u 1.8 0.1u 1.0 {stop}u 1.0 {stop + 0.001}u 1.8 32u 1.8)",
                          f"Vngoff{i} ngoff{i} 0 0",
                          f"Xip{i} pmem{i} snapp{i} spikep{i} capture capture_b reset reset_b leak_en leak_enb pgb{i} ngoff{i} vbias vdd 0 vcm analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100"]
            else:
                lines += [f"Vng{i} ngb{i} 0 PWL(0 0 0.099u 0 0.1u 0.525 {stop}u 0.525 {stop + 0.001}u 0 32u 0)",
                          f"Vpgoff{i} pgoff{i} 0 1.8",
                          f"Xin{i} nmem{i} snapn{i} spiken{i} capture capture_b reset reset_b leak_en leak_enb pgoff{i} ngb{i} vbias vdd 0 vcm analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100"]
    count = len(WIDTHS_US)
    vectors = "v(pmemref) " + " ".join(f"v(pmem{i})" for i in range(count))
    vectors += " v(nmemref) " + " ".join(f"v(nmem{i})" for i in range(count))
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 10n 32u uic",
              f"wrdata ../results/sky130_ms_pulse_width_injection.dat {vectors}", "quit", ".endc", ".end"]
    deck = "\n".join(lines)
    path = BENCH / "sky130_ms_pulse_width_injection.cir"
    path.write_text(deck + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", path.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = proc.stdout + proc.stderr
    (RES / "sky130_ms_pulse_width_injection.log").write_text(log, encoding="utf-8")
    data = RES / "sky130_ms_pulse_width_injection.dat"
    rows = []
    if data.exists():
        for line in data.read_text().splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                pass
    # wrdata is time, p-membrane 0..3, n-membrane 0..3.
    measured: dict[str, list[float]] = {"positive": [0.0] * count, "negative": [0.0] * count}
    if rows:
        last = rows[-1]
        if len(last) >= 2 * count + 3:
            measured["positive"] = [last[i + 2] - last[1] for i in range(count)]
            measured["negative"] = [last[count + 2] - last[i + count + 3] for i in range(count)]
    curves = {}
    for pol in ("positive", "negative"):
        vals = measured[pol]
        duration_scale = 7.0 if pol == "positive" else 1.0
        per_us = [v / t for v, t in zip(vals, WIDTHS_US)]
        per_physical_us = [v / (t * duration_scale) for v, t in zip(vals, WIDTHS_US)]
        mean = sum(per_us) / len(per_us) if per_us else 0.0
        curves[pol] = {
            "signed_delta_v": vals,
            "delta_v_per_us": per_us,
            "delta_v_per_physical_pulse_us": per_physical_us,
            "correct_sign": all(v > 0 for v in vals),
            "monotonic": all(a < b for a, b in zip(vals, vals[1:])),
            "max_relative_slope_error": max((abs(x - mean) / abs(mean) for x in per_us), default=float("inf")) if mean else None,
        }
    polarity_gain_ratio = (sum(curves["positive"]["delta_v_per_us"]) /
                           sum(curves["negative"]["delta_v_per_us"])) if curves["negative"]["delta_v_per_us"] else 0.0
    completed = proc.returncode == 0 and len(rows) > 0
    passed = completed and all(curves[p]["correct_sign"] and curves[p]["monotonic"] and
                               curves[p]["max_relative_slope_error"] is not None and
                               curves[p]["max_relative_slope_error"] <= 0.15 for p in curves) and 0.85 <= polarity_gain_ratio <= 1.15
    report = {
        "test": "sky130_tt_analog_plif_pulse_duration_charge_injection",
        "simulation_completed": completed,
        "exit_code": proc.returncode,
        "pulse_widths_us": list(WIDTHS_US),
        "positive_duration_scale": 7.0,
        "negative_duration_scale": 1.0,
        "membrane_capacitor": "SKY130 PDK MIM model, 100um x 100um",
        "pmos_on_gate_v": 1.0,
        "nmos_on_gate_v": 0.525,
        "curves": curves,
        "max_relative_slope_error_limit": 0.15,
        "positive_to_negative_effective_gain_ratio": polarity_gain_ratio,
        "polarity_gain_ratio_limits": [0.85, 1.15],
        "candidate_screen_pass": bool(passed),
        "channel_integration": "analog_plif_channel_pulse_duration; reset inactive, leak disabled, snapshot capture inactive",
        "scope": "TT transient through the PLIF channel variant, SKY130 PDK MIM capacitors, and no-pulse references; no mismatch, corners, extracted parasitics, event multiplicity, or Q7.16 accuracy claim.",
    }
    (RES / "sky130_ms_pulse_width_injection.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
