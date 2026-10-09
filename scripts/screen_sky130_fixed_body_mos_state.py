"""Screen physical MOS-gate/MIM storage with fixed-body PEX TG and shared bus."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
PAIR = BASE / "benches/sky130_min_mim_pair_pex_reducedmim_subground.spice"
MOSCAP = BASE / "layout/sky130_moscap_pcell_probe_10x1_nf1/moscap_pcell_probe.spice"
TG = BASE / "layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corner", choices=("ss", "tt", "ff"), default="ff")
    parser.add_argument("--offset-mv", type=float, default=1)
    parser.add_argument("--gmin", type=float, default=1e-18)
    parser.add_argument("--refined", action="store_true")
    args = parser.parse_args()
    if not 0 < args.offset_mv <= 750 or not 0 < args.gmin <= 1e-12:
        raise ValueError("offset/GMIN outside bounded diagnostic")
    temp = {"ss": 0, "tt": 27, "ff": 85}[args.corner]
    low, high = 0.9 - args.offset_mv / 1000, 0.9 + args.offset_mv / 1000
    cases = ("bare", "fixed_body", "fixed_body_overdrive")
    stem = (f"sky130_fixed_body_pex_tg_mos_state_{args.corner}{temp}_offset{args.offset_mv:g}mv"
            f"_gmin{args.gmin:g}" + ("_refined" if args.refined else ""))
    lines = ["* Physical MOS gate storage + reduced MIM + fixed-body physical TG; shared VCM source",
             (".options scale=1u reltol=1e-6 abstol=1e-16 vntol=1e-10 method=gear maxord=2" if args.refined else
              ".options scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2"),
             f".options gmin={args.gmin:g}", f'.lib "{LIB}" {args.corner}',
             *[f'.include "/workspace/{p.relative_to(ROOT).as_posix()}"' for p in (PAIR, MOSCAP, TG)],
             f".temp {temp}", "Vcm vcm 0 0.9", "Vdd vdd 0 1.8",
             f"Vlo init_low 0 {low:.12g}", f"Vhi init_high 0 {high:.12g}",
             "Vgn gn 0 0", "Vgp gp 0 1.8", "Vgn_boost gn_boost 0 -0.3", "Vgp_boost gp_boost 0 2.1",
             "Vinit init_en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)",
             ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)"]
    for case in cases:
        lo, hi = f"{case}_low", f"{case}_high"
        lines.append(f"Xpair_{case} vcm {lo} vcm {hi} sky130_differential_trim_cap_pair")
        for side, state in (("low", lo), ("high", hi)):
            lines += [f"Xcap_{case}_{side} {state} 0 0 moscap_pcell_probe",
                      f"Sinit_{case}_{side} init_{side} {state} init_en 0 ideal_init"]
            if case != "bare":
                gates = "gn_boost gp_boost" if case.endswith("overdrive") else "gn gp"
                lines.append(f"Xaccess_{case}_{side} vcm {state} {gates} vdd 0 sky130_transmission_gate_raw")
    lines += [".control", "set numdgt=15", "tran 0.5u 5m" if args.refined else "tran 1u 5m"]
    for case in cases:
        for side in ("low", "high"):
            for when, time in (("start", "2u"), ("end", "5m")):
                lines.append(f"meas tran {case}_{side}_{when} find v({case}_{side}) at={time}")
    lines += ["quit", ".endc", ".end", ""]
    deck = BASE / f"benches/{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "4g", "--cpus", "2",
           "--env", "NGSPICE_MEAS_PRECISION=15", "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice47", "180", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=195)
    log = proc.stdout + proc.stderr
    log_path = BASE / f"results/{stem}.log"
    log_path.write_text(log, encoding="utf-8")
    values = {k: float(v) for k, v in re.findall(
        r"(?m)^\s*((?:bare|fixed_body(?:_overdrive)?)_(?:low|high)_(?:start|end))\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and "ngspice-47 done" in log and len(values) == 12
    rows = []
    if complete:
        for case in cases:
            row = {"case": case, **{k: values[f"{case}_{k}"]
                                    for k in ("low_start", "low_end", "high_start", "high_end")}}
            row["initialization_error_v"] = {"low": row["low_start"] - low, "high": row["high_start"] - high}
            initial = (row["high_start"] - row["low_start"]) * 1000
            final = (row["high_end"] - row["low_end"]) * 1000
            row.update(initial_differential_mv=initial, end_differential_mv=final,
                       differential_drift_mv=final-initial,
                       common_mode_drift_mv=((row["low_end"]-row["low_start"])
                                             +(row["high_end"]-row["high_start"])) * 500,
                       retained_signed_fraction=final/initial)
            rows.append(row)
    init_tolerance = max(5e-6, args.offset_mv / 1000 * 0.005)
    initialization_pass = complete and all(abs(error) < init_tolerance
                                          for row in rows for error in row["initialization_error_v"].values())
    report = {"test": "sky130_fixed_body_shared_bus_physical_mos_state_hold",
              "simulation_completed": complete, "initialization_screen_pass": initialization_pass,
              "initialization_screen_tolerance_v": init_tolerance, "return_code": proc.returncode,
              "corner": args.corner.upper(), "temperature_c": temp,
              "gmin_siemens_requested": args.gmin, "rail_offset_mv": args.offset_mv,
              "refined_tolerances": args.refined, "rows": rows,
              "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (PAIR, MOSCAP, TG, deck, log_path)},
              "limitations": "Independent physical component views only; combined cell unrouted. Reduced nominal minimum-MIM C keeps physical couplings; MOS gate PCell contributes PDK nonlinear capacitance. Fixed-body TG includes capacitive PEX. Ideal initialization and static gate biases; boost -0.3/2.1V has no generator/reliability qualification. Model MOS gate leakage coverage, well/substrate network, real write/read disturbance, noise/mismatch, signed events, full-float fidelity, area and5ms population service remain open. Initialization screen is diagnostic, not an accuracy acceptance criterion."}
    out = BASE / f"results/{stem}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "completed": complete, "initialization_pass": initialization_pass,
                      "rows": rows, "error_tail": log[-1000:] if not complete else None}, indent=2))
    if not complete or not initialization_pass:
        raise RuntimeError("physical fixed-body state screen incomplete or initialization outside diagnostic bound")


if __name__ == "__main__":
    main()
