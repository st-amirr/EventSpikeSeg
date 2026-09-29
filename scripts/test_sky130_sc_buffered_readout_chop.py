"""Test two-phase signal/reference swapping on the buffered closed-loop readout."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
GAIN = 10.1
HEADER = r"""* SKY130 buffered closed-loop readout with signal/reference phase swap
.option scale=1u reltol=1e-6 abstol=1e-15 vntol=1e-9
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    args = sys.argv[1:]
    corner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--corner=")), "tt")
    rcorner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--rescorner=")), "typical")
    temp = float(next((a.split("=", 1)[1] for a in args if a.startswith("--temp-c=")), "27"))
    delta_uv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--delta-uv=")), "0.145"))
    common_v = float(next((a.split("=", 1)[1] for a in args if a.startswith("--common-mode-v=")), "0.9"))
    rf_length = float(next((a.split("=", 1)[1] for a in args if a.startswith("--rf-length=")), str(338*(GAIN-1))))
    if corner not in ("tt", "ss", "ff") or rcorner not in ("typical", "high", "low"):
        raise ValueError("corner must be tt/ss/ff; rescorner typical/high/low")
    cm_tag = f"_cm{common_v:g}v" if common_v != 0.9 else ""
    rf_tag = f"_rf{rf_length:g}" if rf_length != 338*(GAIN-1) else ""
    tag = f"{corner}_r{rcorner}_t{temp:g}c_d{delta_uv:g}uv{cm_tag}{rf_tag}"
    lines = [f"SKY130 buffered closed-loop chopped differential readout {tag}", HEADER]
    lines[1] = lines[1].replace("Vcm vcm 0 0.9", f"Vcm vcm 0 {common_v:.12f}")
    if rcorner != "typical":
        lines[1] = lines[1].replace("res_typical__cap_typical__lin.spice", f"res_{rcorner}__cap_{rcorner}__lin.spice")
    lines[1] = lines[1].replace("__tt.corner.spice", f"__{corner}.corner.spice")
    dv = delta_uv * 1e-6
    lines += [f".temp {temp:g}", f"Vsig sigsrc 0 {common_v+dv:.12f}", f"Vref refsrc 0 {common_v:.12f}",
              "Vbn vbnn 0 0.65", "Vbp vbpp 0 0.75",
              "Xbufs bufs sigsrc bufs vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
              "Xbufr bufr refsrc bufr vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
              "Rbufs bufs vcm 1Meg", "Rbufr bufr vcm 1Meg",
              "VselA sela 0 PWL(0 1.8 10.1u 1.8 10.2u 0 22.1u 0 22.2u 1.8 29.9u 1.8 30u 0)",
              "VselAb selab 0 PWL(0 0 10.1u 0 10.2u 1.8 22.1u 1.8 22.2u 0 29.9u 0 30u 1.8)",
              "VselB selb 0 PWL(0 0 10.1u 0 10.2u 1.8 22.1u 1.8 22.2u 0 29.9u 0 30u 1.8)",
              "VselBb selbb 0 PWL(0 1.8 10.1u 1.8 10.2u 0 22.1u 0 22.2u 1.8 29.9u 1.8 30u 0)",
              "Xra bufr refsel sela selab vdd 0 transmission_gate", "Xrb bufs refsel selb selbb vdd 0 transmission_gate",
              "Xsa bufs sigsel sela selab vdd 0 transmission_gate", "Xsb bufr sigsel selb selbb vdd 0 transmission_gate",
              "Xrg refsel inp 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=338",
              f"Xrf out inp 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={rf_length:g}",
              "Rload out vcm 1Meg", "Xamp inp sigsel out vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f"]
    dat_name = f"sky130_sc_buffered_readout_chop_{tag}.dat"
    dat = RES / dat_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 10n 30u uic",
              f"wrdata ../results/{dat_name} v(out) v(bufs) v(bufr) v(refsel) v(sigsel)", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_buffered_readout_chop_{tag}.cir"
    deck.write_text("\n".join(lines)+"\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    (RES/f"sky130_sc_buffered_readout_chop_{tag}.log").write_text(run.stdout+run.stderr,encoding="utf-8")
    rows=[]
    if dat.exists():
        for line in dat.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(x) for x in line.split()])
            except ValueError: continue
    report={"test":"sky130_buffered_closedloop_readout_chopper_screen","process_corner":corner,"resistor_corner":rcorner,
            "temperature_c":temp,"input_differential_uv":delta_uv,"simulation_completed":run.returncode==0 and len(rows)>10,
            "return_code":run.returncode,"scope":"amp-only transient; physical unity OTA buffers and xhigh-poly closed-loop readout; same OTA reads normal and swapped inputs; no membrane, comparator latch, mismatch/noise/extraction"}
    if report["simulation_completed"]:
        at=lambda t:min(range(len(rows)),key=lambda i:abs(rows[i][0]-t))
        a1,b1,b2,a2=(rows[at(t)] for t in (10.0e-6,16.0e-6,22.0e-6,28.0e-6))
        out_a=(a1[1]+a2[1])*.5; out_b=(b1[1]+b2[1])*.5
        chopped=(out_a-out_b)*.5
        expected=GAIN*delta_uv*1e-6
        report.update({"phase_a_outputs_v":[a1[1],a2[1]],"phase_b_outputs_v":[b1[1],b2[1]],"chopped_output_uv":chopped*1e6,
                       "expected_chopped_output_uv":expected*1e6,"input_equivalent_chopped_error_uv":(chopped-expected)/GAIN*1e6,
                       "phase_a_buffer_diff_uv":[(a1[2]-a1[3])*1e6,(a2[2]-a2[3])*1e6],
                       "phase_b_buffer_diff_uv":[(b1[2]-b1[3])*1e6,(b2[2]-b2[3])*1e6],
                       "input_delta_sign_correct":(chopped>0)==(delta_uv>0)})
    (RES/f"sky130_sc_buffered_readout_chop_{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
