"""Track the stored reference common mode briefly before an OTA threshold compare."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell


def main() -> int:
    seq = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--sequence=")), "pp")
    win = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--win=")), "0.5"))
    window_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--window-us=")), "1.5"))
    precharge_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--precharge-us=")), "0.8"))
    if seq not in ("pp", "nn", "pn", "np") or win not in (0.5, 1, 2) or not 0.5 <= window_us <= 10 or not 0.2 <= precharge_us <= 5:
        raise ValueError("invalid sequence, input size, compare window, or precharge interval")
    pre_on_m = 4.8990
    pre_off_m = pre_on_m + precharge_us / 1000.0
    read_on_m = 4.9000
    read_off_m = read_on_m + window_us / 1000.0
    read_at_m = read_off_m - 0.0001
    post_m = read_off_m + 0.0001
    lines = [f"SKY130 TT dynamic-reference-precharge PLIF comparator {seq}", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
    lines += [
        f"Vpre pre_{seq} 0 PWL(0 0 {pre_on_m:.6f}m 0 {pre_on_m+0.0001:.6f}m 1.8 {pre_off_m:.6f}m 1.8 {pre_off_m+0.0001:.6f}m 0 5.005m 0)",
        f"Vpreb preb_{seq} 0 PWL(0 1.8 {pre_on_m:.6f}m 1.8 {pre_on_m+0.0001:.6f}m 0 {pre_off_m:.6f}m 0 {pre_off_m+0.0001:.6f}m 1.8 5.005m 1.8)",
        f"Vread read_{seq} 0 PWL(0 0 {pre_off_m+0.0001:.6f}m 0 {read_on_m:.6f}m 1.8 {read_at_m:.6f}m 1.8 {read_off_m:.6f}m 0 5.005m 0)",
        f"Vreadb readb_{seq} 0 PWL(0 1.8 {pre_off_m+0.0001:.6f}m 1.8 {read_on_m:.6f}m 0 {read_at_m:.6f}m 0 {read_off_m:.6f}m 1.8 5.005m 1.8)",
        f"Xref_pre_{seq} out_r_{seq} ref_gate_{seq} pre_{seq} preb_{seq} vdd 0 transmission_gate",
        f"Xsig_pre_{seq} out_r_{seq} sig_gate_{seq} pre_{seq} preb_{seq} vdd 0 transmission_gate",
        f"Xref_sample_{seq} out_r_{seq} ref_gate_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Xsig_sample_{seq} out_s_{seq} sig_gate_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Vbncomp_{seq} vbnn_comp_{seq} 0 0.65",
        f"Vbpcomp_{seq} vbpp_comp_{seq} 0 0.75",
        f"Rcomp_{seq} comp_out_{seq} vcm 1Meg",
        f"Rcal_{seq} cal_out_{seq} vcm 1Meg",
        f"Xcomp_{seq} ref_gate_{seq} sig_gate_{seq} comp_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
        f"Xcal_{seq} ref_gate_{seq} ref_gate_{seq} cal_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
    ]
    suffix = f"{seq}_w{win:g}_t{window_us:g}us_pc{precharge_us:g}us"
    data_name = f"sky130_sc_ota_plif_comparator_dynamic_precharge_{suffix}.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 50n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(ref_gate_{seq}) v(sig_gate_{seq}) v(comp_out_{seq}) v(cal_out_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_plif_comparator_dynamic_precharge_{suffix}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{root}:/workspace:ro", "--volume", f"{root / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=135)
    (RES / f"sky130_sc_ota_plif_comparator_dynamic_precharge_{suffix}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows=[]
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(v) for v in line.split()])
            except ValueError: pass
    report={"test":"sky130_tt_dynamic_reference_precharge_OTA_comparator","simulation_completed":run.returncode==0 and len(rows)>10,"return_code":run.returncode,"sequence":seq,"ota_input_width_um":win,"comparison_window_us":window_us,"reference_precharge_us":precharge_us,"scope":"TT physical MIM state pair; OTA gates track the live no-event reference briefly before the comparison; gate-only reference matching, no mismatch/noise/extraction"}
    if report["simulation_completed"]:
        at=lambda t:min(range(len(rows)),key=lambda i:abs(rows[i][0]-t))
        a,b,c=rows[at(4.89e-3)],rows[at(read_at_m*1e-3)],rows[at(post_m*1e-3)]
        d0,d1,d2=a[1]-a[2],b[1]-b[2],c[1]-c[2]
        outdiff=b[5]-b[6]
        report.update({"state_diff_before_precharge_uv":d0*1e6,"state_diff_at_comparison_uv":d1*1e6,"state_diff_after_compare_uv":d2*1e6,"state_diff_disturbance_uv":(d2-d0)*1e6,"input_diff_at_comparison_uv":(b[3]-b[4])*1e6,"comparator_minus_matched_reference_v":outdiff,"decision_positive_state":outdiff>0,"decision_matches_state_sign":(outdiff>0)==(d1>0),"comparator_output_v":b[5],"matched_reference_output_v":b[6]})
    out_path=RES/f"sky130_sc_ota_plif_comparator_dynamic_precharge_{suffix}.json"
    out_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__=="__main__": raise SystemExit(main())
