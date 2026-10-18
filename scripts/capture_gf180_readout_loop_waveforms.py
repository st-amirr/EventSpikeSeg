"""Capture native readout loop waveforms from an immutable qualified diagnostic deck."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--donor',required=True);a=p.parse_args();source=Path(__file__);donor=ROOT/a.donor;d=json.loads(donor.read_text());assert d['simulation_completed']
 files={source,donor}
 for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 original=next(ROOT/n for n in d['sha256'] if '/benches/' in n and n.endswith('.spice'))
 stem='gf180_readout_loop_waveforms_'+sha(donor)[:10]+'_src'+sha(source)[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists()
 data=BASE/'results'/(stem+'.dat');deck=BASE/'benches'/(stem+'.spice')
 vectors=[f'v({node}_{level})' for level in ['low','high'] for node in ['column','mirror_gate','refcol','decoded']]
 text=original.read_text();assert text.count('quit\n')==1
 text=text.replace('quit\n','set wr_singlescale\nset wr_vecnames\nwrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(vectors)+'\nquit\n')
 deck.write_text(text,encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(source.read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 rows=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,9));complete=run.returncode==0 and rows.ndim==2 and rows.shape[1]==9 and len(rows)>0 and rows[-1,0]>=.00508 and np.isfinite(rows).all() and 'aborted' not in log.lower()
 if data.exists():files.add(data)
 windows={}
 for title,start,end in [('read_early',5050,5055),('read_late',5070,5074.5)]:
  subset=rows[(rows[:,0]>=start*1e-6)&(rows[:,0]<=end*1e-6)]
  windows[title]={'sample_count':len(subset),'peak_to_peak_v':{v:float(np.ptp(subset[:,i+1])) for i,v in enumerate(vectors)} if len(subset) else {}}
 report={'simulation_completed':bool(complete),'donor':a.donor,'readout_cell':d['readout_cell'],'windows':windows,'scope':'Same immutable model/deck/timing and full extracted modules as donor; only waveform output added. Variable-step raw points, no waveform correction. Low/high clamp-column, PF gate, replica-column and decoded-output observables diagnose coupled loops. Nominal deterministic diagnostic only, no acceptance.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),'windows':windows},indent=2))
 if not complete:raise RuntimeError(log[-1800:])
if __name__=='__main__':main()
