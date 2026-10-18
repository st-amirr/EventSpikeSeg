"""Export a physical LEF abstract from an independently qualified GF180 cell."""
import argparse
import hashlib
import json
import re
import probe_gf180_mos_gate_cap as flow


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cell', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_]+', args.cell):
        raise ValueError('Expected an existing cell identifier')
    directory = flow.BASE / 'layout' / args.cell
    qualification = directory / 'qualification.json'
    q = json.loads(qualification.read_text())
    if q['cell'] != args.cell or q['magic_drc_count'] != 0 or not q['lvs_unique']:
        raise ValueError('A separately qualified physical cell is required')
    original = {directory / name: sha for name, sha in q['sha256'].items()}
    if any(digest(path) != sha for path, sha in original.items()):
        raise ValueError('Original physical-view provenance mismatch')
    geometry={}
    for name,expected in q.get('input_sha256',{}).items():
        p=flow.ROOT/name
        if p.suffix!='.mag':continue
        if digest(p)!=expected:raise ValueError('Qualified descendant changed: '+name)
        geometry.setdefault(p.stem, set()).add(p)
    child_views=[];visited=set()
    def visit(name):
        if name in visited:return
        if name not in geometry:raise ValueError('Missing qualified descendant '+name)
        candidates=geometry[name]
        if len(candidates)!=1:raise ValueError('Ambiguous reachable descendant '+name)
        p=next(iter(candidates))
        for child in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(child)
        child_views.append(p);visited.add(name)
    for name in re.findall(r'^use\s+(\S+)\s+',(directory/(args.cell+'.mag')).read_text(),re.M):visit(name)
    flow.OUT = directory
    preload = ''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in child_views)
    log = flow.magic(preload+f'load {args.cell}\nproperty FIXED_BBOX ""\nlef write {args.cell} -hide\nquit -noprompt\n')
    if any(marker in log for marker in ["couldn't be read","Failure to read","I/O error"]):raise ValueError('Incomplete native hierarchy during LEF export')
    logpath = directory / 'lef_export.log'
    logpath.write_text(log, encoding='utf-8')
    if any(digest(path) != sha for path, sha in original.items()):
        raise ValueError('Physical source view changed during abstract export')
    lef = directory / (args.cell + '.lef')
    content = lef.read_text()
    if not re.search(r'^\s*MACRO\s+' + re.escape(args.cell) + r'\s*$', content, re.M):
        raise ValueError('LEF macro identifier mismatch')
    pinblocks = list(re.finditer(r'(?ms)^\s*PIN\s+(\S+)\s*\n(.*?)^\s*END\s+\1\s*$', content))
    ports = [m.group(1) for m in pinblocks]
    physical_ports = q.get('ports')
    if physical_ports is None:
        headers = []
        for path in original:
            if path.suffix != '.spice':
                continue
            flat = re.sub(r'\n\+\s*', ' ', path.read_text())
            match = re.search(r'^\.subckt\s+' + re.escape(args.cell) + r'\s+([^\n]+)', flat, re.M | re.I)
            if match:
                headers.append(match.group(1).split())
        if not headers or any(set(header) != set(headers[0]) for header in headers):
            raise ValueError('Extracted physical port headers missing or inconsistent')
        physical_ports = headers[0]
    if set(ports) != set(physical_ports) or len(ports) != len(physical_ports):
        raise ValueError('LEF pins do not match the extracted physical ports')
    for match in reversed(pinblocks):
        name = match.group(1)
        use = 'POWER' if name == 'VDD' else 'GROUND' if name == 'VSS' else 'SIGNAL'
        block = match.group(0)
        if not re.search(r'\bLAYER\s+\S+\s*;', block) or not re.search(r'\bRECT\s+', block):
            raise ValueError('LEF pin lacks physical routing geometry: ' + name)
        block = re.sub(r'\bUSE\s+\S+\s*;', 'USE ' + use + ' ;', block)
        if not re.search(r'\bUSE\s+', block):
            block = block.replace('\n', '\n    USE ' + use + ' ;\n', 1)
        content = content[:match.start()] + block + content[match.end():]
    size = [float(x) for x in re.search(r'\bSIZE\s+([\d.]+)\s+BY\s+([\d.]+)', content).groups()]
    bbox = q['bbox_um']
    expected = [bbox[2] - bbox[0], bbox[3] - bbox[1]]
    if any(abs(a - b) > 0.005001 for a, b in zip(size, expected)):
        raise ValueError('LEF size does not match the qualified physical bounding box')
    origin = [float(x) for x in re.search(r'\bORIGIN\s+([-\d.]+)\s+([-\d.]+)', content).groups()]
    for rect in re.findall(r'\bRECT\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)', content):
        coordinates = [float(x) for x in rect]
        if any(value + offset < -0.005001 or value + offset > extent + 0.005001
               for value, offset, extent in zip(coordinates, origin * 2, size * 2)):
            raise ValueError('LEF geometry extends outside the physical bounding box')
    if not re.search(r'^\s*OBS\s*$', content, re.M):
        raise ValueError('LEF must retain internal routing obstructions')
    lef.write_text(content, encoding='ascii')
    source = __import__('pathlib').Path(__file__)
    snapshot = flow.BASE / 'tools/source_snapshots' / ('export_gf180_hierarchical_layout_abstract_' + digest(source) + '.py')
    if not snapshot.exists():
        snapshot.write_bytes(source.read_bytes())
    report = {
        'cell': args.cell, 'size_um': size, 'ports': ports, 'source_snapshot': snapshot.relative_to(flow.ROOT).as_posix(),
        'source_geometry_hashes_unchanged': True, 'physical_ports_and_size_verified': True,
        'routing_obstructions_present': True, 'all_rectangles_within_abstract_boundary': True,
        'native_pcell_fixed_bbox_removed_in_memory': True, 'complete_native_hierarchy_preloaded':True,
        'scope': 'Magic hidden-detail LEF with native FIXED_BBOX removed in memory so added substrate taps are included; actual exported size verified against qualified geometry; original MAG not saved. From real separately DRC/LVS-qualified geometry. VDD/VSS abstract uses assigned POWER/GROUND; other ports SIGNAL. No assembled routing, pin-access DRC, timing library, resistance extraction or model/service/full-chip acceptance.',
        'full_chip_accepted': False,
        'sha256': {p.relative_to(flow.ROOT).as_posix(): digest(p)
                   for p in [*original, *child_views, qualification, lef, logpath, snapshot]},
    }
    target = directory / 'abstract_qualification.json'
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(target), 'size_um': size, 'ports': ports}))


if __name__ == '__main__':
    main()
