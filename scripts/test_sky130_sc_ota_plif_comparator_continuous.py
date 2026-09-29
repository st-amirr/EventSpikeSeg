"""Check always-connected high-impedance OTA comparator on physical SC states."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

SEQUENCES = ("pp", "nn", "pn", "np")


def main() -> int:
    seq = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--sequence=")), "pp")
    win = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--win=")), "2"))
    if seq not in SEQUENCES or win not in (2, 5, 10):
        raise ValueError("choose sequence pp/nn/pn/np and win 2/5/10")
    lines = [f"SKY130 TT always-connected OTA PLIF comparator {seq} win={win:g}um", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
    lines += [
        f"Vbncomp_{seq} vbnn_comp_{seq} 0 0.65",
        f"Vbpcomp_{seq} vbpp_comp_{seq} 0 0.75",
        f"Rcomp_{seq} comp_out_{seq} vcm 1Meg",
        f"Rcal_{seq} cal_out_{seq} vcm 1Meg",
        f"Xcomp_{seq} out_r_{seq} out_s_{seq} comp_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
        f"Xcal_{seq} out_r_{seq} out_r_{seq} cal_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
    ]
    data_name = f"sky130_sc_ota_plif_comparator_continuous_{seq}_w{win:g}.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 100n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(comp_out_{seq}) v(cal_out_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_plif_comparator_continuous_{seq}_w{win:g}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{Path(__file__).resolve().parents[1]}:/workspace:ro", "--volume", f"{Path(__file__).resolve().parents[1] / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    RES.joinpath(f"sky130_sc_ota_plif_comparator_continuous_{seq}_w{win:g}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(v) for v in line.split()])
            except ValueError:
                continue
    report = {
        "test": "sky130_tt_physical_membrane_continuous_OTA_comparator",
        "simulation_completed": run.returncode == 0 and len(rows) > 10,
        "return_code": run.returncode,
        "sequence": seq,
        "ota_input_width_um": win,
        "scope": "TT schematic; physical MIM membrane cells; comparator and matched offset reference gates continuously connected; no input switch kick, noise, mismatch, extraction or model replay",
    }
    if report["simulation_completed"]:
        def row_at(t: float) -> list[float]:
            return min(rows, key=lambda r: abs(r[0] - t))
        pre, final = row_at(4.89e-3), row_at(5.0e-3)
        d_pre, d_final = pre[1] - pre[2], final[1] - final[2]
        out_delta = final[3] - final[4]
        report.update({
            "state_diff_before_last_bin_readout_uv": d_pre * 1e6,
            "state_diff_at_5ms_uv": d_final * 1e6,
            "state_diff_change_during_last_110us_uv": (d_final - d_pre) * 1e6,
            "comparator_minus_matched_reference_v": out_delta,
            "decision_positive_state": out_delta > 0,
            "decision_matches_state_sign": (out_delta > 0) == (d_final > 0),
            "comparator_output_v": final[3],
            "matched_reference_output_v": final[4],
        })
    out_path = RES / f"sky130_sc_ota_plif_comparator_continuous_{seq}_w{win:g}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
