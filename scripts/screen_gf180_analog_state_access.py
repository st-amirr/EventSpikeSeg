"""Bounded GF180MCU schematic switch hold screen for analog-state process triage."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "artifacts/analog_asic/pdk/gf180_screen/sm141064.ngspice"
DESIGN = MODEL.parent / "design.ngspice"
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
STEM = "gf180_schematic_tg_ideal100ff_hold_ff85_ngspice47"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offset-mv", type=float, default=750)
    parser.add_argument("--body-v", type=float, default=3.3)
    parser.add_argument("--corner", choices=("ff", "ss", "typical"), default="ff")
    parser.add_argument("--temp-c", type=float, default=85)
    parser.add_argument("--family", choices=("3p3", "6p0"), default="3p3")
    parser.add_argument("--gmin", type=float, default=None)
    parser.add_argument("--vcm-v", type=float, default=0.9)
    parser.add_argument("--refined", action="store_true")
    parser.add_argument("--mos-gate-storage", action="store_true")
    parser.add_argument("--event-time", action="store_true")
    args = parser.parse_args()
    if args.gmin is not None and not 0 < args.gmin <= 1e-12:
        raise ValueError("diagnostic gmin must be in (0, 1e-12]")
    if not 0 < args.offset_mv <= 750 or not 1.8 <= args.body_v <= 3.3:
        raise ValueError("state offset/body voltage outside bounded screen")
    if not 0.9 <= args.vcm_v <= 1.65 or args.vcm_v + args.offset_mv / 1000 > args.body_v:
        raise ValueError("state/common-mode voltage exceeds bounded reverse-biased body window")
    stem = STEM
    if (args.offset_mv, args.body_v, args.corner, args.temp_c, args.family) != (750, 3.3, "ff", 85, "3p3"):
        stem = (f"gf180_schematic_tg_{args.family}_ideal100ff_hold_{args.corner}_temp{args.temp_c:g}"
                f"_offset{args.offset_mv:g}mv_body{args.body_v:g}v_ngspice47")
    length_um = 0.28 if args.family == "3p3" else 0.7
    if args.gmin is not None:
        stem += f"_gmin{args.gmin:g}"
    if args.vcm_v != 0.9:
        stem += f"_vcm{args.vcm_v:g}v"
    if args.refined:
        stem += "_refined"
    if args.mos_gate_storage:
        stem += "_mosgate10x1"
    if args.event_time:
        stem += "_equalevents"
    model_sha = hashlib.sha256(MODEL.read_bytes()).hexdigest()
    if model_sha != "73fc67d38747d95ce03f3c2ba5f0a25c98f56a293363a9df4c971a3a28a3dcda":
        raise RuntimeError("GF180 source model changed")
    lines = [
        "* GF180MCU FF/85C schematic switch hold; ideal 100fF analog states",
        (".option reltol=1e-6 abstol=1e-18 vntol=1e-11 method=gear maxord=2" if args.refined else
         ".option reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2"),
        '.include "/workspace/artifacts/analog_asic/pdk/gf180_screen/design.ngspice"',
        ".param sw_stat_global=0 sw_stat_mismatch=0",
        f'.lib "/workspace/artifacts/analog_asic/pdk/gf180_screen/sm141064.ngspice" {args.corner}',
        f".temp {args.temp_c:g}", f"Vbus bus 0 {args.vcm_v:g}", f"Vdd vdd 0 {args.body_v:g}",
        f"Vlo init_low 0 {args.vcm_v-args.offset_mv/1000:g}",
        f"Vhi init_high 0 {args.vcm_v+args.offset_mv/1000:g}",
        "Ven en 0 0", "Venb enb 0 3.3",
        "Vinit init_en 0 PWL(0 3.3 0.9u 3.3 1u 0 5.01m 0)",
        ".model ideal_init SW(Ron=10 Roff=1e30 Vt=1.65 Vh=0.1)",
    ]
    kinds = ("tg_control", "tg_early", "tg_late", "ideal_control", "ideal_early", "ideal_late") if args.event_time else ("tg", "ideal")
    for kind in kinds:
        for side, init in (("low", "init_low"), ("high", "init_high")):
            node = f"{kind}_{side}"
            lines.append(f"Sinit_{node} {init} {node} init_en 0 ideal_init")
            if args.mos_gate_storage:
                lines.append(f"Xstore_{node} 0 {node} 0 0 nmos_{args.family} w=10u l=1u as=5p ad=5p ps=21u pd=21u")
            else:
                lines.append(f"C_{node} {node} 0 100f")
            if kind.startswith("tg"):
                # Diagnostic diffusion geometry, 0.5um source/drain extension per side.
                lines += [
                    f"Xn_{node} bus en {node} 0 nmos_{args.family} w=1u l={length_um:g}u as=0.5p ad=0.5p ps=3u pd=3u",
                    f"Xp_{node} bus enb {node} vdd pmos_{args.family} w=2u l={length_um:g}u as=1p ad=1p ps=5u pd=5u",
                ]
            if args.event_time and not kind.endswith("control"):
                start_us = 500 if kind.endswith("early") else 4500
                amplitude = 2e-9 if side == "low" else -2e-9
                lines.append(f"Ievent_{node} {node} 0 PWL(0 0 {start_us:.12g}u 0 "
                             f"{start_us+0.001:.12g}u {amplitude:.12g} {start_us+0.051:.12g}u {amplitude:.12g} "
                             f"{start_us+0.052:.12g}u 0 5.01m 0)")
    if args.gmin is not None:
        lines.append(f".options gmin={args.gmin:g}")
    step = "20n" if args.event_time else "0.5u" if args.refined else "1u"
    lines += [".control", "set numdgt=15", f"tran {step} 5m"]
    for kind in kinds:
        for side in ("low", "high"):
            for label, at in (("start", "2u"), ("end", "5m")):
                lines.append(f"meas tran {kind}_{side}_{label} find v({kind}_{side}) at={at}")
    lines += ["quit", ".endc", ".end", ""]
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "4g", "--cpus", "2",
           "--env", "NGSPICE_MEAS_PRECISION=15", "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/gf180_screen",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice47", "120", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=135, cwd=ROOT)
    log = proc.stdout + proc.stderr
    log_path = RESULTS / f"{stem}.log"
    log_path.write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*((?:tg|ideal)(?:_(?:control|early|late))?_(?:low|high)_(?:start|end))\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and "ngspice-47 done" in log and len(values) == 4 * len(kinds)
    rows = {}
    if complete:
        for kind in kinds:
            rows[kind] = {side: {"start_v": values[f"{kind}_{side}_start"],
                                  "end_v": values[f"{kind}_{side}_end"],
                                  "drift_mv": (values[f"{kind}_{side}_end"]
                                               - values[f"{kind}_{side}_start"]) * 1000}
                          for side in ("low", "high")}
            rows[kind]["initial_differential_mv"] = (values[f"{kind}_high_start"]
                                                       - values[f"{kind}_low_start"]) * 1000
            rows[kind]["end_differential_mv"] = (values[f"{kind}_high_end"]
                                                   - values[f"{kind}_low_end"]) * 1000
        if args.event_time:
            for group in ("tg", "ideal"):
                early = rows[f"{group}_early"]["end_differential_mv"] - rows[f"{group}_control"]["end_differential_mv"]
                late = rows[f"{group}_late"]["end_differential_mv"] - rows[f"{group}_control"]["end_differential_mv"]
                rows[f"{group}_event_time"] = {"early_final_increment_mv": early,
                                                "late_final_increment_mv": late,
                                                "early_to_late_ratio": early / late}
    report = {
        "test": f"gf180mcu_schematic_{args.family}_tg_analog_state_process_screen",
        "simulation_completed": complete, "return_code": proc.returncode,
        "corner": args.corner.upper(), "temperature_c": args.temp_c, "simulator": "ngspice-47",
        "rail_offset_mv": args.offset_mv, "pmos_body_v": args.body_v,
        "shared_bus_common_mode_v": args.vcm_v,
        "refined_tolerances": args.refined,
        "mos_gate_storage": args.mos_gate_storage,
        "equal_charge_event_time": args.event_time,
        "ideal_charge_c_per_rail": 1.02e-16 if args.event_time else None,
        "gmin_siemens_requested": args.gmin,
        "six_volt_corner_caveat": "6p0 models in the ff library are typical; ff is not a qualified fast 6V corner" if args.family == "6p0" else None,
        "source_model_url": "https://github.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr/blob/main/models/ngspice/sm141064.ngspice",
        "source_model_sha256": model_sha,
        "design_switches_sha256": hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
        "state_capacitance_f_per_rail": None if args.mos_gate_storage else 100e-15,
        "storage_geometry": "schematic10/1um NMOS, D/S/B grounded" if args.mos_gate_storage else "ideal100fF",
        "switch_geometry": f"schematic nmos_{args.family} 1/{length_um:g}um, pmos_{args.family} 2/{length_um:g}um; diagnostic source/drain extensions 0.5um",
        "rows": rows,
        "source_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (MODEL, DESIGN, deck, log_path)},
        "limitations": "Exploratory cross-process schematic only. Storage is either ideal100fF or schematic MOS gate capacitance as identified above; access diffusion areas, gate control and initial programming are assumed/ideal. Event mode uses ideal equal-charge sources, not a physical injector. No GF180 physical layout, DRC/LVS/PEX, well/substrate network, complete device-corner validation, mismatch/noise, write/read, physical signed event precision, 5ms service or full-float replay. Do not compare as a qualified migration to SKY130 physical PEX.",
    }
    out = RESULTS / f"{stem}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "simulation_completed": complete,
                      "rows": rows, "error_tail": log[-1600:] if not complete else None}, indent=2))
    if not complete:
        raise RuntimeError(f"GF180 process screen incomplete: {log[-1600:]}")


if __name__ == "__main__":
    main()
