"""Replay the completed native cycle with reset internal nodes saved; no circuit changes."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1]; B=R/'artifacts/analog_asic'
def main():
 src=B/'benches/gf180_decoded_shared_compute_tile_v2_native_selected_row_cycle_v1.spice'
 stem='gf180_guarded_tile_reset_internal_diagnosis_v1'; rp=B/'results'/(stem+'.json'); assert not rp.exists()
 deck=B/'benches'/(stem+'.spice'); raw=rp.with_suffix('.raw')
 nodes=['xtile.compute.reset.event.EN','xtile.compute.reset.event.ENB','xtile.compute.reset.event.A','xtile.compute.reset.sink.D','xtile.a_3147880_n88#','C_RESET_PROGRAM','C_NCAS']
 s=src.read_text(); s,n=re.subn(r'(?m)^(\.save .*)$',lambda m:m[1]+' '+' '.join('v('+v+')' for v in nodes),s);assert n==1;deck.write_text(s)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
 lp=rp.with_suffix('.log');lp.write_text(p.stdout+p.stderr);o={'returncode':p.returncode,'circuit_changed':False,'scope':'Same completed230us selected-row cycle; additional reset-node observations only. No fitting, tolerance change, or new circuit.'}
 if raw.exists():
  h,b=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];w=np.frombuffer(b[:len(b)//(8*nv)*(8*nv)],dtype='<f8').reshape(-1,nv);np.savez_compressed(rp.with_suffix('.npz'),waveforms=w,variables=np.array(names));t=w[:,0]
  o['last_time_s']=float(t[-1]);o['completed']=bool(p.returncode==0 and abs(t[-1]-230e-6)<1e-12 and 'aborted' not in (p.stdout+p.stderr).lower());o['reset_epochs_v']={str(us):{n:float(np.interp(us*1e-6,t,w[:,names.index('v('+n.lower()+')')])) for n in nodes+['C_STATE','C_SPIKE','C_PARK','C_RESET']} for us in [109.5,110.5,111,112,116]}
 o['sha256']={x.relative_to(R).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in [Path(__file__),src,deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
if __name__=='__main__':main()
