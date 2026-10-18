"""Repair minimum-MIM exported pin attachment in a separate reusable view."""
import hashlib
import json
import re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    cell = 'gf180_mim_22x22_ports_routed_v1'
    native = flow.BASE/'layout/gf180_mim_22x22'
    qpath = native/'qualification.json'
    q = json.loads(qpath.read_text(encoding='utf-8'))
    inputs = {qpath, Path(__file__)}
    for name, expected in q['sha256'].items():
        p = native/name
        assert sha(p) == expected
        inputs.add(p)
    out = flow.BASE/'layout'/cell
    assert not out.exists(), 'Preserve prior geometry and failures'
    out.mkdir(parents=True)
    flow.OUT = out
    text = (native/'gf180_mim_22x22.mag').read_text(encoding='utf-8')
    text = text[:text.index('<< labels >>')]
    # Explicit M5 paint and M5 label at the native top-plate contact.
    # Put M on real M4 plate rim, rather than a via label.
    text = text.replace('<< metal5 >>', '<< metal5 >>\nrect -180 -60 -60 2800', 1)
    text += ('<< labels >>\nrlabel metal5 s -135 2700 -105 2730 4 P\nport 1 nsew\n'
             'rlabel metal4 s -2400 -15 -2370 15 4 M\nport 2 nsew\n'
             'rlabel metal1 s 2820 -20 2860 20 4 VSS\nport 3 nsew\n<< end >>\n')
    (out/(cell+'.mag')).write_text(text, encoding='utf-8')
    snapshot = out/'build_source.py'
    snapshot.write_bytes(Path(__file__).read_bytes())
    log = flow.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (out/'extraction.log').write_text(log, encoding='utf-8')
    drc = re.search(r'Total DRC errors found:\s*(\d+)', log)
    assert drc and int(drc[1]) == 0, log[-2500:]
    assert not re.search(r'\d+ problems occurred',log), 'GDS export problem'
    (out/'reference.spice').write_text('.subckt reference P M VSS\nX0 P M cap_mim_2f0_m4m5_noshield c_width=22u c_length=22u\n.ends\n', encoding='utf-8')
    lvs = flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',
                    '/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out'])
    (out/'netgen.log').write_text(lvs, encoding='utf-8')
    assert 'Circuits match uniquely' in lvs
    log = flow.magic(f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n')
    (out/'capacitance_extraction.log').write_text(log, encoding='utf-8')
    feedback = (out/'warnings.feedback').read_text()+(out/'capacitance_warnings.feedback').read_text()
    assert not feedback
    rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
    readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
    setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
    rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text()
    for pp in [out/(cell+'.spice'),rd/'roundtrip.spice']:
        txt=pp.read_text().replace('\n+',' ');ports=re.search(r'(?m)^\.subckt\s+'+cell+r'\s+([^\n]+)',txt)[1].split();assert ports==['P','M','VSS'];devices=[line.split() for line in txt.splitlines() if line.startswith('X') and 'cap_mim_2f0_m4m5_noshield' in line];assert len(devices)==1 and set(devices[0][1:3])=={'P','M'}
    result = {'cell':cell, 'ports':['P','M','VSS'], 'square_size_um':22,
              'magic_drc_count':0, 'drc_style':'drc(full)', 'lvs_unique':True,
              'extraction_feedback':feedback,
              'bbox_um':[int(v)*0.005 for v in re.search(r'BBOX ([-0-9 ]+)',(out/'extraction.log').read_text())[1].split()],
              'gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'actual_source_ports_verified':True,'actual_gds_ports_verified':True,'mos_count':0,'native_mim_count':1,'physical_storage_accepted':False, 'full_chip_accepted':False,
              'scope':'New22um compensation MIM view, actual source/GDS P/M/device connection verified. Separate repaired22um MIM view: explicit M5 top port and M4 bottom rim port; native capacitor geometry/substrate preserved, with tiny top pin paint added. Full MAG DRC/LVS and capacitance extraction; exported GDS connectivity is audited separately. No sampler/storage cell, retention, RPEX, sampled noise or model/service qualification.',
              'sha256':{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='qualification.json'},
              'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in inputs},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
    (out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cell':cell,'drc':0,'lvs_unique':True,'bbox_um':result['bbox_um']}))

if __name__ == '__main__':
    main()
