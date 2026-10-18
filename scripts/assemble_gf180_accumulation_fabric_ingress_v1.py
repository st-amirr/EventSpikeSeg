"""Route the existing fabric/ingress hard macros without numerical digital state.

Parent routes use explicit out-of-macro channels. The output is a reusable
research macro pair; full-population integration and loaded timing are separate.
"""
from pathlib import Path
import collections
import hashlib
import json
import struct
import time
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import begin, rec, reference, records
from assemble_gf180_full25_physical_candidate_v5 import rect, label
from prove_gf180_shared_page_parent_metal_v5 import Paint, VIA

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
OUT = BASE / 'assembly/accumulation_fabric_ingress_v1'
LAYERS = {'Metal3': 42, 'Metal4': 46, 'Metal5': 81}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def wire(layer, a, b):
    assert a[0] == b[0] or a[1] == b[1]
    h = 140 if layer in [42, 46] else 220
    return layer, (min(a[0], b[0])-h, min(a[1], b[1])-h,
                   max(a[0], b[0])+h, max(a[1], b[1])+h)


def via(low, high, cut, point):
    x, y = point
    return [(low, (x-300, y-300, x+300, y+300)),
            (high, (x-300, y-300, x+300, y+300)),
            (cut, (x-130, y-130, x+130, y+130))]


def renamed(blob, prefix):
    return b''.join(rec(t, d, (prefix+v.rstrip(b'\0').decode()).encode())
                    if t in [6, 18] else raw for t, d, v, raw in records(blob))


def main():
    started = time.monotonic()
    assert not OUT.exists(), 'Preserve attempted route evidence.'
    OUT.mkdir(parents=True)
    contract_path = BASE/'assembly/accumulation_architecture_v1/physical_binding_contract.json'
    contract = json.loads(contract_path.read_text())
    for p, digest in contract['sha256'].items():
        assert sha(ROOT/p) == digest, p
    manifests = {side: BASE/f'assembly/{folder}/physical_macro.json' for side, folder in [
        ('FABRIC', 'full25_packet_fabric_v1'), ('INGRESS', 'full25_actor_ingress_v2')]}
    mm = {side: json.loads(path.read_text()) for side, path in manifests.items()}
    count = len(contract['bindings']) + 2
    max_escape = 20000 + (2*count)*2000
    fw, fh = [round(v*1000) for v in mm['FABRIC']['size_um']]
    iw, ih = [round(v*1000) for v in mm['INGRESS']['size_um']]
    origins = {'FABRIC': (0, 0), 'INGRESS': (fw+2*max_escape+2000000, 0)}
    bounds = {'FABRIC': (0, 0, fw, fh), 'INGRESS': (*origins['INGRESS'], origins['INGRESS'][0]+iw, ih)}
    top_y = max(fh, ih) + max_escape + 2000000
    routes = []
    for binding in contract['bindings']:
        routes.append(dict(net=binding['net'], nodes=binding['endpoints']))
    for pin in ['clk', 'reset']:
        routes.append(dict(net=pin, nodes=[dict(instance=side, pin=pin,
                           rectangles=mm[side]['ports'][pin]['rectangles']) for side in mm]))
    terminal_index = 0
    for index, net in enumerate(routes):
        track = top_y + index*3200
        xs = []
        shapes = []
        nodes = []
        for node in net['nodes']:
            side = node['instance']; r = node['rectangles'][0]
            layer = LAYERS[r['layer']]
            x, y = [round(v*1000) for v in r['center_um']]
            ox, oy = origins[side]; x += ox; y += oy
            bb = bounds[side]
            extra = 20000 + terminal_index*2000; terminal_index += 1
            assert layer in [42, 46], ('unexpected signal pin layer', node)
            if layer == 42:
                edge = 'left' if x < (bb[0]+bb[2])/2 else 'right'
                ex = bb[0]-extra if edge == 'left' else bb[2]+extra
                shapes.append(wire(42, (x, y), (ex, y)))
                shapes += via(42, 46, 40, (ex, y))
                shapes.append(wire(46, (ex, y), (ex, track)))
                shapes += via(46, 81, 41, (ex, track))
            else:
                edge = 'bottom' if y < (bb[1]+bb[3])/2 else 'top'
                ey = bb[1]-extra if edge == 'bottom' else bb[3]+extra
                ex = bb[0]-extra
                shapes.append(wire(46, (x, y), (x, ey)))
                shapes += via(46, 81, 41, (x, ey))
                shapes.append(wire(81, (x, ey), (ex, ey)))
                shapes += via(46, 81, 41, (ex, ey))
                shapes.append(wire(46, (ex, ey), (ex, track)))
                shapes += via(46, 81, 41, (ex, track))
            xs.append(ex)
            nodes.append(dict(instance=side, pin=node['pin'], layer=layer, xy_dbu=[x, y], edge=edge))
        shapes.append(wire(81, (min(xs), track), (max(xs), track)))
        net.update(nodes=nodes, track_y_dbu=track, shapes=shapes)
    # Independently indexed new-net spacing/contact screen, including cut layers.
    paint = Paint(); shape_owner = []; conflicts = []
    for net in routes:
        for layer, box in net['shapes']:
            guard = 460 if layer == 81 else 280 if layer in [42, 46] else 260
            q = (box[0]-guard, box[1]-guard, box[2]+guard, box[3]+guard)
            for hit in paint.hits(layer, q):
                if shape_owner[hit] != net['net']:
                    conflicts.append((net['net'], shape_owner[hit], layer, box, paint.shapes[hit][1]))
            layers = VIA.get(layer, ()) if layer in VIA else [c for c, metals in VIA.items() if layer in metals]
            for other in layers:
                for hit in paint.hits(other, box):
                    if shape_owner[hit] != net['net']:
                        conflicts.append((net['net'], shape_owner[hit], layer, box, paint.shapes[hit][1]))
            paint.add(layer, box); shape_owner.append(net['net'])
    plan = dict(routes=routes, origins_dbu=origins, bounds_dbu=bounds,
                new_rectangles=len(paint.shapes), conflicts=conflicts,
                new_net_spacing_and_contacts_pass=not conflicts,
                source_manifest_paths={s: p.relative_to(ROOT).as_posix() for s, p in manifests.items()})
    (OUT/'route_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    assert not conflicts, conflicts[:3]
    del paint
    cells = {}; prefix = None; gds_paths = []
    source_roots = {}
    for side in ['FABRIC', 'INGRESS']:
        path = next(ROOT/p for p in mm[side]['sha256'] if p.endswith('.gds'))
        h, cc = cells_read(path.read_bytes())
        if prefix is None: prefix = h
        # Rename every ingress cell/reference, including shared standard cells.
        # This avoids silently conflating same-named cells from separate streams.
        rename = '' if side == 'FABRIC' else 'ACC_'
        for name, blob in cc.items():
            key = rename+name; assert key not in cells
            cells[key] = renamed(blob, rename) if rename else blob
        source_roots[side] = rename+mm[side]['design']; gds_paths.append(path)
    body = b''.join(reference(source_roots[s], *origins[s]) for s in source_roots)
    body += b''.join(rect(l, b) for net in routes for l, b in net['shapes'])
    body += b''.join(label(net['net'], min(n['xy_dbu'][0] for n in net['nodes']), net['track_y_dbu']) for net in routes)
    top = 'GF180_ACCUMULATION_FABRIC_INGRESS_V1'
    cells[top] = begin(top)+body+rec(7, 0)
    gds = OUT/'accumulation_fabric_ingress_v1.gds'
    with gds.open('wb') as stream:
        stream.write(prefix)
        for blob in cells.values(): stream.write(blob)
        stream.write(rec(4, 0))
    report = dict(top_cell=top, gds=gds.relative_to(ROOT).as_posix(), gds_bytes=gds.stat().st_size,
                  source_roots=source_roots, actor_interfaces=25, fabric_ingress_signal_routes=1475,
                  shared_clock_reset_routes=2, new_rectangles=plan['new_rectangles'],
                  new_net_spacing_and_contacts_pass=True,
                  actual_gds_readback_pass=False, native_pin_approaches_verified=False,
                  full_architecture_layout_complete=False, accumulation_5ms_accepted=False,
                  elapsed_seconds=time.monotonic()-started,
                  scope='Reusable research hard-macro pair with 1475 categorical event/ready/tag routes plus clock/reset. Parent supplies and unbound analog accumulation boundaries remain external. Actual GDS readback and macro-edge contact checks are required. Long channels are not compact die area or loaded timing claims.',
                  sha256={p.relative_to(ROOT).as_posix(): sha(p) for p in
                          [Path(__file__), contract_path, *manifests.values(), *gds_paths, gds, OUT/'route_plan.json']})
    (OUT/'physical_assembly.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['gds', 'gds_bytes', 'fabric_ingress_signal_routes', 'new_rectangles', 'elapsed_seconds']}))


if __name__ == '__main__':
    main()
