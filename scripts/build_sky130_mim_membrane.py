"""Generate a reusable SKY130 10x10um MIM cell and qualify its extracted C."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2"
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
CELL = "membrane_cap_mim_10x10um"
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
        input_text=tcl, timeout=180,
        workdir="/workspace/artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2")
    log = result.stdout + result.stderr
    if result.returncode:
        raise RuntimeError(f"Magic failed ({result.returncode}):\n{log}")
    return log


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "membrane_mim_raw.mag"
    raw.write_text("magic\ntech sky130A\nmagscale 1 2\ntimestamp 0\n"
                   "<< checkpaint >>\n<< end >>\n", encoding="ascii")
    phase1 = run_magic("\n".join([
        "load membrane_mim_raw",
        "magic::gencell sky130::sky130_fd_pr__cap_mim_m3_2 cap -spice w 10 l 10",
        "save", "writeall force", "quit -noprompt", "",
    ]))

    raw_text = raw.read_text(encoding="ascii")
    labels = ("<< labels >>\n"
              "rlabel mimcap2 s 1000 1000 1500 1200 4 MEM_P\nport 1 nsew\n"
              "rlabel metal4 s 500 500 1000 900 4 MEM_N\nport 2 nsew\n")
    if "<< labels >>" in raw_text or raw_text.count("<< end >>") != 1:
        raise RuntimeError("Unexpected raw Magic cell structure; refusing to label it")
    raw.write_text(raw_text.replace("<< end >>", labels + "<< end >>"), encoding="ascii")
    phase2 = run_magic("\n".join([
        "load membrane_mim_raw", f"flatten {CELL}", f"load {CELL}",
        "drc check", "drc count", "extract all", "ext2spice lvs",
        "ext2spice scale off", f"ext2spice -o {CELL}.spice",
        f"gds write {CELL}.gds", "save", "quit -noprompt", "",
    ]))
    (OUT / "magic_build.log").write_text(
        phase1 + "\n--- labeled flatten and extraction ---\n" + phase2, encoding="utf-8")
    if "Total DRC errors found: 0" not in phase2:
        raise RuntimeError("Magic DRC did not report zero errors; inspect magic_build.log")

    spice = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    if not re.search(rf"\.subckt\s+{CELL}\s+MEM_P\s+MEM_N\b", spice, re.I):
        raise RuntimeError("Extracted macro does not expose the expected two terminals")
    if not re.search(r"X\S+\s+MEM_P\s+MEM_N\s+sky130_fd_pr__cap_mim_m3_2\b.*\bw=1e\+07u\b.*\bl=1e\+07u\b", spice, re.I) and not re.search(r"X\S+\s+MEM_P\s+MEM_N\s+sky130_fd_pr__cap_mim_m3_2\b.*\bl=1e\+07u\b.*\bw=1e\+07u\b", spice, re.I):
        raise RuntimeError("Extracted MIM device pins or 10x10um dimensions are unexpected")

    ref = OUT / "mim_reference.spice"
    ref.write_text(".subckt mim_reference MEM_P MEM_N\n"
                   "X0 MEM_P MEM_N sky130_fd_pr__cap_mim_m3_2 w=10 l=10\n"
                   ".ends\n", encoding="ascii")
    lvs = docker_run(
        LAYOUT_IMAGE, ["netgen-lvs", "-batch", "lvs", f"{CELL}.spice {CELL}",
                       "mim_reference.spice mim_reference",
                       "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl",
                       "mim_lvs.out"], timeout=120,
        workdir="/workspace/artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2")
    lvs_log = lvs.stdout + lvs.stderr
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    if lvs.returncode or "Result: Circuits match uniquely." not in lvs_log:
        raise RuntimeError(f"Netgen LVS failed:\n{lvs_log}")

    cv = OUT / "mim_cap_cv.cir"
    cv.write_text(f"""* Extracted SKY130 MIM transient capacitance check
.include \"/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/parameters/invariant.spice\"
.lib \"/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice\" tt
.include \"/workspace/artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2/{CELL}.spice\"
Vdrive vin 0 PWL(0 0 1n 10m)
Xcap vin 0 {CELL}
.control
set noaskquit
tran 10p 0.9n
meas tran imean AVG i(Vdrive) from=0.2n to=0.8n
let ceff=abs(imean)/(10m/1n)
print ceff
quit
.endc
.end
""", encoding="ascii")
    sim = docker_run(
        SIM_IMAGE, ["ngspice", "-b",
                    "/workspace/artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2/mim_cap_cv.cir"],
        timeout=150, workdir="/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice")
    sim_log = sim.stdout + sim.stderr
    (OUT / "ngspice_cv.log").write_text(sim_log, encoding="utf-8")
    match = re.search(r"\bceff\s*=\s*([-+0-9.eE]+)", sim_log, re.I)
    if sim.returncode or not match or "ngspice-36 done" not in sim_log:
        raise RuntimeError(f"Extracted MIM transient simulation failed:\n{sim_log}")
    ceff = float(match.group(1))
    expected = 207.6e-15
    error_pct = 100 * (ceff - expected) / expected
    if abs(error_pct) > 2:
        raise RuntimeError(f"Extracted C differs from 207.6fF by {error_pct:.3f}%")

    ruby = OUT / "inspect_gds.rb"
    ruby.write_text(f"""include RBA
l=Layout.new
l.read('/workspace/artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2/{CELL}.gds')
c=l.cell('{CELL}')
b=c.bbox
puts \"bbox_um=#{{(b.width*l.dbu).round(4)}}x#{{(b.height*l.dbu).round(4)}}\"
""", encoding="ascii")
    inspect = docker_run(
        LAYOUT_IMAGE, ["klayout", "-b", "-r",
                       "/workspace/artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2/inspect_gds.rb"],
        timeout=90, workdir="/workspace")
    gds_log = inspect.stdout + inspect.stderr
    (OUT / "klayout_geometry.log").write_text(gds_log, encoding="utf-8")
    bbox = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", gds_log)
    if inspect.returncode or not bbox:
        raise RuntimeError(f"KLayout could not inspect GDS:\n{gds_log}")

    report = {
        "cell": CELL, "device": "sky130_fd_pr__cap_mim_m3_2",
        "terminal_order": ["MEM_P", "MEM_N"], "device_geometry_um": {"w": 10, "l": 10},
        "gds_bbox_um": [float(bbox.group(1)), float(bbox.group(2))],
        "drc_zero_errors": True, "netgen_lvs_unique_match": True,
        "expected_cv_f": expected, "extracted_cv_f": ceff, "cv_error_pct": error_pct,
        "cv_simulation_completed": True,
        "scope": "Single extracted MIM capacitor; no switch, state update, retention, noise, PVT spread, fan-in, or model accuracy qualification.",
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

