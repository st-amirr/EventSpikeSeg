"""PVT-process/resistor screening for the buffered SKY130 differential readout."""
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
PROCESS = ("tt", "ss", "ff")
RESISTOR = ("typical", "high", "low")
ERROR_UV = 0.145
GAIN = 10.1

HEADER = r"""* SKY130 process-corner buffered readout amp-only precision screen
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
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    args = sys.argv[1:]
    corner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--corner=")), "tt")
    rcorner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--rescorner=")), "typical")
    temp = float(next((a.split("=", 1)[1] for a in args if a.startswith("--temp-c=")), "27"))
    if corner not in PROCESS or rcorner not in RESISTOR:
        raise ValueError("corner must be tt/ss/ff and rescorner typical/high/low")
    suffix = f"{corner}_r{rcorner}_t{temp:g}c"
    signals: list[str] = []
    outputs: list[str] = []
    for i, delta_uv in enumerate((-ERROR_UV, 0.0, ERROR_UV)):
        delta_v = delta_uv * 1e-6
        signals += [
            f"Vsig{i} sig{i} 0 {0.9+delta_v:.12f}", f"Vref{i} ref{i} 0 0.900000000000",
            f"Vbn{i} vbnn{i} 0 0.65", f"Vbp{i} vbpp{i} 0 0.75",
            f"Xbufs{i} bufs{i} sig{i} bufs{i} vbnn{i} vbpp{i} vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
            f"Xbufr{i} bufr{i} ref{i} bufr{i} vbnn{i} vbpp{i} vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
            f"Rbufs{i} bufs{i} vcm 1Meg", f"Rbufr{i} bufr{i} vcm 1Meg",
            f"Xrg{i} bufr{i} inp{i} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=338",
            f"Xrf{i} out{i} inp{i} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={338*(GAIN-1):g}",
            f"Rload{i} out{i} vcm 1Meg",
            f"Xamp{i} inp{i} bufs{i} out{i} vbnn{i} vbpp{i} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
            f"Xrgc{i} bufr{i} inpc{i} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=338",
            f"Xrfc{i} calout{i} inpc{i} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={338*(GAIN-1):g}",
            f"Rloadc{i} calout{i} vcm 1Meg",
            f"Xcal{i} inpc{i} bufr{i} calout{i} vbnn{i} vbpp{i} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
        ]
        outputs += [f"v(out{i})", f"v(calout{i})", f"v(bufs{i})", f"v(bufr{i})"]
    header = HEADER.replace("__tt.corner.spice", f"__{corner}.corner.spice")
    if rcorner != "typical":
        header = header.replace("res_typical__cap_typical__lin.spice", f"res_{rcorner}__cap_{rcorner}__lin.spice")
    deck = BENCH / f"sky130_sc_buffered_readout_corners_{suffix}.cir"
    deck.write_text(header + f".temp {temp:g}\n" + "\n".join(signals) + "\n.control\nop\nprint " + " ".join(outputs) + "\nquit\n.endc\n.end\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "30", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=40)
    log = run.stdout + run.stderr
    (RES / f"sky130_sc_buffered_readout_corners_{suffix}.log").write_text(log, encoding="utf-8")
    parsed = {name: float(value) for name, value in re.findall(r"v\(([^)]+)\)\s*=\s*([+\-0-9.eE]+)", log)}
    points = []
    for i, delta_uv in enumerate((-ERROR_UV, 0.0, ERROR_UV)):
        out, cal = parsed.get(f"out{i}"), parsed.get(f"calout{i}")
        bsignal, bref = parsed.get(f"bufs{i}"), parsed.get(f"bufr{i}")
        relation = None if out is None or cal is None else out-cal
        expected = None if bsignal is None or bref is None else GAIN*(bsignal-bref)
        points.append({"input_delta_uv": delta_uv, "signal_buffer_v": bsignal, "reference_buffer_v": bref,
                       "readout_v": out, "matched_baseline_v": cal,
                       "offset_cancelled_output_v": relation,
                       "expected_output_v_from_measured_buffer_delta": expected,
                       "input_equivalent_relation_error_uv": None if relation is None or expected is None else (relation-expected)/GAIN*1e6})
    report = {"test": "sky130_buffered_readout_process_resistor_corner_screen", "process_corner": corner,
              "resistor_corner": rcorner, "temperature_c": temp, "simulation_completed": run.returncode == 0 and len(parsed) == len(outputs),
              "return_code": run.returncode, "candidate_gain_trim": GAIN,
              "scope": "amp-only OP; physical xhigh-poly feedback network; two unity OTA buffers plus signal and matched-baseline gain stages; input-source differential ±0.145uV around0.9V; no physical membrane, mismatch, noise or extraction",
              "points": points}
    (RES / f"sky130_sc_buffered_readout_corners_{suffix}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
