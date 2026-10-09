"""Combine the routed GF180 gate capacitor and fixed-body access TG."""
import hashlib
import json
import re
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

CELL = 'gf180_gate_state_cell'
OUT = flow.BASE/'layout'/CELL


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    flow.OUT = OUT
    layers = rectangles(flow.BASE/'layout/gf180_fixed_body_tg/gf180_fixed_body_tg.mag', 0)
    cap = rectangles(flow.BASE/'layout/gf180_mos_gate_cap_10x1/gf180_mos_gate_cap_10x1.mag', 0)
    for layer, rects in cap.items():
        layers.setdefault(layer, []).extend((x1+1600,y1,x2+1600,y2) for x1,y1,x2,y2 in rects)
    layers.setdefault('metal1',[]).extend([(1562,962,1638,1079), (195,-23,1333,23)])
    layers.setdefault('via1',[]).append((1574,974,1626,1026))
    layers.setdefault('metal2',[]).extend([(42,962,1638,1038)])
    lines = ['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
    for layer, rects in layers.items():
        lines += [f'<< {layer} >>']+['rect '+' '.join(map(str,r)) for r in rects]
    lines += ['<< labels >>']
    for i, (layer,box,name) in enumerate([
        ('metal2',[-100,700,-60,740],'BUS'), ('metal2',[700,980,740,1020],'STATE'),
        ('polycontact',[-20,140,20,170],'EN'), ('polycontact',[-20,1840,20,1870],'ENB'),
        ('metal1',[700,-20,740,20],'VSS'), ('metal1',[-220,1940,-200,1970],'VDD')],1):
        lines += [f'rlabel {layer} s '+' '.join(map(str,box))+f' 4 {name}',f'port {i} nsew']
    lines += ['<< end >>','']
    (OUT/f'{CELL}.mag').write_text('\n'.join(lines),encoding='ascii')
    log = flow.magic(f'load {CELL}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (OUT/'extraction.log').write_text(log)
    drc = re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc.group(1)):
        raise RuntimeError(log[-4000:])
    (OUT/'reference.spice').write_text('.subckt reference BUS STATE EN ENB VSS VDD\nXn STATE EN BUS VSS nfet_03v3 w=1u l=0.28u\nXp STATE ENB BUS VDD pfet_03v3 w=2u l=0.28u\nXcap VSS STATE VSS VSS nfet_03v3 w=10u l=1u\n.ends\n')
    lvs = flow.run(['netgen-lvs','-batch','lvs',f'{CELL}.spice {CELL}','reference.spice reference',f'/workspace/{flow.PDK.relative_to(flow.ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out'])
    (OUT/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3000:])
    caplog = flow.magic(f'load {CELL}\nextract do capacitance\nextract all\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {CELL}_cap.spice\nquit -noprompt\n')
    (OUT/'capacitance_extraction.log').write_text(caplog)
    report = {'cell':CELL,'magic_drc_count':0,'lvs_unique':True,
              'bbox_um':[int(v)*0.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],
              'extraction_feedback':(OUT/'warnings.feedback').read_text(),
              'physical_state_accepted':False,'scope':'Single routed gate-cap state plus fixed-body access; no resistance extraction, noise or complete state service acceptance.',
              'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/f'{CELL}.mag',OUT/f'{CELL}.gds',OUT/f'{CELL}.spice',OUT/f'{CELL}_cap.spice']}}
    (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
