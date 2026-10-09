#!/usr/bin/env python3
"""Screen OTA buffering between extracted TG bit sources and R-2R ladder."""
from __future__ import annotations

import json
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAY = ROOT / "artifacts/analog_asic/layout"
OUT = ROOT / "artifacts/analog_asic/results/sky130_buffered_tg_r2r2"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corner", choices=("tt", "ss", "ff", "all"), default="all")
    parser.add_argument("--ideal-buffer", action="store_true",
                        help="replace the OTA followers with ideal voltage sources at the selected rail")
    parser.add_argument("--wn3", type=float, default=2.0)
    parser.add_argument("--wp3", type=float, default=27.8)
    parser.add_argument("--cc-f", type=float, default=500e-15)
    parser.add_argument("--vbiasn", type=float, default=0.65)
    parser.add_argument("--vbiasp", type=float, default=0.75)
    parser.add_argument("--ss-vbiasn", type=float)
    parser.add_argument("--ss-vbiasp", type=float)
    parser.add_argument("--ff-vbiasn", type=float)
    parser.add_argument("--ff-vbiasp", type=float)
    args = parser.parse_args()
    if args.cc_f <= 0:
        raise ValueError("--cc-f must be positive")
    OUT.mkdir(parents=True, exist_ok=True)
    ladder = LAY / "sky130_physical_r2r2_slice/sky130_physical_r2r2_slice.spice"
    bank = LAY / "sky130_parallel_tg_bank_32/sky130_parallel_tg_bank_32_pex.spice"
    pdk = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
    ladder_body = re.search(
        r"(?im)^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41", ladder.read_text()
    )
    if not ladder_body or not bank.exists():
        raise RuntimeError("missing extracted ladder or 32-TG physical bank")
    body = ladder_body.group(1)
    cases = {}
    corner_rows = (("tt", 27), ("ss", 0), ("ff", 85))
    if args.corner != "all":
        corner_rows = tuple(row for row in corner_rows if row[0] == args.corner)
    for corner, temp in corner_rows:
        vbn = args.vbiasn if corner == "tt" or args.ss_vbiasn is None and corner == "ss" or args.ff_vbiasn is None and corner == "ff" else (args.ss_vbiasn if corner == "ss" else args.ff_vbiasn)
        vbp = args.vbiasp if corner == "tt" or args.ss_vbiasp is None and corner == "ss" or args.ff_vbiasp is None and corner == "ff" else (args.ss_vbiasp if corner == "ss" else args.ff_vbiasp)
        outputs = []
        for code in range(4):
            lines = [
                "* Extracted 32-TG bit source, closed-loop OTA followers, extracted R-2R",
                ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
                f".temp {temp}",
                f'.include "{pdk}/models/parameters/invariant.spice"',
                f'.include "{pdk}/models/r+c/res_typical__cap_typical__lin.spice"',
                f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',
                f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
                f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',
                f'.include "{pdk}/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
                f'.include "{pdk}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
                f'.include "{pdk}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
                f'.include "/workspace/{ladder.relative_to(ROOT).as_posix()}"',
                f'.include "/workspace/{bank.relative_to(ROOT).as_posix()}"',
                '.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"',
                f".global {body}",
                ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
                ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
                f"Vbody {body} 0 0", "Vdd vdd 0 1.8", "Vss vss 0 0",
                "Vhi rail_hi 0 0.95", "Vlo rail_lo 0 0.85", "Vlo_ref vlo 0 0.85", "Vcm cm 0 0.9",
            ]
            bits = {"b1": code >> 1, "b0": code & 1}
            bank_instances = []
            for bit, val in bits.items():
                for rail, selected in (("hi", val), ("lo", 1 - val)):
                    if not selected:
                        continue
                    en, enb = f"en_{bit}_{rail}", f"enb_{bit}_{rail}"
                    lines += [f"V{en} {en} 0 1.8", f"V{enb} {enb} 0 0"]
                    pins = " ".join(x for _ in range(32) for x in (en, enb))
                    source = "rail_hi" if rail == "hi" else "rail_lo"
                    target = f"raw_{bit}"
                    lines += [f"X{bit}_{rail} {source} {target} {pins} vdd vss sky130_parallel_tg_bank_32_raw"]
            for bit in ("b1", "b0"):
                if args.ideal_buffer:
                    selected = bits[bit]
                    voltage = 0.95 if selected else 0.85
                    lines += [f"Vbuf_{bit} buf_{bit} 0 {voltage}"]
                else:
                    lines += [
                        f"Vbn_{bit} vbnn_{bit} 0 {vbn:g}",
                        f"Vbp_{bit} vbpp_{bit} 0 {vbp:g}",
                        f"Xbuf_{bit} buf_{bit} raw_{bit} buf_{bit} vbnn_{bit} vbpp_{bit} vdd 0 sky130_sc_ota wn3={args.wn3:g} wp3={args.wp3:g} cc={args.cc_f:g}",
                    ]
            lines += [
                f"Xdac out vlo buf_b1 buf_b0 sky130_physical_r2r2_slice_raw",
                "Rload out cm 100Meg", ".control", "set numdgt=15", "op", "print v(out)",
                "print v(raw_b1) v(raw_b0) v(buf_b1) v(buf_b0)", "quit", ".endc", ".end", "",
            ]
            tag = f"{corner}_code{code}"
            deck = OUT / f"buffered_{tag}.cir"
            deck.write_text("\n".join(lines), encoding="ascii")
            cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v",
                   f"{ROOT}:/workspace", "-w", "/workspace/artifacts/analog_asic/results",
                   "--entrypoint", "ngspice", IMAGE, "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
            run = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=90)
            log = run.stdout + run.stderr
            (OUT / f"buffered_{tag}.log").write_text(log, encoding="utf-8")
            vals = [float(v) for v in re.findall(r"(?im)^\s*v\(out\)\s*=\s*([-+0-9.eE]+)", log)]
            if run.returncode or "ngspice-36 done" not in log or not vals:
                raise RuntimeError(f"{tag} SPICE failed: {log[-2500:]}")
            outputs.append(vals[-1])
        steps = [outputs[i + 1] - outputs[i] for i in range(3)]
        mean = sum(steps) / len(steps)
        cases[f"{corner.upper()}_{temp}C"] = {
            "output_v": outputs,
            "steps_v": steps,
            "strictly_monotonic": all(x > 0 for x in steps),
            "max_step_deviation_from_mean_pct": max(abs(x / mean - 1) for x in steps) * 100,
            "vbiasn_v": vbn,
            "vbiasp_v": vbp,
        }
    report = {
        "test": "sky130_extracted_tg32_ideal_bit_buffers_r2r2_dc" if args.ideal_buffer else "sky130_extracted_tg32_ota_bit_buffers_r2r2_dc",
        "simulation_completed": True,
        "temperature_and_corner": cases,
        "buffer": ("ideal bit-rail voltage sources after extracted TG bank (control); no physical buffer" if args.ideal_buffer else f"one schematic closed-loop sky130_sc_ota voltage follower per R-2R bit input; PDK MOS, wn3={args.wn3:g}um wp3={args.wp3:g}um cc={args.cc_f*1e15:g}fF vbiasn={args.vbiasn:g}V vbiasp={args.vbiasp:g}V; schematic only"),
        "scope": "32-device TG-bank PEX plus extracted seven-resistor ladder; selected branches only; DC transfer only, no buffer layout/PVT mismatch/noise/settling/full-float replay.",
    }
    report["all_output_codes_within_0_to_1p8_v"] = all(
        0.0 <= voltage <= 1.8
        for corner_row in cases.values()
        for voltage in corner_row["output_v"]
    )
    report["tested_subset_transfer_pass"] = (
        report["all_output_codes_within_0_to_1p8_v"]
        and all(row["strictly_monotonic"] for row in cases.values())
        and max(row["max_step_deviation_from_mean_pct"] for row in cases.values()) < 1.0
    )
    report["buffer_transfer_qualified"] = (
        set(cases) == {"TT_27C", "SS_0C", "FF_85C"}
        and report["tested_subset_transfer_pass"]
    )
    report_name = "ideal_buffer_tg_r2r2.json" if args.ideal_buffer else "buffered_tg_r2r2.json"
    (OUT / report_name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["buffer_transfer_qualified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
