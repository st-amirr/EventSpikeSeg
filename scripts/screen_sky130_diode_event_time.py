"""Measure event-time dependence of an extracted-diode analog state candidate."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
PAIR = BENCH / "sky130_min_mim_pair_pex_reducedmim_subground.spice"
MOSCAP = ROOT / "artifacts/analog_asic/layout/sky130_moscap_pcell_probe_10x1_nf1/moscap_pcell_probe.spice"
DIODE_DIR = ROOT / "artifacts/analog_asic/layout/sky130_diode_pd2nw_05v5_probe_1x1"
DIODE = DIODE_DIR / "diode_pd2nw_05v5_probe_pex.spice"
QUAL = DIODE_DIR / "qualification.json"
STEM = "sky130_diode_event_time_ff85_ngspice47"


def main() -> None:
    args = sys.argv[1:]
    strict = "--strict" in args
    refined = "--refined" in args
    if strict and refined:
        raise ValueError("choose strict or refined tolerances")
    reverse = "--reverse-state" in args
    negative_event = "--negative-event" in args
    corner = args[args.index("--corner") + 1] if "--corner" in args else "ff"
    if corner not in ("tt", "ss", "ff"):
        raise ValueError("corner must be tt, ss, ff")
    temp_c = {"tt": 27, "ss": 0, "ff": 85}[corner]
    gmin = float(args[args.index("--gmin") + 1]) if "--gmin" in args else None
    if gmin is not None and not 0 < gmin <= 1e-12:
        raise ValueError("diagnostic gmin must be in (0, 1e-12]")
    offset_mv = float(args[args.index("--offset-mv") + 1]) if "--offset-mv" in args else 1.0
    early_scale = float(args[args.index("--early-scale") + 1]) if "--early-scale" in args else 1.0
    if not 0 < offset_mv <= 750 or not 0.5 <= early_scale <= 2:
        raise ValueError("offset or early scale outside bounded screen")
    stem = (STEM + (f"_offset{offset_mv:g}mv" if offset_mv != 1 else "")
            + (f"_earlyscale{early_scale:g}" if early_scale != 1 else ""))
    if gmin is not None:
        stem += f"_gmin{gmin:g}"
    if strict:
        stem += "_strict"
    if reverse:
        stem += "_reversed"
    if negative_event:
        stem += "_negativeevent"
    if corner != "ff":
        stem += f"_{corner}{temp_c}"
    if refined:
        stem += "_refined"
    stem += "_pwlprecise"
    low_v, high_v = 0.9 - offset_mv / 1000, 0.9 + offset_mv / 1000
    if reverse:
        low_v, high_v = high_v, low_v
    qual = json.loads(QUAL.read_text(encoding="utf-8"))
    if not (qual["magic_drc_zero"] and qual["netgen_lvs_unique_match"]
            and qual["ports_in_extracted_order"] == ["ANODE", "SUB", "CATHODE"]):
        raise RuntimeError("physical diode qualification failed")
    well_area = qual["estimated_nwell_area_um2_from_mag_rectangle"]
    well_perimeter = qual["estimated_nwell_perimeter_um_from_mag_rectangle"]
    lines = [
        "* Equal ideal charge events at two times on extracted diode state",
        (".option scale=1u reltol=1e-6 abstol=1e-17 vntol=1e-10 method=gear maxord=2" if refined else
         ".option scale=1u reltol=1e-6 abstol=1e-18 vntol=1e-11 method=gear maxord=2" if strict
         else ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2"),
        f'.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" {corner}',
        *[f'.include "/workspace/{p.relative_to(ROOT).as_posix()}"' for p in (PAIR, MOSCAP, DIODE)],
        f".temp {temp_c}", "Vcm vcm 0 0.9", "Vplus plus_idle 0 0", "Vminus minus_idle 0 1.8",
        f"Vlo init_low 0 {low_v:g}",
        f"Vhi init_high 0 {high_v:g}",
        "Vinit init_en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)",
        ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)",
    ]
    cases = {"control": None, "early": 0.5, "late": 4.5}
    for name, time_ms in cases.items():
        lo, hi = f"{name}_low", f"{name}_high"
        lines += [
            f"Xpair_{name} vcm {lo} vcm {hi} sky130_differential_trim_cap_pair",
            f"Sinit_{name}_low init_low {lo} init_en 0 ideal_init",
            f"Sinit_{name}_high init_high {hi} init_en 0 ideal_init",
        ]
        for side, node in (("low", lo), ("high", hi)):
            lines += [
                f"Xcap_{name}_{side} {node} 0 0 moscap_pcell_probe",
                f"Xplus_{name}_{side} plus_idle 0 {node} diode_pd2nw_05v5_probe",
                f"Xminus_{name}_{side} {node} 0 minus_idle diode_pd2nw_05v5_probe",
                f"Dwell_{name}_{side} 0 {node} sky130_fd_pr__model__parasitic__diode_ps2nw area={well_area:g} pj={well_perimeter:g}",
            ]
        if time_ms is not None:
            start_us = time_ms * 1000
            # Equal and opposite rail charge. SPICE positive current leaves the low node.
            amplitude = 2e-9 * (early_scale if name == "early" else 1.0)
            if negative_event:
                amplitude = -amplitude
            for side, node, current in (("low", lo, amplitude), ("high", hi, -amplitude)):
                times_us = [start_us, start_us + 0.001, start_us + 0.051, start_us + 0.052]
                rendered = [f"{time:.12g}" for time in times_us]
                actual = [float(time) for time in rendered]
                if not all(b > a for a, b in zip(actual, actual[1:])):
                    raise RuntimeError("serialized pulse edges are not increasing")
                duration_ns = (0.5 * (actual[1] - actual[0]) + actual[2] - actual[1]
                               + 0.5 * (actual[3] - actual[2])) * 1000
                if abs(duration_ns - 51) > 1e-5:
                    raise RuntimeError("serialized pulse charge differs from 51ns trapezoid")
                lines.append(f"Ievent_{name}_{side} {node} 0 PWL(0 0 {rendered[0]}u 0 "
                             f"{rendered[1]}u {current:.12g} {rendered[2]}u {current:.12g} "
                             f"{rendered[3]}u 0 5.01m 0)")
    if gmin is not None:
        lines.append(f".options gmin={gmin:g}")
    lines += [".control", "set numdgt=15", "tran 10n 5m" if strict or refined else "tran 20n 5m"]
    for name in cases:
        for side in ("low", "high"):
            for label, at in (("initial", "2u"), ("early_pre", "499u"),
                              ("early_post", "501u"), ("late_pre", "4499u"),
                              ("late_post", "4501u"), ("end", "5m")):
                lines.append(f"meas tran {name}_{side}_{label} find v({name}_{side}) at={at}")
    lines += ["quit", ".endc", ".end", ""]
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--env", "NGSPICE_MEAS_PRECISION=15",
           "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice47", "300", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=315, cwd=ROOT)
    log = proc.stdout + proc.stderr
    log_path = RESULTS / f"{stem}.log"
    log_path.write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*((?:control|early|late)_(?:low|high)_(?:initial|early_pre|early_post|late_pre|late_post|end))\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and "ngspice-47 done" in log and len(values) == 36
    initialization_pass = complete and all(
        abs(values[f"{name}_{side}_initial"] - target) < min(0.03, offset_mv * 0.0005)
        for name in cases for side, target in (("low", low_v), ("high", high_v)))
    rows = {}
    if complete:
        for name in cases:
            rows[name] = {label: (values[f"{name}_high_{label}"] - values[f"{name}_low_{label}"]) * 1e3
                          for label in ("initial", "early_pre", "early_post", "late_pre", "late_post", "end")}
        rows["incremental"] = {
            name: {label: rows[name][label] - rows["control"][label]
                   for label in ("early_post", "late_post", "end")}
            for name in ("early", "late")
        }
        rows["early_to_late_final_increment_ratio"] = (rows["incremental"]["early"]["end"]
                                                          / rows["incremental"]["late"]["end"])
    report = {
        "test": "sky130_extracted_diode_state_equal_charge_event_time",
        "simulation_completed": complete, "return_code": proc.returncode,
        "initialization_pass": initialization_pass,
        "simulator": "ngspice-47", "corner": corner.upper(), "temperature_c": temp_c,
        "strict_tolerances": strict,
        "refined_tolerances": refined,
        "maximum_time_step_ns": 10 if strict or refined else 20,
        "serialized_pulse_charge_checked": True,
        "reversed_state": reverse, "negative_event": negative_event,
        "gmin_siemens_requested": gmin,
        "initial_rail_offset_mv": offset_mv, "early_current_scale": early_scale,
        "event_current_a_per_rail": 2e-9, "event_flat_top_ns": 50,
        "event_total_trapezoid_ns": 51,
        "nominal_ideal_charge_c_per_rail": 1.02e-16,
        "signed_state_charge_c": {"low": 1.02e-16 if negative_event else -1.02e-16,
                                  "high": -1.02e-16 if negative_event else 1.02e-16},
        "event_times_ms": {"early": 0.5, "late": 4.5},
        "rows_mv": rows,
        "source_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (PAIR, MOSCAP, DIODE, QUAL, deck, log_path)},
        "limitations": "Ideal matched current events and ideal initialization on an unrouted combined state. Well junction is a geometry-based PDK proxy. This isolates event-time leakage response; it does not supply a physical signed injector, address selection, calibration, switched noise, full-float replay or service closure.",
    }
    out = RESULTS / f"{stem}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "simulation_completed": complete, "rows_mv": rows,
                      "error_tail": log[-1500:] if not complete else None}, indent=2))
    if not complete or not initialization_pass:
        raise RuntimeError(f"incomplete diode event-time screen: {log[-1500:]}")


if __name__ == "__main__":
    main()
