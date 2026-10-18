"""Three native replica-feedback inverse-read trials before new parent layout."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 names=['gf180_replica_feedback_reader_v3','gf180_shared_underplate_3t_v2','gf180_nmos_bias_reference_nf05_l1_v1','gf180_source_nf05_l1_compact'];files={Path(__file__)};text=[];ports={}
 for cell in names:
  d=B/'layout'/cell;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];files.add(qp);fp=d/'flat_cap_qualification.json'
  if fp.exists():
   f=json.loads(fp.read_text());assert f['flat_lvs_unique'];files.add(fp);sub=f['flat_subcircuit'];src=d/(sub+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()]
  else:
   sub=cell;src=d/(cell+'_cap.spice');assert sha(src)==q['sha256'][src.name]
  files.add(src);branches=branches_units(src,sub);assert not any(v< -1e-20 for v in branches.values());text.append(re.sub(r'(?<![A-Za-z0-9_])'+re.escape(sub)+r'(?![A-Za-z0-9_])',cell,src.read_text()));ports[cell]=q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix();stem='gf180_replica_feedback_reader_v3_sampled_three_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Native replica-feedback inverse membrane read',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vcm VCM 0 1.2']
 def instance(label,cell,m):lines.append('X'+label+' '+' '.join(m[p] for p in ports[cell])+' '+cell)
 reader,mem,bias,sink=names
 for i,target in enumerate([1.,1.2,1.4]):
  lines +=[f'Vin{i} INPUT{i} 0 {target}',f'Ip{i} PBIAS{i} 0 1u',f'In{i} 0 NBIAS{i} 1u',f'Vw{i} WRITE{i} 0 PWL(0 3.3 4.9u 3.3 5u 0 60u 0)',f'Vr{i} READ{i} 0 PWL(0 0 9.9u 0 10u 3.3 54.9u 3.3 55u 0 60u 0)']
  instance('memory'+str(i),mem,{'STATE':f'STATE{i}','DATA':f'INPUT{i}','WRITE':f'WRITE{i}','READ':f'READ{i}','READOUT':f'RAW{i}','VCM':'VCM','VDD':'VDD','VSS':'0'})
  instance('reader'+str(i),reader,{'RAW':f'RAW{i}','RECOV':f'RECOV{i}','NBIAS':f'NBIAS{i}','PBIAS':f'PBIAS{i}','READ_EN':f'READ{i}','VCM':'VCM','VDD':'VDD','VSS':'0'})
  instance('bias'+str(i),bias,{'BIAS':f'NBIAS{i}','VSS':'0'})
  instance('load'+str(i),sink,{'D':f'RAW{i}','G':f'NBIAS{i}','S':'0','VSS':'0'})
 nodes=[f'{n}{i}' for i in range(3) for n in ['INPUT','STATE','RAW','READ','RECOV']]
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 60u 0 .1u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes),'quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,native_replica_feedback_reconstruction_observed=False,simulator_returncode=p.returncode,new_parent_layout_qualified=True,original_float_accuracy_accepted=False,full_chip_layout_complete=False,scope='Three60us native sampled read trials using actual flat12MOS5MIM reader with58 interconnect C branches and real source/GDS DRC0/LVS/LEF. Source-qualified extracted3T memory, native diode NF reference and native NF read sink fixtures. Write releases5us; both actual and replica read select10..55us; reconstruct at50us. Numerical membrane stays analog. No fitted inverse, ideal readout buffer, integer DAC or QAT. Typical27C/noise-off/mismatch disabled; current refs and categorical control/data external. New reader parent physical qualification complete, but separately composed memory fixture wiring has no new physical layout. Shared bank loading, PVT/mismatch, connected compute/global service remain incomplete.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==16 and np.isfinite(w).all() and abs(t[-1]-60e-6)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda c:float(np.interp(50e-6,t,w[:,c]));cases=[]
   for i,target in enumerate([1.,1.2,1.4]):
    offset=5*i;state=sample(offset+2);recover=sample(offset+5);mask=(t>45e-6)&(t<54e-6);cases.append(dict(target_v=target,state_v=state,raw_read_v=sample(offset+3),read_enable_v=sample(offset+4),recovered_v=recover,reconstruction_error_v=recover-state,final9us_peak_to_peak_v=float(np.ptp(w[mask,offset+5]))))
   r['cases']=cases;r['max_reconstruction_error_v']=max(abs(c['reconstruction_error_v']) for c in cases);r['native_replica_feedback_reconstruction_observed']=bool(r['max_reconstruction_error_v']<.01 and all(c['final9us_peak_to_peak_v']<.001 for c in cases))
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
