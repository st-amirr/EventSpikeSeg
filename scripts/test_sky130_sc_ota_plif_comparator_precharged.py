"""Test OTA comparator with its signal gate parked at membrane reference."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

SEQUENCES = ("pp", "nn", "pn", "np")


def main() -> int:
    seq = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--sequence=")), "pp")
    win = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--win=")), "2"))
    window_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--window-us=")), "1.5"))
    if seq not in SEQUENCES or win not in (2, 5, 10) or not 0.5 <= window_us <= 10:
        raise ValueError("sequence pp/nn/pn/np; win 2/5/10; window 0.5..10us")
    read_on_m = 4.900 + 0.0001
    read_off_m = read_on_m + window_us / 1000.0
    read_at_m = read_off_m - 0.0001
    lines = [f"SKY130 TT OTA PLIF comparator precharged from reference {seq}", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
    lines += [
        f"Vpre pre_{seq} 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 5.005m 0)",
        f"Vpreb preb_{seq} 0 PWL(0 0 4.8999m 0 4.900m 1.8 5.005m 1.8)",
        f"Vread read_{seq} 0 PWL(0 0 {read_on_m:.6f}m 0 {read_on_m + 0.0001:.6f}m 1.8 {read_at_m:.6f}m 1.8 {read_off_m:.6f}m 0 5.005m 0)",
        f"Vreadb readb_{seq} 0 PWL(0 1.8 {read_on_m:.6f}m 1.8 {read_on_m + 0.0001:.6f}m 0 {read_at_m:.6f}m 0 {read_off_m:.6f}m 1.8 5.005m 1.8)",
        f"Xpre_{seq} out_r_{seq} sig_gate_{seq} pre_{seq} preb_{seq} vdd 0 transmission_gate",
        f"Xsample_{seq} out_s_{seq} sig_gate_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Vbncomp_{seq} vbnn_comp_{seq} 0 0.65",
        f"Vbpcomp_{seq} vbpp_comp_{seq} 0 0.75",
        f"Rcomp_{seq} comp_out_{seq} vcm 1Meg",
        f"Rcal_{seq} cal_out_{seq} vcm 1Meg",
        f"Xcomp_{seq} out_r_{seq} sig_gate_{seq} comp_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
        f"Xcal_{seq} out_r_{seq} out_r_{seq} cal_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
    ]
    data_name = f"sky130_sc_ota_plif_comparator_precharged_{seq}_w{win:g}_t{window_us:g}us.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 100n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(sig_gate_{seq}) v(comp_out_{seq}) v(cal_out_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_plif_comparator_precharged_{seq}_w{win:g}_t{window_us:g}us.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{root}:/workspace:ro", "--volume", f"{root / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    (RES / f"sky130_sc_ota_plif_comparator_precharged_{seq}_w{win:g}_t{window_us:g}us.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(v) for v in line.split()])
            except ValueError:
                continue
    report = {"test": "sky130_tt_physical_membrane_precharged_OTA_comparator", "simulation_completed": run.returncode == 0 and len(rows) > 10, "return_code": run.returncode, "sequence": seq, "ota_input_width_um": win, "comparison_window_us": window_us, "scope": "TT schematic; physical MIM membrane cells; OTA signal gate parked at matched reference during bin then connected late; OTA continuously biased; no mismatch/noise/extraction"}
    if report["simulation_completed"]:
        at = lambda t: min(range(len(rows)), key=lambda i: abs(rows[i][0] - t))
        i_pre, i_read, i_post = at(4.89e-3), at(read_at_m * 1e-3), at((read_off_m + 0.0001) * 1e-3)
        a, b, c = rows[i_pre], rows[i_read], rows[i_post]
        d_pre, d_read, d_post = a[1] - a[2], b[1] - b[2], c[1] - c[2]
        output_delta = b[4] - b[5]
        report.update({"state_diff_before_readout_uv": d_pre * 1e6, "state_diff_at_comparison_uv": d_read * 1e6, "state_diff_after_readout_uv": d_post * 1e6, "state_diff_disturbance_uv": (d_post - d_pre) * 1e6, "input_diff_at_comparison_uv": (b[1] - b[3]) * 1e6, "comparator_minus_matched_reference_v": output_delta, "decision_positive_state": output_delta > 0, "decision_matches_state_sign": (output_delta > 0) == (d_read > 0), "comparator_output_v": b[4], "matched_reference_output_v": b[5]})
    out_path = RES / f"sky130_sc_ota_plif_comparator_precharged_{seq}_w{win:g}_t{window_us:g}us.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
