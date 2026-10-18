"""One native transient covers categorical input truth table and capacitive output loads."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cells=['gf180_dense_and4_v1','gf180_dense_inverter_v1'];files={Path(__file__)};texts=[]
 for cell in cells:
  d=B/'layout'/cell;fq=d/'flat_cap_qualification.json';q=json.loads(fq.read_text());assert q['flat_lvs_unique'] and not q['negative_aggregate_branches']
  for n,h in q['sha256'].items():assert sha(R/n)==h;files.add(R/n)
  files.add(fq);texts.append((d/(cell+'_cap.spice')).read_text())
 stem='gf180_dense_row_logic_truth_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat');models=B/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+models.relative_to(R).as_posix();files.update(models.rglob('*.spice'))
 lines=['Native compact row logic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3']
 for bit,name in enumerate(['A','B','C','EN']):
  pts=['0 0'];prev=0
  for k in range(1,16):
   v=3.3*((k>>bit)&1);t=k*2e-6
   if v!=prev:pts +=[f'{t-1e-8:.12g} {prev}',f'{t:.12g} {v}'];prev=v
  pts+=['32u '+str(prev)];lines +=[f'V{name} {name} 0 PWL('+ ' '.join(pts)+')']
 lines +=['Xand A B C EN Y YB VDD 0 '+cells[0],'Xinv A INV VDD 0 '+cells[1],'Cy Y 0 100f','Cyb YB 0 100f','Ci INV 0 100f','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 32u 0 .05u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' v(Y) v(YB) v(INV)','quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 result=dict(module_simulation_completed=False,native_categorical_logic_observed=False,simulator_returncode=p.returncode,scope='One32us native extracted typical27C/noise-off fixture:16 categorical combinations of3address inputs+command, native NAND4/output inverter plus address inverter;100fF external output load each. Source/GDS fullDRC0/uniqueLVS,all55routing-C branches retained. Boolean operation is control/address only; no analog-state digitization. Stable samples1.8us into2us intervals; no real bank, global service, PVT or chip acceptance.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];result['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==4 and np.isfinite(w).all() and abs(t[-1]-32e-6)<1e-12 and 'aborted' not in log.lower())
  if result['module_simulation_completed']:
   samples=[]
   for k in range(16):
    y,yb,iv=[float(np.interp((k*2+1.8)*1e-6,t,w[:,j])) for j in range(1,4)];expected=k==15;ok=bool((y>3.0 if expected else y<.3) and (yb<.3 if expected else yb>3.) and (iv<.3 if k&1 else iv>3.));samples.append(dict(code=k,Y=y,YB=yb,INV=iv,pass_logic=ok))
   result['samples']=samples;result['native_categorical_logic_observed']=all(x['pass_logic'] for x in samples);result['cases']=[{'sequence':'16 categorical combinations;100fF each output'}]
 except Exception as e:result['postprocess_error']=str(e)
 result['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['sha256','samples']},indent=2));assert result['module_simulation_completed']
if __name__=='__main__':main()
