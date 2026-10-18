"""Audit primary local-beta waveforms and diagnose phase/area limits; no new simulation."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=BASE/'gf180_resident_beta_phase_boundary.json'
    assert not out.exists(), 'Preserve completed audit'
    files={Path(__file__)};cases=[]
    times={'held':19.,'before_beta':19.99,'sharing':20.45,'after':21.5,'final':24.5}
    for mode,n in [('off',1),('on',1),('on',2)]:
        stem=f'gf180_resident_charge_share_beta_{mode}_plates{n}_src493d42582d19'
        rp=BASE/(stem+'.json');d=json.loads(rp.read_text());files.add(rp)
        assert d['simulation_completed'] and d['simulator_returncode']==0
        for name,h in d['sha256'].items():
            q=ROOT/name;assert sha(q)==h,name
        dp=BASE/(stem+'.dat');files.add(dp)
        header=dp.open().readline().split()
        assert header==['time','v(state_low)','v(aux_low)','v(state_mid)','v(aux_mid)','v(state_high)','v(aux_high)']
        w=np.loadtxt(dp,skiprows=1)
        assert w.shape[1]==7 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and w[-1,0]>=25e-6-1e-12
        phase={label:{tag:{node:float(np.interp(t*1e-6,w[:,0],w[:,1+2*i+j])) for j,node in enumerate(['state','aux'])} for i,tag in enumerate(['low','mid','high'])} for label,t in times.items()}
        for label in ['held','sharing','after','final']:
            for tag in ['low','mid','high']:
                for node in ['state','aux']:
                    assert abs(phase[label][tag][node]-d['measurements'][f'{tag}_{node}_{label}'])<6e-6
        x=np.array([phase['held'][t]['state'] for t in ['low','mid','high']]);fits={}
        for label in ['before_beta','sharing','after']:
            y=np.array([phase[label][t]['state'] for t in ['low','mid','high']]);slope=float((y[2]-y[0])/(x[2]-x[0]));intercept=float(y[0]-slope*x[0])
            fits[label]={'endpoint_slope':slope,'offset_about_VCM_v':intercept+(slope-1)*1.65,'midpoint_residual_from_endpoint_line_v':float(y[1]-(slope*x[1]+intercept))}
        shifts={t:{'aux_precharge_release_state_v':phase['before_beta'][t]['state']-phase['held'][t]['state'],'connect_and_share_state_v':phase['sharing'][t]['state']-phase['before_beta'][t]['state'],'beta_release_state_v':phase['after'][t]['state']-phase['sharing'][t]['state'],'late_hold_state_v':phase['final'][t]['state']-phase['after'][t]['state']} for t in ['low','mid','high']}
        cases.append({'report':rp.relative_to(ROOT).as_posix(),'mode':mode,'state_plates':n,'phases_v':phase,'held_to_phase_transfer':fits,'phase_shifts_v':shifts,'finite_primary_waveform':True,'measure_agreement':True})
    bp=BASE/'gf180_executed_float_beta_inventory.json';b=json.loads(bp.read_text());files.add(bp)
    assert b['measurement_completed'] and b['resident_membranes']==30976000 and b['executed_actors']==25
    # A two-point nominal lumped model is a diagnostic extrapolation only.
    r=[(1-c['held_to_phase_transfer']['after']['endpoint_slope'])/c['held_to_phase_transfer']['after']['endpoint_slope'] for c in cases[1:]]
    fixed=(100*r[1]-50*r[0])/(r[0]-r[1]);aux=r[0]*(50+fixed)
    estimates={key:{'target_beta':v,'continuous_state_plate_equivalent':(aux*v/(1-v)-fixed)/50} for key,v in b['neuron_weighted_beta_quantiles'].items()}
    result={'audit_completed':True,'cases':cases,'executed_beta_report':bp.relative_to(ROOT).as_posix(),'diagnostic_lumped_model':{'nominal_plate_fF':50,'fitted_fixed_state_fF':fixed,'fitted_auxiliary_fF':aux,'unverified_quantile_plate_extrapolations':estimates,'scope':'Endpoint fit to two cases, includes switching injection and C(V); not measured capacitance, accepted beta coverage or physical sizing. Do not replicate from this extrapolation.'},'conclusion':'Aux-reset release couples small state error; connect/share introduces positive common offset and beta-release adds state-dependent error. Existing routed switches/auxiliary add capacitance; growing state MIMs alone has adverse density. Diagnose compact physical switch routing before any storage expansion.','acceptance':{'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(out),'audit_completed':True,'fits':[c['held_to_phase_transfer'] for c in cases],'diagnostic_lumped_model':result['diagnostic_lumped_model']},indent=2))
if __name__=='__main__':main()
