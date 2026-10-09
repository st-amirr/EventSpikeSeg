"""Screen a PDK-switched 24-bit trim DAC mixed into a clocked latch input."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from characterize_sky130_sensor_vth_mismatch import PDK_MODEL, make_variant

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
MISMATCH = "--pdk-vth-1sigma" in sys.argv[1:]
SWAP = "--swap-mismatch" in sys.argv[1:]
SINGLE_DAC = "--single-dac" in sys.argv[1:]
DELTAS = (-10000.0, -1000.0, 0.0, 1000.0, 10000.0) if "--broad" in sys.argv[1:] else (-6.0, -0.537257883, 0.0, 0.537257883, 6.0)
CODE = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--trim-code=")), str((1 << 23) - 1)))


def case_name(delta: float) -> str:
    return "d" + str(delta).replace("-", "m").replace(".", "p")


def main() -> int:
    if not 0 <= CODE <= 0xFFFFFF:
        raise ValueError("trim code must be unsigned 24-bit")
    tag = f"code24_{CODE}" + ("_vth1sigma_swap" if MISMATCH and SWAP else "_vth1sigma" if MISMATCH else "")
    rows = [
        "SKY130 switched R-2R trim DAC into clocked latch input, TT/27C",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        '.include "../../../asic/analog/modules.spice"',
        '.include "../../../asic/analog/sky130_ms_r2r24.spice"',
        "Vdd vdd 0 1.8", "Vss vss 0 0", "Vcm vcm 0 0.9", "Vtrimhi trimhi 0 0.95", "Vtrimlo trimlo 0 0.85",
        "Vpre pre 0 PWL(0 1.8 0.499u 1.8 0.5u 0 5u 0)",
        "Vpreb preb 0 PWL(0 0 0.499u 0 0.5u 1.8 5u 1.8)",
        "Vclk clk 0 PWL(0 0 1.59u 0 1.61u 1.8 5u 1.8)",
        "Vclkbar clkbar 0 PWL(0 1.8 1.599u 1.8 1.6u 0 5u 0)",
    ]
    if MISMATCH:
        source = PDK_MODEL.read_text(encoding="ascii")
        plus = make_variant(source, "plus", 1)
        minus = make_variant(source, "minus", -1)
        model_dir = BENCH / "diff_sensor_probe"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "nfet_vthsigma_plus.spice").write_text(plus, encoding="ascii")
        (model_dir / "nfet_vthsigma_minus.spice").write_text(minus, encoding="ascii")
        rows += ['.include "diff_sensor_probe/nfet_vthsigma_plus.spice"',
                 '.include "diff_sensor_probe/nfet_vthsigma_minus.spice"']
    inp_model = "nfet_vthsigma_plus" if MISMATCH and not SWAP else ("nfet_vthsigma_minus" if MISMATCH else "sky130_fd_pr__nfet_01v8")
    inn_model = "nfet_vthsigma_minus" if MISMATCH and not SWAP else ("nfet_vthsigma_plus" if MISMATCH else "sky130_fd_pr__nfet_01v8")
    rows += [
        ".subckt regen inp inn clk outp outn vdd vss",
        "Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xln outp outn ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xrn outn outp ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xltail ltail clk vss vss sky130_fd_pr__nfet_01v8 w=8 l=0.5",
        f"Xin_p outp inp tail vss {inp_model} w=2 l=0.5",
        f"Xin_n outn inn tail vss {inn_model} w=2 l=0.5",
        "Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w=4 l=1",
        ".ends regen",
    ]
    code_p = CODE
    code_n = 0xFFFFFF - CODE
    for bit in range(24):
        rows += [f"Vbp{bit} bp{bit} 0 {(code_p >> bit) & 1}",
                 f"Vbn{bit} bn{bit} 0 {(code_n >> bit) & 1}"]
    pins_p = " ".join(f"bp{bit}" for bit in range(23, -1, -1))
    pins_n = " ".join(f"bn{bit}" for bit in range(23, -1, -1))
    rows += [f"Xdacp trim_p {pins_p} trimhi trimlo vdd 0 r2r_dac_u24"]
    if not SINGLE_DAC:
        rows += [f"Xdacn trim_n {pins_n} trimhi trimlo vdd 0 r2r_dac_u24"]
    for delta in DELTAS:
        name = case_name(delta)
        rows += [f"Vsig_{name} sig_{name} 0 {0.9+delta*0.5e-6:.12f}",
                 f"Vref_{name} ref_{name} 0 {0.9-delta*0.5e-6:.12f}",
                 f"Xpreinp_{name} inp_{name} vcm pre preb vdd 0 transmission_gate",
                 f"Xpreinn_{name} inn_{name} vcm pre preb vdd 0 transmission_gate",
                 f"Rsigp_{name} sig_{name} inp_{name} 1Meg", f"Rtrimp_{name} trim_p inp_{name} 1Meg",
                 f"Rsign_{name} ref_{name} inn_{name} 1Meg",
                 f"Rtrimn_{name} {'vcm' if SINGLE_DAC else 'trim_n'} inn_{name} 1Meg",
                 f"Xregen_{name} inp_{name} inn_{name} clk outp_{name} outn_{name} vdd vss regen",
                 f"Coutp_{name} outp_{name} 0 20f", f"Coutn_{name} outn_{name} 0 20f",
                 ]
    rows += [".control", "set numdgt=15", "tran 2n 5u",
             f"let dtrim=v(trim_p)-{'v(vcm)' if SINGLE_DAC else 'v(trim_n)'}",
             "meas tran trim_uv find dtrim at=1u"]
    for delta in DELTAS:
        name = case_name(delta)
        rows += [f"let in_diff_{name}=v(inp_{name})-v(inn_{name})",
                 f"let out_diff_{name}=v(outp_{name})-v(outn_{name})",
                 f"meas tran input_{name} find in_diff_{name} at=1.5u",
                 f"meas tran output_{name} find out_diff_{name} at=4.9u"]
    rows += ["quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    stem = f"sky130_physical_trim_dac_latch_{tag}"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(rows)+"\n", encoding="utf-8")
    command = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
               "-w", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
               "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(command, capture_output=True, text=True, timeout=75, cwd=ROOT)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {name: float(value) for name, value in re.findall(
        r"(?im)^\s*(trim_uv|input_[a-z0-9]+|output_[a-z0-9]+)\s*=\s*([-+0-9.eE]+)", log)}
    if run.returncode or "ngspice-36 done" not in log or len(values) != 1 + 2 * len(DELTAS):
        raise RuntimeError(f"physical trim DAC latch simulation failed:\n{log[-3000:]}")
    report = {"test": "sky130_physical_trim_dac_into_latch_input", "simulation_completed": True,
              "corner": "TT", "temperature_c": 27, "pdk_input_vth_mismatch_1sigma": MISMATCH,
              "mismatch_swapped": SWAP if MISMATCH else None, "trim_code24": CODE,
              "nominal_trim_differential_uv": ((2*CODE-0xFFFFFF)/0x1000000)*100000,
              "trim_topology": "single DAC against VCM" if SINGLE_DAC else "complementary DAC pair",
              "measured_trim_differential_uv": values["trim_uv"]*1e6,
              "cases": {str(d): {"mixed_latch_input_diff_uv": values[f"input_{case_name(d)}"]*1e6,
                                  "latch_output_diff_v": values[f"output_{case_name(d)}"]}
                         for d in DELTAS},
              "scope": (("One ideal-resistor R-2R ladder referenced to VCM with PDK transmission-gate bit switches and equal1Meg summing resistors into a clocked latch. Resistor mismatch, DAC extraction, sampled state MIM, noise, PVT and network replay are not included.") if SINGLE_DAC else ("Two complementary ideal-resistor R-2R ladders with PDK transmission-gate bit switches and equal1Meg analog summing resistors into a clocked latch. Resistor mismatch, DAC extraction, sampled state MIM, noise, PVT and network replay are not included."))}
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
