"""Locate existing actor/service terminals in the actual full-population GDS."""
from pathlib import Path
import collections
import hashlib
import json
import struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read, elements

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"


def main():
    source = BASE / "assembly/full25_class_current_service_v13"
    gds = source / "eventspikeseg140k_class_current_service_v13.gds"
    metadata = json.loads((source / "physical_assembly.json").read_text())
    original = json.loads((BASE / "assembly/full25_physical_candidate_v8/physical_assembly.json").read_text())
    _, cells = cells_read(gds.read_bytes())
    top = metadata["top_cell"]
    parents = collections.defaultdict(list)
    children = collections.defaultdict(list)
    pinsets = {}
    for name, blob in cells.items():
        pins = collections.defaultdict(list)
        for element in elements(blob):
            types = {t for t, d, v, raw in element}
            if 10 in types or 11 in types:
                child = next(v.rstrip(b"\0").decode() for t, d, v, raw in element if t == 18)
                xy = next(v for t, d, v, raw in element if t == 16)
                origin = list(struct.unpack(">2i", xy[:8]))
                flags = [int.from_bytes(v, "big") for t, d, v, raw in element if t == 26]
                angles = [v.hex() for t, d, v, raw in element if t == 28]
                link = {"parent": name, "child": child, "origin_dbu": origin, "array": 11 in types, "transform_flags": flags, "angle_records": angles}
                parents[child].append(link)
                children[name].append(child)
            elif 12 in types:
                text = next(v.rstrip(b"\0").decode() for t, d, v, raw in element if t == 25)
                layer = next(struct.unpack(">h", v)[0] for t, d, v, raw in element if t == 13)
                xy = next(struct.unpack(">2i", v[:8]) for t, d, v, raw in element if t == 16)
                if layer in (34, 36, 42, 46, 81):
                    pins[text].append({"layer": layer, "xy_local_dbu": list(xy)})
        pinsets[name] = dict(pins)
    reachable = set()
    def visit(name):
        if name in reachable:
            return
        reachable.add(name)
        for child in children[name]:
            visit(child)
    visit(top)
    def paths(name, seen=()):
        assert name not in seen
        if name == top:
            return [[]]
        result = []
        for link in parents[name]:
            if link["parent"] not in reachable:
                continue
            for chain in paths(link["parent"], seen + (name,)):
                result.append(chain + [link])
        return result
    def contract(name):
        options = paths(name)
        assert len(options) == 1, (name, len(options))
        chain = options[0]
        assert all(not p["array"] and not any(p["transform_flags"]) and not p["angle_records"] for p in chain), chain
        ox = sum(p["origin_dbu"][0] for p in chain)
        oy = sum(p["origin_dbu"][1] for p in chain)
        pins = {}
        for net, entries in pinsets[name].items():
            pins[net] = [{**p, "xy_top_dbu": [p["xy_local_dbu"][0] + ox, p["xy_local_dbu"][1] + oy]} for p in entries]
        return {"cell": name, "path": chain, "origin_top_dbu": [ox, oy], "ports": pins}
    actors = []
    adaptation = {w["actor"]: w for w in metadata["adaptation_service_wrappers"]}
    for i, row in enumerate(original["actor_regions"]):
        name = row["gds_cell"]
        assert name in reachable
        actor = row["actor"]
        if actor in adaptation:
            service_name = next(m["cell"] for m in adaptation[actor]["modules"] if m["instance"] == "RESIDENT")
        else:
            service_name = f"ESS_MEMBRANE_SERVICE_{i:02d}_V10"
        actors.append({"actor_index": i, "actor": actor, "native_actor": contract(name), "membrane_service": contract(service_name), "graph_input_bound": False, "graph_output_bound": False})
    output = BASE / "assembly/full25_layout_integration_v14/actor_boundary_ports_v1.json"
    assert not output.exists()
    output.parent.mkdir(parents=True)
    result = {"extraction_completed": True, "source_top": top, "source_db_unit_um": .001, "actor_count": len(actors), "actors": actors, "actual_reachable_hierarchy_checked": True, "scope": "Actual conductor TEXT terminals and checked translation-only unique instance paths. Provides routing endpoints; does not itself connect the graph or qualify parent loading. Full layout remains incomplete.", "sha256": {gds.relative_to(ROOT).as_posix(): hashlib.sha256(gds.read_bytes()).hexdigest(), "scripts/extract_gf180_full25_physical_actor_ports_v1.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
    assert len(actors) == 25
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(output), "actors": len(actors), "native_actor_terminals": sum(len(a["native_actor"]["ports"]) for a in actors), "service_terminals": sum(len(a["membrane_service"]["ports"]) for a in actors)}, indent=2))


if __name__ == "__main__":
    main()
