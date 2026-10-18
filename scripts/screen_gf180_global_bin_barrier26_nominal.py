"""Native formatted amplitude-times-triangle product voltage characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_global_bin_barrier26_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native26-leaf global bin completion barrier',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vclk clk 0 PULSE(0 3.3 .2u .01u .01u .49u 1u)','Vclear clear 0 PWL(0 3.3 1.99u 3.3 2u 0 34.99u 0 35u 3.3 38.99u 3.3 39u 0 70u 0)','Vdrain drained 0 PWL(0 0 24.99u 0 25u 3.3 33.99u 3.3 34u 0 48.99u 0 49u 3.3 70u 3.3)']
 for i in range(25):
  first=3+i*.2;second=40+i*.2
  lines.append(f'Vactor{i} done{i} 0 PWL(0 0 {first-.01}u 0 {first}u 3.3 33.99u 3.3 34u 0 {second-.01}u 0 {second}u 3.3 70u 3.3)')
 lines +=['Xbarrier clk clear '+' '.join('done'+str(i) for i in range(25))+f' drained complete vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 70u 0 .05u uic','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' v(complete) v(drained) v(clear) v(clk)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native2300MOS25-join binary sticky barrier;25 externally driven actor-completion tokens and one queue-drained token, actual flat extracted source with full long characterization routes. Single hardware instance, two bins with clear interval;1us clock. First all actor tokens arrive by7.8us, queue drained25us; no COMPLETE before drain, eventual complete32us. CLEAR35..39us with old tokens withdrawn34us; second arrivals40..44.8us, drain49us, observe held complete65us. Clock/leaf tokens are external ideal interface stimuli; no actual actor queue drain detection or clock tree/CDC guarantee. No model numeric computation or digital fallback. Spacious characterization geometry is not dense full-chip layout or population5ms proof.','global_barrier_5ms_service_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==5 and np.isfinite(t).all() and abs(t[-1,0]-70e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));times=[1.,20.,24.5,32.,35.5,38.,45.,48.5,58.,65.];r['samples']=[{'time_us':us,'complete_v':sample(1,us),'queue_drained_v':sample(2,us),'clear_v':sample(3,us)} for us in times];low=lambda us:sample(1,us)<.33;high=lambda us:sample(1,us)>2.97;r['all_actor_and_queue_barrier_cases_pass']=bool(all(low(us) for us in [1.,20.,24.5,35.5,38.,45.,48.5]) and all(high(us) for us in [32.,58.,65.]));r['cases']=[{'case':'queue_drain_last_clear_second_bin','barrier_behavior_pass':r['all_actor_and_queue_barrier_cases_pass']}]

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
