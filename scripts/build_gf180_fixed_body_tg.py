"""Route official GF180 fixed-body TG PCells and extract their capacitances."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import probe_gf180_mos_gate_cap as flow

OUT = flow.BASE / 'layout/gf180_fixed_body_tg'
CELL = 'gf180_fixed_body_tg'


def rectangles(path, dy):
    layers = {}
    layer = None
    for line in path.read_text().splitlines():
        if line.startswith('<< '):
            layer = line[3:-3]
        elif line.startswith('rect ') and layer not in ['checkpaint', 'properties']:
            x1, y1, x2, y2 = map(int, line.split()[1:])
            layers.setdefault(layer, []).append((x1, y1+dy, x2, y2+dy))
    return layers


def main():
    global CELL,OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nf-width-um',type=float,choices=[.25,.5,.75,1],default=1)
    parser.add_argument('--pf-width-um',type=float,choices=[.5,1,1.2,1.22,2],default=None)
    args=parser.parse_args();nw=args.nf_width_um;pw=args.pf_width_um if args.pf_width_um is not None else 2*nw
    if nw!=1:
        CELL+='_nf'+f'{nw:g}'.replace('.','p');OUT=flow.BASE/'layout'/CELL
    if args.pf_width_um is not None:
        CELL='gf180_fixed_body_tg_nf'+f'{nw:g}'.replace('.','p')+'_pf'+f'{pw:g}'.replace('.','p');OUT=flow.BASE/'layout'/CELL
    OUT.mkdir(parents=True, exist_ok=True)
    flow.OUT = OUT
    log = flow.magic(f'load gf180_tg_raw\nmagic::gencell gf180mcu::nfet_03v3 n -spice w {nw:g}u l 0.28u nf 1\nmagic::gencell gf180mcu::pfet_03v3 p -spice w {pw:g}u l 0.28u nf 1\nwriteall force\nquit -noprompt\n')
    (OUT/'generation.log').write_text(log)
    layers = {}
    gate_boxes={}
    for family, dy,w in [('nfet', 0,nw), ('pfet', 1600,pw)]:
        files = sorted([p for p in OUT.glob(f'{family}_03v3_*.mag') if f'string parameters w {float(w)} l 0.28 ' in p.read_text()], key=lambda p:p.stat().st_mtime)
        source = files[-1]
        local=rectangles(source,dy)
        gate=next(rect for rect in local['polycontact'] if rect[0]<0<rect[2])
        gate_boxes[family]=[gate[0]+4,gate[1]+4,gate[2]-4,gate[3]-4]
        for layer, rects in local.items():
            layers.setdefault(layer, []).extend(rects)
    # 0.005um internal grid. M2 A/B rails cross guard rings on M1.
    # Each 0.26um via has 0.06um metal enclosure; gate contacts stay on M1.
    for x in [-80, 80]:
        layers.setdefault('metal2', []).append((x-38, -38, x+38, 1638))
        for y in [0, 1600]:
            layers.setdefault('metal1', []).append((x-38, y-38, x+38, y+38))
            layers.setdefault('via1', []).append((x-26, y-26, x+26, y+26))
    lines = ['magic', 'tech gf180mcuD', 'magscale 1 10', 'timestamp 0']
    for layer, rects in layers.items():
        lines.append(f'<< {layer} >>')
        lines += ['rect '+' '.join(map(str,r)) for r in rects]
    lines += ['<< labels >>']
    for index, (layer, box, name) in enumerate([
        ('metal2', [-100, 700, -60, 740], 'A'),
        ('metal2', [60, 700, 100, 740], 'B'),
        ('polycontact', [-20, 140, 20, 170] if nw==1 else gate_boxes['nfet'], 'EN'),
        ('polycontact', [-20, 1840, 20, 1870] if nw==1 else gate_boxes['pfet'], 'ENB'),
        ('metal1', [-220, 230, -200, 260] if nw==1 else [-220,-20,-200,20], 'VSS'),
        ('metal1', [-220, 1940, -200, 1970] if nw==1 else [-220,1580,-200,1620], 'VDD')], start=1):
        lines += [f'rlabel {layer} s '+' '.join(map(str,box))+f' 4 {name}', f'port {index} nsew']
    lines += ['<< end >>', '']
    (OUT/f'{CELL}.mag').write_text('\n'.join(lines), encoding='ascii')
    log = flow.magic(f'load {CELL}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (OUT/'extraction.log').write_text(log)
    drc = re.search(r'Total DRC errors found:\s*(\d+)', log)
    if not drc or int(drc.group(1)):
        raise RuntimeError(log[-4000:])
    ref = f'.subckt reference A B EN ENB VSS VDD\nXn B EN A VSS nfet_03v3 w={nw:g}u l=0.28u\nXp B ENB A VDD pfet_03v3 w={pw:g}u l=0.28u\n.ends\n'
    (OUT/'reference.spice').write_text(ref)
    lvs = flow.run(['netgen-lvs', '-batch', 'lvs', f'{CELL}.spice {CELL}', 'reference.spice reference',
                    f'/workspace/{flow.PDK.relative_to(flow.ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl', 'lvs.out'])
    (OUT/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3000:])
    caplog = flow.magic(f'load {CELL}\nextract do capacitance\nextract all\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {CELL}_cap.spice\nquit -noprompt\n')
    (OUT/'capacitance_extraction.log').write_text(caplog)
    captext = (OUT/f'{CELL}_cap.spice').read_text()
    bbox = [int(v)*0.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()]
    report = {'cell':CELL,'nf_width_um':nw,'pf_width_um':pw,'length_um':.28, 'magic_drc_count':0, 'lvs_unique':True, 'bbox_um':bbox,
              'capacitance_count':len(re.findall(r'(?m)^C\S+',captext)),
              'extraction_feedback':(OUT/'warnings.feedback').read_text(),
              'physical_state_accepted':False,
              'scope':'Fixed-body physical TG only; capacitance extraction, no resistance extraction or combined array qualification.',
              'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/f'{CELL}.mag',OUT/f'{CELL}.gds',OUT/f'{CELL}.spice',OUT/f'{CELL}_cap.spice']}}
    snapshot=OUT/'build_source.py';snapshot.write_bytes(Path(__file__).read_bytes());report['sha256'][snapshot.name]=hashlib.sha256(snapshot.read_bytes()).hexdigest()
    (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
