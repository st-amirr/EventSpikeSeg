"""Three native replica-feedback inverse-read trials before new parent layout."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 names=['gf180_analog_commit_hold_buffer_v2'];files={Path(__file__)};text=[];ports={}
 for cell in names:
  d=B/'layout'/cell;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];files.add(qp);fp=d/'flat_cap_qualification.json'
  if fp.exists():
   f=json.loads(fp.read_text());assert f['flat_lvs_unique'];files.add(fp);sub=f['flat_subcircuit'];src=d/(sub+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()]
  else:
   sub=cell;src=d/(cell+'_cap.spice');assert sha(src)==q['sha256'][src.name]
  files.add(src);branches=branches_units(src,sub);assert not any(v< -1e-20 for v in branches.values());text.append(re.sub(r'(?<![A-Za-z0-9_])'+re.escape(sub)+r'(?![A-Za-z0-9_])',cell,src.read_text()));ports[cell]=q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix();stem='gf180_analog_commit_hold_buffer_v2_three5ms_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Native replica-feedback inverse membrane read',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vcm VCM 0 1.2']
 def instance(label,cell,m):lines.append('X'+label+' '+' '.join(m[p] for p in ports[cell])+' '+cell)
 cell=names[0]
 for i,target in enumerate([1.,1.2,1.4]):
  lines +=[f'Vin{i} INPUT{i} 0 PWL(0 {target} 9.9u {target} 10u 0 1999.9u 0 2000u 3.3 3999.9u 3.3 4000u 0 5050u 0)',f'Ip{i} BIAS{i} 0 1u',f'Vw{i} WRITE{i} 0 PWL(0 3.3 4.9u 3.3 5u 0 5050u 0)',f'Vwb{i} WRITEB{i} 0 PWL(0 0 4.9u 0 5u 3.3 5050u 3.3)',f'Cexternal{i} OUT{i} 0 100f']
  instance('hold'+str(i),cell,{'DATA':f'INPUT{i}','WRITE':f'WRITE{i}','WRITEB':f'WRITEB{i}','OUT':f'OUT{i}','BIAS':f'BIAS{i}','VDD':'VDD','VSS':'0'})
 nodes=[f'{n}{i}' for i in range(3) for n in ['INPUT','OUT']]
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 5050u 0 10u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes),'quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,native_analog_output_hold_observed=False,simulator_returncode=p.returncode,new_parent_layout_qualified=True,original_float_accuracy_accepted=False,full_chip_layout_complete=False,scope='Three5.05ms extracted10MOS5MIM analog commit hold-buffer trials at1.0/1.2/1.4V. Actual source/GDS DRC0,LVS,LEF,new flat C branches. Only hold MIM increased50fF to968fF after diagnosed native routing coupling. Native TG releases5us; DATA changes0/3.3V duringhold to expose feedthrough. Real buffered OUT has100fF external representative load, not yet the actual bank column.1uA external reference into native PF diode. Typical27C/noise-off/mismatch disabled. This qualifies one holding output, not eight-output row commit, upstream compute isolation, learned-model precision,5ms whole-population service or full chip.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==7 and np.isfinite(w).all() and abs(t[-1]-5050e-6)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda c,t0:float(np.interp(t0,t,w[:,c]));cases=[]
   for i,target in enumerate([1.,1.2,1.4]):
    c=2+2*i;initial=sample(c,40e-6);end=sample(c,5040e-6);mask=t>=40e-6;cases.append(dict(target_v=target,after_release_buffered_v=initial,release_error_v=initial-target,after5ms_v=end,hold_drift_v=end-initial,max_hold_excursion_v=float(np.max(np.abs(w[mask,c]-initial)))))
   r['cases']=cases;r['max_release_error_v']=max(abs(c['release_error_v']) for c in cases);r['max_hold_excursion_v']=max(c['max_hold_excursion_v'] for c in cases);r['native_analog_output_hold_observed']=bool(r['max_release_error_v']<.05 and r['max_hold_excursion_v']<.02)

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
