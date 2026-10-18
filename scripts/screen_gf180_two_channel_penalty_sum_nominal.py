"""Three native two-channel penalty-current sums."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_two_channel_penalty_sum_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native two-channel penalty sum',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vbase base 0 .9'];cases=[('zero',0.,0.),('one_active',.05,0.),('two_active',.05,.05)];nodes=[]
 for tag,xa,xb in cases:
  for ch,x in [('a',xa),('b',xb)]:
   lines +=[f'Vx_{ch}_{tag} x_{ch}_{tag} 0 PWL(0 0 4.99u 0 5u {x} 20u {x})',f'Vy_{ch}_{tag} y_{ch}_{tag} 0 .05']
   for pin,cx,cy in [('sp',1,1),('sn',-1,-1),('dp',1,-1),('dn',-1,1)]:lines +=[f'E{pin}_{ch}_{tag} {pin}_{ch}_{tag} base POLY(2) x_{ch}_{tag} 0 y_{ch}_{tag} 0 0 {cx} {cy}']
  lines +=[f'Vout_{tag} out_{tag} 0 1.65',f'Xsum_{tag} sp_a_{tag} sn_a_{tag} dp_a_{tag} dn_a_{tag} sp_b_{tag} sn_b_{tag} dp_b_{tag} dn_b_{tag} out_{tag} vdd 0 {cell}'];nodes.append(f'i(Vout_{tag})')
 lines +=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 20u 0 .02u uic','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native12MOS two-channel square-difference product-current sum, actual extracted interconnect, typical27C. Three zero/one/two-active fixtures. Each active channel x=y=.05V; VBASE=.9V, ideal external gate formatting and1.65V OUT compliance fixture. Reports raw summed current and zero-subtracted increments. Not a native linear voltage receiver, resident-buffered full adaptation circuit or actual model channel-count implementation. No model accuracy, full-population5ms or full-chip acceptance.','complete_adaptation_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==4 and np.isfinite(t).all() and abs(t[-1,0]-20e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   currents=[float(-np.interp(19.5e-6,t[:,0],t[:,i+1])) for i in range(3)];offset=currents[0];inc=[v-offset for v in currents];r['cases']=[{'case':tag,'channel_a_x_v':xa,'channel_b_x_v':xb,'each_y_v':.05,'net_sink_current_a':currents[i],'increment_from_zero_a':inc[i]} for i,(tag,xa,xb) in enumerate(cases)];r['zero_input_summed_offset_a']=offset;r['two_to_one_increment_ratio']=float(inc[2]/inc[1]);r['positive_additive_sum_observed']=bool(inc[2]>inc[1]>0 and abs(inc[2]/inc[1]-2)<.02);r['last4p5us_current_change_a']=[float(-np.interp(19.5e-6,t[:,0],t[:,i+1])+np.interp(15e-6,t[:,0],t[:,i+1])) for i in range(3)]
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
