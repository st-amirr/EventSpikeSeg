"""Route GF180 OTA/reset/reference plus grounded MIM feedback/compensation."""
import hashlib
import argparse
import json
import re
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles
from build_gf180_shared_ota_core import DEVICES as CORE_DEVICES

CELL='gf180_charge_read_frontend'
OUT=flow.BASE/'layout'/CELL
RENAMES={'IP':'VCM','IN':'SUM','first':'CMP'}
DEVICES=[(n,f,w,l,[RENAMES.get(net,net) for net in nets]) for n,f,w,l,nets in CORE_DEVICES]
DEVICES += [('resetn','nfet',1,1,['OUT','RESET','SUM','VSS']),
            ('resetp','pfet',2,1,['OUT','RESETB','SUM','VDD']),
            ('ref','nfet',10,2,['BIAS','BIAS','VSS','VSS'])]


def main():
    global CELL,OUT,DEVICES
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--servo-writer',action='store_true')
    parser.add_argument('--input-width-um',type=float,choices=[2.5,5,10],default=10)
    args=parser.parse_args()
    if args.input_width_um!=10 and not args.servo_writer:
        raise ValueError('input width variant requires servo writer')
    if args.servo_writer:
        CELL='gf180_sensor_servo_writer';OUT=flow.BASE/'layout'/CELL
        mapping={'IP':'VCM','IN':'input','first':'CMP'}
        DEVICES=[(n,f,w,l,[mapping.get(net,net) for net in nets]) for n,f,w,l,nets in CORE_DEVICES]
        DEVICES += [('readn','nfet',1,1,['input','RESET','SUM','VSS']),
                    ('readp','pfet',2,1,['input','RESETB','SUM','VDD']),
                    ('unityn','nfet',1,1,['input','RESETB','OUT','VSS']),
                    ('unityp','pfet',2,1,['input','RESET','OUT','VDD']),
                    ('ref','nfet',10,2,['BIAS','BIAS','VSS','VSS'])]
        if args.input_width_um!=10:
            width_token=f'{args.input_width_um:g}'.replace('.','p')
            CELL+=f'_input{width_token}um';OUT=flow.BASE/'layout'/CELL
            DEVICES=[(n,f,args.input_width_um if n in ['n1','n2'] else w,l,nets)
                     for n,f,w,l,nets in DEVICES]
    OUT.mkdir(parents=True,exist_ok=True);flow.OUT=OUT
    tcl=['load gf180_frontend_raw']+[f'magic::gencell gf180mcu::{f}_03v3 {n} -spice w {w}u l {l}u nf 1' for n,f,w,l,_ in DEVICES]+['writeall force','quit -noprompt','']
    log=flow.magic('\n'.join(tcl));(OUT/'generation.log').write_text(log)
    names=['VCM','SUM','OUT','VDD','VSS','BIAS','CMP','RESET','RESETB','mirror','tail']
    if args.servo_writer:
        names.append('input')
    tracks={n:10000+160*i for i,n in enumerate(names)};layers={}
    for i,(_,f,w,l,nets) in enumerate(DEVICES):
        files=[p for p in OUT.glob(f'{f}_03v3_*.mag') if f'string parameters w {float(w)} l {float(l)} ' in p.read_text()]
        if not files:
            raise RuntimeError('missing frontend transistor PCell')
        source=max(files,key=lambda p:p.stat().st_mtime);dx=i*2000
        for layer,rs in rectangles(source,0).items():
            layers.setdefault(layer,[]).extend((x1+dx,y1,x2+dx,y2) for x1,y1,x2,y2 in rs)
        half_l=int(l*100)
        for (x,y),net in zip([(half_l+52,0),(-half_l-52,0),(0,int(w*100)),(-half_l-190,0)],[nets[0],nets[2],nets[1],nets[3]]):
            x+=dx;track=tracks[net]
            layers.setdefault('metal1',[]).append((x-38,y-38,x+38,y+79 if y else y+38))
            layers.setdefault('via1',[]).append((x-26,y-26,x+26,y+26))
            layers.setdefault('metal2',[]).append((x-38,y-38,x+38,track+38))
            layers.setdefault('via2',[]).append((x-26,track-26,x+26,track+26))
    for track in tracks.values():
        layers.setdefault('metal3',[]).append((-600,track-38,27000,track+38))
    # MIM top plates route left in M5, avoiding their bottom-plate M5 landing.
    # Feedback bottom routes right in M4; compensation bottom joins OUT in M4.
    caps=[('gf180_mim_22x22',21000,6500)] if args.servo_writer else [('gf180_mim_7x7',21000,0),('gf180_mim_22x22',21000,6500)]
    for cap,dx,dy in caps:
        source=flow.BASE/'layout'/cap/f'{cap}.mag'
        rs=rectangles(source,dy)
        for layer,boxes in rs.items():
            layers.setdefault(layer,[]).extend((x1+dx,y1,x2+dx,y2) for x1,y1,x2,y2 in boxes)
        local=rectangles(source,0);tapx=max(r[2] for r in local['metal1'])-38+dx
        layers.setdefault('metal1',[]).append((tapx-38,dy-38,tapx+38,dy+38))
        layers.setdefault('via1',[]).append((tapx-26,dy-26,tapx+26,dy+26))
        layers.setdefault('metal2',[]).append((tapx-38,dy-38,tapx+38,tracks['VSS']+38))
        layers.setdefault('via2',[]).append((tapx-26,tracks['VSS']-26,tapx+26,tracks['VSS']+26))
    def m34(x,y):
        layers.setdefault('via3',[]).append((x-26,y-26,x+26,y+26))
        layers.setdefault('metal4',[]).append((x-38,y-38,x+38,y+38))
    def m45(x,y):
        layers.setdefault('via4',[]).append((x-44,y-44,x+44,y+44))
        layers.setdefault('metal4',[]).append((x-60,y-60,x+60,y+60))
        layers.setdefault('metal5',[]).append((x-60,y-60,x+60,y+60))
    # Cf top OUT: M5 left from its plate, M4 through same-net compensation bottom.
    if not args.servo_writer:
        layers.setdefault('metal5',[]).append((19800-60,-60,20880+60,60));m45(19800,0)
        layers.setdefault('metal4',[]).extend([(19762,-38,19838,tracks['OUT']+38),(19762,tracks['OUT']-38,25038,tracks['OUT']+38)])
    else:
        layers.setdefault('metal4',[]).extend([(23280,6462,25038,6538),(24962,6462,25038,tracks['OUT']+38)])
    m34(25000,tracks['OUT'])
    # Cf bottom SUM, routed outside compensation plate.
    if not args.servo_writer:
        layers.setdefault('metal4',[]).extend([(21790,-38,25638,38),(25562,-38,25638,tracks['SUM']+38)])
        m34(25600,tracks['SUM'])
    # Ccomp top CMP left in M5, then M4 outside its bottom OUT plate.
    layers.setdefault('metal5',[]).append((18000-60,6500-60,20880+60,6500+60));m45(18000,6500)
    layers.setdefault('metal4',[]).append((17962,6500-38,18038,tracks['CMP']+38));m34(18000,tracks['CMP'])
    lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
    for layer,rs in layers.items():
        lines+=[f'<< {layer} >>']+['rect '+' '.join(map(str,r)) for r in rs]
    lines+=['<< labels >>']
    ports=['VCM','SUM','OUT','VDD','VSS','IREF','RESET','RESETB']
    aliases={'VCM':'SETPOINT','SUM':'READBUS','OUT':'WRITEBUS','RESET':'CAL','RESETB':'CALB'} if args.servo_writer else {}
    for i,net in enumerate(ports,1):
        y=tracks['BIAS' if net=='IREF' else net]
        lines += [f'rlabel metal3 s -600 {y-20} -540 {y+20} 4 {aliases.get(net,net)}',f'port {i} nsew']
    ports=[aliases.get(net,net) for net in ports]
    lines+=['<< end >>',''];(OUT/f'{CELL}.mag').write_text('\n'.join(lines),encoding='ascii')
    log=flow.magic(f'load {CELL}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (OUT/'extraction.log').write_text(log)
    drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc.group(1)):
        raise RuntimeError(log[-4000:])
    ref=['.subckt reference '+' '.join(ports)]
    ref += [f'X{n} '+' '.join('IREF' if net=='BIAS' else aliases.get(net,net) for net in nets)+f' {f}_03v3 w={w}u l={l}u' for n,f,w,l,nets in DEVICES]
    if not args.servo_writer:
        ref.append('Xcf OUT SUM cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u')
    ref += [f'Xcomp CMP {aliases.get("OUT","OUT")} cap_mim_2f0_m4m5_noshield c_width=22u c_length=22u','.ends','']
    (OUT/'reference.spice').write_text('\n'.join(ref))
    lvs=flow.run(['netgen-lvs','-batch','lvs',f'{CELL}.spice {CELL}','reference.spice reference',f'/workspace/{flow.PDK.relative_to(flow.ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out'])
    (OUT/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3000:])
    caplog=flow.magic(f'load {CELL}\nextract do capacitance\nextract all\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {CELL}_cap.spice\nquit -noprompt\n')
    (OUT/'capacitance_extraction.log').write_text(caplog)
    captext=(OUT/f'{CELL}_cap.spice').read_text()
    if 'VSUBS' in captext:
        raise RuntimeError('unconnected substrate in frontend')
    report={'cell':CELL,'magic_drc_count':0,'lvs_unique':True,
            'bbox_um':[int(v)*0.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],
            'ports':ports,'extraction_feedback':(OUT/'warnings.feedback').read_text(),
            'extracted_device_count':len(re.findall(r'(?m)^X\S+',captext)),
            'capacitance_entries':len(re.findall(r'(?m)^C\S+',captext)),
            'physical_state_accepted':False,
            'scope':'Combined routed charge-reader frontend: OTA7FET,1um reset pair,reference MOS and7/22um MIM caps. External20uA reference current, state-store/load, phase controls, extraction resistance, mismatch/noise and restore/encoder/full-chip service remain unqualified.',
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/f'{CELL}.mag',OUT/f'{CELL}.gds',OUT/f'{CELL}.spice',OUT/f'{CELL}_cap.spice']}}
    if args.servo_writer:
        report['input_pair_width_um']=args.input_width_um
        report['scope']='Combined routed shared sensor-servo writer: OTA7FET, two1um feedback-selection TGs, reference diode and grounded22um MIM compensation. External20uA reference, setpoint, state/sensor/read load/park, controls, resistance extraction, noise/mismatch, nonlinear encode/restore and full model/service unqualified.'
        if args.input_width_um!=10:
            report['scope']+=f' Both differential-input NFET widths physically changed to{args.input_width_um:g}um; extracted load, gain, settling, input range and noise require requalification. Original writer preserved.'
    (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
