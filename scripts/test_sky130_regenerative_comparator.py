# Historical comparator screen: the latch lacked a clocked footer and resolved during precharge. Use test_sky130_regenerative_comparator_clocked.py for valid clock timing.
"""Bound a SKY130 clocked regenerative comparator around the mapped PLIF signal range."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RESULTS = OUT / "results"


def main() -> int:
    widths = (1.0, 2.0, 4.0)
    deltas_uv = (-26.0, -6.0, -3.0, 0.0, 3.0, 6.0, 26.0)
    lines = [
        "SKY130 TT clocked regenerative comparator differential input screen",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        ".include \"../pdk/sky130_fd_pr/models/parameters/invariant.spice\"",
        ".include \"../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice\"",
        ".include \"../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice\"",
        "Vdd vdd 0 1.8",
        "Vclk clk 0 PWL(0 0 99.9n 0 100n 1.8 500n 1.8)",
        "Vclkb clkb 0 PWL(0 1.8 99.9n 1.8 100n 0 500n 0)",
        ".subckt regen inp inn clk clkb outp outn vdd vss params: win=2 tailw=4",
        "Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xln outp outn vss vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xrn outn outp vss vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xin_p outp inp tail vss sky130_fd_pr__nfet_01v8 w={win} l=0.5",
        "Xin_n outn inn tail vss sky130_fd_pr__nfet_01v8 w={win} l=0.5",
        "Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w={tailw} l=1",
        ".ends regen",
    ]
    outputs = []
    for width in widths:
        for delta in deltas_uv:
            tag = f"w{width:g}_d{delta:g}".replace("-", "m").replace(".", "p")
            inp, inn = 0.9 + delta*0.5e-6, 0.9 - delta*0.5e-6
            lines += [f"Vin_{tag} in_{tag} 0 {inp:.12f}", f"Vim_{tag} im_{tag} 0 {inn:.12f}",
                      f"Xregen_{tag} in_{tag} im_{tag} clk clkb op_{tag} on_{tag} vdd 0 regen win={width:g}",
                      f"Cloadp_{tag} op_{tag} 0 20f", f"Cloadn_{tag} on_{tag} 0 20f"]
            outputs += [f"v(op_{tag})", f"v(on_{tag})"]
    data_name = "sky130_regenerative_comparator_screen.dat"
    deck = BENCH / "sky130_regenerative_comparator_screen.cir"
    data = RESULTS / data_name
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 0.2n 500n uic",
              f"wrdata ../results/{data_name} " + " ".join(outputs), "quit", ".endc", ".end"]
    deck.write_text("\n".join(lines)+"\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    log = run.stdout+run.stderr
    (RESULTS / "sky130_regenerative_comparator_screen.log").write_text(log, encoding="utf-8")
    rows = []
    if data.exists():
        for row in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(value) for value in row.split()])
            except ValueError:
                continue
    report = {"test":"sky130_clocked_regenerative_comparator_input_sensitivity",
              "simulation_completed":run.returncode == 0 and len(rows) > 100,
              "return_code":run.returncode,"input_differentials_uv":list(deltas_uv),
              "input_widths_um":list(widths),"evaluation_clock_rise_ns":100.0,
              "scope":"TT transistor-level schematic with ideal DC differential input and clock; symmetric devices, no mismatch, noise, source/MIM loading, threshold DAC, PVT or extraction; speed/logic screen only"}
    if report["simulation_completed"]:
        times=[row[0] for row in rows]
        measurements=[]
        for width in widths:
            for delta in deltas_uv:
                tag=f"w{width:g}_d{delta:g}".replace("-","m").replace(".","p")
                col=1+outputs.index(f"v(op_{tag})")
                coln=1+outputs.index(f"v(on_{tag})")
                series=[(row[0],row[col],row[coln]) for row in rows]
                decisions=[]
                for time_ns in (105,110,120,150,200,300,450):
                    row=min(series,key=lambda item:abs(item[0]-time_ns*1e-9))
                    decisions.append({"time_ns":time_ns,"outp_v":row[1],"outn_v":row[2],"diff_v":row[1]-row[2],
                                      "correct_polarity":(row[1]>row[2]) == (delta>0) if delta else None})
                first=next((point["time_ns"] for point in decisions if point["correct_polarity"] is True and abs(point["diff_v"])>0.5),None)
                measurements.append({"input_width_um":width,"input_differential_uv":delta,"first_regenerated_decision_ns":first,"samples":decisions})
        report["measurements"]=measurements
    (RESULTS / "sky130_regenerative_comparator_screen.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
