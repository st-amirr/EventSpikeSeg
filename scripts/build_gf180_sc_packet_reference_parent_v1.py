"""Physically join the trained-beta SC lane and its decoupled native reference."""
from pathlib import Path
import hashlib
import json
import re
import probe_gf180_mos_gate_cap as flow


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cell = "gf180_sc_packet_reference_parent_v1"
    lane = "gf180_sc_packet_detailstem_ch3_v4"
    reference = "gf180_aux_reference_divider_v2"
    out = flow.BASE / "layout" / cell
    assert not out.exists()
    out.mkdir(parents=True)
    flow.OUT = out
    geometry = {}
    inputs = set()
    children = {}
    for name in (lane, reference):
        directory = flow.BASE / "layout" / name
        qp = directory / "qualification.json"
        q = json.loads(qp.read_text())
        assert q["magic_drc_count"] == 0 and q["lvs_unique"] and q["gds_roundtrip_drc_count"] == 0 and q["gds_roundtrip_lvs_unique"]
        inputs.add(qp)
        for filename, digest in q["sha256"].items():
            p = directory / filename
            assert sha(p) == digest, str(p)
            inputs.add(p)
            if p.suffix == ".mag":
                geometry[p.stem] = p
        for filename, digest in q.get("input_sha256", {}).items():
            p = flow.ROOT / filename
            if p.suffix == ".mag":
                assert sha(p) == digest, str(p)
                assert p.stem not in geometry or geometry[p.stem] == p
                geometry[p.stem] = p
                inputs.add(p)
        children[name] = (directory, q)
    ports = children[lane][1]["ports"]
    labels = re.findall(r"^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$", geometry[lane].read_text(), re.M)
    pins = {row[-1]: (row[0], tuple(map(int, row[1:5]))) for row in labels}
    assert set(pins) == set(ports)
    uses = []
    for name, inst, transform in ((lane, "compute", "1 0 0 0 1 0"), (reference, "reference", "0 -1 -40000 1 0 2500")):
        bbox = [round(v / .005) for v in children[name][1]["bbox_um"]]
        uses += [f"use {name} {inst}", "transform " + transform, "box " + " ".join(map(str, bbox))]
    layers = {}

    def rect(layer, box):
        layers.setdefault(layer, []).append(tuple(box))

    def via4(x, y):
        rect("metal4", (x - 90, y - 90, x + 90, y + 90))
        rect("metal5", (x - 73, y - 73, x + 73, y + 73))
        rect("via4", (x - 28, y - 28, x + 28, y + 28))

    # Escape on M4 at free locations on the rotated reference's M5 buses.
    routes = {"AUXREF": (-56600, 770, -60800, 19000), "VDD": (-56000, 4500, -61600, 19800), "VSS": (-57800, 8000, -62400, 20600)}
    for net, (rx, ry, escape, track) in routes.items():
        layer, box = pins[net]
        assert layer == "metal5"
        px, py = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        via4(px, py)
        rect("metal4", (px - 80, min(py, track), px + 80, max(py, track)))
        via4(px, track)
        via4(rx, ry)
        rect("metal4", (min(rx, escape), ry - 80, max(rx, escape), ry + 80))
        rect("metal4", (escape - 80, ry - 80, escape + 80, track + 80))
        via4(escape, track)
        rect("metal5", (min(escape, px) - 73, track - 60, max(escape, px) + 73, track + 60))
    lines = ["magic", "tech gf180mcuD", "magscale 1 10", "timestamp 0", *uses]
    for layer, boxes in layers.items():
        lines += ["<< " + layer + " >>"] + ["rect " + " ".join(map(str, box)) for box in boxes]
    lines += ["<< labels >>"]
    for index, net in enumerate(ports, 1):
        layer, box = pins[net]
        lines += [f"rlabel {layer} s " + " ".join(map(str, box)) + f" 4 {net}", f"port {index} nsew"]
    lines += ["<< end >>", ""]
    (out / (cell + ".mag")).write_text("\n".join(lines), encoding="ascii")
    (out / "build_source.py").write_bytes(Path(__file__).read_bytes())
    visited = set()
    views = []

    def visit(name):
        if name in visited:
            return
        p = geometry[name]
        for child in re.findall(r"^use\s+(\S+)\s+", p.read_text(), re.M):
            visit(child)
        visited.add(name)
        views.append(p)

    visit(lane);visit(reference)
    preload = "".join("load /workspace/" + p.with_suffix("").relative_to(flow.ROOT).as_posix() + "\n" for p in views)
    log = flow.magic(preload + f"load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs \"BBOX [box values]\"\nquit -noprompt\n")
    (out / "extraction.log").write_text(log)
    assert re.search(r"Total DRC errors found:\s*0\b", log), log[-3000:]
    assert not (out / "warnings.feedback").read_text() and not (out / "gds_warnings.feedback").read_text()
    ref = "\n".join((directory / (name + ".spice")).read_text() for name, (directory, _) in children.items())
    ref += "\n.subckt reference " + " ".join(ports) + "\nXcompute " + " ".join(ports) + " " + lane + "\nXref VDD AUXREF REFMID VSS " + reference + "\n.ends reference\n"
    (out / "reference.spice").write_text(ref)
    setup = "/workspace/" + flow.PDK.relative_to(flow.ROOT).as_posix() + "/libs.tech/netgen/gf180mcuD_setup.tcl"
    lvs = flow.run(["netgen-lvs", "-batch", "lvs", cell + ".spice " + cell, "reference.spice reference", setup, "lvs.out"])
    (out / "netgen.log").write_text(lvs)
    assert "Circuits match uniquely" in lvs, lvs[-3000:]
    caplog = flow.magic(preload + f"load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n")
    (out / "capacitance_extraction.log").write_text(caplog)
    assert not (out / "capacitance_warnings.feedback").read_text()
    rd = flow.BASE / "verification/gds_roundtrip" / cell
    rd.mkdir(parents=True)
    flow.OUT = rd
    readlog = flow.magic("gds read /workspace/" + (out / (cell + ".gds")).relative_to(flow.ROOT).as_posix() + f"\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n")
    (rd / "readback.log").write_text(readlog)
    rlvs = flow.run(["netgen-lvs", "-batch", "lvs", "roundtrip.spice " + cell, "/workspace/" + (out / "reference.spice").relative_to(flow.ROOT).as_posix() + " reference", setup, "lvs.out"])
    (rd / "netgen.log").write_text(rlvs)
    assert re.search(r"Total DRC errors found:\s*0\b", readlog) and "Circuits match uniquely" in rlvs
    assert not (rd / "roundtrip.feedback").read_text()
    outputs = [out / (cell + s) for s in (".mag", ".spice", ".gds", "_cap.spice")] + [out / n for n in ("build_source.py", "reference.spice", "extraction.log", "netgen.log", "capacitance_extraction.log", "warnings.feedback", "gds_warnings.feedback", "capacitance_warnings.feedback")]
    q = {"cell": cell, "ports": ports, "children": [lane, reference], "magic_drc_count": 0, "lvs_unique": True, "gds_roundtrip_drc_count": 0, "gds_roundtrip_lvs_unique": True, "extraction_feedback": "", "bbox_um": [int(v) * .005 for v in re.search(r"BBOX ([-0-9 ]+)", log)[1].split()], "scope": "Actual routed reference-to-compute parent, including native poly reference and MIM decoupling. One compute lane; separate21-load sharing evidence does not prove this parent32/128-lane service. Capacitance extraction, no routing RPEX. Extracted transient, physical weight/VCM/control producers, model accuracy and5ms service remain unqualified.", "sha256": {p.name: sha(p) for p in outputs}, "input_sha256": {p.relative_to(flow.ROOT).as_posix(): sha(p) for p in sorted(inputs)}, "gds_roundtrip_sha256": {p.relative_to(flow.ROOT).as_posix(): sha(p) for p in (rd / "readback.log", rd / "netgen.log", rd / "roundtrip.spice", rd / "roundtrip.feedback")}}
    (out / "qualification.json").write_text(json.dumps(q, indent=2) + "\n")
    print(json.dumps({"cell": cell, "bbox_um": q["bbox_um"], "DRC_LVS_GDS_readback": True}, indent=2))


if __name__ == "__main__":
    main()
