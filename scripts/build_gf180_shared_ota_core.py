"""Route the seven-transistor GF180 OTA core using official PCells."""
import argparse
import hashlib
import json
import re
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

CELL='gf180_shared_ota_core'
OUT=flow.BASE/'layout'/CELL
DEVICES=[('n1','nfet',10,1,['mirror','IN','tail','VSS']),
         ('n2','nfet',10,1,['first','IP','tail','VSS']),
         ('tail','nfet',10,2,['tail','BIAS','VSS','VSS']),
         ('p1','pfet',20,1,['mirror','mirror','VDD','VDD']),
         ('p2','pfet',20,1,['first','mirror','VDD','VDD']),
         ('pout','pfet',40,1,['OUT','first','VDD','VDD']),
         ('sink','nfet',20,1,['OUT','BIAS','VSS','VSS'])]


def main():
    global CELL,OUT,DEVICES
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pmos-input',action='store_true')
    args=parser.parse_args()
    if args.pmos_input:
        CELL='gf180_shared_ota_core_pmos_input';OUT=flow.BASE/'layout'/CELL
        DEVICES=[('p1','pfet',20,1,['mirror','IN','tail','VDD']),
                 ('p2','pfet',20,1,['first','IP','tail','VDD']),
                 ('tail','pfet',20,2,['tail','BIAS','VDD','VDD']),
                 ('n1','nfet',10,1,['mirror','mirror','VSS','VSS']),
                 ('n2','nfet',10,1,['first','mirror','VSS','VSS']),
                 ('nout','nfet',80,1,['OUT','first','VSS','VSS']),
                 ('source','pfet',40,1,['OUT','BIAS','VDD','VDD'])]
    OUT.mkdir(parents=True,exist_ok=True);flow.OUT=OUT
    tcl=['load gf180_ota_raw']
    for name,family,w,l,_ in DEVICES:
        tcl.append(f'magic::gencell gf180mcu::{family}_03v3 {name} -spice w {w}u l {l}u nf 1')
    tcl+=['writeall force','quit -noprompt','']
    log=flow.magic('\n'.join(tcl));(OUT/'generation.log').write_text(log)
    layers={};netnames=['IP','IN','OUT','VDD','VSS','BIAS','mirror','first','tail']
    tracks={n:6000+160*i for i,n in enumerate(netnames)}
    for index,(_,family,w,l,nets) in enumerate(DEVICES):
        files=[p for p in OUT.glob(f'{family}_03v3_*.mag') if f'string parameters w {float(w)} l {float(l)} ' in p.read_text()]
        if not files:
            raise RuntimeError(f'missing PCell {family} {w}/{l}')
        p=max(files,key=lambda p:p.stat().st_mtime);dx=2000*index
        for layer,rs in rectangles(p,0).items():
            layers.setdefault(layer,[]).extend((x1+dx,y1,x2+dx,y2) for x1,y1,x2,y2 in rs)
        half_l=int(l*100)
        terminals=[(half_l+52,0),(-half_l-52,0),(0,int(w*100)),(-half_l-190,0)]
        # D/G/S/B electrical order; the terminal geometry is D/S/G/B.
        terminal_nets=[nets[0],nets[2],nets[1],nets[3]]
        for (x,y),net in zip(terminals,terminal_nets):
            x+=dx;track=tracks[net]
            top=y+79 if y else y+38
            layers.setdefault('metal1',[]).append((x-38,y-38,x+38,top))
            layers.setdefault('via1',[]).append((x-26,y-26,x+26,y+26))
            layers.setdefault('metal2',[]).append((x-38,min(y-38,track-38),x+38,max(top,track+38)))
            layers.setdefault('via2',[]).append((x-26,track-26,x+26,track+26))
    for track in tracks.values():
        layers.setdefault('metal3',[]).append((-600,track-38,12600,track+38))
    lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
    for layer,rs in layers.items():
        lines+=[f'<< {layer} >>']+['rect '+' '.join(map(str,r)) for r in rs]
    lines+=['<< labels >>']
    for i,net in enumerate(netnames[:6],1):
        y=tracks[net];lines += [f'rlabel metal3 s -600 {y-20} -540 {y+20} 4 {net}',f'port {i} nsew']
    y=tracks['first'];lines += [f'rlabel metal3 s -600 {y-20} -540 {y+20} 4 CMP','port 7 nsew']
    lines+=['<< end >>',''];(OUT/f'{CELL}.mag').write_text('\n'.join(lines),encoding='ascii')
    log=flow.magic(f'load {CELL}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (OUT/'extraction.log').write_text(log)
    drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc.group(1)):
        raise RuntimeError(log[-4000:])
    ref=['.subckt reference IP IN OUT VDD VSS BIAS CMP']
    ref += [f'X{name} '+' '.join('CMP' if net=='first' else net for net in nets)+f' {family}_03v3 w={w}u l={l}u' for name,family,w,l,nets in DEVICES]
    ref+=['.ends',''];(OUT/'reference.spice').write_text('\n'.join(ref))
    lvs=flow.run(['netgen-lvs','-batch','lvs',f'{CELL}.spice {CELL}','reference.spice reference',f'/workspace/{flow.PDK.relative_to(flow.ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out'])
    (OUT/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3000:])
    caplog=flow.magic(f'load {CELL}\nextract do capacitance\nextract all\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {CELL}_cap.spice\nquit -noprompt\n')
    (OUT/'capacitance_extraction.log').write_text(caplog)
    bbox=[int(v)*0.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()]
    captext=(OUT/f'{CELL}_cap.spice').read_text()
    report={'cell':CELL,'magic_drc_count':0,'lvs_unique':True,'bbox_um':bbox,
            'extraction_feedback':(OUT/'warnings.feedback').read_text(),'device_count':len(re.findall(r'(?m)^X\S+',captext)),
            'capacitance_entries':len(re.findall(r'(?m)^C\S+',captext)),
            'physical_state_accepted':False,'scope':'Routed OTA transistor core only. Compensation resistor/capacitor, bias reference, feedback/load, extraction resistance, matching/noise/service acceptance and combined front-end layout are absent.',
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/f'{CELL}.mag',OUT/f'{CELL}.gds',OUT/f'{CELL}.spice',OUT/f'{CELL}_cap.spice']}}
    report['pmos_input']=args.pmos_input
    if args.pmos_input:
        report['scope']='Routed seven-MOS PMOS-input two-stage OTA core with NF mirror/output and PF tail/current source. Low common-mode, compensation, bias, feedback, noise/mismatch/settling and encoder operation unqualified; no resistance extraction or complete assembly.'
    (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
