"""Bounded 5 ms hold screen of the isolated body-tied TG physical probe.

The MIM is a nominal-capacitance reduction of a routed pair. Magic PEX does
not extract deep-well junction leakage; this script does not qualify retention.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
BENCH = BASE / "benches"
RESULTS = BASE / "results"
PEX = BASE / "layout/sky130_body_tied_transmission_gate/sky130_body_tied_transmission_gate_pex.spice"
PAIR = BENCH / "sky130_min_mim_pair_pex_reducedmim_subground.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> None:
    version = "47" if "--ngspice47" in sys.argv else "36"
    strict = "--strict" in sys.argv
    refined = "--refined" in sys.argv
    if strict and refined:
        raise ValueError("choose strict or refined tolerances")
    initial_condition = "--initial-condition" in sys.argv
    off_overdrive = float(sys.argv[sys.argv.index("--off-overdrive-v") + 1]) if "--off-overdrive-v" in sys.argv else 0.0
    if not 0 <= off_overdrive <= 0.3:
        raise ValueError("off-gate diagnostic overdrive must be in [0,0.3] V")
    init_ron = float(sys.argv[sys.argv.index("--init-ron") + 1]) if "--init-ron" in sys.argv else 10.0
    init_roff = float(sys.argv[sys.argv.index("--init-roff") + 1]) if "--init-roff" in sys.argv else 1e30
    if not 10 <= init_ron <= 1000 or not 1e18 <= init_roff <= 1e30:
        raise ValueError("initializer resistance outside bounded diagnostic")
    gmin = float(sys.argv[sys.argv.index("--gmin") + 1]) if "--gmin" in sys.argv else None
    if gmin is not None and not 0 < gmin <= 1e-12:
        raise ValueError("diagnostic gmin must be in (0,1e-12]")
    corner = sys.argv[sys.argv.index("--corner") + 1].lower() if "--corner" in sys.argv else "ss"
    temp = {"ss": 0, "tt": 27, "ff": 85}[corner]
    offset_mv = float(sys.argv[sys.argv.index("--offset-mv") + 1]) if "--offset-mv" in sys.argv else 1.0
    dnw_v = float(sys.argv[sys.argv.index("--dnw-v") + 1]) if "--dnw-v" in sys.argv else 1.8
    pwell_geometry = sys.argv[sys.argv.index("--pwell-geometry") + 1] if "--pwell-geometry" in sys.argv else "outer"
    source_mode = sys.argv[sys.argv.index("--source-mode") + 1] if "--source-mode" in sys.argv else "vcm"
    if not 0 < offset_mv <= 300:
        raise ValueError("offset must be in (0,300] mV")
    if not 0.9 + offset_mv / 1000 <= dnw_v <= 1.8:
        raise ValueError("DNW bias must be at least the high-state voltage and at most 1.8 V")
    if pwell_geometry not in ("outer", "remaining"):
        raise ValueError("pwell geometry must be outer or remaining")
    if source_mode not in ("vcm", "parked"):
        raise ValueError("source mode must be vcm or parked")
    pwell_area, pwell_perimeter = (35.75, 24.0) if pwell_geometry == "outer" else (27.625, 21.5)
    pex = PEX.read_text(encoding="ascii")
    ports = re.search(r"(?im)^\.subckt\s+\S+\s+([^\r\n]+)", pex).group(1).split()
    if ports != ["A", "B", "EN", "ENB", "DNW", "BULKP", "BULKN"] or "C15 BULKN DNW" not in pex:
        raise RuntimeError("unexpected extracted body-tied TG port order or well coupling")
    if "Vsubstrate VSUBS 0 0" not in PAIR.read_text(encoding="ascii"):
        raise RuntimeError("MIM PEX substrate must be grounded")
    grounded = BENCH / "sky130_body_tied_tg_pex_subground.spice"
    grounded.write_text(pex.replace(".ends", "Vsubstrate VSUBS 0 0\n.ends"), encoding="ascii")
    low, high = 0.9 - offset_mv / 1000, 0.9 + offset_mv / 1000
    cases = ("bare", "physical_body_tied", "physical_with_well_diode", "well_diode_area_mismatch_1pct",
             "physical_with_both_well_diodes", "both_well_diodes_area_mismatch_1pct")
    lines = ["* Grounded-substrate physical TG hold probe; junction leakage absent",
             (".option scale=1u reltol=1e-6 abstol=1e-16 vntol=1e-10 method=gear maxord=2" if refined else
              ".option scale=1u reltol=1e-6 abstol=1e-18 vntol=1e-11 method=gear maxord=2" if strict
              else ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2"),
             f'.lib "{LIB}" {corner}',
             f'.include "/workspace/{PAIR.relative_to(ROOT).as_posix()}"',
             f'.include "/workspace/{grounded.relative_to(ROOT).as_posix()}"',
             f".temp {temp}", "Vcm vcm 0 0.9", "Vdd vdd 0 1.8", f"Vdnw dnw 0 {dnw_v:.12g}",
             f"Vlow low 0 {low:.12g}", f"Vhigh high 0 {high:.12g}",
             f"Vgn gn 0 {-off_overdrive:g}", f"Vgp gp 0 {1.8+off_overdrive:g}",
             "Vinit_en init_en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)",
             f".model ideal_init SW(Ron={init_ron:g} Roff={init_roff:g} Vt=0.9 Vh=0.1)"]
    for case in cases:
        a, b = f"state_{case}_low", f"state_{case}_high"
        lines.append(f"Xpair_{case} vcm {a} vcm {b} sky130_differential_trim_cap_pair")
        for side, state in (("low", a), ("high", b)):
            if initial_condition:
                lines.append(f".ic v({state})={low if side == 'low' else high:.12g}")
            else:
                lines.append(f"Sinit_{case}_{side} {side} {state} init_en 0 ideal_init")
            if case != "bare":
                switch_source = "vcm" if source_mode == "vcm" else side
                lines.append(f"Xsw_{case}_{side} {switch_source} {state} gn gp dnw {state} {state} sky130_body_tied_transmission_gate_raw")
            if case in ("physical_with_well_diode", "well_diode_area_mismatch_1pct",
                        "physical_with_both_well_diodes", "both_well_diodes_area_mismatch_1pct"):
                # DNW rectangle is 5.5 x 6.5 um; the N-well bias strip
                # overlaps 1.25 x 6.5 um. Neither is extracted junction area.
                factor = 1.01 if case in ("well_diode_area_mismatch_1pct", "both_well_diodes_area_mismatch_1pct") and side == "high" else 1.0
                lines.append(f"Dwell_{case}_{side} {state} dnw sky130_fd_pr__model__parasitic__diode_pw2dn area={pwell_area*factor:g} pj={pwell_perimeter*factor:g}")
            if case in ("physical_with_both_well_diodes", "both_well_diodes_area_mismatch_1pct"):
                # PFET PCell n-well is 2.11 x 4.19 um before its shift.
                lines.append(f"Dpfwell_{case}_{side} 0 {state} sky130_fd_pr__model__parasitic__diode_ps2nw area=8.8409 pj=12.6")
    if gmin is not None:
        lines.append(f".options gmin={gmin:g}")
    lines += [".control", "set numdgt=15", "tran 0.5u 5m" if strict or refined else "tran 1u 5m"]
    for case in cases:
        for side in ("low", "high"):
            lines += [f"meas tran {case}_{side}_start find v(state_{case}_{side}) at=2u",
                      f"meas tran {case}_{side}_end find v(state_{case}_{side}) at=5m"]
    lines += ["quit", ".endc", ".end", ""]
    stem = f"sky130_body_tied_tg_pex_hold_{corner}_temp{temp}_offset{offset_mv:g}mv"
    if dnw_v != 1.8:
        stem += f"_dnw{dnw_v:g}v"
    if pwell_geometry != "outer":
        stem += f"_pwell{pwell_geometry}"
    if source_mode == "vcm":
        stem += "_sourcevcm"
    if version != "36":
        stem += f"_ngspice{version}"
    if gmin is not None:
        stem += f"_gmin{gmin:g}"
    if strict:
        stem += "_strict"
    if refined:
        stem += "_refined"
    if (init_ron, init_roff) != (10.0, 1e30):
        stem += f"_initron{init_ron:g}_roff{init_roff:g}"
    if initial_condition:
        stem += "_initialcondition"
    if off_overdrive:
        stem += f"_offoverdrive{off_overdrive:g}v"
    path = BENCH / f"{stem}.cir"
    path.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace",
           "--env", "NGSPICE_MEAS_PRECISION=15",
           "--workdir", "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", f"eventspikeseg:analog-ngspice{version}", "180", "ngspice", "-b",
           f"/workspace/{path.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=195, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{stem}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k, v in re.findall(
        r"(?im)^\s*([a-z0-9_]+_(?:low|high)_(?:start|end))\s*=\s*([-+0-9.eE]+)", log)}
    simulator_complete = proc.returncode == 0 and f"ngspice-{version} done" in log and len(vals) == 4 * len(cases)
    complete = simulator_complete
    if complete:
        complete = all(abs(vals[f"{case}_{side}_start"] - target) < min(0.03, offset_mv * 0.0005)
                       for case in cases for side, target in (("low", low), ("high", high)))
    report = {"test": "sky130_body_tied_tg_physical_pex_hold", "completed": complete,
              "simulation_completed": simulator_complete,
              "initialization_pass": complete,
              "simulator": f"ngspice-{version}", "gmin_siemens_requested": gmin,
              "strict_tolerances": strict, "refined_tolerances": refined,
              "maximum_time_step_us": 0.5 if strict or refined else 1,
              "ideal_initializer_ron_ohm": init_ron, "ideal_initializer_roff_ohm": init_roff,
              "ideal_initial_condition_without_switch": initial_condition,
              "ideal_off_gate_overdrive_v": off_overdrive,
              "off_gate_biases_v": [-off_overdrive, 1.8 + off_overdrive],
              "return_code": proc.returncode, "corner": corner.upper(), "temperature_c": temp,
              "offset_mv": offset_mv, "dnw_bias_v": dnw_v,
              "pwell_geometry_proxy": pwell_geometry,
              "off_switch_source_mode": source_mode,
              "cases": [], "physical_layout_bbox_um": [6.25, 16.345],
              "well_diode_proxy": f"PDK pw2dn diode area={pwell_area:g}um2, perimeter={pwell_perimeter:g}um from {pwell_geometry} DNW/pwell geometry; PDK ps2nw diode area=8.8409um2, perimeter=12.6um from PFET PCell nwell rectangle. Mismatch cases increase high-side pw2dn area and perimeter by 1%. Geometry, mismatch distribution and current not extraction-verified",
              "limitations": "Magic/Netgen probe PEX plus reduced nominal MIM, ideal initial write, grounded substrate. Well-junction leakage is absent from PEX and inserted as drawn-region PDK-diode proxies in the named cases. Off-switch source is either fixed VCM (shared-bus diagnostic) or parked at each initial state (optimistic control). Body pins and DNW bias are externally connected in the bench, not routed in the GDS. The 1% geometry perturbation is not a mismatch distribution. No foundry signoff, real programming, readout, switched noise, or full-chip service qualification."}
    if simulator_complete:
        for case in cases:
            item = {"switch": case, **{
                f"{side}_{when}_v": vals[f"{case}_{side}_{when}"]
                for side in ("low", "high") for when in ("start", "end")}, **{
                f"{side}_drift_mv": 1000 * (vals[f"{case}_{side}_end"] - vals[f"{case}_{side}_start"])
                for side in ("low", "high")}}
            item["common_mode_drift_mv"] = 0.5 * (item["low_drift_mv"] + item["high_drift_mv"])
            item["differential_drift_mv"] = item["high_drift_mv"] - item["low_drift_mv"]
            report["cases"].append(item)
    report["source_sha256"] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (PEX, PAIR, grounded, path, RESULTS / f"{stem}.log")}
    (RESULTS / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not complete:
        raise RuntimeError(f"ngspice incomplete: {log[-2500:]}")


if __name__ == "__main__":
    main()
