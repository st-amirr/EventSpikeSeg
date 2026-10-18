"""Repeat actual native read/restore phases without reinitializing membrane or retuning."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,choices=[0,29],required=True);parser.add_argument('--cycles',type=int,choices=[3,10],default=3);a=parser.parse_args()
 donor=BASE/f'results/gf180_memory_charge_restore_corrected_independent_on_seed{a.seed}_src529813f902c1.json';d=json.loads(donor.read_text());assert d['simulation_completed'];files={Path(__file__),donor}
 for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 original=next(ROOT/n for n in d['sha256'] if n.endswith(f'gf180_memory_charge_restore_corrected_independent_on_seed{a.seed}_src529813f902c1.spice'))
 text=original.read_text().split('.control')[0];end=100*(a.cycles-1)+115
 stem=f'gf180_memory_charge_restore_repeated{a.cycles}_seed{a.seed}_src{sha(Path(__file__))[:12]}';rp=BASE/'results'/(stem+'.json');assert not rp.exists()
 phases={'init':[(0,3.3),(19.99,3.3),(20,0)],'reset':[(0,3.3),(49.99,3.3),(50,0)],'restorereset':[(0,3.3),(59.89,3.3),(59.9,0)],'write':[(0,3.3),(19.97,3.3),(19.98,0)],'outer':[(0,3.3),(19.99,3.3),(20,0)],'midclamp':[(0,0),(20.01,0),(20.02,3.3)],'buspark':[(0,0),(20.03,0),(20.04,3.3)],'restore':[(0,0)],'transfer':[(0,0)]}
 for k in range(a.cycles):
  offset=100*k
  if k:
   phases['reset'] +=[(offset+19.99,0),(offset+20,3.3),(offset+49.99,3.3),(offset+50,0)]
   phases['restorereset'] +=[(offset+19.99,0),(offset+20,3.3),(offset+59.89,3.3),(offset+59.9,0)]
  for phase,edges in {'write':[(60.01,0),(60.02,3.3),(109.97,3.3),(109.98,0)],'outer':[(59.99,0),(60,3.3),(109.99,3.3),(110,0)],'midclamp':[(59.93,3.3),(59.94,0),(110.01,0),(110.02,3.3)],'buspark':[(59.93,3.3),(59.94,0),(110.01,0),(110.02,3.3)],'restore':[(85.03,0),(85.04,3.3),(109.93,3.3),(109.94,0)],'transfer':[(59.95,0),(59.96,3.3),(84.99,3.3),(85,0)]}.items():
   phases[phase]+=[(offset+t,v) for t,v in edges]
 for phase,edges in phases.items():
  edges.append((end,edges[-1][1]));assert all(y[0]>x[0] for x,y in zip(edges,edges[1:]))
  wave='PWL('+' '.join(f'{t:.8g}u {v}' for t,v in edges)+')'
  text,count=re.subn(r'(?m)^V'+phase+r' '+phase+r'_command 0 .*$',f'V{phase} {phase}_command 0 {wave}',text);assert count==1
 lines=['.control','set numdgt=15']
 if a.seed:lines +=[f'setseed {a.seed}','reset']
 lines +=[f'tran .1u {end}u 0 .5u uic']
 for k in range(a.cycles):
  for tag in ['low','mid','high']:
   for label,node,t in [('held','state',59),('restored','state',114),('prerelease','state',109.5),('baseline','out',59),('read','out',84.5),('restore_output','restore_out',84.5)]:
    lines.append(f'meas tran {tag}_c{k}_{label} find v({node}_{tag}) at={100*k+t}u')
 data=BASE/'results'/(stem+'.dat');vectors=[f'v({node}_{tag})' for tag in ['low','mid','high'] for node in ['state','out','sum','bus','restore_out']]
 lines+=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(vectors),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text(text+'\n'+'\n'.join(lines)+'\n',encoding='utf-8');files.add(deck)
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_c[0-9]+_[a-z_]+)\s*=\s*([-+0-9.eE]+)',log)}
 rows=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,16))
 complete=run.returncode==0 and len(values)==18*a.cycles and 'aborted' not in log.lower() and rows.shape[1]==16 and len(rows)>1 and np.isfinite(rows).all() and rows[-1,0]>=end*1e-6-1e-12
 if data.exists():files.add(data)
 summary={}
 if complete:
  for tag in ['low','mid','high']:
   initial=values[tag+'_c0_held'];summary[tag]={'initial_held_v':initial,'cycles':[{'cycle':k,'held_v':values[f'{tag}_c{k}_held'],'restored_v':values[f'{tag}_c{k}_restored'],'restore_error_v':values[f'{tag}_c{k}_restored']-values[f'{tag}_c{k}_held'],'cumulative_change_v':values[f'{tag}_c{k}_restored']-initial} for k in range(a.cycles)]}
 report={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,'settings':vars(a),'measurements':values,'summary':summary,'frozen_reference_v':d['frozen_restore_reference_v'],'coupling_unit_count':d['coupling_unit_count'],'scope':'Repeat native analog read/restore with same physical extracted children, instance hierarchy, frozen ratio/reference and seed. Membrane initialized only once through nativeTG, no .IC/reset or numerical state correction between cycles; each reader/restore AZ resets while memory isolated.100us cycle period,40us initial andabout49us subsequent idle holds; this is accelerated repeated access, not5ms retention or service proof. External phase generator/bias/reference and schematic fractionalMIM/parent, no samplednoise/leakage/RPEX/model/yield/fullchip acceptance. Native state phases per first cycle match donor; compare first cycle before interpreting drift.','acceptance':{'readout':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),'summary':summary},indent=2))
 if not complete:raise RuntimeError(log[-1800:])
if __name__=='__main__':main()
