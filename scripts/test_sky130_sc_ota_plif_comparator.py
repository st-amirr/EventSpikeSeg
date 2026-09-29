"""Test late switched, high-impedance OTA threshold sensing on stored SNN state."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

ROOT = Path(__file__).resolve().parents[1]
SEQUENCES = ("pp", "nn", "pn", "np")


def main() -> int:
    seq = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--sequence=")), "pp")
    win = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--win=")), "10"))
    window_us = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--window-us=")), "3.9"))
    gate_precharge_v = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--gate-precharge-v=")), "0.9"))
    max_step_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--max-step-ns=")), "100"))
    threshold_uv = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--threshold-uv=")), "0"))
    if seq not in SEQUENCES:
        raise ValueError(f"sequence must be one of {SEQUENCES}")
    if win not in (0.5, 1, 2, 5, 10) or not 0.5 <= window_us <= 10 or not 5 <= max_step_ns <= 100:
        raise ValueError("win must be 0.5, 1, 2, 5, or 10um and window-us must be 0.5..10")
    sample_off_m = 4.900 + window_us / 1000.0
    sample_read_m = sample_off_m - 0.0001
    sample_post_m = sample_off_m + 0.0001
    control_off_m = sample_off_m
    control_on_m = sample_off_m + 0.0001
    # Hold OTA gate nodes at VCM while the membrane integrates, then connect
    # both gates for a short late-bin decision window. A matched zero-diff OTA
    # samples the same reference common mode for nominal offset subtraction.
    lines = [f"SKY130 TT physical PLIF differential comparator {seq}", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", f"Vgatecm gatecm 0 {gate_precharge_v:.9f}"]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    reference_lines = cell(f"r_{seq}", 0.90, None, long_bin=True)
    if threshold_uv:
        threshold_state_v = 0.90 + threshold_uv * 1e-6
        reference_lines = [line.replace("Vinitlvl_r_", "Vinitlvl_r_").replace("0.9", f"{threshold_state_v:.9f}")
                           if line.startswith("Vinitlvl_r_") else line for line in reference_lines]
        reference_lines = [line.replace("=0.9", f"={threshold_state_v:.9f}") if line.startswith(".ic v(out_r_") else line
                           for line in reference_lines]
    lines += reference_lines
    lines += [
        f"Vgate_reset gate_reset_{seq} 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 {sample_off_m:.6f}m 0 {control_on_m:.6f}m 1.8 5.005m 1.8)",
        f"Vgate_resetb gate_resetb_{seq} 0 PWL(0 0 4.8999m 0 4.900m 1.8 {sample_off_m:.6f}m 1.8 {control_on_m:.6f}m 0 5.005m 0)",
        f"Vread read_{seq} 0 PWL(0 0 4.8999m 0 4.900m 1.8 {sample_read_m:.6f}m 1.8 {sample_off_m:.6f}m 0 5.005m 0)",
        f"Vreadb readb_{seq} 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 {sample_read_m:.6f}m 0 {sample_off_m:.6f}m 1.8 5.005m 1.8)",
        f"Xref_reset ref_gate_{seq} gatecm gate_reset_{seq} gate_resetb_{seq} vdd 0 transmission_gate",
        f"Xsig_reset sig_gate_{seq} gatecm gate_reset_{seq} gate_resetb_{seq} vdd 0 transmission_gate",
        f"Xref_sample out_r_{seq} ref_gate_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Xsig_sample out_s_{seq} sig_gate_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Vbncomp_{seq} vbnn_comp_{seq} 0 0.65",
        f"Vbpcomp_{seq} vbpp_comp_{seq} 0 0.75",
        f"Rcomp_{seq} comp_out_{seq} vcm 1Meg",
        f"Rcal_{seq} cal_out_{seq} vcm 1Meg",
        f"Xcomp_{seq} ref_gate_{seq} sig_gate_{seq} comp_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
        f"Xcal_{seq} ref_gate_{seq} ref_gate_{seq} cal_out_{seq} vbnn_comp_{seq} vbpp_comp_{seq} vdd 0 sky130_sc_ota win={win:g} wn3=2 wp3=27.8 cc=100f",
    ]
    pre_tag = str(gate_precharge_v).replace('.', 'p')
    step_tag = f"s{max_step_ns:g}n"
    threshold_tag = f"_th{threshold_uv:g}uv" if threshold_uv else ""
    data_name = f"sky130_sc_ota_plif_comparator_{seq}_w{win:g}_t{window_us:g}us_p{pre_tag}_{step_tag}{threshold_tag}.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", f"tran {max_step_ns:g}n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(ref_gate_{seq}) v(sig_gate_{seq}) v(comp_out_{seq}) v(cal_out_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_plif_comparator_{seq}_w{win:g}_t{window_us:g}us_p{pre_tag}_{step_tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
            "eventspikeseg:analog-ngspice36", "180", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=195)
    (RES / f"sky130_sc_ota_plif_comparator_{seq}_w{win:g}_t{window_us:g}us_p{pre_tag}_{step_tag}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(value) for value in line.split()])
            except ValueError:
                continue
    report = {
        "test": "sky130_tt_physical_membrane_OTA_comparator",
        "simulation_completed": run.returncode == 0 and len(rows) > 10,
        "return_code": run.returncode,
        "sequence": seq,
        "ota_input_width_um": win,
        "comparison_window_us": window_us,
        "gate_precharge_v": gate_precharge_v,
        "threshold_reference_uv": threshold_uv,
        "max_timestep_ns": max_step_ns,
        "scope": "TT schematic; physical SC MIM membrane cells; gate reset during integration, comparator connected for selected short window; nominal matched offset reference OTA; no mismatch/noise/extraction/model replay",
    }
    if report["simulation_completed"]:
        at = lambda t: min(range(len(rows)), key=lambda i: abs(rows[i][0] - t))
        i_pre, i_read, i_post = at(4.89e-3), at(sample_read_m * 1e-3), at(sample_post_m * 1e-3)
        a, b, c = rows[i_pre], rows[i_read], rows[i_post]
        d_pre = a[1] - a[2]
        d_read = b[1] - b[2]
        d_post = c[1] - c[2]
        delta_output = b[5] - b[6]
        report.update({
            "state_diff_before_readout_uv": d_pre * 1e6,
            "state_diff_at_comparison_uv": d_read * 1e6,
            "state_diff_after_readout_uv": d_post * 1e6,
            "state_diff_disturbance_uv": (d_post - d_pre) * 1e6,
            "comparator_minus_matched_reference_v": delta_output,
            "decision_positive_state": delta_output > 0,
            "decision_matches_state_sign": (delta_output > 0) == (d_read > 0),
            "comparator_output_v": b[5],
            "matched_reference_output_v": b[6],
            "input_reference_minus_signal_uv": (b[3] - b[4]) * 1e6,
        })
    out_path = RES / f"sky130_sc_ota_plif_comparator_{seq}_w{win:g}_t{window_us:g}us_p{pre_tag}_{step_tag}{threshold_tag}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
