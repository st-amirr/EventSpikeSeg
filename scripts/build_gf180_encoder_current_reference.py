"""Route a GF180 cascaded current divider and low-reference mirror."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

CELL='gf180_encoder_current_reference_divider'
OUT=flow.BASE/'layout'/CELL
DEVICES=[('pdiv','pfet',1,2,['nmid','BIAS','VDD','VDD']),
         ('ndiode','nfet',10,1,['nmid','nmid','VSS','VSS']),
         ('ndiv','nfet',1,2,['pmid','nmid','VSS','VSS']),
         ('pdiode','pfet',20,2,['pmid','pmid','VDD','VDD']),
         ('pcal','pfet',8,2,['CAL','pmid','VDD','VDD']),
         ('plow','pfet',40,2,['LOW','BIAS','VDD','VDD'])]
PORTS=['BIAS','CAL','LOW','VDD','VSS']


def main():
    OUT.mkdir(parents=True,exist_ok=True);flow.OUT=OUT
    tcl=['load gf180_ota_raw']
    for name,family,w,l,_ in DEVICES:
        tcl.append(f'magic::gencell gf180mcu::{family}_03v3 {name} -spice w {w}u l {l}u nf 1')
    tcl+=['writeall force','quit -noprompt','']
    log=flow.magic('\n'.join(tcl));(OUT/'generation.log').write_text(log)
    layers={};netnames=PORTS+['nmid','pmid']
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
    for i,net in enumerate(PORTS,1):
        y=tracks[net];lines += [f'rlabel metal3 s -600 {y-20} -540 {y+20} 4 {net}',f'port {i} nsew']
    lines+=['<< end >>',''];(OUT/f'{CELL}.mag').write_text('\n'.join(lines),encoding='ascii')
    log=flow.magic(f'load {CELL}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (OUT/'extraction.log').write_text(log)
    drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc.group(1)):
        raise RuntimeError(log[-4000:])
    ref=['.subckt reference '+' '.join(PORTS)]
    ref += [f'X{name} '+' '.join(nets)+f' {family}_03v3 w={w}u l={l}u' for name,family,w,l,nets in DEVICES]
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
    snapshot=OUT/'build_source.py';snapshot.write_bytes(Path(__file__).read_bytes());report['sha256'][snapshot.name]=hashlib.sha256(snapshot.read_bytes()).hexdigest()
    report['ports']=PORTS;report['devices']=DEVICES
    report['scope']='Routed six-MOS PF/NF/PF current divider and PF low-reference mirror. Nominal geometry ratios target1nA/2uA from external1uA through separately qualified20/2um PF root; actual current/compliance/PVT/mismatch/noise/startup and encoder integration are unqualified. Root current generator remains external/ideal; capacitance-only extraction, no RPEX or chip acceptance.'
    (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
