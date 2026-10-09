"""Build an official GF180 M4/M5 capacitor with explicit substrate tap."""
import argparse
import hashlib
import json
import re
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size-um',type=float,default=7)
    args=parser.parse_args();size=args.size_um
    if not 5 <= size <= 30:
        raise ValueError('bounded square size5..30um')
    cell=f'gf180_mim_{size:g}x{size:g}'.replace('.','p')
    out=flow.BASE/'layout'/cell;out.mkdir(parents=True,exist_ok=True);flow.OUT=out
    log=flow.magic(f'load {cell}_raw\nmagic::gencell gf180mcu::cap_mim_2p0fF c -spice w {size:g}u l {size:g}u\nwriteall force\nquit -noprompt\n')
    (out/'generation.log').write_text(log)
    files=[p for p in out.glob('cap_mim*.mag') if f'string parameters w {float(size)} l {float(size)} ' in p.read_text()]
    if not files:
        raise RuntimeError('missing capacitor PCell')
    source=max(files,key=lambda p:p.stat().st_mtime).read_text()
    rs=rectangles(max(files,key=lambda p:p.stat().st_mtime),0)
    labels=['<< labels >>']
    for i,(layer,net) in enumerate([('mimcapcontact','P'),('via4','M')],1):
        x1,y1,x2,y2=rs[layer][0];x=(x1+x2)//2;y=(y1+y2)//2
        labels += [f'rlabel {layer} s {x-15} {y-15} {x+15} {y+15} 4 {net}',f'port {i} nsew']
    tapx=max(r[2] for r in rs['metal4'])+400
    tap=['<< pwell >>',f'rect {tapx-180} -200 {tapx+180} 200',
         '<< psubdiff >>',f'rect {tapx-36} -100 {tapx+36} 100',
         '<< psubdiffcont >>',f'rect {tapx-23} -87 {tapx+23} 87',
         '<< metal1 >>',f'rect {tapx-38} -98 {tapx+38} 98']
    labels += [f'rlabel metal1 s {tapx-20} -20 {tapx+20} 20 4 VSS','port 3 nsew']
    source=source.replace('<< end >>','\n'.join(tap)+'\n<< end >>')
    source=source.replace('<< end >>','\n'.join(labels)+'\n<< end >>')
    (out/f'{cell}.mag').write_text(source,encoding='ascii')
    log=flow.magic(f'load {cell}\ndrc check\ndrc count\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (out/'extraction.log').write_text(log)
    drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc.group(1)):
        raise RuntimeError(log[-3000:])
    (out/'reference.spice').write_text(f'.subckt reference P M VSS\nXcap P M cap_mim_2f0_m4m5_noshield c_length={size:g}u c_width={size:g}u\n.ends\n')
    lvs=flow.run(['netgen-lvs','-batch','lvs',f'{cell}.spice {cell}','reference.spice reference',f'/workspace/{flow.PDK.relative_to(flow.ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out'])
    (out/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3000:])
    caplog=flow.magic(f'load {cell}\nextract do capacitance\nextract all\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n')
    (out/'capacitance_extraction.log').write_text(caplog)
    captext=(out/f'{cell}_cap.spice').read_text()
    if 'VSUBS' in captext or f'.subckt {cell} P M VSS' not in captext:
        raise RuntimeError('Capacitor substrate must be explicitly connected to the VSS port')
    report={'cell':cell,'square_size_um':size,'magic_drc_count':0,'lvs_unique':True,
            'bbox_um':[int(v)*0.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],
            'extraction_feedback':(out/'warnings.feedback').read_text(),
            'scope':'Standalone official2fF/um2 M4/M5 MIM geometry and capacitance extraction. Actual model capacitance/leakage and combined read/restore validation reported separately. No resistance extraction or full frontend acceptance.',
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/f'{cell}.mag',out/f'{cell}.spice',out/f'{cell}_cap.spice',out/f'{cell}.gds']}}
    (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
