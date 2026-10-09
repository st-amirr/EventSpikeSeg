"""Generate one SKY130 xhigh-poly resistor PCell to establish its physical floor."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe"
IMAGE = "eventspikeseg:analog-layout"
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "res_probe_raw.mag").write_text(
        "magic\ntech sky130A\nmagscale 1 2\ntimestamp 0\n<< checkpaint >>\n<< end >>\n",
        encoding="ascii")
    tcl = "\n".join((
        "load res_probe_raw",
        "magic::gencell sky130::sky130_fd_pr__res_xhigh_po_1p41 resistor -spice w 1.41 l 0.7",
        "save", "writeall force", "quit -noprompt", ""))
    cmd = ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace", "-e",
           "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root", "-w",
           "/workspace/artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe",
           "--entrypoint", "magic", IMAGE, "-dnull", "-noconsole", "-rcfile", MAGIC_RC]
    run = subprocess.run(cmd, input=tcl, text=True, capture_output=True, timeout=180, cwd=ROOT)
    log = run.stdout + run.stderr
    (OUT / "magic_pcell.log").write_text(log, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(f"Magic resistor PCell generation failed:\n{log[-4000:]}")
    pcell = next(OUT.glob("sky130_fd_pr__res_xhigh_po_1p41_*.mag"))
    mag = pcell.read_text(encoding="ascii")
    labels = ("<< labels >>\n"
              "rlabel metal1 s -131 484 131 496 4 R1\nport 1 nsew\n"
              "rlabel metal1 s -131 -496 131 -484 4 R0\nport 2 nsew\n")
    pcell.write_text(mag.replace("<< end >>", labels + "<< end >>"), encoding="ascii")
    phase2_tcl = "\n".join((
        "load sky130_fd_pr__res_xhigh_po_1p41_DFRRR3", "drc check", "drc count", "extract all", "ext2spice lvs",
        "ext2spice scale off", "ext2spice -o r1k_probe.spice", "gds write r1k_probe.gds",
        "save", "quit -noprompt", ""))
    phase2_cmd = ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace", "-e",
                  "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root", "-w",
                  "/workspace/artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe",
                  "--entrypoint", "magic", IMAGE, "-dnull", "-noconsole", "-rcfile", MAGIC_RC]
    phase2 = subprocess.run(phase2_cmd, input=phase2_tcl, text=True, capture_output=True,
                            timeout=180, cwd=ROOT)
    phase2_log = phase2.stdout + phase2.stderr
    (OUT / "magic_extract.log").write_text(phase2_log, encoding="utf-8")
    for p in OUT.glob("*"):
        if p.is_file():
            print(f"generated {p.name} ({p.stat().st_size} bytes)")
    print(phase2_log[-3500:])
    if phase2.returncode:
        raise RuntimeError(f"Magic resistor extraction failed:\n{phase2_log[-4000:]}")
    if "Total DRC errors found: 0" not in phase2_log:
        raise RuntimeError("Magic reported resistor PCell DRC errors")
    cell = "sky130_fd_pr__res_xhigh_po_1p41_DFRRR3"
    (OUT / "r1k_reference.spice").write_text(
        ".subckt r1k_reference R1 R0\n"
        "X0 R0 R1 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=0.7\n"
        ".ends\n", encoding="ascii")
    netgen = subprocess.run([
        "docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-e",
        "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root", "-w",
        "/workspace/artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe",
        "--entrypoint", "netgen-lvs", IMAGE, "-batch", "lvs",
        f"r1k_probe.spice {cell}", "r1k_reference.spice r1k_reference",
        "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl",
        "r1k_lvs.out"], text=True, capture_output=True, timeout=120, cwd=ROOT)
    lvs_log = netgen.stdout + netgen.stderr
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    if netgen.returncode or "Circuits match uniquely" not in lvs_log:
        raise RuntimeError(f"Resistor PCell LVS failed:\n{lvs_log[-3000:]}")
    deck = OUT / "r1k_dc.cir"
    deck.write_text(f"""* SKY130 extracted resistor DC screen
.option scale=1u
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
.include "/workspace/artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe/r1k_probe.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
Vtest R1 0 1m
Xprobe R1 0 {cell}
.control
op
let r_meas=1m/abs(i(Vtest))
print r_meas
quit
.endc
.end
""", encoding="ascii")
    sim = subprocess.run([
        "docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
        "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models",
        "--entrypoint", "ngspice", "eventspikeseg:analog-ngspice36", "-b",
        "/workspace/artifacts/analog_asic/layout/sky130_r2r_resistor_pcell_probe/r1k_dc.cir"],
        text=True, capture_output=True, timeout=90, cwd=ROOT)
    sim_log = sim.stdout + sim.stderr
    (OUT / "ngspice_dc.log").write_text(sim_log, encoding="utf-8")
    match = re.search(r"r_meas\s*=\s*([-+0-9.eE]+)", sim_log, re.I)
    if sim.returncode or not match or "ngspice-36 done" not in sim_log:
        raise RuntimeError(f"Extracted resistor SPICE screen failed:\n{sim_log[-3000:]}")
    report = {"test": "sky130_xhigh_poly_resistor_pcell_probe", "simulation_completed": True,
              "cell": cell, "drawn_w_um": 1.41, "drawn_l_um": 0.7,
              "pcell_nominal_ohms": 1259, "extracted_dc_ohms": float(match.group(1)),
              "magic_drc_zero": True, "netgen_lvs_unique": True,
              "scope": "One xhigh-poly resistor PCell at TT/27C; no full R-2R ladder, array matching, PVT sweep, or readout integration."}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
