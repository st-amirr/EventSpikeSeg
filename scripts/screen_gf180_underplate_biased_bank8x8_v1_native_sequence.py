"""One connected native bank sequence: selective overwrite,5ms hold and two-row read."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_underplate_biased_bank8x8_v1';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text())
 assert q['magic_drc_count']==0 and q['gds_roundtrip_drc_count']==0 and f['flat_lvs_unique'] and not f['negative_aggregate_branches']
 files={Path(__file__),qp,fp};src=d/(cell+'_cap.spice')
 for n,h in f['sha256'].items():assert sha(R/n)==h,n;files.add(R/n)
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix()
 stem=cell+'_native_select_write_hold_read_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();data=rp.with_suffix('.dat')
 lines=['Native shared-row/shared-column analog memory bank',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcom VCM 0 1.2']
 for row,stop in [(r,20e-6 if r==7 else 1e-6) for r in range(8)]:
  lines +=[f'Vw{row} WRITE{row} 0 PWL(0 3.3 {stop-1e-7} 3.3 {stop} 0 5.2m 0)']
 for row,start in [(r,5.13e-3 if r==7 else 5.03e-3) for r in range(8)]:
  if row not in [0,7]:lines +=[f'Vr{row} READ{row} 0 0'];continue
  lines +=[f'Vr{row} READ{row} 0 PWL(0 0 {start-1e-6} 0 {start} 3.3 {start+49e-6} 3.3 {start+50e-6} 0 5.2m 0)']
 for col,initial,target in [(c,1.+.05*c,1.4-.03*c) for c in range(8)]:
  lines +=[f'Vd{col} DATA{col} 0 PWL(0 {initial} 9u {initial} 10u {target} 1.999m {target} 2m 0 3.999m 0 4m 3.3 5.2m 3.3)']
 lines +=['Ireference 0 BIAS PWL(0 0 5.031m 0 5.032m 1u 5.077m 1u 5.078m 0 5.131m 0 5.132m 1u 5.177m 1u 5.178m 0 5.2m 0)']
 lines +=['Xbank '+' '.join(q['ports'])+' '+cell]
 nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+[f'READOUT{c}' for c in range(8)]
 lines +=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 5.2m 0 10u','wrdata /workspace/'+data.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
 log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_shared_bank_sequence_observed=False,full_chip_layout_complete=False,full_5ms_population_service_accepted=False,original_float_accuracy_accepted=False,
  scope='One actual201MOS/64MIM8x8 shared-row/shared-column bank with all native nonnegative routing-cap branches. All64 states initialized through native single-NFET write access; rows0-6 held while row7 is overwritten on shared DATA columns, then each state held at least5ms with DATA rail stress. Sequential native source-follower reads of rows0and7; six middle rows remain unselected. All64 analog states and8 read columns recorded; no ideal output buffer. External ideal references/wordlines/data and one gated1uA master-reference fixture driving actual9MOS shared column-current mirror. Typical27C/noise disabled. 100ns external write-wordline slew, matching the completed3T bank sequence. Transistors occupy lower layers under MIM. Source-follower offset uncalibrated. Native8column sinks and1diode master included. No decoder/write-driver geometry, trained beta, threshold/RMS, large-array loading, population service, accuracy or fullchip acceptance.')
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);t=w[:,0]
  r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==74 and np.isfinite(w).all() and abs(t[-1]-5.2e-3)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda k,s:float(np.interp(s,t,w[:,k]));states=[]
   for j in range(64):
    row=j//8;col=j%8;target=1.4-.03*col if row==7 else 1.+.05*col
    release=22e-6 if row==7 else 3e-6;hold=5.021e-3 if row==7 else 5.001e-3;read=5.15e-3 if row==7 else 5.05e-3;base=sample(j+1,release);held=sample(j+1,hold);mask=(t>=release)&(t<=hold)
    record=dict(state=nodes[j],target_v=target,after_write_release_v=base,write_error_v=base-target,after5ms_v=held,max_hold_excursion_v=float(np.max(np.abs(w[mask,j+1]-base))),total_final_state_change_v=sample(j+1,5.19e-3)-held)
    if row in [0,7]:record.update(readout_v=sample(65+col,read),state_on_read_v=sample(j+1,read))
    states.append(record)
   r['states']=states;r['cases']=[{'sequence':'64states; overwrite row7, hold others, read rows0and7'}]
   r['max_write_error_v']=max(abs(x['write_error_v']) for x in states)
   r['max_hold_excursion_v']=max(x['max_hold_excursion_v'] for x in states)
   r['max_read_disturbance_v']=max(abs(x['total_final_state_change_v']) for x in states)
   increasing=all(states[c]['readout_v']<states[c+1]['readout_v'] for c in range(7));decreasing=all(states[56+c]['readout_v']>states[57+c]['readout_v'] for c in range(7))
   r['native_shared_bank_sequence_observed']=bool(r['max_write_error_v']<.02 and r['max_hold_excursion_v']<.02 and r['max_read_disturbance_v']<.02 and increasing and decreasing)
   r['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['sha256','states']},indent=2))
 assert r['module_simulation_completed']
if __name__=='__main__':main()
