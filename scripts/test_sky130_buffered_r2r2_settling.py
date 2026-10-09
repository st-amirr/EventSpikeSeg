#!/usr/bin/env python3
"""Transient code-change and settling screen for the extracted TG/R-2R path."""
from __future__ import annotations

import json
import re
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAY = ROOT / "artifacts/analog_asic/layout"
OUT = ROOT / "artifacts/analog_asic/results/sky130_buffered_tg_r2r2_settling"
IMAGE = "eventspikeseg:analog-ngspice36"
PDK = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
LADDER_TOP = "sky130_physical_r2r2_slice_raw"
BANK_TOP = "sky130_parallel_tg_bank_32_raw"


def gate_points(bit: str, rail: str, selected_codes: list[int]) -> tuple[str, str]:
    # The code is held for 5us. Switches open for100ns before the next code
    # connects, preventing the low and high analog reference rails from shorting.
    transitions = [(0.0, selected_codes[0])]
    for i in range(1, 4):
        transitions += [(i * 5.0 - 0.1, 0), (i * 5.0, 0),
                        (i * 5.0 + 0.0001, selected_codes[i])]
    en_values = []
    for time_us, val in transitions:
        en_values.extend((f"{time_us:g}u", "1.8" if val else "0"))
    enb_values = []
    for time_us, val in transitions:
        enb_values.extend((f"{time_us:g}u", "0" if val else "1.8"))
    return "PWL(" + " ".join(en_values) + ")", "PWL(" + " ".join(enb_values) + ")"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc-f", type=float, default=500e-15)
    parser.add_argument("--wn3", type=float, default=20.0)
    parser.add_argument("--wp3", type=float, default=100.0)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    dc_path = ROOT / "artifacts/analog_asic/results/sky130_buffered_tg_r2r2/buffered_tg_r2r2.json"
    dc_report = json.loads(dc_path.read_text(encoding="utf-8"))
    dc_outputs = dc_report["temperature_and_corner"]
    ladder = LAY / "sky130_physical_r2r2_slice/sky130_physical_r2r2_slice.spice"
    bank = LAY / "sky130_parallel_tg_bank_32/sky130_parallel_tg_bank_32_pex.spice"
    source = ladder.read_text(encoding="ascii")
    body_match = re.search(r"(?im)^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41", source)
    if not body_match or not bank.exists():
        raise RuntimeError("Missing extracted ladder or TG32 bank")
    body = body_match.group(1)
    reports = {}
    for corner, temp, vbn, vbp in (("tt", 27, 0.65, 0.75),
                                   ("ss", 0, 0.55, 0.65),
                                   ("ff", 85, 0.65, 0.75)):
        lines = [
            f"* SKY130 {corner.upper()} buffered extracted TG32/R-2R code transition settling",
            ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear",
            f".temp {temp}",
            f'.include "{PDK}/models/parameters/invariant.spice"',
            f'.include "{PDK}/models/r+c/res_typical__cap_typical__lin.spice"',
            f'.include "{PDK}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',
            f'.include "{PDK}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
            f'.include "{PDK}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',
            f'.include "{PDK}/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
            f'.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
            f'.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
            f'.include "/workspace/{ladder.relative_to(ROOT).as_posix()}"',
            f'.include "/workspace/{bank.relative_to(ROOT).as_posix()}"',
            '.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"',
            f".global {body}",
            ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
            ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
            f"Vbody {body} 0 0", "Vdd vdd 0 1.8", "Vss vss 0 0",
            "Vhi rail_hi 0 0.95", "Vlo rail_lo 0 0.85", "Vlo_ref vlo 0 0.85", "Vcm cm 0 0.9",
        ]
        codes = range(4)
        for bit in ("b1", "b0"):
            values = [((code >> 1) if bit == "b1" else (code & 1)) for code in codes]
            for rail, selected in (("hi", values), ("lo", [1-v for v in values])):
                enpwl, enbpwl = gate_points(bit, rail, selected)
                en, enb = f"en_{bit}_{rail}", f"enb_{bit}_{rail}"
                lines += [f"V{en} {en} 0 {enpwl}", f"V{enb} {enb} 0 {enbpwl}"]
                ctrl = " ".join(node for _ in range(32) for node in (en, enb))
                rail_node = "rail_hi" if rail == "hi" else "rail_lo"
                lines += [f"Xsw_{bit}_{rail} {rail_node} raw_{bit} {ctrl} vdd vss {BANK_TOP}"]
            lines += [f"Vbn_{bit} vbnn_{bit} 0 {vbn}", f"Vbp_{bit} vbpp_{bit} 0 {vbp}",
                      f"Xbuf_{bit} buf_{bit} raw_{bit} buf_{bit} vbnn_{bit} vbpp_{bit} vdd 0 sky130_sc_ota wn3={args.wn3:g} wp3={args.wp3:g} cc={args.cc_f:g}"]
        lines += [f"Xdac out vlo buf_b1 buf_b0 {LADDER_TOP}", "Rload out cm 100Meg",
                  ".control", "set numdgt=15", "set wr_singlescale", "set wr_vecnames",
                  "tran 10n 16u", "wrdata /workspace/artifacts/analog_asic/results/sky130_buffered_tg_r2r2_settling/trace_"+corner+".dat v(out)",
                  "quit", ".endc", ".end", ""]
        deck = OUT / f"settling_{corner}.cir"
        deck.write_text("\n".join(lines), encoding="ascii")
        cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v", f"{ROOT}:/workspace",
               "-w", "/workspace/artifacts/analog_asic/results", "--entrypoint", "ngspice", IMAGE,
               "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=150)
        log = run.stdout + run.stderr
        (OUT / f"settling_{corner}.log").write_text(log, encoding="utf-8")
        dat = OUT / f"trace_{corner}.dat"
        rows = []
        if dat.exists():
            for row in dat.read_text(encoding="ascii").splitlines()[1:]:
                try:
                    values = list(map(float, row.split()))
                    rows.append((values[0], values[-1]))
                except ValueError:
                    continue
        if run.returncode or "ngspice-36 done" not in log or len(rows) < 100:
            raise RuntimeError(f"{corner} transient did not complete: {log[-2500:]}")
        measurements = []
        for code in range(4):
            start, stop = code*5e-6, min((code+1)*5e-6, 16e-6)
            key = f"{corner.upper()}_{temp}C"
            target = dc_outputs[key]["output_v"][code]
            transition = start + (0 if code == 0 else 0.1e-9)
            tol = 25e-6
            settling = None
            tail = [(t, v) for t, v in rows if t >= transition]
            for idx, (t, v) in enumerate(tail):
                window = [(t2, v2) for t2, v2 in tail[idx:] if t2 <= stop-0.05e-6]
                if t < stop-0.05e-6 and window and all(abs(v2-target) <= tol for _, v2 in window):
                    settling = t-transition
                    break
            measurements.append({"code": code, "target_dc_v": target,
                                 "settling_time_s_to_25uv": settling})
        reports[f"{corner.upper()}_{temp}C"] = {"bias_v": {"vbiasn": vbn, "vbiasp": vbp},
            "sample_count": len(rows), "measurements": measurements,
            "max_abs_output_v": max(abs(v) for _, v in rows)}
    result = {"test": "sky130_extracted_tg32_buffered_r2r2_code_transition_settling",
        "simulation_completed": True, "temperature_and_corner": reports,
        "buffer_output_stage_um": {"wn3": args.wn3, "wp3": args.wp3},
        "compensation_capacitance_f": args.cc_f,
        "scope": "32-device TG bank PEX with extracted capacitances, extracted resistor ladder, schematic SKY130 OTA bit followers at corner-screened biases; ideal digital gate edges with100ns break-before-make; no gate-driver layout, OTA layout/PEX, mismatch, noise or full-float replay.",
        "all_codes_settle_to_dc_within_25uv_before_next_change": all(
            item["settling_time_s_to_25uv"] is not None and item["settling_time_s_to_25uv"] < 5e-6
            for corner_row in reports.values() for item in corner_row["measurements"]),
        "qualification": "DC-code transfer plus settling screen only; not a qualified event-weight path or neuron macro."}
    (OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["all_codes_settle_to_dc_within_25uv_before_next_change"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
