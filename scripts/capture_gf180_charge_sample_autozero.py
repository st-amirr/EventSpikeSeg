"""Instrument the unchanged selected native sample-isolated read/restore circuit."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,choices=[0,29],required=True);a=parser.parse_args()
 donor=BASE/f'results/gf180_memory_charge_sample_corrected_independent_isolate_repeated3_seed{a.seed}_src8f7c9627040a.json';d=json.loads(donor.read_text());assert d['simulation_completed'];files={Path(__file__),donor}
 for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 original=donor.with_suffix('.spice');original=BASE/'benches'/original.name;assert original.relative_to(ROOT).as_posix() in d['sha256']
 text=original.read_text();stem=f'gf180_charge_sample_autozero_seed{a.seed}_src{sha(Path(__file__))[:12]}';rp=BASE/'results'/(stem+'.json');assert not rp.exists()
 data=BASE/'results'/(stem+'.dat');dump=BASE/'results'/(stem+'_instances.txt')
 vectors=[f'v({node}_{tag})' for tag in ['low','mid','high'] for node in ['state','out','sum','bus','restore_out','sampled','azin','restore_sum','restore_azin']]
 text,n=re.subn(r'(?m)^wrdata .*$', 'wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(vectors)+'\nshow all : delvto mulu0 l w > /workspace/'+dump.relative_to(ROOT).as_posix(),text);assert n==1
 deck=BASE/'benches'/(stem+'.spice');deck.write_text(text,encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_c[0-9]+_[a-z_]+)\s*=\s*([-+0-9.eE]+)',log)}
 rows=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,28))
 complete=run.returncode==0 and len(values)==54 and 'aborted' not in log.lower() and rows.shape[1]==28 and len(rows)>1 and np.isfinite(rows).all() and rows[-1,0]>=315e-6-1e-12
 for f in [data,dump]:
  if f.exists():files.add(f)
 maximum_match_error=max((abs(v-d['measurements'][k]) for k,v in values.items()),default=None)
 if complete:assert maximum_match_error<1e-5
 summary={}
 if complete:
  for i,tag in enumerate(['low','mid','high']):
   col=1+9*i;at=lambda t,c:float(np.interp(t*1e-6,rows[:,0],rows[:,c]))
   summary[tag]={'phase_voltages':[{'time_us':t,'state_v':at(t,col),'reader_out_v':at(t,col+1),'reader_sum_v':at(t,col+2),'reader_azin_v':at(t,col+6),'reader_stored_offset_v':at(t,col+6)-at(t,col+2),'restore_out_v':at(t,col+4),'restore_sum_v':at(t,col+7),'restore_azin_v':at(t,col+8),'restore_stored_offset_v':at(t,col+8)-at(t,col+7)} for t in [49.9,50.1,59.8,59.92,60.5,84.5,84.98,85.03,85.5,109.5,114]]}
 report={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,'settings':vars(a),'measurements':values,'maximum_donor_measure_difference_v':maximum_match_error,'summary':summary,'scope':'Instrument-only rerun of selected native3cycle read/restore. Circuit models/device hierarchy/phase waveforms/reference/ratio/seed unchanged; adds AZIN/restoreSUM/restoreAZIN observations and printed nativeinstance parameters. Stored-offset voltages include finite gain, native input offset and switching charge; do not identify all error as intrinsic OTA mismatch. No topology/noise/retention/model/service/layout acceptance change.','acceptance':d['acceptance'],'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),'maximum_donor_measure_difference_v':maximum_match_error},indent=2))
 if not complete:raise RuntimeError(log[-1800:])
if __name__=='__main__':main()
