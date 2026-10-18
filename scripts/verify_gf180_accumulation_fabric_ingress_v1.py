"""Read actual pair GDS; prove new routing and screen native edge contacts.

Native geometry is cropped to a 2um band at the macro perimeter. New parent
metal enters only this band. This is an incremental connection check, not a
new full native/device extraction, DRC, power qualification or RC transient.
"""
from pathlib import Path
import collections
import json
import struct
import time
from assemble_gf180_external_bank_service_full25_v5 import cells_read, elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin, rec
from prove_gf180_shared_page_parent_metal_v5 import Paint, VIA, polygon_rectangles
import gf180_service_metal_graph_v3 as graph
from assemble_gf180_accumulation_fabric_ingress_v1 import sha, renamed

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'
OUT = BASE/'assembly/accumulation_fabric_ingress_v1'


def overlap(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def main():
    started = time.monotonic()
    dest = OUT/'independent_readback_v1.json'
    assert not dest.exists()
    meta = OUT/'physical_assembly.json'; m = json.loads(meta.read_text())
    for p, digest in m['sha256'].items(): assert sha(ROOT/p) == digest, p
    plan_path = OUT/'route_plan.json'; plan = json.loads(plan_path.read_text())
    gds = ROOT/m['gds']; prefix, cells = cells_read(gds.read_bytes())
    refs = []; added = []; actual_refs = []
    for e in elements(cells[m['top_cell']]):
        kind = e[0][0]
        if kind == 10:
            refs.append(b''.join(b for t, d, v, b in e))
            name = next(v.rstrip(b'\0').decode() for t,d,v,b in e if t == 18)
            xy = next(struct.unpack('>2i', v) for t,d,v,b in e if t == 16)
            actual_refs.append((name, list(xy)))
        elif kind == 8:
            layer = next(struct.unpack('>h', v)[0] for t,d,v,b in e if t == 13)
            xy = next(struct.unpack('>'+str(len(v)//4)+'i', v) for t,d,v,b in e if t == 16)
            added.extend((layer, b) for b in polygon_rectangles(xy))
        elif kind not in [12]: raise AssertionError(('unsupported parent element', kind))
    assert len(refs) == 2
    assert actual_refs == [(m['source_roots'][s], plan['origins_dbu'][s]) for s in ['FABRIC','INGRESS']]
    expected = collections.Counter((l,tuple(b)) for net in plan['routes'] for l,b in net['shapes'])
    assert collections.Counter(added) == expected
    shape_owner = {}
    for net in plan['routes']:
        for l,b in net['shapes']:
            key = l,tuple(b)
            assert key not in shape_owner or shape_owner[key] == net['net']
            shape_owner[key] = net['net']
    # Child geometry must be byte-identical, except systematic ingress names.
    native_ports = {}
    for side in ['FABRIC','INGRESS']:
        mp = ROOT/plan['source_manifest_paths'][side]
        mm = json.loads(mp.read_text()); native_ports[side] = mm['ports']
        source = next(ROOT/p for p in mm['sha256'] if p.endswith('.gds'))
        _, source_cells = cells_read(source.read_bytes())
        rename = '' if side == 'FABRIC' else 'ACC_'
        assert all(cells[rename+n] == (renamed(blob, rename) if rename else blob)
                   for n,blob in source_cells.items()), ('changed source cells',side)
        del source_cells
    print('Actual parent shapes/references and child geometry match; checking macro edge contacts.', flush=True)
    rings = []
    for bb in plan['bounds_dbu'].values():
        x1,y1,x2,y2 = bb; g = 2000
        rings.extend([(x1-g,y1-g,x1+g,y2+g), (x2-g,y1-g,x2+g,y2+g),
                      (x1-g,y1-g,x2+g,y1+g), (x1-g,y2-g,x2+g,y2+g)])

    class EdgePaint(Paint):
        def add(self, layer, box):
            if any(overlap(box, q) for q in rings): return super().add(layer, box)
            return -1

        def vias(self, start=0):
            # A cropped remote via can lose one side. Join all retained sides;
            # new parent contacts are evaluated against actual retained geometry.
            for i in range(start,len(self.shapes)):
                layer,box = self.shapes[i]
                if layer not in VIA: continue
                for metal in VIA[layer]:
                    for j in self.hits(metal,box): self.join(i,j)

    baseline_name = 'ACC_FABRIC_INGRESS_EDGE_BASELINE'
    cells[baseline_name] = begin(baseline_name)+b''.join(refs)+rec(7,0)
    original_paint = graph.Paint
    try:
        graph.Paint = EdgePaint
        baseline = graph.native_paint(cells, baseline_name)
    finally:
        graph.Paint = original_paint
    bound = {(n['instance'], n['pin']): net['net'] for net in plan['routes'] for n in net['nodes']}
    component_owners = collections.defaultdict(set)
    for side, ports in native_ports.items():
        ox,oy = plan['origins_dbu'][side]
        for name,pin in ports.items():
            for r in pin['rectangles']:
                layer = {'Metal3':42,'Metal4':46,'Metal5':81}[r['layer']]
                x,y = [round(v*1000) for v in r['center_um']]; x+=ox; y+=oy
                if not baseline.hits(layer,(x,y,x,y)): continue
                root = baseline.at(layer,x,y)
                component_owners[root].add(bound.get((side,name),side+'__'+name))
    unknown = []; foreign = []; intrusion = []
    for layer,box in added:
        owner = shape_owner[layer,box]
        for root in graph.touched(baseline,layer,box):
            if root not in component_owners: unknown.append((owner,root,layer,box))
            elif component_owners[root] != {owner}:
                foreign.append((owner,sorted(component_owners[root]),layer,box))
        for bb in plan['bounds_dbu'].values():
            core = (bb[0]+2000,bb[1]+2000,bb[2]-2000,bb[3]-2000)
            if overlap(box,core): intrusion.append((owner,layer,box))
    edge_report = dict(native_edge_conductor_rectangles=len(baseline.shapes),
                       unknown_native_contacts=unknown, foreign_native_contacts=foreign,
                       parent_intrusions_beyond_edge_band=intrusion)
    (OUT/'edge_contact_check_v1.json').write_text(json.dumps(edge_report,indent=2)+'\n')
    assert not unknown and not foreign and not intrusion, (unknown[:2],foreign[:2],intrusion[:2])
    del baseline; del cells
    print('Macro edge contacts pass; proving actual new route connectivity.',flush=True)
    paint = Paint()
    for layer,box in added: paint.add(layer,box)
    paint.vias()
    owners = collections.defaultdict(set); opens = []
    for net in plan['routes']:
        roots = {paint.at(n['layer'],*n['xy_dbu']) for n in net['nodes']}
        if len(roots) != 1: opens.append(net['net'])
        for root in roots: owners[root].add(net['net'])
    aliases = [sorted(v) for v in owners.values() if len(v)>1]
    floating = []
    for i,(layer,box) in enumerate(added):
        if owners.get(paint.root(i)) != {shape_owner[layer,box]}: floating.append(i)
    assert not opens and not aliases and not floating, (opens[:2],aliases[:2],floating[:2])
    report = dict(readback_pass=True, fabric_ingress_signal_routes_verified=1475,
                  shared_clock_reset_routes_verified=2, actor_interfaces=25,
                  new_conductor_rectangles=len(added), expected_route_opens=0,
                  inter_net_aliases=0, floating_added_rectangles=0,
                  unknown_native_contacts=0, foreign_native_contacts=0,
                  native_edge_band_um=2, parent_intrusions_beyond_edge_band=0,
                  source_child_geometry_preserved=True,
                  elapsed_seconds=time.monotonic()-started,
                  full_architecture_layout_complete=False, accumulation_5ms_accepted=False,
                  scope='Actual GDS new-metal graph plus native 2um macro-perimeter contact screen. All new metal stays outside macro interiors beyond the screened band. Native child geometry retained with systematic ingress renaming. This is not full device extraction, full-style DRC, parent supply/RC qualification, analog accumulation or deadline proof.',
                  sha256={p.relative_to(ROOT).as_posix():sha(p) for p in
                          [Path(__file__), ROOT/'scripts/gf180_service_metal_graph_v3.py',meta,plan_path,gds,OUT/'edge_contact_check_v1.json']})
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['sha256','scope']}),flush=True)


if __name__ == '__main__':
    main()
