"""Native amplitude buffer three-point settling characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_analog_range_clamp_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native threshold mechanism',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcom vcom 0 1.2','Vmin vmin 0 1.26','Vmax vmax 0 1.7','Ireference bias 0 1u','Va a 0 PWL(0 1.22 14.99u 1.22 15u 1.6 29.99u 1.6 30u 1.92 50u 1.92)','Vb b 0 PWL(0 1.2 14.99u 1.2 15u 1.36 29.99u 1.36 30u 1.68 50u 1.68)',f'Xmechanism a vmin vmax output bias vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 50u 0 .02u','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' v(a) v(b) v(output) v(bias)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native27MOS comparator/TG range clamp, actual extracted wiring, typical27C. Three externally buffered input voltages1.22/1.6/1.92V, bounds1.26/1.7V,1uA reference. Output native; no ideal min/max. Illustrative mappingV=1.2+.4*model_value maps default threshold bounds.15/1.25 to1.26/1.7V, not calibrated trained hardware scaling. No near-bound/PVT/output load/model precision/population5ms/full-chip acceptance.','complete_PLIF_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==5 and np.isfinite(t).all() and abs(t[-1,0]-50e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));r['cases']=[]
   for tag,us in [('below_lower_bound',14.5),('within_bounds',29.5),('above_upper_bound',49.5)]:
    a=sample(1,us);b=sample(2,us);target=max(1.26,min(a,1.7));actual=sample(3,us);r['cases'].append({'case':tag,'a_v':a,'b_v':b,'target_v':target,'actual_v':actual,'error_v':actual-target,'bias_v':sample(4,us)})
   r['max_abs_error_v']=max(abs(c['error_v']) for c in r['cases']);r['native_range_clamp_10mv_gate_pass']=r['max_abs_error_v']<.01
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
