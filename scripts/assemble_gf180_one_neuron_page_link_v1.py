"""Connect one routed neuron SPIKE pad to lane 0 of the routed 128-neuron page."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import struct
import uuid
from pathlib import Path

import probe_gf180_mos_gate_cap as flow
from assemble_gf180_full_capacity_storage_gds_v2 import begin, rec, reference, records
from assemble_gf180_full25_physical_candidate_v5 import rect, via


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
OUT = BASE / "assembly/gf180_one_neuron_page_link_v1"
NEURON = "gf180_neuron_five_module_parent_v6"
PAGE = "gf180_analog_spike_event_page128_v1"
NEURON_GDS = BASE / f"layout/{NEURON}/{NEURON}.gds"
NEURON_Q = BASE / f"layout/{NEURON}/qualification.json"
PAGE_GDS = BASE / f"orfs/results/gf180/{PAGE}/page128_v1/6_final.gds"
PAGE_LEF = BASE / f"orfs/results/gf180/{PAGE}/page128_v1/{PAGE}.lef"
MAGIC_TECH = BASE / "pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_magic(tcl: str, timeout_s: int = 360) -> str:
    name = f"ess-magic-{uuid.uuid4().hex[:10]}"
    cmd = ["docker", "run", "--name", name, "--rm", "--network", "none", "--memory", "5g", "--cpus", "4", "-i",
           "--volume", f"{ROOT}:/workspace", "--workdir",
           f"/workspace/{OUT.relative_to(ROOT).as_posix()}", "--entrypoint", "magic",
           "eventspikeseg:analog-gf180-layout", "-dnull", "-noconsole", "-rcfile",
           f"/workspace/{MAGIC_TECH.relative_to(ROOT).as_posix()}"]
    try:
        result = subprocess.run(cmd, input=tcl, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        # subprocess.run kills the Docker client, not necessarily its container.
        subprocess.run(["docker", "stop", "--timeout", "2", name],
                       capture_output=True, text=True, timeout=10)
        raise
    log = result.stdout + result.stderr
    if result.returncode:
        raise RuntimeError(log[-4000:])
    return log


def text_pins(path: Path, top_cell: str) -> dict[str, tuple[int, int, int]]:
    cell = None
    active = False
    layer = None
    xy = None
    result: dict[str, tuple[int, int, int]] = {}
    for typ, _dtype, data, _raw in records(path.read_bytes()):
        if typ == 6:
            cell = data.rstrip(b"\0").decode("ascii")
        elif typ == 12:
            active = True
            layer = None
            xy = None
        elif active and typ == 13:
            layer = struct.unpack(">h", data[:2])[0]
        elif active and typ == 16:
            xy = struct.unpack(">2i", data[:8])
        elif active and typ == 25:
            name = data.rstrip(b"\0").decode("ascii")
            if cell == top_cell and layer is not None and xy is not None:
                result[name] = (layer, int(xy[0]), int(xy[1]))
            active = False
    return result


def verify_spice_link(path: Path, page: str, neuron: str) -> dict[str, object]:
    """Confirm that the page lane 0 input and neuron SPIKE share one extracted net."""
    statements: list[str] = []
    for line in path.read_text(encoding="ascii", errors="replace").splitlines():
        if line.startswith("+") and statements:
            statements[-1] += " " + line[1:].strip()
        elif line and not line.startswith("*"):
            statements.append(line.strip())
    ports: dict[str, list[str]] = {}
    instances: list[tuple[str, str, list[str]]] = []
    for statement in statements:
        fields = statement.split()
        if fields[0].lower() == ".subckt" and len(fields) >= 2:
            ports[fields[1]] = fields[2:]
        elif fields[0][0].lower() == "x" and len(fields) > 2:
            instances.append((fields[0], fields[-1], fields[1:-1]))
    child_nets: dict[str, dict[str, str]] = {}
    for instance_name, cell, nets in instances:
        if cell not in {page, neuron}:
            continue
        if cell not in ports or len(ports[cell]) != len(nets):
            raise RuntimeError(f"SPICE pin mismatch for {instance_name} / {cell}")
        child_nets[cell] = dict(zip(ports[cell], nets))
    page_net = child_nets.get(page, {}).get("spike_bitmap_i[0]")
    neuron_net = child_nets.get(neuron, {}).get("SPIKE")
    if not page_net or page_net != neuron_net:
        raise RuntimeError(f"Extracted SPIKE link mismatch: {neuron_net} -> {page_net}")
    return {
        "verified": True,
        "source": f"{neuron}.SPIKE",
        "destination": f"{page}.spike_bitmap_i[0]",
        "shared_extracted_net": page_net,
        "page_subcircuit_port_count": len(ports[page]),
        "neuron_subcircuit_port_count": len(ports[neuron]),
    }


def gds_library_parts(path: Path) -> tuple[bytes, bytes, set[str]]:
    """Stream GDS boundaries without materializing millions of element records."""
    data = path.read_bytes()
    offset = 0
    first_structure = None
    end_library = None
    current_name = None
    names: set[str] = set()
    while offset < len(data):
        size, typ, _dtype = struct.unpack_from(">HBB", data, offset)
        if typ == 5 and first_structure is None:
            first_structure = offset
        elif typ == 6:
            current_name = data[offset+4:offset+size].rstrip(b"\0").decode("ascii")
        elif typ == 7:
            if current_name is None:
                raise RuntimeError(f"Unnamed structure in {path}")
            names.add(current_name)
            current_name = None
        elif typ == 4:
            end_library = offset
            break
        offset += size
    if first_structure is None or end_library is None:
        raise RuntimeError(f"Incomplete GDS library: {path}")
    return data[:first_structure], data[first_structure:end_library], names


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    neuron_q = json.loads(NEURON_Q.read_text(encoding="utf-8"))
    neuron_pins = text_pins(NEURON_GDS, NEURON)
    page_pins = text_pins(PAGE_GDS, PAGE)
    assert neuron_q["magic_drc_count"] == neuron_q["gds_roundtrip_drc_count"] == 0
    assert neuron_pins["SPIKE"][0] == 81, neuron_pins.get("SPIKE")
    assert page_pins["spike_bitmap_i[0]"][0] == 46, page_pins.get("spike_bitmap_i[0]")

    # GDS database unit is 1 nm. Place the characterized neuron macro 10 um
    # left of the digital page, then route around both macro bounds.
    bbox = [round(v * 1000) for v in neuron_q["bbox_um"]]
    neuron_tx = -bbox[2] - 10_000
    neuron_ty = 0
    source_layer, source_x, source_y = neuron_pins["SPIKE"]
    target_layer, target_x, target_y = page_pins["spike_bitmap_i[0]"]
    source_x += neuron_tx
    source_y += neuron_ty
    track_x = bbox[0] + neuron_tx - 10_000
    track_y = 1_115_000
    route_width = 500

    prefix, page_structures, page_cells = gds_library_parts(PAGE_GDS)
    neuron_prefix, neuron_structures, neuron_cells = gds_library_parts(NEURON_GDS)
    assert PAGE in page_cells and NEURON in neuron_cells
    assert page_cells.isdisjoint(neuron_cells), page_cells & neuron_cells
    # Both sources use the same 1 nm user unit. Preserve the routed page's
    # library header and append the source-native neuron cell structures.
    assert prefix[0:4] == neuron_prefix[0:4] and prefix[0:4] == struct.pack(">HBB", 6, 0, 2)
    top = "ESS_NEURON_SPIKE_TO_PAGE0_V1"
    body = reference(PAGE, 0, 0)
    body += reference(NEURON, neuron_tx, neuron_ty)
    # Source is already on M5. Leave the analog macro from its left edge,
    # rise outside the macro pair, cross back on M4, and land on the page's
    # M4 lane-0 input. The sole inter-macro net is SPIKE -> spike_bitmap_i[0].
    body += rect(81, (min(source_x, track_x), source_y-route_width//2,
                      max(source_x, track_x), source_y+route_width//2))
    body += rect(81, (track_x-route_width//2, min(source_y, track_y),
                      track_x+route_width//2, max(source_y, track_y)))
    # Square off both inside corners; an unfilled L-junction creates a narrow
    # concave notch that violates the GF180 minimum-width check.
    body += rect(81, (track_x-route_width//2, source_y-route_width//2,
                      track_x+route_width//2, source_y+route_width//2))
    body += via(46, 81, 41, track_x, track_y)
    body += rect(46, (min(track_x, target_x), track_y-route_width//2,
                      max(track_x, target_x), track_y+route_width//2))
    body += rect(46, (target_x-route_width//2, target_y,
                      target_x+route_width//2, track_y))
    body += rect(46, (target_x-route_width//2, track_y-route_width//2,
                      target_x+route_width//2, track_y+route_width//2))
    top_structure = begin(top) + body + rec(7, 0)
    gds = OUT / f"{top}.gds"
    gds.write_bytes(prefix + page_structures + neuron_structures + top_structure + rec(4, 0))

    # Full-style Magic DRC and hierarchical extraction validate the real GDS
    # port-to-port connection while preserving both qualified child layouts.
    flat = top + "_FLAT"
    tcl = (
        "drc off\n"
        f"gds read /workspace/{gds.relative_to(ROOT).as_posix()}\n"
        f"load {top}\nflatten {flat}\nload {flat}\n"
        "drc on\ndrc style drc(full)\nselect top cell\n"
        "drc check\ndrc catchup\ndrc count total\n"
        "feedback save route_drc.feedback\n"
        "quit -noprompt\n"
    )
    log = run_magic(tcl)
    (OUT / "magic_check.log").write_text(log, encoding="utf-8")
    (OUT / "route_drc.feedback").write_text("", encoding="ascii")
    match = re.search(r"Total DRC errors found:\s*(\d+)", log)
    if not match:
        raise RuntimeError("Magic did not report completion of full-style DRC")
    drc_count = int(match.group(1))
    spice = OUT / f"{top}.spice"
    extract_tcl = (
        f"gds read /workspace/{gds.relative_to(ROOT).as_posix()}\n"
        f"load {top}\nextract no capacitance\nextract no coupling\n"
        "extract all\nfeedback save extraction.feedback\n"
        "ext2spice lvs\next2spice scale off\next2spice hierarchy on\n"
        f"ext2spice -o /workspace/{spice.relative_to(ROOT).as_posix()}\n"
        "quit -noprompt\n"
    )
    extraction_error = None
    try:
        extract_log = run_magic(extract_tcl, timeout_s=360)
    except (subprocess.TimeoutExpired, RuntimeError) as exc:
        extract_log = str(exc)
        extraction_error = type(exc).__name__
    (OUT / "hierarchical_extract.log").write_text(extract_log, encoding="utf-8")
    text = spice.read_text(encoding="ascii", errors="replace") if spice.exists() else ""
    link_check = verify_spice_link(spice, PAGE, NEURON) if text else None
    report = {
        "design": top,
        "status": "PASS" if drc_count == 0 else "DRC_FAIL",
        "analog_child": NEURON,
        "digital_child": PAGE,
        "physical_net": {"from": "SPIKE", "to": "spike_bitmap_i[0]"},
        "analog_pin_gds": {"layer": source_layer, "xy_dbu_after_placement": [source_x, source_y]},
        "page_pin_gds": {"layer": target_layer, "xy_dbu": [target_x, target_y]},
        "neuron_macro_translation_dbu": [neuron_tx, neuron_ty],
        "route": {"met5_gds_layer": 81, "met4_gds_layer": 46, "via4_gds_layer": 41,
                  "track_xy_dbu": [track_x, track_y], "width_dbu": route_width},
        "magic_full_style_gds_drc_count": drc_count,
        "hierarchical_extraction_completed": bool(text),
        "hierarchical_extraction_error": extraction_error,
        "extracted_top_ports": [],
        "extracted_connectivity": link_check,
        "limitations": [
            "Only one physically connected analog neuron macro feeds one bitmap lane; the other 127 lane inputs and analog controls remain macro ports.",
            "This is an interface demonstration parent, not a 128-channel actor or full graph layout.",
            "No new analog simulation, accuracy result, or full-population 5 ms service follows from this GDS composition."
        ],
        "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in
                   [Path(__file__), NEURON_GDS, NEURON_Q, PAGE_GDS, PAGE_LEF, gds,
                    OUT / "magic_check.log", OUT / "hierarchical_extract.log"]
                   + ([spice] if spice.exists() else [])},
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "sha256"}, indent=2))
    if drc_count:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
