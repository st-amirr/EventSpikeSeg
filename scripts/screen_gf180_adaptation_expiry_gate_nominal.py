"""Native formatted amplitude-times-triangle product voltage characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_adaptation_expiry_gate_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native analog adaptation expiry and advance gate',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vexpire expire 0 2.0','Vage age 0 PWL(0 1.4 9.99u 1.4 10u 2.2 19.99u 2.2 20u 1.2 30u 1.2)','Vadvance advance 0 PULSE(0 3.3 .2u .01u .01u .49u 1u)','Ireference bias 0 1u',f'Xexpiry age expire advance gated gatedb active expired bias vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 30u 0 .02u','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' v(age) v(active) v(expired) v(gated) v(gatedb)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native18MOS analog AGE<VEXPIRE comparator and advance gate, actual extracted interconnect, typical27C,1uA physical reference. Three wide voltage fixtures: active1.4V, expired2.2V, new-spike reset fixture1.2V;VEXPIRE2.0V,1us advance command clock. Native gate blocks expired age advancement and resumes after age reset. AGE is externally driven for this interface fixture; connected resident initialization/spike/reset/continuous-duration mapping and near-boundary precision remain unqualified. Expired analog age held above2T has zero triangle until next spike, observationally equivalent for frozen inference duration; no digital numeric state or duration rounding. No full adaptation/model/population5ms/full-chip acceptance.','complete_adaptation_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==6 and np.isfinite(t).all() and abs(t[-1,0]-30e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));r['cases']=[]
   for tag,us,enabled in [('active',9.4,True),('expired',19.4,False),('spike_reset_fixture',29.4,True)]:
    active=sample(2,us);expired=sample(3,us);gated=sample(4,us);gatedb=sample(5,us);high=lambda v:v>2.97;low=lambda v:v<.33;passed=(high(active) and low(expired) and high(gated) and low(gatedb)) if enabled else (low(active) and high(expired) and low(gated) and high(gatedb));r['cases'].append({'case':tag,'age_v':sample(1,us),'active_v':active,'expired_v':expired,'gated_advance_high_phase_v':gated,'gated_advanceb_high_phase_v':gatedb,'gated_advance_low_phase_v':sample(4,us+.5),'expiry_gate_fixture_pass':bool(passed and low(sample(4,us+.5)))})
   r['all_analog_expiry_gate_fixtures_pass']=all(c['expiry_gate_fixture_pass'] for c in r['cases'])

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
