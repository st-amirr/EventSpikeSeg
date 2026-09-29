"""Bounded test of unity-OTA buffers isolating stored membrane nodes from feedback resistors."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

ROOT = Path(__file__).resolve().parents[1]
HEADER = r"""* SKY130 physical membranes with powered-late MOS follower and poly-feedback OTA
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    argv = __import__("sys").argv[1:]
    seq = next((a.split("=", 1)[1] for a in argv if a.startswith("--sequence=")), "pp")
    max_step_ns = float(next((a.split("=", 1)[1] for a in argv if a.startswith("--max-step-ns=")), "100"))
    precharge_v = float(next((a.split("=", 1)[1] for a in argv if a.startswith("--precharge-v=")), "0.8845"))
    gain = float(next((a.split("=", 1)[1] for a in argv if a.startswith("--gain=")), "10"))
    buffer_win = float(next((a.split("=", 1)[1] for a in argv if a.startswith("--buffer-win=")), "4"))
    threshold_uv = float(next((a.split("=", 1)[1] for a in argv if a.startswith("--threshold-uv=")), "0"))
    cal_offset_uv = float(next((a.split("=", 1)[1] for a in argv if a.startswith("--cal-offset-uv=")), "0"))
    if seq not in ("pp", "nn", "pn", "np"):
        raise ValueError("sequence must be pp/nn/pn/np")
    if not 5 <= max_step_ns <= 100:
        raise ValueError("max timestep must be between 5 and 100ns")
    if gain not in (10, 10.1, 10.2, 10.5, 30, 100):
        raise ValueError("closed-loop gain must be 10, 10.1, 10.2, 10.5, 30, or 100")
    if buffer_win not in (0.5, 1, 2, 4):
        raise ValueError("buffer OTA input width must be 0.5, 1, 2, or 4um")
    lines = [f"SKY130 TT buffered late differential readout {seq}", COMMON, HEADER]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    reference_lines = cell(f"r_{seq}", 0.90, None, long_bin=True)
    if threshold_uv:
        threshold_state_v = 0.90 + threshold_uv * 1e-6
        reference_lines = [line.replace("0.9", f"{threshold_state_v:.9f}") if line.startswith("Vinitlvl_r_") else line
                           for line in reference_lines]
        reference_lines = [line.replace("=0.9", f"={threshold_state_v:.9f}") if line.startswith(".ic v(out_r_") else line
                           for line in reference_lines]
    lines += reference_lines
    lines += [f"Vcmcal vcmcal 0 {0.9 + cal_offset_uv*1e-6:.9f}"]
    lines += [
        # The physical-cell 100ns common mode is ~0.8845V; precharge there
        # to avoid a deliberate gate-to-membrane step when the TG closes.
        f"Vgatecm_{seq} gatecm_{seq} 0 {precharge_v:.9f}",
        f"Vreset_{seq} reset_{seq} 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 4.9041m 0 4.9042m 1.8 5.005m 1.8)",
        f"Vresetb_{seq} resetb_{seq} 0 PWL(0 0 4.8999m 0 4.900m 1.8 4.904m 1.8 4.9041m 0 5.005m 0)",
        f"Vbn_{seq} vbnn_{seq} 0 PWL(0 0 4.8989m 0 4.899m 0.65 4.9042m 0.65 4.9043m 0 5.005m 0)",
        f"Vbp_{seq} vbpp_{seq} 0 PWL(0 1.8 4.8989m 1.8 4.899m 0.75 4.9042m 0.75 4.9043m 1.8 5.005m 1.8)",
        f"Xgs_{seq} gs_{seq} gatecm_{seq} reset_{seq} resetb_{seq} vdd 0 transmission_gate",
        f"Xgr_{seq} gr_{seq} gatecm_{seq} reset_{seq} resetb_{seq} vdd 0 transmission_gate",
        f"Xms_{seq} out_s_{seq} gs_{seq} resetb_{seq} reset_{seq} vdd 0 transmission_gate",
        f"Xmr_{seq} out_r_{seq} gr_{seq} resetb_{seq} reset_{seq} vdd 0 transmission_gate",
        f"Xbufs_{seq} buf_s_{seq} gs_{seq} buf_s_{seq} vbnn_{seq} vbpp_{seq} vdd 0 sky130_sc_ota win={buffer_win:g} wn3=2 wp3=27.8 cc=100f",
        f"Xbufr_{seq} buf_r_{seq} gr_{seq} buf_r_{seq} vbnn_{seq} vbpp_{seq} vdd 0 sky130_sc_ota win={buffer_win:g} wn3=2 wp3=27.8 cc=100f",
        f"Rbufs_{seq} buf_s_{seq} vcm 1Meg",
        f"Rbufr_{seq} buf_r_{seq} vcm 1Meg",
        f"Xgain_{seq} buf_r_{seq} inp_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=338",
        f"Xfeedback_{seq} readout_{seq} inp_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={338*(gain-1):g}",
        f"Rload_{seq} readout_{seq} vcm 1Meg",
        f"Xota_{seq} inp_{seq} buf_s_{seq} readout_{seq} vbnn_{seq} vbpp_{seq} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
        f"Xgaincal_{seq} buf_r_{seq} inpcal_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=338",
        f"Xfeedbackcal_{seq} calout_{seq} inpcal_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={338*(gain-1):g}",
        f"Rloadcal_{seq} calout_{seq} vcmcal 1Meg",
        f"Xotacal_{seq} inpcal_{seq} buf_r_{seq} calout_{seq} vbnn_{seq} vbpp_{seq} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
    ]
    threshold_tag = f"_th{threshold_uv:g}uv" if threshold_uv else ""
    trim_tag = f"_cm{cal_offset_uv:g}uv" if cal_offset_uv else ""
    step_tag = f"s{max_step_ns:g}n_rg1m_g{gain:g}_bw{str(buffer_win).replace('.', 'p')}{threshold_tag}{trim_tag}"
    data_name = f"sky130_sc_ota_buffered_diffreadout_{seq}_{step_tag}.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", f"tran {max_step_ns:g}n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(gs_{seq}) v(gr_{seq}) v(buf_s_{seq}) v(buf_r_{seq}) v(readout_{seq}) v(calout_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_buffered_diffreadout_{seq}_{step_tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir",
           "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "180", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=195)
    (RES / f"sky130_sc_ota_buffered_diffreadout_{seq}_{step_tag}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    rows = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(v) for v in line.split()])
            except ValueError:
                continue
    report = {"test": "sky130_tt_physical_membrane_unity_OTA_buffered_closedloop_readout", "sequence": seq, "closed_loop_gain": gain, "buffer_ota_input_width_um": buffer_win, "threshold_reference_uv": threshold_uv,
              "simulation_completed": run.returncode == 0 and len(rows) > 10, "return_code": run.returncode,
              "max_timestep_ns": max_step_ns, "gate_precharge_v": precharge_v, "calibration_reference_offset_uv": cal_offset_uv,
              "scope": f"TT schematic; physical MIM membrane pair; late-switched unity OTA buffers isolate membrane nodes from SKY130 xhigh-poly gain resistors; closed-loop gain~{gain}; no mismatch/noise/extraction"}
    if report["simulation_completed"]:
        at = lambda t: min(range(len(rows)), key=lambda i: abs(rows[i][0] - t))
        a, b, c = rows[at(4.89e-3)], rows[at(4.9039e-3)], rows[at(4.9044e-3)]
        d0, d1, d2 = a[1]-a[2], b[1]-b[2], c[1]-c[2]
        report.update({"state_diff_before_readout_uv": d0*1e6, "state_diff_at_readout_uv": d1*1e6,
                       "state_diff_after_readout_uv": d2*1e6, "state_diff_disturbance_uv": (d2-d0)*1e6,
                       "buffer_diff_at_readout_uv": (b[6]-b[5])*1e6, "output_v": b[7],
                       "output_diff_from_vcm_mv": (b[7]-0.9)*1e3,
                       "output_diff_from_buffer_common_uv": (b[7]-(b[5]+b[6])/2)*1e6,
                       "expected_gain_output_diff_mv": ((b[5]-b[6])*gain)*1e3,
                       "matched_baseline_output_v": b[8],
                       "offset_cancelled_output_difference_mv": (b[7]-b[8])*1e3,
                       "offset_cancelled_decision_matches_state_sign": ((b[7]-b[8])>0)==(d1>0),
                       "offset_cancelled_output_relation_error_uv": ((b[7]-b[8])-(b[5]-b[6])*gain)*1e6})
    out = RES / f"sky130_sc_ota_buffered_diffreadout_{seq}_{step_tag}.json"
    out.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
