"""Screen a transistor-level monotonic differential preamp ahead of the latch."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
RES = OUT / "results"
BENCH = OUT / "benches"


def main() -> int:
    vcm = 0.9
    cases: dict[str, tuple[float, float]] = {}
    for delta_uv in (5, 12, 100, 1_000, 10_000, 50_000, 100_000, 200_000):
        for sign, suffix in ((-1, "neg"), (1, "pos")):
            d = sign * delta_uv * 1e-6
            cases[f"d{delta_uv}_{suffix}"] = (vcm + d/2, vcm - d/2)
    rows = [
        "SKY130 TT monotonic readout preamplifier range probe",
        ".option scale=1u", ".temp 27",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        '.include "../../../asic/analog/modules.spice"',
        "Vdd vdd 0 1.8",
        "Vena ena 0 PWL(0 1.8 0.99u 1.8 1u 0 1.55u 0 1.56u 1.8 2u 1.8)",
        "Vpre pre 0 PWL(0 1.8 1.499u 1.8 1.5u 0 2u 0)",
        "Vpreb preb 0 PWL(0 0 1.499u 0 1.5u 1.8 2u 1.8)",
        "Vclk clk 0 PWL(0 0 1.599u 0 1.6u 1.8 2u 1.8)",
        "Vclkbar clkbar 0 PWL(0 1.8 1.599u 1.8 1.6u 0 2u 0)",
        # PMOS differential pair produces bounded, monotonic voltage output;
        # tail is clocked only for the read aperture.
        ".subckt monotonic_pre inp inn ena op on tailout vdd vss",
        "Xtail tailout ena vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=1",
        "Xinp op inp tailout vdd sky130_fd_pr__pfet_01v8 w=4 l=1",
        "Xinn on inn tailout vdd sky130_fd_pr__pfet_01v8 w=4 l=1",
        "Rop op 0 2k", "Ron on 0 2k",
        ".ends monotonic_pre",
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
        "Xtailn tail clk vss vss sky130_fd_pr__nfet_01v8 w=4 l=1",
        ".ends weighted_regen",
    ]
    for name, (sig, ref) in cases.items():
        rows += [f"Vsig_{name} sig_{name} 0 {sig:.12g}",
                 f"Vref_{name} ref_{name} 0 {ref:.12g}",
                 f"Xpreamp_{name} sig_{name} ref_{name} ena op_{name} on_{name} tail_{name} vdd 0 monotonic_pre",
                 # Swap the inverting PMOS-preamp outputs into the latch so
                 # positive model differential maps to the spike polarity.
                 f"Xlatch_{name} on_{name} op_{name} clk clkbar outp_{name} outn_{name} vdd 0 weighted_regen",
                 f"Coutp_{name} outp_{name} 0 20f", f"Coutn_{name} outn_{name} 0 20f"]
    rows += [".control", "set numdgt=15", "tran 2n 2u uic"]
    for name in cases:
        rows += [f"let preamp_{name}=v(op_{name})-v(on_{name})",
                 f"let latch_{name}=v(outp_{name})-v(outn_{name})",
                 f"meas tran pre_{name} find preamp_{name} at=1.55u",
                 f"meas tran opp_{name} find v(op_{name}) at=1.55u",
                 f"meas tran onn_{name} find v(on_{name}) at=1.55u",
                 f"meas tran tail_{name} find v(tail_{name}) at=1.55u",
                 f"meas tran latch_{name} find latch_{name} at=1.9u"]
    rows += ["quit", ".endc", ".end"]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / "sky130_monotonic_readout_preamplifier.cir"
    deck.write_text("\n".join(rows) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "-v", f"{ROOT}:/workspace", "-w", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60",
           "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / "sky130_monotonic_readout_preamplifier.log").write_text(log, encoding="utf-8")
    vals = {(kind, name): float(value) for kind, name, value in re.findall(
        r"(?im)^\s*(pre|opp|onn|tail|latch)_([a-zA-Z0-9_]+)\s*=\s*([-+0-9.eE]+)", log)}
    if run.returncode or "ngspice-36 done" not in log or len(vals) != len(cases)*5:
        raise RuntimeError(f"preamp screen failed or lacked measurements:\n{log[-3000:]}")
    result = {name: {"input_diff_uv": (sig-ref)*1e6,
                     "preamp_diff_v": vals[("pre", name)],
                     "preamp_output_common_mode_v": (vals[("opp", name)]+vals[("onn", name)])/2,
                     "preamp_tail_v": vals[("tail", name)],
                     "latch_diff_v": vals[("latch", name)],
                     "expected_spike": sig > ref,
                     "observed_spike": vals[("latch", name)] < 0,
                     "decision_matches": (vals[("latch", name)] < 0) == (sig > ref)}
              for name, (sig, ref) in cases.items()}
    report = {"test": "sky130_monotonic_readout_preamplifier_transient_screen",
              "corner": "TT", "temperature_c": 27, "input_common_mode_v": vcm,
              "preamp_topology": "clocked PMOS differential pair, 2k resistive loads, stronger tail bias",
              "simulation_completed": True, "cases": result,
              "scope": "Transistor-level front-end and clocked regenerative latch only. Bias is ideal and no mismatch/noise, OTA bucket, extracted layout, or energy/area accounting is included."}
    (RES / "sky130_monotonic_readout_preamplifier.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
