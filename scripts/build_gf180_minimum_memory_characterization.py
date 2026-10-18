"""Route a characterization memory module with repaired minimum MIM and quieter writer terminal."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shielded', action='store_true')
    args = parser.parse_args()
    cell = 'gf180_minimum_memory_characterization_fullroute'+('_shielded' if args.shielded else '')
    out = flow.BASE / 'layout' / cell
    out.mkdir(parents=True, exist_ok=True)
    if (out/'qualification.json').exists():
        raise ValueError('Preserve qualified sampler')
    flow.OUT = out
    inputs = set()
    children = {}
    for name in ['gf180_fixed_body_tg_fullroute_quarter','gf180_mim_5x5_ports_routed','gf180_nondestructive_sense_nf05_l1_fullroute']:
        directory = flow.BASE/'layout'/name
        qp = directory/'qualification.json'
        q = json.loads(qp.read_text())
        if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:
            raise ValueError('Native input unqualified')
        if ('tg_' in name or 'sense_' in name) and (not q['gds_roundtrip_lvs_unique'] or q['gds_roundtrip_drc_count']):
            raise ValueError('Corrected TG GDS connectivity required')
        inputs.add(qp)
        for filename, expected in q['sha256'].items():
            p = directory/filename
            if digest(p) != expected:
                raise ValueError('Child view changed')
            inputs.add(p)
        children[name] = directory
    audit_path=flow.BASE/'results/gf180_minimum_mim_routed_gds_integrity.json'
    audit=json.loads(audit_path.read_text())
    assert audit['audit_completed'] and audit['cases'][0]['physical_layout_accepted']
    for name,h in audit['sha256'].items():assert digest(flow.ROOT/name)==h,name
    inputs.add(audit_path)
    nets = ['STATE','VCM','IN','COL','DRAIN','WRITE','WRITEB','READ','READB','PARK','PARKB','VSS','VDD']
    tracks = {net: 24000+i*240 for i,net in enumerate(nets)}
    guard_tracks = []
    if args.shielded:
        active = [net for net in nets if net != 'VSS']
        tracks = {net: 24000+i*480 for i,net in enumerate(active)}
        tracks['VSS'] = 24000+(2*len(active)-1)*240
        guard_tracks = [24000+(2*i+1)*240 for i in range(len(active)-1)]
    layers = {}
    def rect(layer, box):
        layers.setdefault(layer, []).append(tuple(box))
    def via(low, high, cut, x, y):
        for layer in [low, high]:
            rect(layer, (x-40,y-40,x+40,y+40))
        rect(cut, (x-28,y-28,x+28,y+28))
    uses = []
    full = 'gf180_fixed_body_tg_fullroute_quarter'
    half = full+'_half'
    configurations = [
        ('write',full,0,0,['STATE','IN','WRITE','WRITEB','VSS','VDD']),
        ('select',full,10000,0,['DRAIN','COL','READ','READB','VSS','VDD']),
        ('park',full,0,10000,['DRAIN','VSS','PARK','PARKB','VSS','VDD']),
        ('sense','gf180_nondestructive_sense_nf05_l1_fullroute',10000,10000,['DRAIN','STATE','VSS','VSS']),
    ]
    for instance, name, dx, dy, mapping in configurations:
        uses += [f'use {name} {instance}', f'transform 1 0 {dx} 0 1 {dy}', 'box -1600 -1000 6000 7240']
        for i, net in enumerate(mapping):
            x = dx+(-1400 if dy == 0 else 2000)+i*240
            y = dy+([6000,6480,6240,6960][i] if 'sense_' in name else 6000+i*240)
            via('metal3','metal4','via3',x,y)
            rect('metal4',(x-40,y-40,x+40,tracks[net]+40))
            via('metal4','metal5','via4',x,tracks[net])
    cx, cy = 24000, 20000
    # Flatten only the capacitor geometry. Its legacy mimcapcontact port text
    # exports on M4, leaving a phantom P port after hierarchical GDS import.
    # The actual M5 top-plate strap below defines P directly in the parent.
    for layer, boxes in rectangles(children['gf180_mim_5x5_ports_routed']/'gf180_mim_5x5_ports_routed.mag',0).items():
        for x1,y1,x2,y2 in boxes:
            rect(layer,(x1+cx,y1+cy,x2+cx,y2+cy))
    # Native top contact exits on M5, below the first global track.
    px = cx-120
    rect('metal5',(px-60,cy-60,px+60,tracks['STATE']+60))
    # Native bottom plate exits on its left M4 rim.
    mx = cx-700
    rect('metal4',(mx-60,cy-60,mx+60,tracks['VCM']+60))
    via('metal4','metal5','via4',mx,tracks['VCM'])
    # A via on the extended native bottom plate needs the MIM-specific 0.4um
    # bottom-plate enclosure, beyond an ordinary routing-via enclosure.
    rect('metal4',(mx-108,tracks['VCM']-108,mx+108,tracks['VCM']+108))
    # Preserve the native capacitor substrate tap, connected through a real stack.
    sx = cx+1140
    for low, high, cut in [('metal1','metal2','via1'),('metal2','metal3','via2'),('metal3','metal4','via3')]:
        via(low,high,cut,sx,cy)
    rect('metal4',(sx-40,cy-40,sx+40,tracks['VSS']+40))
    via('metal4','metal5','via4',sx,tracks['VSS'])
    for y in guard_tracks:
        rect('metal5',(-1800,y-60,26000,y+60))
        via('metal4','metal5','via4',sx,y)
    for y in tracks.values():
        rect('metal5',(-1800,y-60,26000,y+60))
    lines = ['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
    for layer, boxes in layers.items():
        lines += ['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
    lines += ['<< labels >>']
    for i,net in enumerate(nets,1):
        y = tracks[net]
        lines += [f'rlabel metal5 s -1750 {y-20} -1710 {y+20} 4 {net}',f'port {i} nsew']
    lines += ['<< end >>','']
    (out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii')
    (out/'build_source.py').write_bytes(Path(__file__).read_bytes())
    preload = '\n'.join('load /workspace/'+(directory/name).relative_to(flow.ROOT).as_posix() for name,directory in children.items())+'\n'
    log = flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (out/'extraction.log').write_text(log)
    drc = re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc[1]) or (out/'gds_warnings.feedback').read_text() or re.search(r'\d+ problems occurred',log):
        raise RuntimeError(log[-5000:])
    ref = ''.join((directory/(name+'.spice')).read_text()+'\n' for name,directory in children.items())
    ref += '.subckt reference '+ ' '.join(nets)+'\n'
    for instance,name,dx,dy,mapping in configurations:
        ref += 'X'+instance+' '+' '.join(mapping)+' '+name+'\n'
    ref += 'Xstorage STATE VCM cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u\n.ends\n'
    (out/'reference.spice').write_text(ref)
    setup = '/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
    lvs = flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out'])
    (out/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3500:])
    caplog = flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n')
    (out/'capacitance_extraction.log').write_text(caplog)
    if (out/'warnings.feedback').read_text() or (out/'capacitance_warnings.feedback').read_text():
        raise ValueError('Unresolved extraction feedback')
    rd = flow.BASE/'verification/gds_roundtrip'/cell
    rd.mkdir(parents=True,exist_ok=True)
    flow.OUT = rd
    readlog = flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n')
    (rd/'readback.log').write_text(readlog)
    rdr = re.search(r'Total DRC errors found:\s*(\d+)',readlog)
    rlvs = flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out'])
    (rd/'netgen.log').write_text(rlvs)
    if not rdr or int(rdr[1]) or 'Circuits match uniquely' not in rlvs or (rd/'roundtrip.feedback').read_text():
        raise RuntimeError('GDS roundtrip failed\n'+readlog[-1600:]+'\n'+rlvs[-1600:])
    files = [out/(cell+suffix) for suffix in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
    q = {'cell':cell,'ports':nets,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)',
         'gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'',
         'bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],
         'native_mim_count':1,'mos_count':7,'native_sense_junction_geometry_preserved_hierarchically':True,
         'grounded_global_route_guards':args.shielded,'ground_guard_count':len(guard_tracks),
         'capacitance_count':len(re.findall(r'(?m)^C\S+',(out/(cell+'_cap.spice')).read_text())),
         'physical_storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,
         'scope':'Spacious characterization memory with three quarter TGs, quieter writer A terminal on STATE, zero-parked NF0.5um/L1um sensing and repaired native5um MIM, explicit body connections and M4/M5 routing. DRAIN/STATE exposed for diagnostics. Full DRC/LVS/exported-GDS readback and cap extraction only; clocks/column frontend/bias are external. No prior performance transferred, no compact cell density, RPEX, noise, mismatch, PVT, qualified leakage, accurate initialization, full-float PLIF or population service acceptance',
         'sha256':{p.name:digest(p) for p in files},
         'input_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in sorted(inputs)},
         'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
    (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n')
    print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'gds_roundtrip_lvs_unique':True},indent=2))


if __name__ == '__main__':
    main()
