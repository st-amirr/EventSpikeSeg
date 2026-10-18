"""Repeat fully settled NF local beta including physical auxiliary rearm, without state reset."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=[0,29],required=True);p.add_argument('--state-plates',type=int,choices=[1,2],default=1);a=p.parse_args()
 donor=BASE/f'results/gf180_resident_beta_nf_corrected_seed{a.seed}_on_plates{a.state_plates}_src04f3c11b868c.json';d=json.loads(donor.read_text());assert d['simulation_completed'];files={Path(__file__),donor}
 for name,h in d['sha256'].items():assert sha(ROOT/name)==h,name;files.add(ROOT/name)
 original=next(ROOT/name for name in d['sha256'] if name.endswith(f'gf180_resident_beta_nf_corrected_seed{a.seed}_on_plates{a.state_plates}_src04f3c11b868c.spice'))
 text=original.read_text().split('.control')[0];calpath=BASE/'results/gf180_resident_beta_nf_repeated_boundary.json';cal=json.loads(calpath.read_text());files.add(calpath);newref=cal['predicted_full_cycle_aux_reference_v']
 for name,h in cal['sha256'].items():assert sha(ROOT/name)==h,name;files.add(ROOT/name)
 text,count=re.subn(r'(?m)^Vauxref auxref 0 .*$',f'Vauxref auxref 0 {newref:.16g}',text);assert count==1
 for tag,v in [('low',1.2),('mid',1.65),('high',2.1)]:
  text,count=re.subn(r'(?m)^Vtarget_'+tag+' target_'+tag+r' 0 .*$',f'Vtarget_{tag} target_{tag} 0 {v}',text);assert count==1
 stem=f'gf180_resident_beta_nf_5ms_cadence3_seed{a.seed}_plates{a.state_plates}_src{sha(Path(__file__))[:12]}';rp=BASE/'results'/(stem+'.json');assert not rp.exists()
 phases={'write':[(0,3.3),(9.99,3.3),(10,0)],'auxreset':[(0,3.3)],'beta':[(0,0)]}
 for k in range(3):
  off=5000*k;phases['auxreset'] +=[(off+19.97,3.3),(off+19.98,0),(off+29.99,0),(off+30,3.3)];phases['beta'] +=[(off+19.99,0),(off+20,3.3),(off+20.49,3.3),(off+20.5,0)]
 for phase,edges in phases.items():
  edges.append((15015,edges[-1][1]));assert all(y[0]>x[0] for x,y in zip(edges,edges[1:]))
  wave='PWL('+' '.join(f'{t:.8g}u {v}' for t,v in edges)+')';text,n=re.subn(r'(?m)^V'+phase+r' '+phase+r'_command 0 .*$',f'V{phase} {phase}_command 0 {wave}',text);assert n==1
 lines=['.control','set numdgt=15']
 if a.seed:lines +=[f'setseed {a.seed}','reset']
 lines +=['tran .01u 15015u 0 .5u uic']
 for tag in ['low','mid','high']:
  lines.append(f'meas tran {tag}_released find v(state_{tag}) at=10.5u')
  for k in range(3):
   for node in ['state','aux']:
    for label,t in [('before',19),('sharing',20.45),('after',21.5),('rearmed',31.5),('late',4999.5)]:lines.append(f'meas tran {tag}_c{k}_{node}_{label} find v({node}_{tag}) at={5000*k+t}u')
 data=BASE/'results'/(stem+'.dat');vectors=[f'v({node}_{tag})' for tag in ['low','mid','high'] for node in ['state','aux']]+['v(beta)','v(auxreset)']
 lines +=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(vectors),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text(text+'\n'+'\n'.join(lines)+'\n',encoding='utf-8');files.add(deck)
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp);values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_(?:released|c[0-9]+_[a-z_]+))\s*=\s*([-+0-9.eE]+)',log)}
 rows=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,9));complete=run.returncode==0 and len(values)==93 and rows.shape[1]==9 and len(rows)>1 and np.isfinite(rows).all() and rows[-1,0]>=15015e-6-1e-12 and 'aborted' not in log.lower()
 if data.exists():files.add(data)
 result={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,'settings':vars(a),'measurements':values,'frozen_auxiliary_reference_v':newref,'scope':'One frozen common auxiliary precharge prediction from prior nominal1plate complete-cycle endpoints, now at independent1.2/1.65/2.1V targets for3nativeNF cycles with auxiliary recharge. Full commit is after recharge. State written only once, no per-lane fit/state reset/numerical correction.5000us update period,15015us waveform with nearly5ms native held intervals between completed recharge and next update, qualified children and schematic parent, external references/clocks. No native sampled noise/dielectric leakage/PVT/yield/model/population service qualification; modeled junction leakage only is not physical retention acceptance or completePLIF acceptance. Target/reference changes preclude first-cycle donor waveform equivalence; hierarchy/device provenance preserved.','acceptance':{'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),'final_state_v':{t:values.get(f'{t}_c2_state_late') for t in ['low','mid','high']}},indent=2))
 if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
