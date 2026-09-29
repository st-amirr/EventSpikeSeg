"""Estimate the isolated SKY130 regenerative latch input capacitance by AC admittance."""
from __future__ import annotations
import cmath
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
STEM = "sky130_regenerative_isolated_input_capacitance"


def main() -> int:
    lines = [
        "SKY130 clocked latch isolated input AC admittance at precharge bias",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        '.include "../../../asic/analog/modules.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vclk clk 0 0", "Vread read 0 0", "Vreadb readb 0 1.8", "Vpre pre 0 0", "Vpreb preb 0 1.8",
        "Itest inp vcm DC 0 AC 1", "Rbias inp vcm 1e15", "Rmem mem vcm 1e15", "Cmem mem vcm 20p",
        "Xread mem inp read readb vdd 0 transmission_gate", "Xpreinp inp vcm pre preb vdd 0 transmission_gate",
        "Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xln outp outn ltail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xrn outn outp ltail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xlatchtail ltail clk 0 0 sky130_fd_pr__nfet_01v8 w=8 l=0.5",
        "Xin_p outp inp tail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xin_n outn vcm tail 0 sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xtail tail clk 0 0 sky130_fd_pr__nfet_01v8 w=4 l=1",
        "Cloadp outp 0 20f", "Cloadn outn 0 20f",
        ".control", "set wr_singlescale", "set wr_vecnames", "ac dec 10 100k 10meg", f"wrdata ../results/{STEM}.dat v(inp)", "quit", ".endc", ".end",
    ]
    deck = BENCH / f"{STEM}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"{STEM}.log").write_text(log, encoding="utf-8")
    data = RES / f"{STEM}.dat"
    rows = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                row = [float(value) for value in line.split()]
                if len(row) >= 3:
                    rows.append(row)
            except ValueError:
                continue
    report = {"test": "sky130_isolated_latch_input_ac_capacitance", "simulation_completed": run.returncode == 0 and bool(rows), "return_code": run.returncode, "scope": "TT small-signal AC at 0.9V precharge bias, clock/read/input-precharge gates off; approximate off-switch plus latch input-node capacitance, excludes switched thermal-noise correlation and regeneration"}
    if report["simulation_completed"]:
        points = []
        for row in rows:
            freq = row[0]
            voltage = complex(row[1], row[2])
            admittance = -1 / voltage
            c_eff = abs(admittance.imag) / (2 * math.pi * freq)
            points.append({"frequency_hz": freq, "input_voltage_real_v_per_a": row[1], "input_voltage_imag_v_per_a": row[2], "effective_capacitance_f": c_eff, "kTC_rms_uv_300K": math.sqrt(1.380649e-23 * 300 / c_eff) * 1e6})
        report["points"] = points
    (RES / f"{STEM}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
