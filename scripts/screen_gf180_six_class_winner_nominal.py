"""Native amplitude buffer three-point settling characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_six_class_winner_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 scores=[[1.4,1.7,1.3,1.5,1.45,1.65],[1.6,1.2,1.3,1.4,1.45,1.5],[1.5,1.3,1.4,1.2,1.55,1.7]]
 lines=['Native six-class winner selector',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Ireference bias 0 1u']
 for i in range(6):lines.append(f'Vclass{i} class{i} 0 PWL(0 {scores[0][i]} 49.99u {scores[0][i]} 50u {scores[1][i]} 99.99u {scores[1][i]} 100u {scores[2][i]} 150u {scores[2][i]})')
 lines +=['Xwinner '+' '.join('class'+str(i) for i in range(6))+' '+' '.join('win'+str(i) for i in range(6))+f' bias vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 150u 0 .05u','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' '+' '.join('v(win'+str(i)+')' for i in range(6)),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native280MOS six-class one-hot analog-score winner selector, actual extracted comparators/complements/AND gates and wiring, typical27C. Three external buffered score fixtures with strict separated maxima atclasses1/0/5; external1uA master. Native WIN logic outputs, no ideal comparison/argmax inside circuit. Scores are illustrative voltages, not actual trained readout. Exact/near tie handling, lowest-index tie contract, native class-bank loading, record-done capture andPVT/noise/model precision/population5ms/full-chip acceptance unqualified. Categorical output logic does not quantize analog numerical state.','complete_readout_accepted':False,'exact_tie_behavior_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==7 and np.isfinite(t).all() and abs(t[-1,0]-150e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));r['cases']=[]
   for i,us in enumerate([49.5,99.5,149.5]):
    expected=int(np.argmax(scores[i]));v=[sample(j+1,us) for j in range(6)];r['cases'].append({'case':'winner_class'+str(expected),'score_voltages_v':scores[i],'expected_class':expected,'native_win_voltages_v':v,'one_hot_correct':bool(v[expected]>2.97 and all(x<.33 for j,x in enumerate(v) if j!=expected))})
   r['native_one_hot_winner_cases_pass']=all(c['one_hot_correct'] for c in r['cases'])
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
