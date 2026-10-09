"""Build and characterize a three-segment tapped SKY130 resistor string.

Each segment is one 1.41um xhigh-poly PCell. The layout is flattened so Magic
extracts the physical interconnect; extracted devices are mapped back to the
size-specific SKY130 PCell wrapper recorded by the source gencell.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_tapped_resistor_string3"
IMAGE = "eventspikeseg:analog-layout"
SIM = "eventspikeseg:analog-ngspice36"
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "sky130_tapped_resistor_string3"
TOP = f"{CELL}_raw"
PCELL = "sky130_fd_pr__res_xhigh_po_1p41_DFRRR3"


def docker(entrypoint: str, args: list[str], *, input_text: str | None = None,
           image: str = IMAGE, timeout: int = 180) -> str:
    cmd = ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
           "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
           "-w", "/workspace/artifacts/analog_asic/layout/sky130_tapped_resistor_string3",
           "--entrypoint", entrypoint, image, *args]
    proc = subprocess.run(cmd, input=input_text, text=True, capture_output=True,
                          timeout=timeout, cwd=ROOT)
    log = proc.stdout + proc.stderr
    if proc.returncode:
        raise RuntimeError(f"{entrypoint} failed ({proc.returncode}):\n{log[-5000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pcell_src = ROOT / "artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe" / f"{PCELL}.mag"
    if not pcell_src.is_file():
        raise FileNotFoundError("Run scripts/probe_sky130_r2r_resistor_pcell.py first")
    shutil.copy2(pcell_src, OUT / pcell_src.name)
    raw = OUT / f"{CELL}_raw.mag"
    raw.write_text(
        "magic\ntech sky130A\nmagscale 1 2\ntimestamp 0\n<< checkpaint >>\n<< labels >>\n"
        "rlabel metal1 s -131 -6 131 6 4 IN\nport 1 nsew\n"
        "rlabel metal1 s -131 2994 131 3006 4 TAP1\nport 2 nsew\n"
        "rlabel metal1 s -131 5994 131 6006 4 TAP2\nport 3 nsew\n"
        "rlabel metal1 s -131 6974 131 6986 4 OUT\nport 4 nsew\n<< end >>\n",
        encoding="ascii")
    build_tcl = "\n".join((
        f"load {CELL}_raw",
        f"dump {PCELL} child R0 parent IN",
        f"dump {PCELL} child R0 parent TAP1",
        f"dump {PCELL} child R0 parent TAP2",
        "wire segment metal1 75 0 490 0 1500",
        "wire segment metal1 75 0 1990 0 3000",
        "save", "quit -noprompt", ""))
    magic_cmd = ["magic", "-dnull", "-noconsole", "-rcfile", MAGIC_RC]
    build_log = docker(magic_cmd[0], magic_cmd[1:], input_text=build_tcl)
    (OUT / "magic_build.log").write_text(build_log, encoding="utf-8")

    # Keep only the parent pins; dumped PCell port labels would short all
    # identically named resistor terminals together in a flat extraction.
    mag_path = OUT / f"{CELL}_raw.mag"
    lines = mag_path.read_text(encoding="ascii").splitlines()
    clean: list[str] = []
    skip_port = False
    for line in lines:
        if skip_port and line.startswith("port "):
            skip_port = False
            continue
        skip_port = False
        if line.startswith("rlabel ") and line.rsplit(" ", 1)[-1] in {"R0", "R1"}:
            skip_port = True
            continue
        clean.append(line)
    mag_path.write_text("\n".join(clean) + "\n", encoding="ascii")
    extract_tcl = "\n".join((
        f"load {CELL}_raw", "drc check", "drc count", "extract all", "ext2spice lvs",
        "ext2spice scale off", f"ext2spice -o {CELL}.spice", f"gds write {CELL}.gds",
        "save", "quit -noprompt", ""))
    extract_log = docker(magic_cmd[0], magic_cmd[1:], input_text=extract_tcl)
    (OUT / "magic_build_extract.log").write_text(build_log + extract_log, encoding="utf-8")
    if "Total DRC errors found: 0" not in extract_log:
        raise RuntimeError(f"Magic DRC failed:\n{extract_log[-4000:]}")

    spice_path = OUT / f"{CELL}.spice"
    magic_spice = spice_path.read_text(encoding="ascii")
    if f".subckt {TOP} IN TAP1 TAP2 OUT" not in magic_spice:
        raise RuntimeError(f"Unexpected extracted pins:\n{magic_spice[:2000]}")
    (OUT / f"{CELL}.magic.spice").write_text(
        magic_spice.replace(f".subckt {TOP} IN TAP1 TAP2 OUT",
                            f".subckt {TOP}_generic IN TAP1 TAP2 OUT", 1),
        encoding="ascii")
    magic_spice, mapped = re.subn(
        r"sky130_fd_pr__res_xhigh_po\s+w=1\.41e\+06u\s+l=700000u",
        "sky130_fd_pr__res_xhigh_po_1p41 l=700000u", magic_spice)
    if mapped != 3:
        raise RuntimeError(f"Expected three PCell device mappings, found {mapped}")
    spice_path.write_text(magic_spice, encoding="ascii")
    bodies = sorted(set(re.findall(
        r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41\s",
        magic_spice, re.M)) - {"IN", "TAP1", "TAP2", "OUT"})
    if not bodies:
        raise RuntimeError("Could not identify PCell substrate node")
    body = bodies[0]

    ref = OUT / "string3_reference.spice"
    ref.write_text(
        f".subckt {TOP} IN TAP1 TAP2 OUT\n"
        "Xr0 IN TAP1 VSUBS sky130_fd_pr__res_xhigh_po_1p41 l=700000u\n"
        "Xr1 TAP1 TAP2 VSUBS sky130_fd_pr__res_xhigh_po_1p41 l=700000u\n"
        "Xr2 TAP2 OUT VSUBS sky130_fd_pr__res_xhigh_po_1p41 l=700000u\n"
        ".ends\n", encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs_log = docker("netgen-lvs", ["-batch", "lvs",
                       f"{CELL}.spice {TOP}", f"string3_reference.spice {TOP}",
                       setup, "string3_lvs.out"])
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    if "Circuits match uniquely" not in lvs_log:
        raise RuntimeError(f"Netgen LVS failed:\n{lvs_log[-4000:]}")

    deck = OUT / "string3_dc.cir"
    deck.write_text(f"""* SKY130 extracted three-tap resistor string
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.include "/workspace/artifacts/analog_asic/layout/sky130_tapped_resistor_string3/{CELL}.spice"
.include "/workspace/artifacts/analog_asic/layout/sky130_tapped_resistor_string3/{CELL}.magic.spice"
.global {body}
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
Vbody {body} 0 0
Vt0 IN TAP1 1m
Vt1 TAP1 TAP2 1m
Vt2 TAP2 OUT 1m
Xmapped IN TAP1 TAP2 OUT {TOP}
Vg0 GIN GTAP1 1m
Vg1 GTAP1 GTAP2 1m
Vg2 GTAP2 GOUT 1m
Xgeneric GIN GTAP1 GTAP2 GOUT {TOP}_generic
Vflat flat 0 1m
Xflat flat 0 0 sky130_fd_pr__res_xhigh_po w=1.41 l=0.7
Vwrap wrapped 0 1m
Xwrap wrapped 0 0 sky130_fd_pr__res_xhigh_po_1p41 l=0.7
Vdiv_hi d_hi 0 1.8
Vdiv_lo d_lo 0 0.9
Xdivider d_hi d_tap1 d_tap2 d_lo {TOP}
Rdiv_load1 d_tap1 0 1G
Rdiv_load2 d_tap2 0 1G
Vldiv_hi ld_hi 0 1.8
Vldiv_lo ld_lo 0 0.9
Xloaded_divider ld_hi ld_tap1 ld_tap2 ld_lo {TOP}
Rloaded_div1 ld_tap1 0 10Meg
Rloaded_div2 ld_tap2 0 10Meg
.control
op
let r0=1m/abs(i(Vt0))
let r1=1m/abs(i(Vt1))
let r2=1m/abs(i(Vt2))
let rtotal=r0+r1+r2
let rg0=1m/abs(i(Vg0))
let rg1=1m/abs(i(Vg1))
let rg2=1m/abs(i(Vg2))
let rgeneric=rg0+rg1+rg2
let rflat=1m/abs(i(Vflat))
let rwrap=1m/abs(i(Vwrap))
let unloaded_tap1=v(d_tap1)
let unloaded_tap2=v(d_tap2)
let loaded_tap1=v(ld_tap1)
let loaded_tap2=v(ld_tap2)
print r0
print r1
print r2
print rtotal
print rgeneric
print rflat
print rwrap
print unloaded_tap1
print unloaded_tap2
print loaded_tap1
print loaded_tap2
quit
.endc
.end
""", encoding="ascii")
    sim = subprocess.run([
        "docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
        "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models",
        "--entrypoint", "ngspice", SIM, "-b",
        f"/workspace/{deck.relative_to(ROOT).as_posix()}"],
        text=True, capture_output=True, timeout=120, cwd=ROOT)
    sim_log = sim.stdout + sim.stderr
    (OUT / "ngspice_dc.log").write_text(sim_log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"^(r0|r1|r2|rtotal|rgeneric|rflat|rwrap|unloaded_tap1|unloaded_tap2|loaded_tap1|loaded_tap2)\s*=\s*([-+0-9.eE]+)",
        sim_log, re.M | re.I)}
    required = {"r0", "r1", "r2", "rtotal", "rgeneric", "rflat", "rwrap",
                "unloaded_tap1", "unloaded_tap2", "loaded_tap1", "loaded_tap2"}
    if sim.returncode or set(values) != required or "ngspice-36 done" not in sim_log:
        raise RuntimeError(f"Extracted tap simulation failed:\n{sim_log[-4000:]}")
    report = {
        "test": "sky130_three_segment_tapped_resistor_string",
        "cell": TOP,
        "resistor_count": 3,
        "tap_count": 2,
        "nominal_segment_ohms": 1259,
        "segment_resistances_ohms": [values["r0"], values["r1"], values["r2"]],
        "segment_spread_fraction": (max(values[k] for k in ("r0", "r1", "r2")) - min(values[k] for k in ("r0", "r1", "r2"))) / (sum(values[k] for k in ("r0", "r1", "r2")) / 3),
        "mapped_total_ohms": values["rtotal"],
        "magic_generic_total_ohms": values["rgeneric"],
        "flat_generic_single_ohms": values["rflat"],
        "pcell_wrapper_single_ohms": values["rwrap"],
        "divider_source_v": [1.8, 0.9],
        "unloaded_tap_voltages_v": [values["unloaded_tap1"], values["unloaded_tap2"]],
        "unloaded_ideal_tap_voltages_v": [1.5, 1.2],
        "loaded_tap_load_ohms": 10_000_000,
        "loaded_tap_voltages_v": [values["loaded_tap1"], values["loaded_tap2"]],
        "loaded_tap_errors_vs_unloaded_mv": [
            (values["loaded_tap1"] - values["unloaded_tap1"]) * 1e3,
            (values["loaded_tap2"] - values["unloaded_tap2"]) * 1e3],
        "mapped_pcell_model": "sky130_fd_pr__res_xhigh_po_1p41",
        "mapped_device_count": mapped,
        "magic_drc_zero": True,
        "netgen_lvs_unique": True,
        "gds_written": (OUT / f"{CELL}.gds").is_file(),
        "simulation_completed": True,
        "scope": "Three extracted and wrapper-mapped PCell devices with two physical taps and metal1 series links; TT/27C DC only. No switch loading, PCell mismatch Monte Carlo, parasitic transient, or full R-2R array.",
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
