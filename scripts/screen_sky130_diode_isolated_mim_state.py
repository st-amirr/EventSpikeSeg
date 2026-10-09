"""Bounded two-diode update-port hold screen for the extracted small MIM state."""
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
DIODE_QUAL = DIODE_DIR / "qualification.json"
DIODE_PEX = DIODE_DIR / "diode_pd2nw_05v5_probe_pex.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"
KINDS = ("bare", "moscap", "two_diode_moscap")


def main() -> None:
    args = sys.argv[1:]
    gmin = float(args[args.index("--gmin") + 1]) if "--gmin" in args else None
    if gmin is not None and not 0 < gmin <= 1e-12:
        raise ValueError("diagnostic gmin must be in (0, 1e-12]")
    version = "47" if "--ngspice47" in args else "36"
    corner = args[args.index("--corner") + 1].lower() if "--corner" in args else "tt"
    if corner not in ("tt", "ss", "ff"):
        raise ValueError("corner must be tt, ss, or ff")
    temp_c = float(args[args.index("--temp-c") + 1]) if "--temp-c" in args else {"tt": 27, "ss": 0, "ff": 85}[corner]
    offset_mv = float(args[args.index("--offset-mv") + 1]) if "--offset-mv" in args else 1
    hold_us = float(args[args.index("--hold-us") + 1]) if "--hold-us" in args else 5000.0
    if not 20 <= hold_us <= 5000:
        raise ValueError("hold window must be 20..5000 us")
    if not 0 < offset_mv <= 750:
        raise ValueError("offset must be in (0, 750] mV")
    reverse = "--reverse-state" in args
    well_proxy = "--well-proxy" in args
    physical_diode = "--physical-diode" in args
    kinds = KINDS + (("two_diode_moscap_wellproxy",) if well_proxy else ())
    area_um2 = float(args[args.index("--diode-area-um2") + 1]) if "--diode-area-um2" in args else 1.0
    perimeter_um = float(args[args.index("--diode-perimeter-um") + 1]) if "--diode-perimeter-um" in args else 4.0
    if not 1 <= area_um2 <= 100 or not 4 <= perimeter_um <= 100:
        raise ValueError("diode area/perimeter outside bounded screen")
    if physical_diode and (area_um2 != 1 or perimeter_um != 4):
        raise ValueError("physical diode PEX has fixed 1um2/4um junction geometry")
    for path in (PAIR, MOSCAP):
        if not path.exists():
            raise FileNotFoundError(path)
    diode_qualification = None
    if physical_diode:
        diode_qualification = json.loads(DIODE_QUAL.read_text(encoding="utf-8"))
        if not (diode_qualification["magic_drc_zero"] and diode_qualification["netgen_lvs_unique_match"]
                and diode_qualification["ports_in_extracted_order"] == ["ANODE", "SUB", "CATHODE"]):
            raise RuntimeError("physical diode qualification/port order failed")
    well_area = (diode_qualification["estimated_nwell_area_um2_from_mag_rectangle"]
                 if diode_qualification else 8.8409)
    well_perimeter = (diode_qualification["estimated_nwell_perimeter_um_from_mag_rectangle"]
                      if diode_qualification else 12.6)
    low_v, high_v = 0.9 - offset_mv / 1000, 0.9 + offset_mv / 1000
    if reverse:
        low_v, high_v = high_v, low_v
    lines = [
        "* Extracted small MIM and MOS gate cap; PDK two-terminal diode update ports",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
        f'.lib "{LIB}" {corner}',
        f'.include "/workspace/{PAIR.relative_to(ROOT).as_posix()}"',
        f'.include "/workspace/{MOSCAP.relative_to(ROOT).as_posix()}"',
        f".temp {temp_c:g}",
        "Vcm vcm 0 0.9", "Vplus plus_idle 0 0", "Vminus minus_idle 0 1.8",
        f"Vlow low 0 {low_v:.12g}", f"Vhigh high 0 {high_v:.12g}",
        f"Vinit_en init_en 0 PWL(0 1.8 0.9u 1.8 1u 0 {hold_us + 10:g}u 0)",
        ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)",
    ]
    if physical_diode:
        lines.append(f'.include "/workspace/{DIODE_PEX.relative_to(ROOT).as_posix()}"')
    for kind in kinds:
        lo, hi = f"state_{kind}_low", f"state_{kind}_high"
        lines.append(f"Xpair_{kind} vcm {lo} vcm {hi} sky130_differential_trim_cap_pair")
        for side, node in (("low", lo), ("high", hi)):
            lines.append(f"Sinit_{kind}_{side} {side} {node} init_en 0 ideal_init")
            if kind != "bare":
                lines.append(f"Xcap_{kind}_{side} {node} 0 0 moscap_pcell_probe")
            if kind.startswith("two_diode_moscap"):
                if physical_diode:
                    lines += [f"Xplus_{kind}_{side} plus_idle 0 {node} diode_pd2nw_05v5_probe",
                              f"Xminus_{kind}_{side} {node} 0 minus_idle diode_pd2nw_05v5_probe"]
                else:
                    lines += [
                        f"Dplus_{kind}_{side} plus_idle {node} sky130_fd_pr__diode_pd2nw_05v5 area={area_um2:g} pj={perimeter_um:g}",
                        f"Dminus_{kind}_{side} {node} minus_idle sky130_fd_pr__diode_pd2nw_05v5 area={area_um2:g} pj={perimeter_um:g}",
                    ]
                if kind.endswith("wellproxy"):
                    lines.append(f"Dwell_{kind}_{side} 0 {node} sky130_fd_pr__model__parasitic__diode_ps2nw area={well_area:g} pj={well_perimeter:g}")
    if gmin is not None:
        lines.append(f".options gmin={gmin:g}")
    lines += [".control", "set numdgt=15", f"tran 1u {hold_us:g}u"]
    for kind in kinds:
        for side in ("low", "high"):
            lines += [f"meas tran {kind}_{side}_start find v(state_{kind}_{side}) at=2u",
                      f"meas tran {kind}_{side}_end find v(state_{kind}_{side}) at={hold_us:g}u"]
    lines += ["quit", ".endc", ".end", ""]
    stem = f"sky130_diode_isolated_mim_state_{corner}_temp{temp_c:g}_offset{offset_mv:g}mv"
    if reverse:
        stem += "_reversed"
    stem += f"_area{area_um2:g}um2_perim{perimeter_um:g}um"
    if well_proxy:
        stem += "_wellproxy"
    if physical_diode:
        stem += "_physicaldiode"
    if version == "47":
        stem += "_ngspice47"
    if hold_us != 5000:
        stem += f"_hold{hold_us:g}us"
    if gmin is not None:
        stem += f"_gmin{gmin:g}"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--env", "NGSPICE_MEAS_PRECISION=15", "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", f"eventspikeseg:analog-ngspice{version}", "180", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=195, cwd=ROOT)
    log = proc.stdout + proc.stderr
    log_path = RESULTS / f"{stem}.log"
    log_path.write_text(log, encoding="utf-8")
    measured = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*((?:bare|moscap|two_diode_moscap(?:_wellproxy)?)_(?:low|high)_(?:start|end))\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and f"ngspice-{version} done" in log and len(measured) == 4 * len(kinds)
    cases = []
    if complete:
        for kind in kinds:
            initial = (measured[f"{kind}_high_start"] - measured[f"{kind}_low_start"]) * 1e3
            final = (measured[f"{kind}_high_end"] - measured[f"{kind}_low_end"]) * 1e3
            cases.append({"kind": kind,
                          "low_start_v": measured[f"{kind}_low_start"],
                          "low_end_v": measured[f"{kind}_low_end"],
                          "high_start_v": measured[f"{kind}_high_start"],
                          "high_end_v": measured[f"{kind}_high_end"],
                          "initial_differential_mv": initial,
                          "end_differential_mv": final,
                          "retained_signed_fraction": final / initial})
    report = {
        "test": "sky130_two_diode_update_port_hold_screen",
        "simulation_completed": complete, "return_code": proc.returncode,
        "corner": corner.upper(), "temperature_c": temp_c,
        "simulator": f"ngspice-{version}",
        "hold_us": hold_us,
        "gmin_siemens_requested": gmin,
        "commanded_rail_offset_mv": -offset_mv if reverse else offset_mv,
        "diode_model": "sky130_fd_pr__diode_pd2nw_05v5",
        "diode_area_um2": area_um2, "diode_perimeter_um": perimeter_um,
        "physical_diode_pex": physical_diode,
        "physical_diode_qualification": (str(DIODE_QUAL.relative_to(ROOT)).replace("\\", "/")
                                         if physical_diode else None),
        "nwell_to_substrate_proxy": (f"ps2nw PDK diode, area{well_area:g}um2 perimeter{well_perimeter:g}um on each state Nwell"
                                      if well_proxy else None),
        "cases": cases,
        "sources": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in ((PAIR, MOSCAP, deck, log_path, DIODE_QUAL, DIODE_PEX)
                                 if physical_diode else (PAIR, MOSCAP, deck, log_path))},
        "limitations": "Ideal initial programming. Separate plus/minus buses are parked at 0/1.8V and not routed or addressed. The optional nwell-to-substrate diode uses provisional drawn-well geometry, not an extracted junction. The isolated diode primitive has DRC/LVS/PEX only when physical_diode_pex is true. Other well parasitics, half-select disturb, forward-write voltage/time/energy, combined state layout, mismatch/noise, readout, event sequence and 5ms population service are not measured. Do not promote from hold alone.",
    }
    out = RESULTS / f"{stem}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "simulation_completed": complete, "cases": cases,
                      "error_tail": log[-1200:] if not complete else None}, indent=2))
    if not complete:
        raise RuntimeError(f"incomplete two-diode screen: {log[-1600:]}")


if __name__ == "__main__":
    main()
