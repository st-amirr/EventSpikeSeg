"""Three native replica-feedback inverse-read trials before new parent layout."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 names=['gf180_candidate_penalty_subtractor_v2'];files={Path(__file__)};text=[];ports={}
 for cell in names:
  d=B/'layout'/cell;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];files.add(qp);fp=d/'flat_cap_qualification.json';f=json.loads(fp.read_text());assert f['flat_lvs_unique'];files.add(fp);sub=f['flat_subcircuit'];src=d/(sub+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);branches=branches_units(src,sub);assert not any(v< -1e-20 for v in branches.values());text.append(re.sub(r'(?<![A-Za-z0-9_])'+re.escape(sub)+r'(?![A-Za-z0-9_])',cell,src.read_text()));ports[cell]=q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix();stem='gf180_storage_compute_level_contract_v1_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Native replica-feedback inverse membrane read',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vsref SREF 0 1.2','Vcref CREF 0 1.65']
 def instance(label,cell,m):lines.append('X'+label+' '+' '.join(m[p] for p in ports[cell])+' '+cell)
 cell=names[0]
 for i,target in enumerate([1.,1.2,1.4]):
  lines +=[f'Vin{i} INPUT{i} 0 PWL(0 1.2 1.9u 1.2 2u {target} 40u {target})',f'Ib{i} BIAS{i} 0 2u',f'Cfixture{i} RETURN{i} 0 100f']
  instance('forward'+str(i),cell,{'CANDIDATE':f'INPUT{i}','PENALTY':'SREF','VCOM':'CREF','ADJUSTED':f'COMPUTE{i}','BIAS':f'BIAS{i}','VDD':'VDD','VSS':'0'})
  instance('reverse'+str(i),cell,{'CANDIDATE':f'COMPUTE{i}','PENALTY':'CREF','VCOM':'SREF','ADJUSTED':f'RETURN{i}','BIAS':f'BIAS{i}','VDD':'VDD','VSS':'0'})
 nodes=[f'{n}{i}' for i in range(3) for n in ['INPUT','COMPUTE','RETURN']]
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 40u 0 .05u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes),'quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,native_storage_compute_translation_observed=False,simulator_returncode=p.returncode,new_parent_layout_qualified=False,original_float_accuracy_accepted=False,full_chip_layout_complete=False,scope='Three40us native bidirectional storage/compute common-mode trials. Two separately qualified8MOS4R4MIM subtractors per trial perform forwardCOMPUTE=STORAGE-1.2+1.65 and reverseRETURN=COMPUTE-1.65+1.2. Six actual flat extracted physical cells, no ideal arithmetic or digital conversion. External analog sources at1.0/1.2/1.4V,100fF return loads and2uA master for two native PF references per trial. This explicit affine voltage-domain interface preserves unit voltage scale and zero offsets for original-float mapping; learned channel scaling and original-v6 beta/threshold precision are not established. Intermodule wiring remains schematic here; physically joined tile with actual reader,compute-state isolation,hold/writeback loading remains to qualify. Typical27C/noise/mismatch off; no full-chip/service/model precision claim.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==10 and np.isfinite(w).all() and abs(t[-1]-40e-6)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda c:float(np.interp(35e-6,t,w[:,c]));cases=[]
   for i,target in enumerate([1.,1.2,1.4]):
    forward=sample(2+3*i);back=sample(3+3*i);cases.append(dict(storage_v=target,compute_target_v=target+.45,compute_v=forward,forward_error_v=forward-target-.45,returned_v=back,roundtrip_error_v=back-target))
   r['cases']=cases;r['max_forward_error_v']=max(abs(c['forward_error_v']) for c in cases);r['max_roundtrip_error_v']=max(abs(c['roundtrip_error_v']) for c in cases);r['native_storage_compute_translation_observed']=bool(r['max_forward_error_v']<.01 and r['max_roundtrip_error_v']<.01)

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
