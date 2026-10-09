"""Compare physical sampler layouts and measured extracted switching errors."""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def layout_caps(text, root):
    definitions = {name: (ports.split(), body) for name,ports,body in re.findall(r'(?ms)^\.subckt\s+(\S+)\s+([^\n]+)\n(.*?)^\.ends[^\n]*',text)}
    caps = defaultdict(float)
    def visit(name, mapping, prefix):
        ports, body = definitions[name]
        def node(n):
            return mapping.get(n,prefix+'/'+n)
        for line in body.splitlines():
            words = line.split()
            if not words:
                continue
            if words[0].startswith('C'):
                a,b = node(words[1]),node(words[2])
                match = re.fullmatch(r'([-+0-9.eE]+)([fpnu]?)',words[3])
                if not match:
                    raise ValueError('Unsupported capacitance value')
                value = float(match[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6}[match[2]]
                if a != b:
                    caps[tuple(sorted([a,b]))] += value
            elif words[0].startswith('X') and words[-1] in definitions:
                child = words[-1]
                child_ports = definitions[child][0]
                if len(words[1:-1]) != len(child_ports):
                    raise ValueError('Hierarchy interface differs')
                visit(child,dict(zip(child_ports,map(node,words[1:-1]))),prefix+'/'+words[0])
    visit(root,dict(zip(definitions[root][0],definitions[root][0])),root)
    return caps


def main():
    sources = {Path(__file__)}
    rows = []
    for cell in ['gf180_compensated_bottom_sampler','gf180_compensated_bottom_sampler_shielded']:
        directory = BASE/'layout'/cell
        qp = directory/'qualification.json'
        q = json.loads(qp.read_text())
        if q['magic_drc_count'] or not q['gds_roundtrip_lvs_unique'] or q['gds_roundtrip_drc_count']:
            raise ValueError('Actual GDS qualification required')
        sources.add(qp)
        for name,expected in q['sha256'].items():
            p = directory/name
            if sha(p) != expected:
                raise ValueError('Physical source differs')
            sources.add(p)
        caps = layout_caps((directory/(cell+'_cap.spice')).read_text(),cell)
        def pair(a,b):
            return caps[tuple(sorted([a,b]))]*1e15
        reports = []
        for p in (BASE/'results').glob('gf180_fullroute_tg_hold_step100_*macro1_shield*.json'):
            r = json.loads(p.read_text())
            if r['simulation_completed'] and r['settings'].get('macro_cell') == cell:
                reports.append((p,r))
        if not reports:
            raise ValueError('Matched physical simulation absent')
        path,r = max(reports,key=lambda item:item[0].stat().st_mtime)
        sources.add(path)
        for name,expected in r['sha256'].items():
            p = ROOT/name
            if sha(p) != expected:
                raise ValueError('Simulation provenance differs')
            sources.add(p)
        bbox = q['bbox_um']
        rows.append({'cell':cell,'layout_evidence':qp.relative_to(ROOT).as_posix(),
                     'simulation_evidence':path.relative_to(ROOT).as_posix(),
                     'simulation_source_sha256':sha(ROOT/r['source_snapshot']),
                     'bbox_area_um2':(bbox[2]-bbox[0])*(bbox[3]-bbox[1]),
                     'extracted_layout_PM_ff':pair('P','M'),
                     'extracted_layout_P_VSS_ff':pair('P','VSS'),
                     'extracted_layout_M_VSS_ff':pair('M','VSS'),
                     'extracted_layout_clock_coupling_ff':{n:{clock:pair(n,clock) for clock in ['EN','ENB','BEN','BENB']} for n in ['P','M']},
                     'maximum_absolute_release_error_mv':max(abs(c['release_step_uv']) for c in r['cases'])/1000,
                     'cases':r['cases'],
                     'settings':r['settings']})
    if rows[0]['simulation_source_sha256'] != rows[1]['simulation_source_sha256'] or {k:v for k,v in rows[0]['settings'].items() if k != 'macro_cell'} != {k:v for k,v in rows[1]['settings'].items() if k != 'macro_cell'}:
        raise ValueError('Layout comparison changes executable or commands')
    result = {'cases':rows,'same_simulation_executable_and_command_settings_except_layout':True,
              'shielded_bbox_area_increase_percent':100*(rows[1]['bbox_area_um2']/rows[0]['bbox_area_um2']-1),
              'maximum_release_error_reduction_percent':100*(1-rows[1]['maximum_absolute_release_error_mv']/rows[0]['maximum_absolute_release_error_mv']),
              'scope':'Actual hierarchical layout parasitic capacitor sums including each primitive instance; excludes native model MIM capacitance and voltage-dependent intrinsic MOS capacitances. Same nominal deterministic stimulus; three voltages and ideal clock/input/reference sources. Shielding changes both coupling and load, so switching-error changes are not uniquely attributed to one capacitance. Spacious shared macro, not compact per-state storage. No RPEX, sampled noise, PVT/mismatch, read/restore, PLIF/model or population-service acceptance.',
              'physical_storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,
              'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(sources)}}
    target = BASE/'results/gf180_sampler_routing_boundary.json'
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(target),'cases':[{k:v for k,v in row.items() if k not in ['cases','settings']} for row in rows], 'area_increase_percent':result['shielded_bbox_area_increase_percent'],'release_error_reduction_percent':result['maximum_release_error_reduction_percent']},indent=2))


if __name__ == '__main__':
    main()
