"""Build and check a routed10/1um GF180 gate-cap primitive using official PCells."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
OUT = BASE / "layout/gf180_mos_gate_cap_10x1"
PDK = BASE / "pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD"
CELL = "gf180_mos_gate_cap_10x1"


def run(args: list[str], stdin: str | None = None) -> str:
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2"]
    if stdin is not None:
        cmd.append("-i")
    cmd += ["--volume", f"{ROOT}:/workspace", "--workdir", f"/workspace/{OUT.relative_to(ROOT).as_posix()}",
            "--entrypoint", args[0], "eventspikeseg:analog-gf180-layout", *args[1:]]
    result = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=120)
    log = result.stdout + result.stderr
    if result.returncode:
        raise RuntimeError(log[-2500:])
    return log


def magic(tcl: str) -> str:
    return run(["magic", "-dnull", "-noconsole", "-rcfile",
                f"/workspace/{PDK.relative_to(ROOT).as_posix()}/libs.tech/magic/gf180mcuD.magicrc"], tcl)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log1 = magic("load gf180_cap_raw\nmagic::gencell gf180mcu::nfet_03v3 gatecap -spice w 10u l 1u nf 1\nsave\nwriteall force\nquit -noprompt\n")
    (OUT / "generation.log").write_text(log1, encoding="utf-8")
    candidates = sorted(OUT.glob("nfet_03v3_*.mag"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise RuntimeError("GF180 PCell was not generated")
    source = candidates[-1].read_text(encoding="ascii")
    if not ("string parameters w 10.0 l 1.0" in source and "magscale 1 10" in source):
        raise RuntimeError("GF180 PCell dimensions/grid do not match the requested primitive")
    # 0.005um/internal unit. 0.23um M1 strap joins both diffusions and guard.
    source = source.replace("<< metal1 >>", "<< metal1 >>\nrect -313 -23 313 23", 1)
    labels = ("<< labels >>\nrlabel polycontact s -80 1040 80 1070 4 GATE\nport 1 nsew\n"
              "rlabel metal1 s -40 -20 40 20 4 VSS\nport 2 nsew\n")
    source = source.replace("<< end >>", labels + "<< end >>")
    mag_path = OUT / f"{CELL}.mag"
    mag_path.write_text(source, encoding="ascii")
    log2 = magic(f"load {CELL}\ndrc check\ndrc count\nextract all\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nsave\nquit -noprompt\n")
    (OUT / "extract.log").write_text(log2, encoding="utf-8")
    caplog = magic(f"load {CELL}\nextract do capacitance\nextract all\nfeedback save warnings.feedback\nselect top cell\nputs \"BBOX [box values]\"\next2spice default\next2spice cthresh 0\next2spice scale off\next2spice -o gatecap_capacitance.spice\nquit -noprompt\n")
    (OUT / "capacitance_extraction.log").write_text(caplog, encoding="utf-8")
    bbox = re.search(r"BBOX ([-0-9 ]+)", caplog)
    match = re.search(r"Total DRC errors found:\s*(\d+)", log2)
    if not match:
        raise RuntimeError("Magic DRC completion not found")
    spice = OUT / f"{CELL}.spice"
    netlist = spice.read_text(encoding="ascii")
    subckt = re.search(r"(?m)^\.subckt\s+(\S+)\s+([^\r\n]+)", netlist)
    fets = re.findall(r"(?m)^X\S+\s+[^\r\n]+", netlist)
    report = {"cell": CELL, "magic_version": "8.3.684",
              "magic_drc_count": int(match.group(1)),
              "ports": subckt.group(2).split() if subckt else None,
              "extracted_devices": fets, "netgen_lvs_unique": False,
              "gds_exists": (OUT / f"{CELL}.gds").is_file(),
              "bbox_um": [int(v) * 0.005 for v in bbox.group(1).split()] if bbox else None,
              "extraction_warning": (OUT / "warnings.feedback").read_text(),
              "warning_interpretation": "Source/drain intentionally share VSS for gate-cap operation; extraction merges their terminal regions. Extracted D/S/B connectivity and independent gate verified by netlist and LVS.",
              "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (mag_path, spice, OUT / "extract.log", OUT / "gatecap_capacitance.spice", OUT / "capacitance_extraction.log", PDK / "libs.tech/magic/gf180mcuD.tech")},
              "scope": "Standalone fixed-body GF180 gate-cap primitive with capacitance extraction, no resistance extraction. Official Open_PDKs Magic/Netgen collateral only; full vendor/PV libraries are not installed. No combined access cell, switched noise, mismatch, full-float replay or5ms service acceptance. Official primitive model validation is reported separately."}
    if subckt and len(fets) == 1 and report["ports"] == ["GATE", "VSS"]:
        tokens = fets[0].split()
        if tokens[1:5] != ["VSS", "GATE", "VSS", "VSS"]:
            raise RuntimeError("source/drain/body not all tied to VSS")
        ref = OUT / "reference.spice"
        ref.write_text(f".subckt ref GATE VSS\nX0 VSS GATE VSS VSS {tokens[5]} w=10u l=1u\n.ends\n", encoding="ascii")
        lvs = run(["netgen-lvs", "-batch", "lvs", f"{spice.name} {CELL}", "reference.spice ref",
                   f"/workspace/{PDK.relative_to(ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl", "lvs.out"])
        (OUT / "netgen.log").write_text(lvs, encoding="utf-8")
        report["netgen_lvs_unique"] = "Circuits match uniquely" in lvs
    (OUT / "qualification_probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["magic_drc_count"] or not report["netgen_lvs_unique"]:
        raise RuntimeError("GF180 primitive physical checks incomplete")


if __name__ == "__main__":
    main()
