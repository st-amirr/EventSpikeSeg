"""Build and qualify a two-resistor extracted SKY130 ladder segment.

This is a physical resistor/interconnect probe, not a complete DAC. It places
two xhigh-poly resistor PCells in series, routes the middle node in metal1, and
checks DRC, LVS, and the extracted DC resistance.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_r2r2_extracted"
IMAGE = "eventspikeseg:analog-layout"
SIM = "eventspikeseg:analog-ngspice36"
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "sky130_r2r2_extracted"
TOP = f"{CELL}_raw"
PCELL = "sky130_fd_pr__res_xhigh_po_1p41_DFRRR3"


def run_docker(args: list[str], *, input_text: str | None = None,
               timeout: int = 180, image: str = IMAGE) -> str:
    cmd = ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
           "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
           "-w", "/workspace/artifacts/analog_asic/layout/sky130_r2r2_extracted",
           "--entrypoint", args[0], image, *args[1:]]
    proc = subprocess.run(cmd, input=input_text, text=True, capture_output=True,
                          timeout=timeout, cwd=ROOT)
    log = proc.stdout + proc.stderr
    if proc.returncode:
        raise RuntimeError(f"Docker command failed ({proc.returncode}):\n{log[-5000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pcell_source = ROOT / "artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe" / f"{PCELL}.mag"
    if not pcell_source.is_file():
        raise FileNotFoundError("Run scripts/probe_sky130_r2r_resistor_pcell.py first")
    shutil.copy2(pcell_source, OUT / pcell_source.name)
    raw = OUT / f"{CELL}_raw.mag"
    raw.write_text(
        "magic\ntech sky130A\nmagscale 1 2\ntimestamp 0\n"
        "<< checkpaint >>\n<< labels >>\n"
        "rlabel metal1 s -131 -6 131 6 4 IN\nport 1 nsew\n"
        "rlabel metal1 s -131 4980 131 4992 4 OUT\nport 2 nsew\n"
        "<< end >>\n", encoding="ascii")
    tcl = "\n".join((
        f"load {CELL}_raw",
        f"dump {PCELL} child R0 parent IN",
        f"dump {PCELL} child R1 parent OUT",
        # The two external resistor taps are 5,000 database units apart;
        # this metal1 leg joins the first R1 to the second R0.
        "wire segment metal1 75 0 490 0 2010",
        "save", "quit -noprompt", ""))
    cmd = ["magic", "-dnull", "-noconsole", "-rcfile", MAGIC_RC]
    magic = run_docker(cmd, input_text=tcl)
    (OUT / "magic_build.log").write_text(magic, encoding="utf-8")
    # PCell R0/R1 labels are useful during placement but become global when
    # dumped into a flat parent. Keep only the explicit external IN/OUT pins.
    flat_lines = (OUT / f"{CELL}_raw.mag").read_text(encoding="ascii").splitlines()
    cleaned: list[str] = []
    skip_port = False
    for line in flat_lines:
        if skip_port and line.startswith("port "):
            skip_port = False
            continue
        skip_port = False
        if line.startswith("rlabel ") and line.rsplit(" ", 1)[-1] in {"R0", "R1"}:
            skip_port = True
            continue
        cleaned.append(line)
    (OUT / f"{CELL}_raw.mag").write_text("\n".join(cleaned) + "\n", encoding="ascii")
    extract_tcl = "\n".join((
        f"load {CELL}_raw", "drc check", "drc count", "extract all", "ext2spice lvs",
        "ext2spice scale off", f"ext2spice -o {CELL}.spice",
        f"gds write {CELL}.gds", "save", "quit -noprompt", ""))
    magic_extract = run_docker(cmd, input_text=extract_tcl)
    (OUT / "magic_build_extract.log").write_text(magic + magic_extract, encoding="utf-8")
    if "Total DRC errors found: 0" not in magic_extract:
        raise RuntimeError(f"Magic DRC failed:\n{magic_extract[-4000:]}")
    extracted = OUT / f"{CELL}.spice"
    spice_text = extracted.read_text(encoding="ascii")
    if f".subckt {TOP} IN OUT" not in spice_text:
        raise RuntimeError(f"Extracted cell does not expose IN/OUT pins:\n{spice_text[:2000]}")
    generic_netlist = spice_text.replace(f".subckt {TOP} IN OUT", f".subckt {TOP}_generic IN OUT", 1)
    (OUT / f"{CELL}.magic.spice").write_text(generic_netlist, encoding="ascii")
    # Magic's flat resistor recognition emits the generic device model. The
    # source PCell carries the intended size-specific wrapper, so restore that
    # wrapper on each extracted device while leaving all extracted nets/geometry.
    spice_text, mapped_count = re.subn(
        r"sky130_fd_pr__res_xhigh_po\s+w=1\.41e\+06u\s+l=700000u",
        "sky130_fd_pr__res_xhigh_po_1p41 l=700000u", spice_text)
    if mapped_count != 2:
        raise RuntimeError(f"Expected to map two extracted PCells, mapped {mapped_count}")
    extracted.write_text(spice_text, encoding="ascii")
    body_nodes = re.findall(
        r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41\s",
        spice_text, re.M)
    body_nodes = sorted(set(body_nodes) - {"IN", "OUT"})
    if not body_nodes:
        raise RuntimeError("Could not identify the extracted resistor substrate node")
    substrate_node = body_nodes[0]

    reference = OUT / "two_res_reference.spice"
    reference.write_text(
        f".subckt {TOP} IN OUT\n"
        "Xr0 IN MID VSUBS sky130_fd_pr__res_xhigh_po_1p41 l=700000u\n"
        "Xr1 MID OUT VSUBS sky130_fd_pr__res_xhigh_po_1p41 l=700000u\n"
        ".ends\n", encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs = run_docker(["netgen-lvs", "-batch", "lvs",
                      f"{CELL}.spice {TOP}", f"two_res_reference.spice {TOP}",
                      setup, "two_res_lvs.out"])
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely" not in lvs:
        raise RuntimeError(f"Netgen LVS did not report a unique match:\n{lvs[-4000:]}")

    deck = OUT / "two_res_dc.cir"
    deck.write_text(f"""* SKY130 extracted two xhigh-poly resistors in series
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.include "/workspace/artifacts/analog_asic/layout/sky130_r2r2_extracted/{CELL}.spice"
.include "/workspace/artifacts/analog_asic/layout/sky130_r2r2_extracted/{CELL}.magic.spice"
.global {substrate_node}
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
Vsub {substrate_node} 0 0
Vtest IN OUT 1m
Xprobe IN OUT {TOP}
Vgeneric gin gout 1m
Xgeneric gin gout {TOP}_generic
Vflat flat 0 1m
Xflat flat 0 0 sky130_fd_pr__res_xhigh_po w=1.41 l=0.7
Vwrap wrapped 0 1m
Xwrap wrapped 0 0 sky130_fd_pr__res_xhigh_po_1p41 l=0.7
.control
op
let r_meas=1m/abs(i(Vtest))
let r_generic=1m/abs(i(Vgeneric))
let r_flat=1m/abs(i(Vflat))
let r_wrapped=1m/abs(i(Vwrap))
print r_meas
print r_generic
print r_flat
print r_wrapped
quit
.endc
.end
""", encoding="ascii")
    sim = subprocess.run([
        "docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
        "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models",
        "--entrypoint", "ngspice", SIM, "-b",
        f"/workspace/{deck.relative_to(ROOT).as_posix()}"],
        text=True, capture_output=True, timeout=90, cwd=ROOT)
    sim_log = sim.stdout + sim.stderr
    (OUT / "ngspice_dc.log").write_text(sim_log, encoding="utf-8")
    match = re.search(r"r_meas\s*=\s*([-+0-9.eE]+)", sim_log, re.I)
    generic_match = re.search(r"r_generic\s*=\s*([-+0-9.eE]+)", sim_log, re.I)
    flat_match = re.search(r"r_flat\s*=\s*([-+0-9.eE]+)", sim_log, re.I)
    wrap_match = re.search(r"r_wrapped\s*=\s*([-+0-9.eE]+)", sim_log, re.I)
    if sim.returncode or not match or not generic_match or not flat_match or not wrap_match or "ngspice-36 done" not in sim_log:
        raise RuntimeError(f"Extracted series resistance simulation failed:\n{sim_log[-4000:]}")
    measured = float(match.group(1))
    report = {
        "test": "sky130_two_xhigh_poly_resistors_series_extracted",
        "cell": TOP,
        "resistor_pcell": PCELL,
        "resistor_count": 2,
        "nominal_total_ohms": 2518,
        "extracted_dc_ohms": measured,
        "magic_flat_generic_network_ohms": float(generic_match.group(1)),
        "flat_generic_model_single_ohms": float(flat_match.group(1)),
        "pcell_wrapper_model_single_ohms": float(wrap_match.group(1)),
        "mapped_pcell_model": "sky130_fd_pr__res_xhigh_po_1p41",
        "mapped_extracted_device_count": mapped_count,
        "relative_error_vs_nominal": measured / 2518 - 1,
        "within_5pct_of_nominal": abs(measured / 2518 - 1) <= 0.05,
        "magic_drc_zero": True,
        "netgen_lvs_unique": True,
        "extracted_gds_written": (OUT / f"{CELL}.gds").is_file(),
        "simulation_completed": True,
        "scope": "Two xhigh-poly PCells in series with extracted metal1 interconnect; TT/27C DC resistance only. No R-2R taps/switches, matching statistics, parasitic transient, or comparator integration.",
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
