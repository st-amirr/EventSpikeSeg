"""Audit simultaneous and reversed plate release against whole-cycle error."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sources={Path(__file__)};runs=[];loaded=[]
    current=digest(ROOT/'scripts/screen_gf180_release_order_restore.py')[:12]
    for p in sorted((BASE/'results').glob('gf180_release_order_restore_inverse1_*_src'+current+'.json')):
        q=json.loads(p.read_text());sources.add(p)
        for name,h in q['sha256'].items():
            f=ROOT/name;assert digest(f)==h,str(f);sources.add(f)
        assert q['simulation_completed'] and len(q['cases'])==3 and q['dedicated_zero_case']
        assert q['native_gain_trim'] and q['combined_zero_reference_buffer']
        errors=[c['round_trip_error_mv'] for c in q['cases']]
        runs.append({'report':p.relative_to(ROOT).as_posix(),'max_step_ns':q['settings']['max_step_ns'],
            'commanded_bottom_lead_ns':q['commanded_bottom_lead_ns'],'round_trip_error_mv':errors,
            'maximum_absolute_three_case_error_mv':max(map(abs,errors)),
            'restore_acquired_error_mv':[c['restore_acquired_error_mv'] for c in q['cases']],
            'restore_release_step_mv':[c['restore_release_step_mv'] for c in q['cases']]})
        loaded.append(q)
    coarse={r['commanded_bottom_lead_ns']:(r,q) for r,q in zip(runs,loaded) if r['max_step_ns']==20}
    assert all(n in coarse for n in [-20,0,20]),'Need all three bounded timing comparisons'
    best=min(coarse,key=lambda n:coarse[n][0]['maximum_absolute_three_case_error_mv'])
    fine_pairs=[(r,q) for r,q in zip(runs,loaded) if r['commanded_bottom_lead_ns']==best and r['max_step_ns']==10]
    reused_fine_report=False
    if not fine_pairs and best==20:
        # Previous bottom-first fixture is reusable only after exact deck proof.
        bp=BASE/'results/gf180_release_timing_boundary.json'
        boundary=json.loads(bp.read_text());sources.add(bp)
        for name,h in boundary['sha256'].items():
            f=ROOT/name;assert digest(f)==h,str(f);sources.add(f)
        prior=[r for r in boundary['runs'] if r['commanded_bottom_lead_ns']==20 and r['max_step_ns']==10]
        assert len(prior)==1
        p=ROOT/prior[0]['report'];q=json.loads(p.read_text());sources.add(p)
        assert q['simulation_completed'] and len(q['cases'])==3 and q['dedicated_zero_case']
        for name,h in q['sha256'].items():
            f=ROOT/name;assert digest(f)==h,str(f);sources.add(f)
        runs.append(prior[0]);fine_pairs=[(prior[0],q)];reused_fine_report=True
    assert len(fine_pairs)==1,'Need matched fine-step evidence for best measured timing'
    fine=fine_pairs[0][1];coarse_q=coarse[best][1]
    decks=[]
    for q in [fine,coarse_q]:
        paths=[ROOT/p for p in q['sha256'] if p.startswith('artifacts/analog_asic/benches/')];assert len(paths)==1
        decks.append(paths[0].read_text())
    assert re.sub(r'(?m)^tran .*$', 'TRAN',decks[0])==re.sub(r'(?m)^tran .*$', 'TRAN',decks[1])
    cases_a=fine['cases']+[fine['dedicated_zero_case']];cases_b=coarse_q['cases']+[coarse_q['dedicated_zero_case']]
    difference=max(abs(a['measurements_v'][k]-b['measurements_v'][k]) for a,b in zip(cases_a,cases_b) for k in a['measurements_v'])
    result={'runs':runs,'best_measured_three_case_commanded_lead_ns':best,'same_lead_fine_coarse_decks_match_except_tran':True,
        'fine_report_reused_after_exact_deck_and_provenance_check':reused_fine_report,
        'max_312_endpoint_difference_uv':difference*1e6,
        'scope':'Three signed commanded bottom/top lead times (-20 top first,0 simultaneous,+20 bottom first) in native-cap-extracted module chain, typical27C only. Both initial acquisition and restore change. Actual extracted inverters/load determine electrical edges; command separation is not measured electrical nonoverlap or a qualified sequencer. Acquired samples precede the first plate command edge and differ in timestamp across lead settings. Best of three nominal state cases is not range/model/service/PVT/noise/mismatch acceptance. Macro-to-macro/clock/restore interconnect remains schematic. No numeric state correction or new physical layout. Short held/before-hold89us coincide and establish no retention.',
        'calibrated_state_preservation_accepted':False,'nonlinear_inverse_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
        'next_action':'Use evidence to correct range-dependent restore error and integrate physical nonlinear inverse, complete PLIF/model/service and layout.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    p=BASE/'results/gf180_release_order_boundary.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(p),'runs':runs,'best_lead_ns':best,'max_312_endpoint_difference_uv':difference*1e6},indent=2))
if __name__=='__main__':main()
