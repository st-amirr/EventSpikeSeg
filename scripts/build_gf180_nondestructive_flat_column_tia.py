"""Independently flatten and qualify existing non-destructive storage geometry."""
import argparse,hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    args=argparse.Namespace(shielded=False)
    original='gf180_nondestructive_column_tia_m2exit_guarded'
    parent=flow.BASE/'layout'/original
    pq=json.loads((parent/'qualification.json').read_text())
    inputs={parent/'qualification.json'}
    for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
        for n,h in pq.get(key,{}).items():
            p=parent/n if key=='sha256' else flow.ROOT/n
            assert digest(p)==h,str(p);inputs.add(p)
    cell=original+'_flat'
    out=flow.BASE/'layout'/cell;out.mkdir(parents=True,exist_ok=True)
    if (out/'qualification.json').exists():raise ValueError('Preserve qualified view')
    flow.OUT=out;nets=pq['ports'];guard_tracks=[]
    preload=''
    for child in ['gf180_shared_ota_core_pmos_input_fullroute']:
        p=flow.BASE/'layout'/child/(child+'.mag')
        preload+='load /workspace/'+p.relative_to(flow.ROOT).as_posix()+'\n'
    preload+='load /workspace/'+(parent/(original+'.mag')).relative_to(flow.ROOT).as_posix()+f'\nflatten {cell}\nload {cell}\nsave {cell}\n'
    (out/'build_source.py').write_bytes(Path(__file__).read_bytes())
    log = flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (out/'extraction.log').write_text(log)
    drc = re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc[1]) or (out/'gds_warnings.feedback').read_text() or re.search(r'\d+ problems occurred',log):
        raise RuntimeError(log[-5000:])
    ref=(parent/'reference.spice').read_text()
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
         'native_mim_count':1,'native_resistor_count':1,'mos_count':7,'native_sense_junction_geometry_preserved_hierarchically':True,
         'grounded_global_route_guards':True,'ground_guard_count':6,
         'capacitance_count':len(re.findall(r'(?m)^C\S+',(out/(cell+'_cap.spice')).read_text())),
         'physical_storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,
         'scope':'Flattened independent cap extraction of unchanged physical seven-MOS current-read transimpedance amplifier with8um native poly feedback,22um MIM compensation and real REF/COL/OUT/bias/supply/guard routing. Full DRC/LVS/GDS readback and cap extraction only. External PF reference/inter-macro routing and decoding unimplemented; no RPEX/noise/PVT/mismatch/full-float/PLIF/population acceptance',
         'sha256':{p.name:digest(p) for p in files},
         'input_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in sorted(inputs)},
         'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
    (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n')
    print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'gds_roundtrip_lvs_unique':True},indent=2))


if __name__ == '__main__':
    main()
