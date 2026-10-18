"""Three-point low-common-mode readout offset bridge characterization."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 names=['gf180_storage_compute_level_bridge_v1'];files={Path(__file__)};text=[];ports={}
 for cell in names:
  d=B/'layout'/cell;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];files.add(qp);fp=d/'flat_cap_qualification.json';f=json.loads(fp.read_text());assert f['flat_lvs_unique'];files.add(fp);sub=f['flat_subcircuit'];src=d/(sub+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);branches=branches_units(src,sub);assert not any(v< -1e-20 for v in branches.values());text.append(re.sub(r'(?<![A-Za-z0-9_])'+re.escape(sub)+r'(?![A-Za-z0-9_])',cell,src.read_text()));ports[cell]=q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix();stem='gf180_storage_compute_level_bridge_v1_native_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Native replica-feedback inverse membrane read',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vsref SREF 0 1.626','Vcref CREF 0 2.5']
 def instance(label,cell,m):lines.append('X'+label+' '+' '.join(m[p] for p in ports[cell])+' '+cell)
 cell=names[0]
 readouts=[0.1262435095,0.2644610505,0.4144407327]
 for i,target in enumerate(readouts):
  lines +=[f'Vin{i} INPUT{i} 0 PWL(0 {target} 40u {target})',f'Ib{i} BIAS{i} 0 3u',f'Cfixture{i} RETURN{i} 0 100f']
  instance('bridge'+str(i),cell,{'INPUT':f'INPUT{i}','COMPUTE':f'COMPUTE{i}','RETURN':f'RETURN{i}','BIAS':f'BIAS{i}','SREF':'SREF','CREF':'CREF','VDD':'VDD','VSS':'0'})
 nodes=[f'{n}{i}' for i in range(3) for n in ['INPUT','COMPUTE','RETURN']]
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 40u 0 .05u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes),'quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,native_storage_compute_translation_observed=False,simulator_returncode=p.returncode,new_parent_layout_qualified=True,original_float_accuracy_accepted=False,full_chip_layout_complete=False,scope='Existing physical24MOS8R12MIM level bridge tested at three actual GF180 shared-readout points. SREF=1.626V, CREF=2.5V provide a nominal +0.874V analog offset; bridge compute outputs are measured with native OTA/resistor/MIM circuitry and extracted capacitance. This low-input common-mode characterization precedes direct connection to the sequenced injector. Ideal voltage sources drive measured readout points; external 3uA reference and 100fF RETURN load. Typical27C; no mismatch/PVT, model accuracy or5ms acceptance.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==10 and np.isfinite(w).all() and abs(t[-1]-40e-6)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda c:float(np.interp(35e-6,t,w[:,c]));cases=[]
   for i,target in enumerate(readouts):
    forward=sample(2+3*i);back=sample(3+3*i);expected=target+(2.5-1.626);cases.append(dict(readout_input_v=target,compute_target_v=expected,compute_v=forward,forward_error_v=forward-expected,returned_v=back))
   r['cases']=cases;r['max_forward_error_v']=max(abs(c['forward_error_v']) for c in cases);r['native_storage_compute_translation_observed']=bool(r['max_forward_error_v']<.01)

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
