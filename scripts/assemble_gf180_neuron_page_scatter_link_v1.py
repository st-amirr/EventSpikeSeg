"""Compose a physical analog neuron, routed page/scatter front end, and one spike link."""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assemble_gf180_one_neuron_page_link_v1 as gdsutil

ROOT = gdsutil.ROOT
BASE = ROOT / "artifacts/analog_asic"
OUT = BASE / "assembly/gf180_neuron_page_scatter_link_v1"
NEURON = "gf180_neuron_five_module_parent_v6"
PAGE = "gf180_analog_channel_pixel_page_to_pw128_scatter_v1"
NEURON_GDS = BASE / f"layout/{NEURON}/{NEURON}.gds"
NEURON_Q = BASE / f"layout/{NEURON}/qualification.json"
PAGE_GDS = BASE / f"orfs/results/gf180/{PAGE}/channel_pixel_v1/6_final.gds"
PAGE_LEF = BASE / f"orfs/results/gf180/{PAGE}/channel_pixel_v1/{PAGE}.lef"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    neuron_q = json.loads(NEURON_Q.read_text(encoding="utf-8"))
    neuron_pins = gdsutil.text_pins(NEURON_GDS, NEURON)
    page_pins = gdsutil.text_pins(PAGE_GDS, PAGE)
    assert neuron_q["magic_drc_count"] == neuron_q["gds_roundtrip_drc_count"] == 0
    assert neuron_pins["SPIKE"][0] == 81, neuron_pins.get("SPIKE")
    assert page_pins["spike_bitmap_i[0]"][0] == 42, page_pins.get("spike_bitmap_i[0]")

    # GDS database unit is 1 nm; position the analog macro 10 um left of the
    # routed digital macro. Track coordinates are derived from real GDS ports.
    bbox = [round(v * 1000) for v in neuron_q["bbox_um"]]
    neuron_tx = -bbox[2] - 10_000
    neuron_ty = 0
    source_layer, source_x, source_y = neuron_pins["SPIKE"]
    target_layer, target_x, target_y = page_pins["spike_bitmap_i[0]"]
    source_x += neuron_tx
    source_y += neuron_ty
    track_x = bbox[0] + neuron_tx - 10_000
    track_y = target_y + 7_500
    route_width = 500

    prefix, page_structures, page_cells = gdsutil.gds_library_parts(PAGE_GDS)
    neuron_prefix, neuron_structures, neuron_cells = gdsutil.gds_library_parts(NEURON_GDS)
    assert PAGE in page_cells and NEURON in neuron_cells
    assert page_cells.isdisjoint(neuron_cells), page_cells & neuron_cells
    assert prefix[0:4] == neuron_prefix[0:4] == struct.pack(">HBB", 6, 0, 2)

    top = "ESS_NEURON_TO_PAGE_SCATTER_V1"
    body = gdsutil.reference(PAGE, 0, 0)
    body += gdsutil.reference(NEURON, neuron_tx, neuron_ty)
    # Neuron output is M5. Escape around the macro, descend through via4 to
    # M4, then connect to the page's real M3 pin through via3.
    body += gdsutil.rect(81, (min(source_x, track_x), source_y-route_width//2,
                               max(source_x, track_x), source_y+route_width//2))
    body += gdsutil.rect(81, (track_x-route_width//2, min(source_y, track_y),
                               track_x+route_width//2, max(source_y, track_y)))
    body += gdsutil.rect(81, (track_x-route_width//2, source_y-route_width//2,
                               track_x+route_width//2, source_y+route_width//2))
    body += gdsutil.via(46, 81, 41, track_x, track_y)
    body += gdsutil.rect(46, (min(track_x, target_x), track_y-route_width//2,
                               max(track_x, target_x), track_y+route_width//2))
    body += gdsutil.rect(46, (target_x-route_width//2, target_y,
                               target_x+route_width//2, track_y))
    body += gdsutil.rect(46, (target_x-route_width//2, track_y-route_width//2,
                               target_x+route_width//2, track_y+route_width//2))
    body += gdsutil.via(42, 46, 40, target_x, target_y)
    top_structure = gdsutil.begin(top) + body + gdsutil.rec(7, 0)
    gds = OUT / f"{top}.gds"
    gds.write_bytes(prefix + page_structures + neuron_structures + top_structure + gdsutil.rec(4, 0))

    drc_tcl = (
        "drc off\n"
        f"gds read /workspace/{gds.relative_to(ROOT).as_posix()}\n"
        f"load {top}\nflatten {top}_FLAT\nload {top}_FLAT\n"
        "drc on\ndrc style drc(full)\nselect top cell\n"
        "drc check\ndrc catchup\ndrc count total\nquit -noprompt\n"
    )
    drc_log = gdsutil.run_magic(drc_tcl, timeout_s=360)
    (OUT / "magic_flat_drc.log").write_text(drc_log, encoding="utf-8")
    match = re.search(r"Total DRC errors found:\s*(\d+)", drc_log)
    if not match:
        raise RuntimeError("Magic did not report completion of flattened full-style DRC")
    drc_count = int(match.group(1))

    spice = OUT / f"{top}.spice"
    extract_tcl = (
        f"gds read /workspace/{gds.relative_to(ROOT).as_posix()}\n"
        f"load {top}\nextract no capacitance\nextract no coupling\nextract all\n"
        "feedback save extraction.feedback\next2spice lvs\next2spice scale off\n"
        "ext2spice hierarchy on\n"
        f"ext2spice -o /workspace/{spice.relative_to(ROOT).as_posix()}\nquit -noprompt\n"
    )
    extract_error = None
    try:
        extract_log = gdsutil.run_magic(extract_tcl, timeout_s=360)
    except Exception as exc:  # retain qualified GDS/DRC evidence if extraction hits its bound
        extract_log = str(exc)
        extract_error = type(exc).__name__
    (OUT / "hierarchical_extract.log").write_text(extract_log, encoding="utf-8")
    net_check = gdsutil.verify_spice_link(spice, PAGE, NEURON) if spice.exists() else None

    report = {
        "design": top,
        "status": "PASS" if drc_count == 0 and net_check and net_check["verified"] else "INCOMPLETE",
        "analog_child": NEURON,
        "digital_child": PAGE,
        "physical_net": {"from": "SPIKE", "to": "spike_bitmap_i[0]"},
        "analog_pin_gds": {"layer": source_layer, "xy_dbu_after_placement": [source_x, source_y]},
        "page_pin_gds": {"layer": target_layer, "xy_dbu": [target_x, target_y]},
        "neuron_macro_translation_dbu": [neuron_tx, neuron_ty],
        "route": {"met5_gds_layer": 81, "via4_gds_layer": 41, "met4_gds_layer": 46,
                  "via3_gds_layer": 40, "met3_gds_layer": 42,
                  "track_xy_dbu": [track_x, track_y], "width_dbu": route_width},
        "magic_full_style_flat_drc_count": drc_count,
        "hierarchical_extraction_completed": bool(spice.exists()),
        "hierarchical_extraction_error": extract_error,
        "extracted_connectivity": net_check,
        "scope": [
            "One analog neuron SPIKE pad is connected to page lane 0; page output is routed through coordinate decoder to the 128-output pointwise weight selector.",
            "Lanes 1 through 127 remain exposed inputs; this is a physical actor-interface chain, not the full 128-channel analog population.",
            "No extracted RC or loaded analog weight-charge simulation is included in this layout composition.",
            "Full 43-node model graph, full-population accuracy, and 5 ms service remain unaccepted."
        ],
    }
    report["sha256"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in
                         [Path(__file__), NEURON_GDS, NEURON_Q, PAGE_GDS, PAGE_LEF, gds,
                          OUT / "magic_flat_drc.log", OUT / "hierarchical_extract.log"]
                         + ([spice] if spice.exists() else [])}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
