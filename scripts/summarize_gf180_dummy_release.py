"""Audit physical full-top-dummy release compensation and whole-cycle error."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sources={Path(__file__)};runs=[];loaded=[]
    cell='gf180_compensated_bottom_sampler_full_top_dummy_shielded';directory=BASE/'layout'/cell
    p=directory/'qualification.json';q=json.loads(p.read_text());sources.add(p)
    assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['drc_style']=='drc(full)'
    assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
    for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
        for name,h in q.get(key,{}).items():
            f=directory/name if key=='sha256' else ROOT/name;assert digest(f)==h,str(f);sources.add(f)
    current=digest(ROOT/'scripts/screen_gf180_dummy_release_restore.py')[:12]
    for p in sorted((BASE/'results').glob('gf180_dummy_release_restore_inverse1_*.json')):
        q=json.loads(p.read_text());sources.add(p)
        for name,h in q['sha256'].items():
            f=ROOT/name;assert digest(f)==h,str(f);sources.add(f)
        assert q['simulation_completed'] and len(q['cases'])==3 and q['dedicated_zero_case']
        runs.append({'report':p.relative_to(ROOT).as_posix(),'source_sha12':p.stem.split('_src')[-1],
            'max_step_ns':q['settings']['max_step_ns'],'zero_reference':q['zero_reference_enabled'],
            'combined_zero_reference':q.get('combined_zero_reference_buffer',False),'native_gain_trim':q['native_gain_trim'],'full_top_dummy':q['full_top_dummy'],'nominal_inverse_gain_magnitude':q['nominal_inverse_gain_magnitude'],
            'round_trip_error_mv':[c['round_trip_error_mv'] for c in q['cases']],
            'zero_reference_measurements_v':q['zero_reference_measurements_v']})
        loaded.append(q)
    pair={r['max_step_ns']:(r,q) for r,q in zip(runs,loaded) if r['source_sha12']==current and r['combined_zero_reference'] and r['native_gain_trim'] and r['full_top_dummy']}
    assert 10 in pair and 20 in pair,'Need matched combined-reference10/20ns runs'
    fine,coarse=pair[10][1],pair[20][1]
    decks=[]
    for q in [fine,coarse]:
        paths=[ROOT/p for p in q['sha256'] if p.startswith('artifacts/analog_asic/benches/')];assert len(paths)==1
        decks.append(paths[0].read_text())
    assert re.sub(r'(?m)^tran .*$', 'TRAN',decks[0])==re.sub(r'(?m)^tran .*$', 'TRAN',decks[1])
    cases_a=fine['cases']+[fine['dedicated_zero_case']];cases_b=coarse['cases']+[coarse['dedicated_zero_case']]
    difference=max(abs(a['measurements_v'][k]-b['measurements_v'][k]) for a,b in zip(cases_a,cases_b) for k in a['measurements_v'])
    result={'cell':cell,'runs':runs,'same_source_10_20ns_decks_match_except_tran':True,'max_312_endpoint_difference_uv':difference*1e6,
        'scope':'Full-size opposite-clock top dummy changes initial acquisition, effective read capacitance/gain, release behavior and actual clock loading. A smaller release step alone does not prove better state preservation. Dedicated independent known-zero sampler/reader/capture feeds implemented native zero-buffer/divider. Nominal common read/capture offset compensation is physical circuit behavior, with no ideal numeric state correction. All macro-to-macro/clock interconnect remains schematic. Fourth path adds real clock loading and consumes service/resources. Native typical27C model only; no mismatch/noise/PVT/RPEX/gate leakage qualification. Native fixed gain495/123 is implemented with one123um input and series123+123+123+126um feedback. Existing reference divider retains4/5. This nominal gain adjustment is not per-die calibration or nonlinear inverse; gain/reference-state error and signal-dependent acquisition/release remain. Short89us held and before-hold observations coincide and prove no retention.',
        'full_top_dummy_selected':False,'calibrated_state_preservation_accepted':False,'nonlinear_inverse_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
        'next_action':'Retain half-top dummy as current reference; explore bottom/top release timing and range-dependent compensation with actual read/restore gain remeasurement, then nonlinear inverse and complete PLIF/model/service assembly.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    p=BASE/'results/gf180_dummy_release_boundary.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(p),'runs':runs,'max_312_endpoint_difference_uv':difference*1e6},indent=2))
if __name__=='__main__':main()
