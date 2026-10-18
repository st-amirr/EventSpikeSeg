"""Assemble a compact signed-injector, membrane-state and rail-limiter parent."""
from pathlib import Path
import hashlib
import json
import re
import probe_gf180_mos_gate_cap as flow


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cell = "gf180_compact_signed_state_limiter_r3_diag"
    out = flow.BASE / "layout" / cell
    assert not out.exists()
    out.mkdir(parents=True)
    flow.OUT = out
    specs = [
        ("injector", "gf180_signed_event_injection_v1", 0, 0),
        ("state", "gf180_nf_state_update_aux_overlap", 63000, 24000),
        ("clamp_lo", "gf180_fixed_body_tg_quarter_shorttracks", 76000, 24000),
        ("clamp_hi", "gf180_fixed_body_tg_quarter_shorttracks", 84000, 30000),
    ]
    children = {}
    geometry = {}
    source_files = {Path(__file__)}
    for _, name, _, _ in specs:
        directory = flow.BASE / "layout" / name
        if name in children:
            continue
        qpath = directory / "qualification.json"
        q = json.loads(qpath.read_text())
        assert q["magic_drc_count"] == 0 and q["lvs_unique"]
        assert q["gds_roundtrip_drc_count"] == 0 and q["gds_roundtrip_lvs_unique"]
        children[name] = (directory, q)
        source_files.add(qpath)
        for key in ("sha256", "input_sha256", "gds_roundtrip_sha256"):
            for name_, digest in q.get(key, {}).items():
                path = directory / name_ if key == "sha256" else flow.ROOT / name_
                assert sha(path) == digest, name_
                source_files.add(path)
                if path.suffix == ".mag":
                    geometry.setdefault(path.stem, set()).add(path)

    ports = [
        "POS", "POSB", "NEG", "NEGB", "PPROGRAM", "NPROGRAM", "PCAS", "NCAS",
        "STATE", "DATA", "WRITE", "WRITEB", "AUXRESET", "BETA", "AUXREF", "VCM",
        "VDD", "VSS", "VRAIL_LO", "VRAIL_HI", "LIMIT_LO", "LIMIT_LOB", "LIMIT_HI", "LIMIT_HIB",
    ]

    def pinmap(inst, name):
        if inst == "injector":
            return {
                "STATE": "STATE", "PARK": "VCM", "PPROGRAM": "PPROGRAM", "NPROGRAM": "NPROGRAM",
                "PCAS": "PCAS", "NCAS": "NCAS", "POS": "POS", "POSB": "POSB", "NEG": "NEG",
                "NEGB": "NEGB", "VDD": "VDD", "VSS": "VSS",
            }
        if inst == "state":
            return {
                "STATE": "STATE", "AUX": "AUX", "DATA": "DATA", "WRITE": "WRITE", "WRITEB": "WRITEB",
                "AUXRESET": "AUXRESET", "BETA": "BETA", "AUXREF": "AUXREF", "VCM": "VCM",
                "VSS": "VSS", "VDD": "VDD",
            }
        low = inst == "clamp_lo"
        return {
            "A": "STATE", "B": "VRAIL_LO" if low else "VRAIL_HI",
            "EN": "LIMIT_LO" if low else "LIMIT_HI", "ENB": "LIMIT_LOB" if low else "LIMIT_HIB",
            "VSS": "VSS", "VDD": "VDD",
        }

    tracks = {net: 40000 + 1500 * i for i, net in enumerate(ports)}
    tracks["AUX"] = 40000 + 1500 * len(ports)
    layers = {}
    uses = []
    pin_sources = []

    def rect(layer, box):
        layers.setdefault(layer, []).append(tuple(box))

    def via4(x, y):
        rect("metal4", (x - 90, y - 90, x + 90, y + 90))
        rect("metal5", (x - 73, y - 73, x + 73, y + 73))
        rect("via4", (x - 28, y - 28, x + 28, y + 28))

    def via3(x, y):
        rect("metal3", (x - 90, y - 90, x + 90, y + 90))
        rect("metal4", (x - 80, y - 70, x + 80, y + 70))
        rect("via3", (x - 28, y - 28, x + 28, y + 28))
        via4(x, y)

    for inst, name, dx, dy in specs:
        directory, q = children[name]
        bbox = [round(value / 0.005) for value in q["bbox_um"]]
        uses += [f"use {name} {inst}", f"transform 1 0 {dx} 0 1 {dy}", "box " + " ".join(map(str, bbox))]
        mag = (directory / f"{name}.mag").read_text(encoding="ascii")
        labels = re.findall(r"^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$", mag, re.M)
        mapping = pinmap(inst, name)
        assert {row[-1] for row in labels} == set(mapping), (name, {row[-1] for row in labels}, set(mapping))
        for i, (layer, x1, y1, x2, y2, pin) in enumerate(labels):
            net = mapping[pin]
            pin_sources.append((inst, name, dx, dy, layer, int(x1), int(y1), int(x2), int(y2), net, i))

    for idx, (inst, name, dx, dy, layer, x1, y1, x2, y2, net, local_i) in enumerate(pin_sources):
        if idx >= 3:
            continue
        px, py = dx + (x1 + x2) // 2, dy + (y1 + y2) // 2
        if inst == "injector":
            rx = -4000 - idx * 500
        elif inst == "state" and layer == "metal4":
            rx = -30000 - idx * 500
        elif inst == "state":
            rx = 85000 + idx * 500
        elif inst == "clamp_lo":
            rx = 88000 + idx * 500
        else:
            rx = 92000 + idx * 500
        ty = tracks[net]
        if layer == "metal3":
            via3(px, py)
        elif layer == "metal4" and inst == "state":
            edge_x = 52000
            rect("metal4", (min(px, edge_x) - 80, py - 80, max(px, edge_x) + 80, py + 80))
            via4(edge_x, py)
            px = edge_x
        elif layer in ("metal4", "metal5"):
            via4(px, py)
        else:
            raise AssertionError((name, layer, pin))
        rect("metal5", (min(px, rx) - 50, py - 50, max(px, rx) + 50, py + 50))
        via4(rx, py)
        rect("metal4", (rx - 80, min(py, ty), rx + 80, max(py, ty) + 1))
        via4(rx, ty)

    pin_boxes = {}
    for net in ports:
        ty = tracks[net]
        rect("metal5", (-40000, ty - 60, 120000, ty + 60))
        pin_boxes[net] = (-4920, ty - 20, -4880, ty + 20)

    lines = ["magic", "tech gf180mcuD", "magscale 1 10", "timestamp 0", *uses]
    for layer, boxes in layers.items():
        lines += ["<< " + layer + " >>"] + ["rect " + " ".join(map(str, box)) for box in boxes]
    lines += ["<< labels >>"]
    for index, net in enumerate(ports, 1):
        lines += [
            f"rlabel metal5 s " + " ".join(map(str, pin_boxes[net])) + f" 4 {net}",
            f"port {index} nsew",
        ]
    lines += ["<< end >>", ""]
    (out / f"{cell}.mag").write_text("\n".join(lines), encoding="ascii")
    (out / "build_source.py").write_bytes(Path(__file__).read_bytes())

    visited = set()
    views = []

    def visit(name):
        if name in visited:
            return
        assert name in geometry and len(geometry[name]) == 1, name
        path = next(iter(geometry[name]))
        for child in re.findall(r"^use\s+(\S+)\s+", path.read_text(), re.M):
            visit(child)
        visited.add(name)
        views.append(path)

    for _, name, _, _ in specs:
        visit(name)
    preload = "".join("load /workspace/" + path.with_suffix("").relative_to(flow.ROOT).as_posix() + "\n" for path in views)
    flow.OUT = out
    log = flow.magic(preload + f"load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs \"BBOX [box values]\"\nquit -noprompt\n")
    (out / "extraction.log").write_text(log)
    drc = re.search(r"Total DRC errors found:\s*(\d+)", log)
    assert drc and int(drc[1]) == 0, log[-3000:]
    assert not (out / "warnings.feedback").read_text() and not (out / "gds_warnings.feedback").read_text()

    ref = ""
    orders = {}
    included = set()
    for _, name, _, _ in specs:
        directory, _ = children[name]
        txt = (directory / f"{name}.spice").read_text(encoding="ascii")
        flat = txt.replace("\n+", " ")
        match = re.search(r"(?m)^\.subckt\s+" + re.escape(name) + r"\s+([^\n]+)", flat)
        assert match, name
        orders[name] = match.group(1).split()
        if name not in included:
            ref += txt + "\n"
            included.add(name)
    ref += ".subckt reference " + " ".join(ports) + "\n"
    for inst, name, _, _ in specs:
        mapping = pinmap(inst, name)
        ref += "X" + inst + " " + " ".join(mapping[pin] for pin in orders[name]) + " " + name + "\n"
    ref += ".ends reference\n"
    (out / "reference.spice").write_text(ref, encoding="ascii")
    setup = "/workspace/" + flow.PDK.relative_to(flow.ROOT).as_posix() + "/libs.tech/netgen/gf180mcuD_setup.tcl"
    lvs = flow.run(["netgen-lvs", "-batch", "lvs", cell + ".spice " + cell, "reference.spice reference", setup, "lvs.out"])
    (out / "netgen.log").write_text(lvs)
    assert "Circuits match uniquely" in lvs, lvs[-3000:]

    caplog = flow.magic(preload + f"load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n")
    (out / "capacitance_extraction.log").write_text(caplog)
    assert not (out / "capacitance_warnings.feedback").read_text()

    readback = flow.BASE / "verification/gds_roundtrip" / cell
    readback.mkdir(parents=True)
    flow.OUT = readback
    readlog = flow.magic("gds read /workspace/" + (out / f"{cell}.gds").relative_to(flow.ROOT).as_posix() + f"\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n")
    (readback / "readback.log").write_text(readlog)
    roundtrip_drc = re.search(r"Total DRC errors found:\s*(\d+)", readlog)
    roundtrip_lvs = flow.run(["netgen-lvs", "-batch", "lvs", "roundtrip.spice " + cell, "/workspace/" + (out / "reference.spice").relative_to(flow.ROOT).as_posix() + " reference", setup, "roundtrip_lvs.out"])
    (readback / "netgen.log").write_text(roundtrip_lvs)
    assert roundtrip_drc and int(roundtrip_drc[1]) == 0 and "Circuits match uniquely" in roundtrip_lvs
    assert not (readback / "roundtrip.feedback").read_text()

    output_paths = [
        out / f"{cell}{suffix}" for suffix in (".mag", ".gds", ".spice", "_cap.spice")
    ] + [out / name for name in (
        "build_source.py", "extraction.log", "reference.spice", "netgen.log", "capacitance_extraction.log",
        "warnings.feedback", "gds_warnings.feedback", "capacitance_warnings.feedback",
    )]
    q = {
        "cell": cell,
        "ports": ports,
        "children": [name for _, name, _, _ in specs],
        "instances": [name for name, _, _, _ in specs],
        "magic_drc_count": 0,
        "lvs_unique": True,
        "gds_roundtrip_drc_count": 0,
        "gds_roundtrip_lvs_unique": True,
        "bbox_um": [round(int(value) * 0.005, 4) for value in re.search(r"BBOX ([-0-9 ]+)", log)[1].split()],
        "scope": "Compact integration parent: physically connected signed-event injector, native membrane state/update cell, and low/high quarter-TG limiters. POS/NEG pulse inputs and limiter phases/rails are external; weight-duration generation and range detection are not included. This layout test is not full PLIF or model acceptance.",
        "sha256": {path.name: sha(path) for path in output_paths},
        "input_sha256": {path.relative_to(flow.ROOT).as_posix(): sha(path) for path in sorted(source_files)},
        "roundtrip_sha256": {path.relative_to(flow.ROOT).as_posix(): sha(path) for path in (
            readback / "readback.log", readback / "netgen.log", readback / "roundtrip.spice", readback / "roundtrip.feedback",
        )},
    }
    (out / "qualification.json").write_text(json.dumps(q, indent=2) + "\n")
    print(json.dumps({"report": str(out / "qualification.json"), "bbox_um": q["bbox_um"], "lvs_unique": True}, indent=2))


if __name__ == "__main__":
    main()


