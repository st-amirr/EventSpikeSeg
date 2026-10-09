"""Audit native inverse layouts and their actual analog read/restore evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sources={Path(__file__)};layouts=[];runs=[]
    for cell in ['gf180_inverse_resistor_network_123x1','gf180_inverse_amplifier_guarded']:
        directory=BASE/'layout'/cell;p=directory/'qualification.json';q=json.loads(p.read_text());sources.add(p)
        assert q['drc_style']=='drc(full)' and q['magic_drc_count']==q['gds_roundtrip_drc_count']==0
        assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for name,h in q.get(key,{}).items():
                f=directory/name if key=='sha256' else ROOT/name
                assert digest(f)==h,str(f);sources.add(f)
        x1,y1,x2,y2=q['bbox_um']
        layouts.append({'cell':cell,'size_um':[x2-x1,y2-y1],'area_um2':(x2-x1)*(y2-y1),'full_drc_lvs_and_gds_readback_pass':True})
    current=digest(ROOT/'scripts/screen_gf180_analog_read_restore.py')[:12]
    for p in sorted((BASE/'results').glob('gf180_analog_read_restore_inverse1_*_src'+current+'.json')):
        q=json.loads(p.read_text());sources.add(p)
        if not q['settings'].get('combined_inverse'):continue
        for name,h in q['sha256'].items():
            f=ROOT/name;assert digest(f)==h,str(f);sources.add(f)
        assert q['simulation_completed'] and len(q['cases'])==3
        runs.append({'report':p.relative_to(ROOT).as_posix(),'max_step_ns':q['settings']['max_step_ns'],'post_restore_hold_completed':q['post_restore_hold_completed'],
            'round_trip_error_mv':[c['round_trip_error_mv'] for c in q['cases']],
            'restore_acquired_error_mv':[c['restore_acquired_error_mv'] for c in q['cases']],
            'restore_release_step_mv':[c['restore_release_step_mv'] for c in q['cases']]})
    pair={r['max_step_ns']:r for r in runs if not r['post_restore_hold_completed']}
    assert 10 in pair and 20 in pair,'Need matched fine/coarse actual combined-inverse runs'
    reports=[json.loads((ROOT/pair[n]['report']).read_text()) for n in [10,20]]
    decks=[]
    for q in reports:
        paths=[ROOT/p for p in q['sha256'] if p.startswith('artifacts/analog_asic/benches/')]
        assert len(paths)==1
        decks.append(paths[0].read_text())
    assert re.sub(r'(?m)^tran .*$', 'TRAN',decks[0])==re.sub(r'(?m)^tran .*$', 'TRAN',decks[1]),'Convergence decks differ beyond tran'
    difference=max(abs(a['measurements_v'][k]-b['measurements_v'][k]) for a,b in zip(reports[0]['cases'],reports[1]['cases']) for k in a['measurements_v'])
    result={'layouts':layouts,'runs':runs,'matched_10_20ns_decks_equal_except_tran':True,'max_endpoint_difference_uv':difference*1e6,
        'scope':'Actual native combined inverse amplifier with extracted routing, inside schematic module-chain interconnect. Three linear identity storage cases, typical27C only. Numerical comparison is not physical precision. Short held observations equal before-hold89us and establish no retention. No calibrated inverse, nonlinear encoding, complete neuron, noise/mismatch/PVT, original-float accuracy or population5ms/full-chip acceptance.',
        'calibrated_inverse_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
        'next_action':'Implement physical zero/reference calibration for read/capture/inverse/restore, then qualify nonlinear inverse and complete PLIF before array assembly.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    p=BASE/'results/gf180_physical_inverse_boundary.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(p),'runs':runs,'max_endpoint_difference_uv':difference*1e6},indent=2))
if __name__=='__main__':main()
