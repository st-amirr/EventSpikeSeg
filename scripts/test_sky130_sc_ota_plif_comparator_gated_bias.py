"""Measure membrane loading when a small OTA comparator is biased only at bin end."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

SEQUENCES = ("pp", "nn", "pn", "np")


def main() -> int:
    seq = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--sequence=")), "pp")
    win = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--win=")), "0.5"))
    if seq not in SEQUENCES or win not in (0.5, 1, 2):
        raise ValueError("sequence pp/nn/pn/np and win 0.5/1/2")
    lines = [f"SKY130 TT OTA comparator with gated bias {seq}", COMMON, "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
    lines += [
        f"Vbncomp_{seq} vbnn_comp_{seq} 0 PWL(0 0 4.8999m 0 4.900m 0.65 4.904m 0.65 4.9041m 0 5.005m 0)",
        f"Vbpcomp_{seq} vbpp_comp_{seq} 0 PWL(0 1.8 4.8999m 1.8 4.900m 0.75 4.904m 0.75 4.9041m 1.8 5.005m 1.8)",
        f"Rcomp_{seq} comp_out_{seq} vcm 1Meg",
        f"Rcal_{seq} cal_out_{seq} vcm 1Meg",
        f"Xcomp_{seq} out_r_{seq} out_s_{seq} comp_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
        f"Xcal_{seq} out_r_{seq} out_r_{seq} cal_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
    ]
    data_name = f"sky130_sc_ota_plif_comparator_gated_bias_{seq}_w{win:g}.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 100n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(comp_out_{seq}) v(cal_out_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_plif_comparator_gated_bias_{seq}_w{win:g}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{root}:/workspace:ro", "--volume", f"{root / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    (RES / f"sky130_sc_ota_plif_comparator_gated_bias_{seq}_w{win:g}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(v) for v in line.split()])
            except ValueError: pass
    report = {"test": "sky130_tt_membrane_direct_input_gated_bias_comparator", "simulation_completed": run.returncode == 0 and len(rows) > 10, "return_code": run.returncode, "sequence": seq, "ota_input_width_um": win, "scope": "TT physical MIM membrane; comparator MOS gates directly attached with OTA bias off during the bin, bias enabled for 4us near end; no input switches, noise, mismatch or extraction"}
    if report["simulation_completed"]:
        at = lambda t: min(range(len(rows)), key=lambda i: abs(rows[i][0] - t))
        a, b, c = rows[at(4.89e-3)], rows[at(4.904e-3)], rows[at(4.9042e-3)]
        d_pre, d_on, d_post = a[1]-a[2], b[1]-b[2], c[1]-c[2]
        outdiff = b[3]-b[4]
        report.update({"state_diff_before_bias_enable_uv": d_pre*1e6, "state_diff_after_4us_compare_uv": d_on*1e6, "state_diff_after_bias_disable_uv": d_post*1e6, "state_change_during_comparator_enable_uv": (d_on-d_pre)*1e6, "comparator_minus_matched_reference_v": outdiff, "decision_positive_state": outdiff > 0, "decision_matches_state_sign": (outdiff > 0)==(d_on > 0), "comparator_output_v": b[3], "matched_reference_output_v": b[4]})
    out_path=RES / f"sky130_sc_ota_plif_comparator_gated_bias_{seq}_w{win:g}.json"
    out_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__": raise SystemExit(main())
