"""Build a labeled, source/drain-tied SKY130 NFET gate-cap layout primitive."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_NAME = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--output-dir-name=")),
                "sky130_moscap_pcell_probe")
OUT = ROOT / "artifacts/analog_asic/layout" / OUT_NAME
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "moscap_pcell_probe"
W_UM = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--w=")), "1000"))
L_UM = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--l=")), "10"))
NF = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--nf=")), "10"))
LAYOUT_IMAGE = "eventspikeseg:analog-layout"
SIM_IMAGE = "eventspikeseg:analog-ngspice36"


def docker_run(image: str, args: list[str], *, input_text: str | None = None,
               timeout: int = 180, workdir: str | None = None) -> subprocess.CompletedProcess[str]:
    command = ["docker", "run", "--rm"]
    if input_text is not None:
        command.append("-i")
    command += ["-v", f"{ROOT}:/workspace", "-e",
                "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root"]
    if workdir:
        command += ["-w", workdir]
    command += ["--entrypoint", args[0], image, *args[1:]]
    return subprocess.run(command, input=input_text, text=True, capture_output=True,
                          timeout=timeout, cwd=ROOT)


def run_magic(tcl: str) -> str:
    result = docker_run(
        LAYOUT_IMAGE, ["magic", "-dnull", "-noconsole", "-rcfile", MAGIC_RC],
        input_text=tcl, timeout=240,
        workdir=f"/workspace/artifacts/analog_asic/layout/{OUT_NAME}")
    log = result.stdout + result.stderr
    if result.returncode:
        raise RuntimeError(f"Magic failed ({result.returncode}):\n{log[-5000:]}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "moscap_raw.mag"
    raw.write_text("magic\ntech sky130A\nmagscale 1 2\ntimestamp 0\n"
                   "<< checkpaint >>\n<< end >>\n", encoding="ascii")
    phase1 = run_magic("\n".join([
        "load moscap_raw",
        f"magic::gencell sky130::sky130_fd_pr__nfet_01v8 moscap -spice w {W_UM:g} l {L_UM:g} nf {NF}",
        "save", "writeall force", "quit -noprompt", "",
    ]))
    # Attach labels to the actual flattened conductors. The PCell has no
    # interface labels by default, so extraction otherwise emits anonymous
    # nets that cannot be checked or reused hierarchically.
    mag_path = OUT / f"{CELL}.mag"
    generated_cells = sorted(OUT.glob("sky130_fd_pr__nfet_01v8_*.mag"), key=lambda path: path.stat().st_mtime)
    if not generated_cells:
        raise RuntimeError("Magic did not save the generated NFET PCell layout")
    mag_path.write_text(generated_cells[-1].read_text(encoding="ascii"), encoding="ascii")
    mag_text = mag_path.read_text(encoding="ascii")
    if "<< metal1 >>" not in mag_text:
        raise RuntimeError("flattened NFET has no metal1 routing section")
    if W_UM <= 20 and L_UM <= 2:
        # PCell coordinates are in 100 internal units per micrometre here.
        # Derive routes and labels from W/L; the fixed 10x1 coordinates leave
        # both diffusion terminals and the substrate floating at 20x2.
        x_tie = round(5 * W_UM + 26)
        gate_y = round(500 * L_UM + 20)
        bulk_x = round(-(5 * W_UM + 70))
        bulk_y = round(500 * L_UM + 70)
        mag_text = mag_text.replace("<< metal1 >>", f"<< metal1 >>\nrect {-x_tie} -12 {x_tie} 12", 1)
        labels = ("<< labels >>\n"
                  f"rlabel metal1 s -40 {gate_y} 40 {gate_y + 30} 4 GATE\nport 1 nsew\n"
                  "rlabel metal1 s -20 -8 20 8 4 VSS\nport 2 nsew\n"
                  f"rlabel psubdiff s {bulk_x} {bulk_y} {bulk_x + 30} {bulk_y + 10} 4 BULK\nport 3 nsew\n")
    else:
        mag_text = mag_text.replace("<< metal1 >>", "<< metal1 >>\nrect 91 157 2195 169", 1)
        labels = ("<< labels >>\n"
                  "rlabel metal1 s 900 79 1100 125 4 GATE\nport 1 nsew\n"
                  "rlabel metal1 s 1000 157 1200 169 4 VSS\nport 2 nsew\n"
                  "rlabel psubdiff s -17 100 17 200 4 BULK\nport 3 nsew\n")
    if "<< labels >>" in mag_text:
        mag_text = re.sub(r"<< labels >>.*?<< end >>", labels + "<< end >>",
                          mag_text, flags=re.S)
    else:
        mag_text = mag_text.replace("<< end >>", labels + "<< end >>")
    mag_path.write_text(mag_text, encoding="ascii")
    phase2 = run_magic("\n".join([
        f"load {CELL}",
        "drc check", "drc count", "extract all", "ext2spice lvs",
        "ext2spice scale off", f"ext2spice -o {CELL}.spice",
        f"gds write {CELL}.gds", "save", "quit -noprompt", "",
    ]))
    if "Total DRC errors found: 0" not in phase2:
        raise RuntimeError("MOS PCell probe has nonzero Magic DRC errors")
    spice = OUT / f"{CELL}.spice"
    ref = OUT / "nfet_reference.spice"
    ref.write_text(
        ".subckt nfet_reference GATE VSS BULK\n"
        f"X0 VSS GATE VSS BULK sky130_fd_pr__nfet_01v8 w={W_UM:g} l={L_UM:g}\n"
        ".ends\n", encoding="ascii")
    lvs = docker_run(
        LAYOUT_IMAGE, ["netgen-lvs", "-batch", "lvs",
                       f"{CELL}.spice {CELL}", "nfet_reference.spice nfet_reference",
                       "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl",
                       "nfet_lvs.out"], timeout=120,
        workdir=f"/workspace/artifacts/analog_asic/layout/{OUT_NAME}")
    lvs_log = lvs.stdout + lvs.stderr
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    if lvs.returncode or "Result: Circuits match uniquely." not in lvs_log:
        raise RuntimeError(f"MOS PCell probe LVS failed:\n{lvs_log[-5000:]}")
    spice_text = spice.read_text(encoding="ascii")
    extracted_fets = len(re.findall(r"^X\S+\s+.*sky130_fd_pr__nfet_01v8\b", spice_text, re.M | re.I))
    effective_nf = sum(int(value) for value in re.findall(r"^X\S+\s+.*\bnf=(\d+)\b", spice_text, re.M | re.I))
    bench = OUT / "moscap_ac.cir"
    bench.write_text(f'''* Extracted-layout SKY130 MOS gate capacitance probe
.include "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice"
.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
.include "/workspace/artifacts/analog_asic/layout/{OUT_NAME}/{CELL}.spice"
Vgate gate 0 dc 0.9 ac 1
Xcap gate 0 0 {CELL}
.control
set noaskquit
set numdgt=15
ac lin 1 1meg 1meg
let cgate=abs(imag(i(Vgate)))/(2*pi*frequency)
print cgate
quit
.endc
.end
''', encoding="ascii")
    sim = docker_run(
        SIM_IMAGE, ["ngspice", "-b", f"/workspace/artifacts/analog_asic/layout/{OUT_NAME}/moscap_ac.cir"],
        timeout=150, workdir="/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice")
    sim_log = sim.stdout + sim.stderr
    (OUT / "ngspice_ac.log").write_text(sim_log, encoding="utf-8")
    if sim.returncode or "cgate" not in sim_log.lower() or "Timestep too small" in sim_log:
        raise RuntimeError(f"Extracted MOSCAP AC simulation failed:\n{sim_log[-5000:]}")
    hold_bench = OUT / "moscap_hold_5ms.cir"
    hold_bench.write_text(f'''* Extracted-layout SKY130 MOS gate-cap 5ms retention probe
.include "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice"
.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
.include "/workspace/artifacts/analog_asic/layout/{OUT_NAME}/{CELL}.spice"
Vwrite write 0 0.9
Vctrl ctrl 0 PWL(0 1.8 0.999u 1.8 1u 0 5m 0)
Swrite gate write ctrl 0 swmod
.model swmod SW(Ron=100 Roff=1e15 Vt=0.9 Vh=0.1)
Xcap gate 0 0 {CELL}
.ic v(gate)=0.9
.control
set noaskquit
set numdgt=15
tran 10u 5m 0 10u uic
meas tran vstart find v(gate) at=0.999u
meas tran vend find v(gate) at=5m
let droop=vend-vstart
print droop
quit
.endc
.end
''', encoding="ascii")
    hold_sim = docker_run(
        SIM_IMAGE, ["ngspice", "-b", f"/workspace/artifacts/analog_asic/layout/{OUT_NAME}/moscap_hold_5ms.cir"],
        timeout=180, workdir="/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice")
    hold_log = hold_sim.stdout + hold_sim.stderr
    (OUT / "ngspice_hold_5ms.log").write_text(hold_log, encoding="utf-8")
    if hold_sim.returncode or "vend" not in hold_log.lower() or "Timestep too small" in hold_log:
        raise RuntimeError(f"Extracted MOSCAP hold simulation failed:\n{hold_log[-5000:]}")
    def scalar(name: str, log: str) -> float | None:
        match = re.search(rf"\b{name}\s*=\s*([-+0-9.eE]+)", log, re.I)
        return float(match.group(1)) if match else None
    report = {
        "device": "sky130_fd_pr__nfet_01v8 used as a MOS gate capacitor",
        "layout_cell": CELL, "pcell_request_um": {"w": W_UM, "l": L_UM, "nf": NF},
        "extracted_fet_instances": extracted_fets, "extracted_model_nf_total": effective_nf or extracted_fets,
        "requested_nf_realized": NF == (effective_nf or extracted_fets),
        "pins": ["GATE", "VSS", "BULK"],
        "source_drain_tied_in_layout": True, "bulk_tied_to_vss_in_testbench": True,
        "magic_drc_zero": True, "netgen_lvs_unique_match": True,
        "ac_bias_v": 0.9, "ac_frequency_hz": 1e6,
        "extracted_cgate_f": scalar("cgate", sim_log),
        "hold_start_v": scalar("vstart", hold_log),
        "hold_end_v": scalar("vend", hold_log),
        "hold_droop_v": scalar("droop", hold_log),
        "process_corner": "tt", "temperature_c": 27,
        "limitations": ["PCell nf request is not reflected in extracted device count; measured geometry is one device",
                         "schematic PDK device noise and mismatch not included",
                         "ideal write switch; no extracted interconnect resistance/capacitance"]
    }
    (OUT / "moscap_layout_qualification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "magic_build.log").write_text(
        phase1 + "\n--- flattened MOSCAP extraction ---\n" + phase2,
        encoding="utf-8")
    print(phase2[-8000:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
