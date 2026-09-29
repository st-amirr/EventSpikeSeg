"""Check sequential pulse charge accumulation on one SKY130 MIM membrane."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VDD, VCM = 1.8, 0.9

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

# Pulse widths are the measured nominally matched 0.5us logical event widths.
PWIDTH = 3.5
NWIDTH = 0.5
GAP = 1.0
STARTS = {"p": 0.2, "n": 0.2, "pp": 0.2, "pn": 0.2, "np": 0.2}


def pwl(pulses: list[tuple[str, float, float]], pol: str) -> str:
    inactive, active = ((1.8, 1.0) if pol == "p" else (0.0, 0.525))
    points = [(0.0, inactive)]
    for kind, start, width in pulses:
        if kind != pol:
            continue
        points += [(start - 0.001, inactive), (start, active),
                   (start + width, active), (start + width + 0.001, inactive)]
    points += [(24.0, inactive)]
    return "PWL(" + " ".join(f"{t:g}u {v:g}" for t, v in points) + ")"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    cases = {
        "ref": [],
        "p": [("p", 0.2, PWIDTH)],
        "n": [("n", 0.2, NWIDTH)],
        "pp": [("p", 0.2, PWIDTH), ("p", 0.2 + PWIDTH + GAP, PWIDTH)],
        "pn": [("p", 0.2, PWIDTH), ("n", 0.2 + PWIDTH + GAP, NWIDTH)],
        "np": [("n", 0.2, NWIDTH), ("p", 0.2 + NWIDTH + GAP, PWIDTH)],
    }
    lines = ["SKY130 TT pulse accumulation", COMMON, f"Vdd vdd 0 {VDD}",
             f"Vcm vcm 0 {VCM}", "Vcap capture 0 0", "Vcapb capture_b 0 1.8",
             "Vreset reset 0 0", "Vresetb reset_b 0 1.8", "Vleak leak_en 0 0",
             "Vleakb leak_enb 0 1.8", "Vbias vbias 0 0.65"]
    for name, pulses in cases.items():
        for pol, pin in (("p", "pg"), ("n", "ng")):
            lines.append(f"V{name}{pin} {name}_{pin} 0 {pwl(pulses, pol)}")
        lines.append(
            f"X{name} {name}_mem {name}_snap {name}_spike capture capture_b reset reset_b "
            f"leak_en leak_enb {name}_pg {name}_ng vbias vdd 0 vcm "
            "analog_plif_channel_pulse_duration theta=0.4 scale=0.2 w_um=100 l_um=100")
    vectors = " ".join(f"v({name}_mem)" for name in cases)
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 10n 24u uic",
              f"wrdata ../results/sky130_ms_pulse_width_accumulation.dat {vectors}", "quit", ".endc", ".end"]
    deck = BENCH / "sky130_ms_pulse_width_accumulation.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    (RES / "sky130_ms_pulse_width_accumulation.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    data = RES / "sky130_ms_pulse_width_accumulation.dat"
    rows = []
    if data.exists():
        for row in data.read_text().splitlines()[1:]:
            try:
                rows.append([float(v) for v in row.split()])
            except ValueError:
                pass
    vals = {}
    if rows and len(rows[-1]) >= len(cases) + 1:
        last = rows[-1]
        vals = {name: last[i + 1] - last[1] for i, name in enumerate(cases)}
    expected_pp = 2 * vals.get("p", 0.0)
    expected_mix = vals.get("p", 0.0) + vals.get("n", 0.0)
    ppm_error = abs(vals.get("pp", 0.0) - expected_pp) / max(abs(expected_pp), 1e-15)
    pn_error = abs(vals.get("pn", 0.0) - expected_mix) / max(abs(expected_mix), 1e-15)
    np_error = abs(vals.get("np", 0.0) - expected_mix) / max(abs(expected_mix), 1e-15)
    order_error = abs(vals.get("pn", 0.0) - vals.get("np", 0.0)) / max(abs(vals.get("pn", 0.0)), abs(vals.get("np", 0.0)), 1e-15)
    completed = proc.returncode == 0 and len(rows) > 0 and len(vals) == len(cases)
    report = {
        "test": "sky130_tt_pulse_width_sequential_accumulation",
        "simulation_completed": completed,
        "exit_code": proc.returncode,
        "membrane": "SKY130 PDK MIM 100um x 100um",
        "logical_event_width_us": 0.5,
        "positive_physical_width_us": PWIDTH,
        "negative_physical_width_us": NWIDTH,
        "signed_delta_v": vals,
        "same_sign_double_sum_relative_error": ppm_error,
        "mixed_sum_pn_relative_error": pn_error,
        "mixed_sum_np_relative_error": np_error,
        "mixed_order_relative_difference": order_error,
        "relative_error_screen_limit": 0.05,
        "candidate_screen_pass": bool(completed and ppm_error <= .05 and pn_error <= .05 and np_error <= .05 and order_error <= .05),
        "scope": "TT transient only; one sequential event at a time; no PVT, mismatch, extraction, reset/leak, or Q7.16 accuracy claim.",
    }
    (RES / "sky130_ms_pulse_width_accumulation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["candidate_screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
