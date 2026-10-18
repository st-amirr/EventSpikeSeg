"""Enlarge the existing linear AUX/AUXREF metal plates; preserve native devices."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import probe_gf180_mos_gate_cap as flow


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_name = "gf180_nf_state_update_aux_overlap"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--area-um2", type=float, required=True)
    args = parser.parse_args()
    height = round(args.area_um2 / (20 * .005))
    assert 120 <= height <= 6000 and abs(height * 20 * .005 - args.area_um2) < 1e-8
    cell = source_name + str(args.area_um2).replace(".", "p")
    source = flow.BASE / "layout" / source_name
    out = flow.BASE / "layout" / cell
    assert not out.exists()
    original_q = json.loads((source / "qualification.json").read_text())
    assert original_q["magic_drc_count"] == 0 and original_q["lvs_unique"]
    for suffix in (".mag", ".spice", ".gds"):
        path = source / (source_name + suffix)
        assert sha(path) == original_q["sha256"][path.name]
    mag = (source / (source_name + ".mag")).read_text()
    assert mag.count("rect 600 3000 2600 5000") == 2
    mag = mag.replace("rect 600 3000 2600 5000", f"rect -1400 3000 2600 {3000 + height}")
    out.mkdir(parents=True)
    flow.OUT = out
    (out / (cell + ".mag")).write_text(mag, encoding="ascii")
    (out / "build_source.py").write_bytes(Path(__file__).read_bytes())
    (out / "reference.spice").write_bytes((source / "reference.spice").read_bytes())
    leaves = ["gf180_fixed_body_tg_quarter_shorttracks", "gf180_fixed_body_nf025_shorttracks"]
    inputs = {source / "qualification.json", source / (source_name + ".mag"), source / "reference.spice", Path(__file__)}
    preload = ""
    for name in leaves:
        path = flow.BASE / "layout" / name / (name + ".mag")
        inputs.add(path)
        preload += "load /workspace/" + path.with_suffix("").relative_to(flow.ROOT).as_posix() + "\n"
    log = flow.magic(preload + f"load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs \"BBOX [box values]\"\nquit -noprompt\n")
    (out / "extraction.log").write_text(log)
    assert re.search(r"Total DRC errors found:\s*0\b", log), log[-3000:]
    assert not (out / "warnings.feedback").read_text() and not (out / "gds_warnings.feedback").read_text()
    setup = "/workspace/" + flow.PDK.relative_to(flow.ROOT).as_posix() + "/libs.tech/netgen/gf180mcuD_setup.tcl"
    lvs = flow.run(["netgen-lvs", "-batch", "lvs", cell + ".spice " + cell, "reference.spice reference", setup, "lvs.out"])
    (out / "netgen.log").write_text(lvs)
    assert "Circuits match uniquely" in lvs, lvs[-3000:]
    caplog = flow.magic(preload + f"load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n")
    (out / "capacitance_extraction.log").write_text(caplog)
    assert not (out / "capacitance_warnings.feedback").read_text()
    rd = flow.BASE / "verification" / "gds_roundtrip" / cell
    rd.mkdir(parents=True)
    flow.OUT = rd
    readlog = flow.magic("gds read /workspace/" + (out / (cell + ".gds")).relative_to(flow.ROOT).as_posix() + f"\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n")
    (rd / "readback.log").write_text(readlog)
    rlvs = flow.run(["netgen-lvs", "-batch", "lvs", "roundtrip.spice " + cell, "/workspace/" + (out / "reference.spice").relative_to(flow.ROOT).as_posix() + " reference", setup, "lvs.out"])
    (rd / "netgen.log").write_text(rlvs)
    assert re.search(r"Total DRC errors found:\s*0\b", readlog) and "Circuits match uniquely" in rlvs
    assert not (rd / "roundtrip.feedback").read_text()
    captext = (out / (cell + "_cap.spice")).read_text()
    aux_caps = [float(v) for a, b, v in re.findall(r"(?m)^C\S+ (\S+) (\S+) ([-+0-9.eE]+)f", captext) if {a, b} == {"AUX", "AUXREF"}]
    outputs = [out / (cell + s) for s in (".mag", ".spice", ".gds", "_cap.spice")] + [out / n for n in ("build_source.py", "reference.spice", "extraction.log", "netgen.log", "capacitance_extraction.log", "warnings.feedback", "gds_warnings.feedback", "capacitance_warnings.feedback")]
    q = {"cell": cell, "ports": original_q["ports"], "magic_drc_count": 0, "lvs_unique": True, "gds_roundtrip_drc_count": 0, "gds_roundtrip_lvs_unique": True, "extraction_feedback": "", "bbox_um": [int(v) * .005 for v in re.search(r"BBOX ([-0-9 ]+)", log)[1].split()], "auxiliary_overlap_um2": args.area_um2, "extracted_aux_to_auxref_ff": sum(aux_caps), "scope": "Enlarged actual M4/M5 AUX-to-AUXREF overlap with unchanged native devices. DRC/LVS/GDS readback and capacitance extraction complete; assembled transient and full PLIF accuracy remain unqualified.", "sha256": {p.name: sha(p) for p in outputs}, "input_sha256": {p.relative_to(flow.ROOT).as_posix(): sha(p) for p in sorted(inputs)}, "gds_roundtrip_sha256": {p.relative_to(flow.ROOT).as_posix(): sha(p) for p in (rd / "readback.log", rd / "netgen.log", rd / "roundtrip.spice", rd / "roundtrip.feedback")}}
    (out / "qualification.json").write_text(json.dumps(q, indent=2) + "\n")
    print(json.dumps({k: q[k] for k in ("cell", "bbox_um", "auxiliary_overlap_um2", "extracted_aux_to_auxref_ff", "magic_drc_count", "lvs_unique")}, indent=2))


if __name__ == "__main__":
    main()

