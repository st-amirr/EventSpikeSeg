"""Native amplitude buffer three-point settling characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_class_label_capture_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native class-label capture',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vsample sample 0 PWL(0 0 .49u 0 .5u 3.3 .99u 3.3 1u 0 1.99u 0 2u 3.3 2.49u 3.3 2.5u 0 3.99u 0 4u 3.3 4.49u 3.3 4.5u 0 5.99u 0 6u 3.3 6.49u 3.3 6.5u 0 8u 0)']
 for i in range(6):
  a=3.3 if i==1 else 0;b=3.3 if i==0 else 0;c=3.3 if i==5 else 0
  lines.append(f'Vwin{i} win{i} 0 PWL(0 0 1.19u 0 1.2u {a} 2.99u {a} 3u {b} 4.99u {b} 5u {c} 6.99u {c} 7u 0 8u 0)')
 lines+=['Xcapture sample '+' '.join('win'+str(i) for i in range(6))+' '+' '.join('label'+str(i) for i in range(6))+f' vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .001u 8u 0 .002u uic','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' '+' '.join('v(label'+str(i)+')' for i in range(6)),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native114MOS class-label capture, actual extracted phase generator and six static master/slave DFFs. Initialization sample of known-zero WIN vector, then capture labels1/0/5 on SAMPLE falling, input winner changes during closed-master hold. Categorical output bits only; numeric SNN state/weights remain analog.8us standalone fixture, external one-hot winner and sample commands. Native readout/bank loading and ten-bin record-done controller not connected; tie/model/PVT/population5ms/full-chip acceptance unfinished.','complete_readout_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==7 and np.isfinite(t).all() and abs(t[-1,0]-8e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));correct=lambda values,expected:bool(values[expected]>2.97 and all(v<.33 for i,v in enumerate(values) if i!=expected));r['cases']=[]
   for expected,capture,hold in [(1,2.9,3.5),(0,4.9,5.5),(5,6.9,7.5)]:
    cv=[sample(i+1,capture) for i in range(6)];hv=[sample(i+1,hold) for i in range(6)];r['cases'].append({'case':'capture_and_hold_class'+str(expected),'label_after_capture_v':cv,'label_after_input_changes_v':hv,'capture_pass':correct(cv,expected),'hold_pass':correct(hv,expected)})
   r['native_label_capture_hold_pass']=all(c['capture_pass'] and c['hold_pass'] for c in r['cases'])
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
