"""Three small native extracted mirror cases: startup and drain compliance."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 idx=int(sys.argv[1]);assert idx in [0,1,2];iref=[1e-9,1e-8,1e-7][idx];cell='gf180_shared_bias_mirror_v1';folder=BASE/'layout'/cell;fqpath=folder/'flat_cap_qualification.json';qp=folder/'qualification.json';fq=json.loads(fqpath.read_text());q=json.loads(qp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and fq['flat_lvs_unique'] and not fq['negative_aggregate_branches'];files={Path(__file__),qp,fqpath}
 for n,h in fq['sha256'].items():
  pp=ROOT/n
  if pp.suffix!='.ext':assert sha(pp)==h,n
  files.add(pp)
 flat=folder/(fq['flat_subcircuit']+'_cap.spice');txt=flat.read_text().replace(fq['flat_subcircuit'],cell);files.add(flat)
 model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=f'{cell}_nominal_case{idx}_src{sha(Path(__file__))[:12]}';rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_startup.dat')
 vectors='v(pbias) v(nbias) i(Vpm1) i(Vpm2) i(Vnm1) i(Vnm2)'
 lines=['Native shared master-current mirror',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',txt,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3',f'Ip pbias 0 {iref}',f'In 0 nbias {iref}','Vdrain drain 0 1.65','Vpm1 pm1 drain 0','Vpm2 pm2 drain 0','Vnm1 nm1 drain 0','Vnm2 nm2 drain 0',f'Xmirror pbias nbias pm1 pm2 nm1 nm2 vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','dc Vdrain .2 3.1 .1','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' '+vectors,'reset','tran .1u 100u 0 .1u uic','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' '+vectors,'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'reference_current_a':iref,'scope':'Native6MOS mirror,23 flat nonnegative capacitance branches. External ideal master reference currents and ideal output-drain voltage fixtures. Three current points at typical27C; nominal direction/finite startup checks only. Current ratio vs drain voltage reported without unity-gain acceptance. No real load fanout, master-reference generator, noise/mismatch/PVT, analog calibration or5ms/full-chip acceptance.'}
 try:
  d=np.loadtxt(dp,skiprows=1);t=np.loadtxt(tp,skiprows=1);files.update([dp,tp]);ok=bool(run.returncode==0 and d.shape==(30,7) and t.shape[1]==7 and np.isfinite(d).all() and np.isfinite(t).all() and abs(t[-1,0]-100e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   ratios=d[:,3:]/iref;final=t[-1,1:];r['dc_compliance']={'drain_voltages_v':d[:,0].tolist(),'pm1_ratio':ratios[:,0].tolist(),'pm2_ratio':ratios[:,1].tolist(),'nm1_ratio':(-ratios[:,2]).tolist(),'nm2_ratio':(-ratios[:,3]).tolist()};r['startup_at100us']={'pbias_v':float(final[0]),'nbias_v':float(final[1]),'pm1_ratio':float(final[2]/iref),'pm2_ratio':float(final[3]/iref),'nm1_ratio':float(-final[4]/iref),'nm2_ratio':float(-final[5]/iref)};r['nominal_direction_and_startup_pass']=bool(0<final[0]<3.3 and 0<final[1]<3.3 and all(final[2:4]>0) and all(final[4:6]<0) and all(d[:,3:5].ravel()>0) and all(d[:,5:7].ravel()<0))
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k not in ['sha256','dc_compliance']}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
