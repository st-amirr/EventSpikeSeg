#!/usr/bin/env python3
"""Test a high-impedance PDK preamp plus regenerative latch on membrane state."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import BENCH, RES, ROOT

IMAGE = "eventspikeseg:analog-ngspice36"
DELTAS_UV = (-110.0, -20.0, 20.0, 110.0)
VCM = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--vcm=")), "1.05"))
LATCH_TRIM_UV = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--latch-trim-uv=")), "0"))
CORNER = next((a.split("=", 1)[1].lower() for a in sys.argv[1:] if a.startswith("--corner=")), "tt")
TEMP = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--temp=")), {"tt": 27, "ss": 0, "ff": 85}.get(CORNER, 27)))
VBIAS = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--vbias=")), "0.7"))
DIRECT_PAIR = "--direct-pair" in sys.argv[1:]
INPUT_SIZE = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--input-size=")), "1"))
LATCH_INPUT_SIZE = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--latch-input-size=")), "1"))


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 differential preamplifier plus regenerative range latch",
             ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
             '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
             '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
             ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
             f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{CORNER}.corner.spice"',
             f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{CORNER}.corner.spice"',
             '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
             '.include "../../../asic/analog/modules.spice"',
             '.include "../../../asic/analog/sky130_ms_plif.spice"',
             f".temp {TEMP:g}", "Vdd vdd 0 1.8", f"Vcm vcm 0 {VCM:g}", f"Vbias vbias 0 {VBIAS:g}",
             "Vinit init 0 PWL(0 1.8 2.49u 1.8 2.51u 0 2.75u 0)",
             "Vinitb initb 0 PWL(0 0 2.49u 0 2.51u 1.8 2.75u 1.8)",
             "Vclk clk 0 PWL(0 0 2.63u 0 2.65u 1.8 2.75u 1.8)",
             ".subckt sense_preamp inp inn outp outn vbias vdd vss",
             *( [f"Xip outp inp tail vss sky130_fd_pr__nfet_01v8 w={10*INPUT_SIZE:g} l=0.5",
                 f"Xin outn inn tail vss sky130_fd_pr__nfet_01v8 w={10*INPUT_SIZE:g} l=0.5",
                 "Xtail tail vbias vss vss sky130_fd_pr__nfet_01v8 w=5 l=1",
                 "Xload1 outp outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
                 "Xload2 outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5"] if DIRECT_PAIR else
                [f"Xip d1 inp tail vss sky130_fd_pr__nfet_01v8 w={10*INPUT_SIZE:g} l=0.5",
                 f"Xin d2 inn tail vss sky130_fd_pr__nfet_01v8 w={10*INPUT_SIZE:g} l=0.5",
                 "Xtail tail vbias vss vss sky130_fd_pr__nfet_01v8 w=5 l=1",
                 "Xload1 d1 d1 vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
                 "Xload2 d2 d1 vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
                 "Xbufp outp d1 vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
                 "Xbufn outp d1 vss vss sky130_fd_pr__nfet_01v8 w=10 l=0.5",
                 "Xbufp2 outn d2 vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=0.5",
                 "Xbufn2 outn d2 vss vss sky130_fd_pr__nfet_01v8 w=10 l=0.5"]),
             ".ends sense_preamp",
             ".subckt regen inp inn clk outp outn vdd vss",
             "Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
             "Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
             "Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
             "Xln outp outn ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
             "Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
             "Xrn outn outp ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
             "Xlatch_tail ltail clk vss vss sky130_fd_pr__nfet_01v8 w=8 l=0.5",
             f"Xin_p outp inp tail vss sky130_fd_pr__nfet_01v8 w={2*LATCH_INPUT_SIZE:g} l=0.5",
             f"Xin_n outn inn tail vss sky130_fd_pr__nfet_01v8 w={2*LATCH_INPUT_SIZE:g} l=0.5",
             "Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w=4 l=1",
             ".ends regen"]
    vectors: list[str] = []
    for delta in DELTAS_UV:
        tag = str(delta).replace("-", "m").replace(".", "p")
        sig, ref = f"mem_{tag}", f"ref_{tag}"
        sp, sn, li, lj, lp, ln = f"sp_{tag}", f"sn_{tag}", f"li_{tag}", f"lj_{tag}", f"lp_{tag}", f"ln_{tag}"
        target = VCM + delta * 1e-6
        lines += [f"Vtarget_{tag} target_{tag} 0 {target:.12f}",
                  f"Xcmem_{tag} {sig} vcm membrane_mim w_um=100 l_um=100",
                  f"Xcref_{tag} {ref} vcm membrane_mim w_um=100 l_um=100",
                  f"Xinit_mem_{tag} target_{tag} {sig} init initb vdd 0 transmission_gate",
                  f"Xinit_ref_{tag} vcm {ref} init initb vdd 0 transmission_gate",
                  f"Xpre_{tag} {sig} {ref} {sp} {sn} vbias vdd 0 sense_preamp",
                  f"Vtrim_p_{tag} {li} {sp} {LATCH_TRIM_UV*0.5:g}u",
                  f"Vtrim_n_{tag} {lj} {sn} {-LATCH_TRIM_UV*0.5:g}u",
                  f"Xlatch_{tag} {li} {lj} clk {lp} {ln} vdd 0 regen",
                  f"Cloadp_{tag} {lp} 0 20f", f"Cloadn_{tag} {ln} 0 20f"]
        vectors += [f"v({lp})", f"v({ln})", f"v({sig})", f"v({ref})", f"v({sp})", f"v({sn})", f"v({li})", f"v({lj})"]
    vcm_tag = f"{VCM:g}".replace("-", "m").replace(".", "p")
    stem = f"sky130_piecewise_preamplified_latch_{CORNER}_temp{TEMP:g}_vbias{VBIAS:g}_input{INPUT_SIZE:g}x_latchinput{LATCH_INPUT_SIZE:g}x_vcm{vcm_tag}_trim{LATCH_TRIM_UV:g}uv" + ("_directpair" if DIRECT_PAIR else "_buffered")
    deck, data = BENCH / f"{stem}.cir", RES / f"{stem}.dat"
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 2n 2.75u uic",
              f"wrdata ../results/{data.name} " + " ".join(vectors), "quit", ".endc", ".end"]
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{ROOT/'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           IMAGE, "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=150)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    raw: list[list[float]] = []
    if data.exists():
        for row in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                vals = [float(x) for x in row.split()]
                if len(vals) == 1 + 8*len(DELTAS_UV):
                    raw.append(vals)
            except ValueError:
                pass
    complete = run.returncode == 0 and len(raw) > 100 and "tran simulation(s) aborted" not in log.lower()
    report = {"test": "sky130_pdk_differential_preamp_regenerative_range_latch",
              "simulation_completed": complete, "corner": CORNER.upper(), "temperature_c": TEMP,
              "preamp_tail_bias_v": VBIAS,
              "preamp_input_width_scale": INPUT_SIZE,
              "latch_input_width_scale": LATCH_INPUT_SIZE,
              "common_mode_v": VCM, "input_differentials_uv": list(DELTAS_UV),
              "ideal_latch_trim_uv": LATCH_TRIM_UV,
              "preamp_output": "differential pair drain nodes" if DIRECT_PAIR else "buffered pair outputs",
              "state_cap": "two physical 100x100um SKY130 MIM capacitors per case",
              "sample_switch": False, "scope": "Schematic PDK differential input pair and regenerative latch connected directly to physical MIM state; no read TG, trim, PEX, noise, mismatch, event injector or full model replay."}
    if complete:
        def at(ns: float) -> list[float]:
            return min(raw, key=lambda row: abs(row[0]-ns*1e-9))
        rows = []
        for i, delta in enumerate(DELTAS_UV):
            b = 1 + 8*i
            early, before, preeval, decision20, decision50, decision90, after = [at(t) for t in (2568, 2590, 2629.8, 2670, 2700, 2740, 2745)]
            d_before = (before[b+2]-before[b+3])*1e6
            d_pre = (preeval[b+2]-preeval[b+3])*1e6
            d_after = (after[b+2]-after[b+3])*1e6
            output_diff = decision20[b]-decision20[b+1]
            output50 = decision50[b]-decision50[b+1]
            output90 = decision90[b]-decision90[b+1]
            rows.append({"requested_input_uv": delta,
                         "state_diff_before_eval_uv": d_before,
                         "state_diff_at_latch_uv": d_pre,
                         "state_diff_after_latch_uv": d_after,
                         "state_disturbance_vs_before_uv": d_after-d_before,
                         "latch_output_diff_at_20ns_v": output_diff,
                         "latch_output_diff_at_50ns_v": output50,
                         "latch_output_diff_at_90ns_v": output90,
                         "decision_matches_state_sign": (output_diff > 0) == (d_pre > 0),
                         "decision_matches_state_sign_at_90ns": (output90 > 0) == (d_pre > 0),
                         "preamp_diff_before_latch_v": preeval[b+4]-preeval[b+5],
                         "latch_input_diff_before_latch_v": preeval[b+6]-preeval[b+7]})
        report["measurements"] = rows
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
