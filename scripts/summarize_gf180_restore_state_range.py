"""Audit physical state-range errors; fitted curves are diagnostic only."""
import hashlib,json,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sources={Path(__file__)};runs=[];loaded=[];points=[]
    current=digest(ROOT/'scripts/screen_gf180_restore_state_range.py')[:12]
    for p in sorted((BASE/'results').glob('gf180_restore_state_range_inverse1_*_src'+current+'.json')):
        q=json.loads(p.read_text());sources.add(p)
        for name,h in q['sha256'].items():
            f=ROOT/name;assert digest(f)==h,str(f);sources.add(f)
        assert q['simulation_completed'] and len(q['cases'])==3 and q['dedicated_zero_case']
        assert q['native_gain_trim'] and q['combined_zero_reference_buffer']
        errors=[c['round_trip_error_mv'] for c in q['cases']]
        runs.append({'report':p.relative_to(ROOT).as_posix(),'max_step_ns':q['settings']['max_step_ns'],'state_band':q['state_band'],
            'round_trip_error_mv':errors,'maximum_absolute_three_case_error_mv':max(map(abs,errors))})
        loaded.append(q)
        if q['settings']['max_step_ns']==20:
            for c in q['cases']:
                points.append({'band':q['state_band'],'target_v':c['target_v'],'before_read_differential_v':c['measurements_v']['stored_before_read'],
                    'round_trip_error_mv':c['round_trip_error_mv'],'restore_acquired_error_mv':c['restore_acquired_error_mv'],
                    'restore_release_step_mv':c['restore_release_step_mv']})
    coarse={r['state_band']:(r,q) for r,q in zip(runs,loaded) if r['max_step_ns']==20}
    assert all(n in coarse for n in ['lower','middle','upper'])
    worst=max(coarse,key=lambda n:coarse[n][0]['maximum_absolute_three_case_error_mv'])
    fine_pairs=[(r,q) for r,q in zip(runs,loaded) if r['state_band']==worst and r['max_step_ns']==10]
    assert len(fine_pairs)==1,'Need matched fine-step evidence for largest-error band'
    fine=fine_pairs[0][1];coarse_q=coarse[worst][1];decks=[]
    for q in [fine,coarse_q]:
        paths=[ROOT/p for p in q['sha256'] if p.startswith('artifacts/analog_asic/benches/')];assert len(paths)==1
        decks.append(paths[0].read_text())
    assert re.sub(r'(?m)^tran .*$', 'TRAN',decks[0])==re.sub(r'(?m)^tran .*$', 'TRAN',decks[1])
    cases_a=fine['cases']+[fine['dedicated_zero_case']];cases_b=coarse_q['cases']+[coarse_q['dedicated_zero_case']]
    difference=max(abs(a['measurements_v'][k]-b['measurements_v'][k]) for a,b in zip(cases_a,cases_b) for k in a['measurements_v'])
    convergence={worst:{'decks_equal_except_tran':True,'max_312_endpoint_difference_uv':difference*1e6}}
    for r,q in zip(runs,loaded):
        if r['max_step_ns']!=10 or r['state_band']==worst:continue
        other=coarse[r['state_band']][1];other_decks=[]
        for report in [q,other]:
            paths=[ROOT/p for p in report['sha256'] if p.startswith('artifacts/analog_asic/benches/')];assert len(paths)==1
            other_decks.append(paths[0].read_text())
        assert re.sub(r'(?m)^tran .*$', 'TRAN',other_decks[0])==re.sub(r'(?m)^tran .*$', 'TRAN',other_decks[1])
        a_cases=q['cases']+[q['dedicated_zero_case']];b_cases=other['cases']+[other['dedicated_zero_case']]
        delta=max(abs(a['measurements_v'][k]-b['measurements_v'][k]) for a,b in zip(a_cases,b_cases) for k in a['measurements_v'])
        convergence[r['state_band']]={'decks_equal_except_tran':True,'max_312_endpoint_difference_uv':delta*1e6}
    x=np.array([p['before_read_differential_v'] for p in points]);err=np.array([p['round_trip_error_mv'] for p in points])
    fits={}
    for degree in [1,2]:
        c=np.polyfit(x,err,degree);res=err-np.polyval(c,x)
        fits[str(degree)]={'coefficients_descending_error_mv_vs_actual_state_v':c.tolist(),'maximum_residual_mv':float(np.max(np.abs(res))),
            'scope':'Mathematical diagnostic of measured error only; no physical correction or corrected neural state.'}
    anchors={}
    for target in [1.35,1.95]:
        a=[p['round_trip_error_mv'] for p in points if p['target_v']==target];assert len(a)==2
        anchors[str(target)]={'errors_mv':a,'span_uv':(max(a)-min(a))*1000}
    result={'runs':runs,'coarse_points':sorted(points,key=lambda p:p['target_v']),'overlap_anchors':anchors,'diagnostic_error_fits':fits,
        'largest_error_band':worst,'fine_convergence_scope':'Matched convergence for bands in convergence_by_band; other bands coarse20ns only',
        'convergence_by_band':convergence,
        'bands_with_fine_reports':[r['state_band'] for r in runs if r['max_step_ns']==10],
        'same_band_10_20ns_decks_match_except_tran':True,'max_312_endpoint_difference_uv':difference*1e6,
        'scope':'Seven nominal initialized voltages in overlapping three-case bands with dedicated physical zero-reference path and real extracted clock loading. Changing data context can change calibration/clock behavior; repeated anchors expose this. Native typical27C only. Fitted affine/quadratic curves are diagnostics, not applied corrections, implemented inverse or precision acceptance. No range/PVT/noise/mismatch/RPEX/gate-leakage/neural/service qualification. Macro-to-macro interconnect remains schematic. Short held/before-hold89us coincide and prove no retention.',
        'calibrated_state_preservation_accepted':False,'nonlinear_inverse_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
        'next_action':'Implement physical compensation using measured curvature and context sensitivity; then nonlinear inverse, complete PLIF/model/service/layout.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    p=BASE/'results/gf180_restore_state_range_boundary.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(p),'runs':runs,'anchors':anchors,'diagnostic_fits':fits,'largest_error_band':worst,'max_endpoint_difference_uv':difference*1e6},indent=2))
if __name__=='__main__':main()
