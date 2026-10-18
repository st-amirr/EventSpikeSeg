"""Route the qualified MIM writer and scale PFET as a reusable GF180 macro."""
import hashlib
import json
import re
from pathlib import Path

import probe_gf180_mos_gate_cap as flow


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cell = "gf180_membrane_scale_current_cell_v3"
    source = "gf180_sampled_weight_current_cell_fullroute_complete_guarded"
    scale_fet = "gf180_membrane_scale_pf042_l10_fullroute_v2"
    out = flow.BASE / "layout" / cell
    out.mkdir(parents=True, exist_ok=True)
    if (out / "qualification.json").exists():
        raise ValueError("Preserve existing qualified macro")
    flow.OUT = out
    children, qualifications, inputs = {}, {}, set()
    for name in (source, scale_fet):
        directory = flow.BASE / "layout" / name
        qpath = directory / "qualification.json"
        q = json.loads(qpath.read_text(encoding="utf-8"))
        assert q["magic_drc_count"] == 0 and q["lvs_unique"] and q["gds_roundtrip_drc_count"] == 0 and q["gds_roundtrip_lvs_unique"]
        inputs.add(qpath)
        for group in ("sha256", "input_sha256", "gds_roundtrip_sha256"):
            for rel, expected in q.get(group, {}).items():
                path = directory / rel if group == "sha256" else flow.ROOT / rel
                if digest(path) != expected:
                    raise ValueError("Changed child qualification evidence: " + str(path))
                inputs.add(path)
        children[name] = directory
        qualifications[name] = q

    dependencies = ["gf180_source_nf05_l1_compact", "gf180_source_pf05_l1_compact", "gf180_fixed_body_tg_fullroute_half", "gf180_signed_cascode_source_compact_guarded", "gf180_mim_bank_7x7_n9"]
    for name in dependencies:
        children[name] = flow.BASE / "layout" / name

    nets = ["PROGRAM", "WRITE", "WRITEB", "VCM", "NCAS", "PCAS", "VDD", "VSS", "SCALE_OUT", "WEIGHT", "NI", "PI"]
    first_track = 74000
    pitch = 800
    tracks = {net: first_track + i * pitch for i, net in enumerate(nets)}
    layers = {}

    def rect(layer, box):
        layers.setdefault(layer, []).append(tuple(box))

    def via(low, high, cut, x, y, pad=44):
        for layer in (low, high):
            enclosure = max(pad, 60) if layer == "metal5" else pad
            rect(layer, (x - enclosure, y - enclosure, x + enclosure, y + enclosure))
        rect(cut, (x - 28, y - 28, x + 28, y + 28))

    scale_bbox = [round(value / 0.005) for value in qualifications[scale_fet]["bbox_um"]]
    source_bbox = [round(value / 0.005) for value in qualifications[source]["bbox_um"]]
    fet_dx = source_bbox[2] + 12000
    configurations = [
        ("held", source, 0, 0,
         ["PROGRAM", "WRITE", "WRITEB", "VCM", "VCM", "NCAS", "PCAS", "VDD", "VSS", "WEIGHT", "NI", "PI"]),
        ("scalefet", scale_fet, fet_dx, 0, ["SCALE_OUT", "WEIGHT", "VDD"]),
    ]
    uses = []
    for instance, name, dx, dy, mapping in configurations:
        bbox = [round(value / 0.005) for value in qualifications[name]["bbox_um"]]
        uses.extend([f"use {name} {instance}", f"transform 1 0 {dx} 0 1 {dy}", "box " + " ".join(map(str, bbox))])
        mag = (children[name] / f"{name}.mag").read_text(encoding="utf-8")
        labels = re.findall(r"(?m)^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)\nport (\d+)", mag)
        ordered = sorted(labels, key=lambda row: int(row[-1]))
        if len(ordered) != len(mapping):
            raise ValueError(f"Port inventory mismatch for {name}: {len(ordered)} != {len(mapping)}")
        fanout_pitch = 240 if name == source else 500
        for i, (label, net) in enumerate(zip(ordered, mapping)):
            layer, x1, y1, x2, y2, _, _ = label
            x = dx + (int(x1) + int(x2)) // 2
            y = dy + (int(y1) + int(y2)) // 2
            column = dx + bbox[0] - 700 - i * fanout_pitch
            half_width = 60 if layer == "metal5" else 42
            rect(layer, (min(x, column) - half_width, y - half_width, max(x, column) + half_width, y + half_width))
            if layer == "metal1":
                via("metal1", "metal2", "via1", column, y)
                via("metal2", "metal3", "via2", column, y)
                via("metal3", "metal4", "via3", column, y)
            elif layer == "metal2":
                via("metal2", "metal3", "via2", column, y)
                via("metal3", "metal4", "via3", column, y)
            elif layer == "metal3":
                via("metal3", "metal4", "via3", column, y)
            elif layer == "metal4":
                pass
            elif layer != "metal5":
                raise ValueError("Unexpected child port layer " + layer)
            rect("metal4", (column - 42, y - 42, column + 42, tracks[net] + 42))
            via("metal4", "metal5", "via4", column, tracks[net])

    left_edge = min(source_bbox[0], fet_dx + scale_bbox[0]) - 3000
    right_edge = fet_dx + scale_bbox[2] + 3000
    for y in tracks.values():
        rect("metal5", (left_edge, y - 60, right_edge, y + 60))
    lines = ["magic", "tech gf180mcuD", "magscale 1 10", "timestamp 0", *uses]
    for layer, boxes in layers.items():
        lines += ["<< " + layer + " >>"] + ["rect " + " ".join(map(str, box)) for box in boxes]
    lines += ["<< labels >>"]
    for number, net in enumerate(nets, 1):
        y = tracks[net]
        lines += [f"rlabel metal5 s {left_edge + 150} {y-20} {left_edge + 190} {y+20} 4 {net}", f"port {number} nsew"]
    lines += ["<< end >>", ""]
    (out / f"{cell}.mag").write_text("\n".join(lines), encoding="ascii")
    (out / "build_source.py").write_bytes(Path(__file__).read_bytes())
    preload_names = dependencies + [source, scale_fet]
    preload = "\n".join("load /workspace/" + (children[name] / name).relative_to(flow.ROOT).as_posix() for name in preload_names) + "\n"
    log = flow.magic(preload + f"load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs \"BBOX [box values]\"\nquit -noprompt\n")
    (out / "extraction.log").write_text(log, encoding="utf-8")
    drc = re.search(r"Total DRC errors found:\s*(\d+)", log)
    if not drc or int(drc[1]) or (out / "gds_warnings.feedback").read_text() or re.search(r"\d+ problems occurred", log):
        raise RuntimeError("Parent DRC/GDS export failed:\n" + log[-4000:])
    ref = "".join((directory / f"{name}.spice").read_text(encoding="utf-8") + "\n" for name, directory in children.items())
    ref += ".subckt reference " + " ".join(nets) + "\n"
    ref += f"Xheld PROGRAM WRITE WRITEB VCM VCM NCAS PCAS VDD VSS WEIGHT NI PI {source}\n"
    ref += f"Xscale SCALE_OUT WEIGHT VDD {scale_fet}\n.ends\n"
    (out / "reference.spice").write_text(ref, encoding="utf-8")
    setup = "/workspace/" + flow.PDK.relative_to(flow.ROOT).as_posix() + "/libs.tech/netgen/gf180mcuD_setup.tcl"
    lvs = flow.run(["netgen-lvs", "-batch", "lvs", f"{cell}.spice {cell}", "reference.spice reference", setup, "lvs.out"])
    (out / "netgen.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely" not in lvs:
        raise RuntimeError("Parent LVS failed:\n" + lvs[-3500:])
    caplog = flow.magic(preload + f"load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n")
    (out / "capacitance_extraction.log").write_text(caplog, encoding="utf-8")
    if (out / "warnings.feedback").read_text() or (out / "capacitance_warnings.feedback").read_text():
        raise ValueError("Unresolved extraction feedback")
    rd = flow.BASE / "verification/gds_roundtrip" / cell
    rd.mkdir(parents=True, exist_ok=True)
    flow.OUT = rd
    readlog = flow.magic("gds read /workspace/" + (out / f"{cell}.gds").relative_to(flow.ROOT).as_posix() + f"\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n")
    (rd / "readback.log").write_text(readlog, encoding="utf-8")
    rdr = re.search(r"Total DRC errors found:\s*(\d+)", readlog)
    rlvs = flow.run(["netgen-lvs", "-batch", "lvs", f"roundtrip.spice {cell}", "/workspace/" + (out / "reference.spice").relative_to(flow.ROOT).as_posix() + " reference", setup, "lvs.out"])
    (rd / "netgen.log").write_text(rlvs, encoding="utf-8")
    if not rdr or int(rdr[1]) or "Circuits match uniquely" not in rlvs or (rd / "roundtrip.feedback").read_text():
        raise RuntimeError("GDS readback failed\n" + readlog[-1800:] + "\n" + rlvs[-1800:])
    generated = [out / f"{cell}{suffix}" for suffix in (".mag", ".spice", "_cap.spice", ".gds")]
    generated += [out / name for name in ("build_source.py", "extraction.log", "reference.spice", "netgen.log", "capacitance_extraction.log", "warnings.feedback", "gds_warnings.feedback", "capacitance_warnings.feedback")]
    q = {
        "cell": cell, "ports": nets, "magic_drc_count": 0, "lvs_unique": True,
        "gds_roundtrip_drc_count": 0, "gds_roundtrip_lvs_unique": True, "extraction_feedback": "",
        "bbox_um": [int(value) * 0.005 for value in re.search(r"BBOX ([-0-9 ]+)", log).group(1).split()],
        "native_mim_count": 9, "native_mos_count": qualifications[source].get("mos_count", 0) + 1,
        "reused_extracted_source_macro": source, "scale_fet_geometry_um": {"w": 0.42, "l": 10.0},
        "physical_scale_cell_accepted": False, "scope": "Hierarchical GDS macro combines the extracted 9-MIM analog writer with an additional long-channel PFET for bank-scale current. Native child geometry and full routed parent have DRC/LVS/GDS-readback checks; new transient confirms nominal 5ms hold/current transfer. The PFET/layout parasitics require a fresh extracted transient before acceptance. No scale-weight multiplier, full membrane update, PVT/noise or original-float inference is qualified.",
        "sha256": {path.name: digest(path) for path in generated},
        "input_sha256": {path.relative_to(flow.ROOT).as_posix(): digest(path) for path in sorted(inputs)},
        "gds_roundtrip_sha256": {path.relative_to(flow.ROOT).as_posix(): digest(path) for path in (rd / name for name in ("readback.log", "netgen.log", "roundtrip.spice", "roundtrip.feedback"))},
    }
    (out / "qualification.json").write_text(json.dumps(q, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out / "qualification.json"), "bbox_um": q["bbox_um"], "gds_roundtrip_lvs_unique": True}, indent=2))


if __name__ == "__main__":
    main()
