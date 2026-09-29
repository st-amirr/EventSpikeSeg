"""Test active closed-loop OTA readout against physically stored SC membrane states."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

ROOT = Path(__file__).resolve().parents[1]
SEQUENCES = ("pp", "nn", "pn", "np")
HEADER = r"""* SKY130 physical membrane pair with closed-loop OTA differential readout
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    seq = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--sequence=")), "pp")
    gain_tag = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--gain=")), "10")
    if seq not in SEQUENCES:
        raise ValueError(f"sequence must be one of {SEQUENCES}")
    gain = int(gain_tag)
    if gain not in (10, 30):
        raise ValueError("gain must be 10 or 30")
    # Gain 10 uses approximately 100k total feedback resistance to limit
    # current drawn from the reference membrane; gain 30 uses about 300k.
    rg_len = 33.8  # ~100k at w=1.41um
    rf_len = 601.0 if gain == 10 else 197.0 * 10.0
    read_enable = "PWL(0 0 4.8999m 0 4.900m 1.8 4.9039m 1.8 4.904m 0 5.005m 0)"
    read_enable_b = "PWL(0 1.8 4.8999m 1.8 4.900m 0 4.9039m 0 4.904m 1.8 5.005m 1.8)"
    lines = [f"SKY130 TT physical differential closed-loop OTA readout gain{gain} {seq}", COMMON, HEADER]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
    lines += [
        f"Vread_{seq} read_{seq} 0 {read_enable}",
        f"Vreadb_{seq} readb_{seq} 0 {read_enable_b}",
        f"Xsig_{seq} out_s_{seq} sig_s_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Xref_{seq} out_r_{seq} ref_r_{seq} read_{seq} readb_{seq} vdd 0 transmission_gate",
        f"Xgain_{seq} ref_r_{seq} inp_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={rg_len:g}",
        f"Xfeedback_{seq} readout_{seq} inp_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={rf_len:g}",
        f"Rload_{seq} readout_{seq} vcm 1Meg",
        f"Vbnro_{seq} vbnn_ro_{seq} 0 0.65",
        f"Vbpro_{seq} vbpp_ro_{seq} 0 0.75",
        f"Xota_{seq} inp_{seq} sig_s_{seq} readout_{seq} vbnn_ro_{seq} vbpp_ro_{seq} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
    ]
    data_name = f"sky130_sc_ota_physical_diffreadout_{seq}_g{gain}.dat"
    data = RES / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 100n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(sig_s_{seq}) v(ref_r_{seq}) v(readout_{seq})", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_physical_diffreadout_{seq}_g{gain}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"sky130_sc_ota_physical_diffreadout_{seq}_g{gain}.log").write_text(log, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(value) for value in line.split()])
            except ValueError:
                continue
    report = {
        "test": "sky130_tt_physical_membrane_pair_closedloop_ota_readout",
        "simulation_completed": run.returncode == 0 and len(rows) > 10,
        "return_code": run.returncode,
        "sequence": seq,
        "target_gain": gain,
        "scope": "TT schematic; physical MIM membrane integrators and SKY130 xhigh-poly feedback resistors; late TG input connection at 4.9ms; no noise, mismatch, extraction or full model",
    }
    if report["simulation_completed"]:
        tpre = min(range(len(rows)), key=lambda i: abs(rows[i][0] - 4.89e-3))
        tread = min(range(len(rows)), key=lambda i: abs(rows[i][0] - 4.9039e-3))
        tpost = min(range(len(rows)), key=lambda i: abs(rows[i][0] - 4.9041e-3))
        a, b, c = rows[tpre], rows[tread], rows[tpost]
        d_pre, d_read, d_post = a[1] - a[2], b[1] - b[2], c[1] - c[2]
        output_pre, output_read = a[5], b[5]
        out_relative_to_reference = output_read - b[4]
        ideal_output_relative_to_reference = gain * (b[3] - b[4])
        report.update({
            "state_diff_before_readout_uv": d_pre * 1e6,
            "state_diff_at_readout_uv": d_read * 1e6,
            "state_diff_after_readout_uv": d_post * 1e6,
            "state_diff_readout_disturbance_uv": (d_post - d_pre) * 1e6,
            "output_change_from_pre_readout_mv": (output_read - output_pre) * 1e3,
            "output_relative_to_reference_mv": out_relative_to_reference * 1e3,
            "ideal_output_relative_to_reference_mv": ideal_output_relative_to_reference * 1e3,
            "output_relation_error_mv": (out_relative_to_reference - ideal_output_relative_to_reference) * 1e3,
            "reference_common_mode_v": b[4],
            "readout_output_v": output_read,
        })
    out_path = RES / f"sky130_sc_ota_physical_diffreadout_{seq}_g{gain}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
