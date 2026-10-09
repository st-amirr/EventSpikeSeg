"""Check regenerative latch polarity from microvolt to large analog inputs."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
RES = OUT / "results"
BENCH = OUT / "benches"
PDK = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"


def main() -> int:
    scale = 0.21
    vcm = 0.865
    divider_ratio = 0.25
    # Symmetric differential sweep at fixed common mode. Include the measured
    # max-fanin bucket point as well as both polarities around zero.
    cases: dict[str, tuple[float, float]] = {}
    for delta_uv in (5, 12, 100, 1_000, 10_000, 25_000, 50_000, 100_000, 200_000):
        for sign, suffix in ((-1, "neg"), (1, "pos")):
            delta = sign * delta_uv * 1e-6
            name = f"d{delta_uv}_{suffix}"
            cases[name] = (vcm + delta / 2, vcm - delta / 2)
    cases["actual_max_fanin"] = (0.7750682, 0.9552072)
    rows: list[str] = ["SKY130 TT regenerative latch differential-input-range probe",
        ".option scale=1u", ".temp 27",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        ".include \"../../../asic/analog/modules.spice\"",
        "Vdd vdd 0 1.8", f"Vcm vcm 0 {vcm:g}",
        "Vpre pre 0 PWL(0 1.8 0.499u 1.8 0.5u 0 2u 0)",
        "Vpreb preb 0 PWL(0 0 0.499u 0 0.5u 1.8 2u 1.8)",
        "Vread read 0 PWL(0 0 0.599u 0 0.6u 1.8 1.499u 1.8 1.5u 0 2u 0)",
        "Vreadb readb 0 PWL(0 1.8 0.599u 1.8 0.6u 0 1.499u 0 1.5u 1.8 2u 1.8)",
        "Vclk clk 0 PWL(0 0 1.599u 0 1.6u 1.8 2u 1.8)",
        "Vclkbar clkbar 0 PWL(0 1.8 1.599u 1.8 1.6u 0 2u 0)",
        ".subckt weighted_regen inp inn clk clkbar outp outn vdd vss",
        "Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xln outp outn ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xrn outn outp ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xltail ltail clk vss vss sky130_fd_pr__nfet_01v8 w=8 l=0.5",
        "Xin_p outp inp tail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xin_n outn inn tail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w=4 l=1",
        f"Xptail ptail clkbar vdd vdd sky130_fd_pr__pfet_01v8 w={8*scale:g} l=1",
        f"Xpin_p outp inp ptail vdd sky130_fd_pr__pfet_01v8 w={2*scale:g} l=0.5",
        f"Xpin_n outn inn ptail vdd sky130_fd_pr__pfet_01v8 w={2*scale:g} l=0.5",
        ".ends weighted_regen"]
    for name, (sig, ref) in cases.items():
        rows += [f"Vsig_{name} sigsrc_{name} 0 {sig:.12g}",
                 f"Vref_{name} refsrc_{name} 0 {ref:.12g}",
                 f"Rsig_{name} sigsrc_{name} sig_{name} 30k",
                 f"Rbias_sig_{name} sig_{name} vcm 10k",
                 f"Rref_{name} refsrc_{name} ref_{name} 30k",
                 f"Rbias_ref_{name} ref_{name} vcm 10k",
                 f"Xpre_sig_{name} inp_{name} vcm pre preb vdd 0 transmission_gate",
                 f"Xpre_ref_{name} inn_{name} vcm pre preb vdd 0 transmission_gate",
                 f"Xread_sig_{name} sig_{name} inp_{name} read readb vdd 0 transmission_gate",
                 f"Xread_ref_{name} ref_{name} inn_{name} read readb vdd 0 transmission_gate",
                 f"Xregen_{name} inp_{name} inn_{name} clk clkbar outp_{name} outn_{name} vdd 0 weighted_regen",
                 f"Coutp_{name} outp_{name} 0 20f", f"Coutn_{name} outn_{name} 0 20f"]
    rows += [".control", "set numdgt=15", "tran 2n 2u uic"]
    for name in cases:
        rows += [f"let diff_{name}=v(inp_{name})-v(inn_{name})",
                 f"let latch_{name}=v(outp_{name})-v(outn_{name})",
                 f"meas tran input_{name} find diff_{name} at=1.55u",
                 f"meas tran output_{name} find latch_{name} at=1.9u"]
    rows += ["quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / "sky130_regenerative_latch_input_range_attenuated.cir"
    deck.write_text("\n".join(rows) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "-v", f"{ROOT}:/workspace", "-w", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60",
           "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / "sky130_regenerative_latch_input_range_attenuated.log").write_text(log, encoding="utf-8")
    values = {f"{kind}_{name}": float(value) for kind, name, value in re.findall(
        r"(?im)^\s*(input|output)_([a-zA-Z0-9_]+)\s*=\s*([-+0-9.eE]+)", log)}
    if run.returncode or "ngspice-36 done" not in log or len(values) != 2 * len(cases):
        raise RuntimeError(f"latch input range simulation failed or missed measurements:\n{log[-3000:]}")
    result = {name: {"input_diff_uv": values[f"input_{name}"] * 1e6,
                     "latch_output_diff_v": values[f"output_{name}"],
                     "expected_spike": sig > ref,
                     "observed_spike_from_latch_polarity": values[f"output_{name}"] < 0,
                     "decision_matches_expected": (values[f"output_{name}"] < 0) == (sig > ref)}
              for name, (sig, ref) in cases.items()}
    report = {"test": "sky130_regenerative_latch_input_range_pdk_transient",
              "corner": "TT", "temperature_c": 27, "pair_scale": scale,
              "input_common_mode_v": vcm, "source_to_latch_attenuation": divider_ratio,
              "divider": "30k series, 10k to VCM on both differential legs (ideal schematic resistors)",
              "simulation_completed": True,
              "cases": result,
              "scope": "Standalone transistor-level SKY130 clocked latch with minimum legal complementary PMOS input pair, a 4:1 resistive differential attenuator, and physical TG input capture. Attenuator is ideal schematic resistance; no OTA bucket, mismatch/noise, extracted layout or trim circuit."}
    (RES / "sky130_regenerative_latch_input_range_attenuated.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
