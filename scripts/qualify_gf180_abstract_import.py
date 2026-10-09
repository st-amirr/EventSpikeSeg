"""Check component LEF interoperability, not placement/routing or chip readiness."""
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
IMAGE = 'openroad/orfs:latest'
TECH = 'gf180mcu_5LM_1TM_11K_9t_tech.lef'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = Path(__file__)
    image = subprocess.check_output(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], text=True).strip()
    inputs = []
    abstracts = []
    for path in sorted((BASE / 'layout').glob('*/abstract_qualification.json')):
        q = json.loads(path.read_text())
        for name, expected in q['sha256'].items():
            item = ROOT / name
            if digest(item) != expected:
                raise ValueError('Abstract input mismatch: ' + name)
            inputs.append(item)
        inputs.append(path)
        abstracts.append(q)
    if not abstracts:
        raise ValueError('No qualified physical abstracts')
    makefile = BASE / 'pdk/gf180_open_pdks_source/gf180mcu/Makefile'
    if not re.search(r'^D_FULLSTACK\s*=\s*5LM_1TM_11K\s*$', makefile.read_text(), re.M):
        raise ValueError('Expected explicit GF180D metal-stack provenance')
    directory = BASE / 'pdk/router_collateral'
    directory.mkdir(exist_ok=True)
    tech = directory / TECH
    container = ['docker', 'run', '--rm', '--network', 'none', '--memory', '2g', '--cpus', '2',
                 '--volume', f'{ROOT}:/workspace']
    subprocess.run(container + ['--entrypoint', 'cp', image,
        '/OpenROAD-flow-scripts/flow/platforms/gf180/lef/' + TECH,
        '/workspace/' + tech.relative_to(ROOT).as_posix()], check=True, timeout=30)
    technology_text=tech.read_text()
    known=set(re.findall(r'^LAYER\s+(\S+)', technology_text, re.M))
    used=set()
    for q in abstracts:
        used.update(re.findall(r'^\s*LAYER\s+(\S+)\s*;', (BASE/'layout'/q['cell']/(q['cell']+'.lef')).read_text(), re.M))
    missing=sorted(used-known)
    if not set(missing)<= {'Nwell','Pwell'}:raise ValueError('Unknown physical abstract layers: '+str(missing))
    extension=''.join(f'LAYER {name}\n  TYPE MASTERSLICE ;\nEND {name}\n\n' for name in missing)
    extended=directory/'gf180D_11K_with_magic_well_obstructions.lef'
    extended.write_text(technology_text.replace('LAYER Poly2\n',extension+'LAYER Poly2\n',1),encoding='ascii')
    snapshot = BASE / 'tools/source_snapshots' / ('qualify_gf180_abstract_import_' + digest(source) + '.py')
    if not snapshot.exists():
        snapshot.write_bytes(source.read_bytes())
    deck = BASE / 'benches/gf180_component_lef_import.tcl'
    expected_obstructions={}
    for q in abstracts:
        text=(BASE/'layout'/q['cell']/(q['cell']+'.lef')).read_text()
        body=re.search(r'(?ms)^\s*OBS\s*$\n(.*?)^\s*END\s*$',text).group(1)
        counts=Counter();layer=None
        for line in body.splitlines():
            tokens=line.split()
            if tokens and tokens[0]=='LAYER':layer=tokens[1]
            if tokens and tokens[0]=='RECT':counts[layer]+=1
        expected_obstructions[q['cell']]=dict(counts)
    lines = ['read_lef /workspace/' + extended.relative_to(ROOT).as_posix()]
    for q in abstracts:
        lef = BASE / 'layout' / q['cell'] / (q['cell'] + '.lef')
        lines.append('read_lef /workspace/' + lef.relative_to(ROOT).as_posix())
    lines += ['puts "DBU|[[[ord::get_db] getTech] getDbUnitsPerMicron]"']
    for q in abstracts:
        cell = q['cell']
        lines += ['set found {}', 'foreach library [[ord::get_db] getLibs] {',
            ' foreach master [$library getMasters] {',
            f'  if {{[$master getName] eq "{cell}"}} {{set found $master}}', ' }', '}',
            f'if {{$found eq {{}}}} {{error "Missing imported macro {cell}"}}',
            f'puts "MASTER|{cell}|[$found getWidth]|[$found getHeight]"',
            'foreach obstruction [$found getObstructions] {',
            f' puts "OBS|{cell}|[[$obstruction getTechLayer] getName]"', '}',
            'foreach term [$found getMTerms] {',
            f' puts "PIN|{cell}|[$term getName]|[llength [$term getMPins]]|[$term getSigType]"', '}',
        ]
    lines.append('puts "LEF_IMPORT_COMPLETE"')
    deck.write_text('\n'.join(lines) + '\n', encoding='ascii')
    command = container + ['--entrypoint', '/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad',
                          image, '-exit', '/workspace/' + deck.relative_to(ROOT).as_posix()]
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=60)
    log = BASE / 'results/gf180_component_lef_import.log'
    log.write_text(proc.stdout, encoding='utf-8')
    units = re.search(r'^DBU\|(\d+)', proc.stdout, re.M)
    masters = dict((name, [int(w), int(h)]) for name, w, h in
                   re.findall(r'^MASTER\|([^|]+)\|(\d+)\|(\d+)', proc.stdout, re.M))
    obstructions=re.findall(r'^OBS\|([^|]+)\|([^|\n]+)',proc.stdout,re.M)
    pins = re.findall(r'^PIN\|([^|]+)\|([^|]+)\|(\d+)\|(\w+)', proc.stdout, re.M)
    complete = proc.returncode == 0 and 'LEF_IMPORT_COMPLETE' in proc.stdout and units is not None and not re.search(r'undefined layer|\[ERROR|error:',proc.stdout,re.I)
    if complete:
        dbu = int(units.group(1))
        for q in abstracts:
            cell = q['cell']
            actual_obstructions=dict(Counter(layer for name,layer in obstructions if name==cell))
            if actual_obstructions != expected_obstructions[cell]:complete=False
            expected = [round(value * dbu) for value in q['size_um']]
            imported = [(pin, count, use) for name, pin, count, use in pins if name == cell]
            if masters.get(cell) != expected or set(pin for pin, _, _ in imported) != set(q['ports']):
                complete = False
            if any(int(count) < 1 or use != ('POWER' if pin == 'VDD' else 'GROUND' if pin == 'VSS' else 'SIGNAL')
                   for pin, count, use in imported):
                complete = False
    inputs += [tech, extended, makefile, snapshot, deck, log]
    report = {'router_import_verified': complete, 'simulator_returncode': proc.returncode,
              'component_count': len(abstracts), 'technology_stack': 'GF180D_5LM_1TM_11K','docker_image_id':image,'added_nonrouting_masterslice_layers':missing,
              'unsupported_router_rule_messages':re.findall(r'^.*unsupported LEF.*$',proc.stdout,re.M),
              'router_drc_rule_coverage_accepted':False,
              'masters_dbu': masters, 'pins': pins,'obstruction_layer_counts':expected_obstructions,'all_obstruction_rectangles_retained':complete,
              'source_snapshot': snapshot.relative_to(ROOT).as_posix(),
              'full_chip_accepted': False, 'pin_access_drc_accepted': False,
              'scope': 'OpenROAD LEF parser/OpenDB master dimensions, terminal names, pin presence and supply uses checked against qualified physical abstracts. Matching stack selected from local Open_PDKs Makefile. Derived tech adds non-routing MASTERSLICE Nwell/Pwell names emitted by Magic abstracts to retain well obstructions; routing-layer rules unchanged. Unsupported router rule messages retained; no full DRC coverage claim. No synthesis/place/route/ORFS campaign, pin-access DRC, RC/timing, analog transfer or population/model acceptance.',
              'sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in set(inputs)}}
    target = BASE / 'results/gf180_component_lef_import.json'
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(target), 'router_import_verified': complete,
                      'component_count': len(abstracts)}))
    if not complete:
        raise RuntimeError(proc.stdout[-3500:])


if __name__ == '__main__':
    main()
