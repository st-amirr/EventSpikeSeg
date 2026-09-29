"""Precharge comparator gates to membrane reference, then compare late in the bin."""
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
    if seq not in SEQUENCES or win not in (2, 5, 10):
        raise ValueError("sequence pp/nn/pn/np and win 2/5/10")
    lines = [f"SKY130 TT physical OTA comparator precharge and late compare {seq}", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
    lines += [
        f"Vpre pre_{seq} 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 5.005m 0)",
        f"Vpreb preb_{seq} 0 PWL(0 0 4.8999m 0 4.900m 1.8 5.005m 1.8)",
        f"Vread read_{seq} 0 PWL(0 0 4.9009m 0 4.901m 1.8 4.9024m 1.8 4.9025m 0 5.005m 0)",
        f"Vreadb readb_{seq} 0 PWL(0 1.8 4.9009m 1.8 4.901m 0 4.9024m 0 4.9025m 1.8 5.005m 1.8)",
        f"Vbncomp_{seq} vbnn_comp_{seq} 0 PWL(0 0 4.900m 0 4.9001m 0.65 4.9024m 0.65 4.9025m 0 5.005m 0)",
        f"Vbpcomp_{seq} vbpp_comp_{seq} 0 PWL(0 1.8 4.900m 1.8 4.9001m 0.75 4.9024m 0.75 4.9025m 1.8 5.005m 1.8)",
        f"Xref_pre_{seq} out_r_{seq} ref_gate_{seq} pre_{seq} preb_{seq} vdd 0 transmission_gate",
        f"Xsig_pre_{seq} out_r_{seq} sig_gate_{seq} pre_{seq} preb_{seq} vdd 0 transmission_gate",
        f"Xsample_{seq} out_s_{seq} sig_gate_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Rcomp_{seq} comp_out_{seq} vcm 1Meg",
        f"Rcal_{seq} cal_out_{seq} vcm 1Meg",
        f"Xcomp_{seq} ref_gate_{seq} sig_gate_{seq} comp_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
        f"Xcal_{seq} ref_gate_{seq} ref_gate_{seq} cal_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
    ]
    data_name = f"sky130_sc_ota_plif_comparator_autozero_{seq}_w{win:g}.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 100n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(ref_gate_{seq}) v(sig_gate_{seq}) v(comp_out_{seq}) v(cal_out_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_plif_comparator_autozero_{seq}_w{win:g}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{root}:/workspace:ro", "--volume", f"{root / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    (RES / f"sky130_sc_ota_plif_comparator_autozero_{seq}_w{win:g}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(v) for v in line.split()])
            except ValueError:
                continue
    report = {"test": "sky130_tt_membrane_precharged_transistor_OTA_comparator", "simulation_completed": run.returncode == 0 and len(rows) > 10, "return_code": run.returncode, "sequence": seq, "ota_input_width_um": win, "scope": "TT physical SC MIM cells; both OTA gate nodes precharged from reference while OTA bias is off; comparator biased before signal-gate connection; 1.4us compare; no mismatch/noise/extraction"}
    if report["simulation_completed"]:
        at = lambda t: min(range(len(rows)), key=lambda i: abs(rows[i][0] - t))
        a, b, c = rows[at(4.89e-3)], rows[at(4.9024e-3)], rows[at(4.9027e-3)]
        d_pre, d_read, d_post = a[1]-a[2], b[1]-b[2], c[1]-c[2]
        out_delta = b[5]-b[6]
        report.update({"state_diff_before_readout_uv": d_pre*1e6, "state_diff_at_comparison_uv": d_read*1e6, "state_diff_after_readout_uv": d_post*1e6, "state_diff_disturbance_uv": (d_post-d_pre)*1e6, "input_diff_at_comparison_uv": (b[3]-b[4])*1e6, "comparator_minus_matched_reference_v": out_delta, "decision_positive_state": out_delta > 0, "decision_matches_state_sign": (out_delta > 0)==(d_read > 0), "comparator_output_v": b[5], "matched_reference_output_v": b[6]})
    out_path = RES / f"sky130_sc_ota_plif_comparator_autozero_{seq}_w{win:g}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
