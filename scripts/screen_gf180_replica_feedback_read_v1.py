"""Three native replica-feedback inverse-read trials before new parent layout."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 names=['gf180_shared_ota_core_pmos_input_fullroute','gf180_pmos_bias_reference_fullroute_v2','gf180_shared_underplate_3t_v2','gf180_mim_5x5_ports_routed','gf180_mim_22x22_ports_routed_v1'];files={Path(__file__)};text=[];ports={}
 for cell in names:
  d=B/'layout'/cell;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];files.add(qp);src=d/(cell+'_cap.spice');assert sha(src)==q['sha256'][src.name];files.add(src);branches=branches_units(src,cell);assert not any(v< -1e-20 for v in branches.values());text.append(src.read_text());ports[cell]=q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix();stem='gf180_replica_feedback_read_three_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Native replica-feedback inverse membrane read',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vcm VCM 0 1.2']
 def instance(label,cell,m):lines.append('X'+label+' '+' '.join(m[p] for p in ports[cell])+' '+cell)
 ota,bias,mem,small,big=names
 for i,target in enumerate([1.,1.2,1.4]):
  lines +=[f'Vin{i} INPUT{i} 0 PWL(0 1.2 1.9u 1.2 2u {target} 20u {target})',f'Ip{i} PBIAS{i} 0 1u',f'In{i} 0 NBIAS{i} 1u',f'Xdiode{i} NBIAS{i} NBIAS{i} 0 0 nfet_03v3 w=.5u l=1u',f'Xload{i} RAW{i} NBIAS{i} 0 0 nfet_03v3 w=.5u l=1u',f'Xrep_load{i} REP{i} NBIAS{i} 0 0 nfet_03v3 w=.5u l=1u']
  instance('memory'+str(i),mem,{'STATE':f'STATE{i}','DATA':f'INPUT{i}','WRITE':'VDD','READ':'VDD','READOUT':f'RAW{i}','VCM':'VCM','VDD':'VDD','VSS':'0'})
  instance('replica'+str(i),mem,{'STATE':f'RECOV{i}','DATA':'0','WRITE':'0','READ':'VDD','READOUT':f'REP{i}','VCM':'VCM','VDD':'VDD','VSS':'0'})
  instance('ota'+str(i),ota,{'IP':f'RAW{i}','IN':f'REP{i}','OUT':f'RECOV{i}','BIAS':f'PBIAS{i}','CMP':f'CMP{i}','VDD':'VDD','VSS':'0'})
  instance('bias'+str(i),bias,{'BIAS':f'PBIAS{i}','VDD':'VDD','VSS':'0'})
  for j,c in enumerate([small,small,big,big]):instance(f'comp{i}_{j}',c,{'P':f'CMP{i}','M':f'RECOV{i}','VSS':'0'})
 nodes=[f'{n}{i}' for i in range(3) for n in ['INPUT','STATE','RAW','REP','RECOV']]
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 20u 0 .05u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes),'quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,native_replica_feedback_reconstruction_observed=False,simulator_returncode=p.returncode,new_parent_layout_qualified=False,original_float_accuracy_accepted=False,full_chip_layout_complete=False,scope='Three20us native circuit feasibility trials at1.0/1.2/1.4V. Actual extracted3T memory and matched replica,7MOS PMOS-input OTA,1MOS bias reference and four native compensation MIMs per trial; three new schematic NFET mirror devices per trial use official models without new layout parasitics. OTA compares actual raw memory source-follower read against replica read and drives replica gate to reconstruct state; no fitted numerical inverse, ADC or ideal output buffer. Memory write remains actively driven throughout this initial trial; not retention/sampled read evidence. Existing child parasitics retained; parent interconnect/column loading and new mirror physical layout absent. Typical27C/noise-off/mismatch disabled; matching/closed-loop stability and actual bank/read phases remain to qualify.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==16 and np.isfinite(w).all() and abs(t[-1]-20e-6)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda c:float(np.interp(19e-6,t,w[:,c]));cases=[]
   for i,target in enumerate([1.,1.2,1.4]):
    offset=5*i;state=sample(offset+2);recover=sample(offset+5);mask=t>15e-6;cases.append(dict(target_v=target,state_v=state,raw_read_v=sample(offset+3),replica_read_v=sample(offset+4),recovered_v=recover,reconstruction_error_v=recover-state,final5us_peak_to_peak_v=float(np.ptp(w[mask,offset+5]))))
   r['cases']=cases;r['max_reconstruction_error_v']=max(abs(c['reconstruction_error_v']) for c in cases);r['native_replica_feedback_reconstruction_observed']=bool(r['max_reconstruction_error_v']<.01 and all(c['final5us_peak_to_peak_v']<.001 for c in cases))
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
