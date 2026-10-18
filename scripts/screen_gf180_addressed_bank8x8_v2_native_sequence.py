"""One native decoded64-state initialization/overwrite/5ms retention/read sequence."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pwl(points):return 'PWL('+' '.join(f'{t:.12g} {v:.12g}' for t,v in points)+')'
def main():
 cell='gf180_addressed_memory_bank8x8_v2';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['mos_count']==430 and q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and f['flat_lvs_unique'] and not f['negative_aggregate_branches']
 files={Path(__file__),qp,fp};src=d/(cell+'_cap.spice');text=src.read_text()
 for n,h in f['sha256'].items():assert sha(R/n)==h,n;files.add(R/n)
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_decoded_sequence_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();data=rp.with_suffix('.dat')
 lines=['Native addressed analog memory bank',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcom VCM 0 1.2']
 for bit in range(3):
  points=[(0,0)]
  for row in range(1,8):points.extend([(row*10e-6-1e-7,3.3*((row-1)>>bit&1)),(row*10e-6,3.3*(row>>bit&1))])
  points.extend([(5.1899e-3,3.3),(5.19e-3,0),(5.2999e-3,0),(5.3e-3,3.3),(5.4e-3,3.3)]);lines.append(f'Va{bit} A{bit} 0 '+pwl(points))
 points=[(0,3.3),(7.9e-6,3.3),(8e-6,0)]
 for row in range(1,8):points.extend([(row*10e-6+1.9e-6,0),(row*10e-6+2e-6,3.3),(row*10e-6+7.9e-6,3.3),(row*10e-6+8e-6,0)])
 points.extend([(91.9e-6,0),(92e-6,3.3),(97.9e-6,3.3),(98e-6,0),(5.4e-3,0)]);lines.append('Vwrite WRITE_CMD 0 '+pwl(points))
 lines.append('Vread READ_CMD 0 PWL(0 0 5.1999m 0 5.2m 3.3 5.2499m 3.3 5.25m 0 5.3099m 0 5.31m 3.3 5.3599m 3.3 5.36m 0 5.4m 0)')
 for col in range(8):
  points=[(0,1.+.01*col)]
  for row in range(1,8):points.extend([(row*10e-6-1e-7,1.+.03*(row-1)+.01*col),(row*10e-6,1.+.03*row+.01*col)])
  points.extend([(89.9e-6,1.21+.01*col),(90e-6,1.4-.03*col),(1.999e-3,1.4-.03*col),(2e-3,0),(3.999e-3,0),(4e-3,3.3),(5.4e-3,3.3)]);lines.append(f'Vd{col} DATA{col} 0 '+pwl(points))
  lines.append(f'Ir{col} READOUT{col} 0 PWL(0 0 5.2019m 0 5.202m 1u 5.2479m 1u 5.248m 0 5.3119m 0 5.312m 1u 5.3579m 1u 5.358m 0 5.4m 0)')
 lines +=['Xbank '+' '.join(q['ports'])+' '+cell]
 nodes=[f'STATE{row}{col}' for row in range(8) for col in range(8)]+[f'READOUT{col}' for col in range(8)]
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 5.4m 0 10u','wrdata /workspace/'+data.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
 log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_decoded_bank_sequence_observed=False,full_chip_layout_complete=False,full_5ms_population_service_accepted=False,original_float_accuracy_accepted=False,
  scope=f'Actual430MOS64MIM parent,174MOS native3to8 address/read/write decoder joined to256MOS64MIM bank, all{f["linear_branch_count"]} nonnegative extracted routing branches. External three categorical address bits and separate write/read commands drive real decoded wordlines, not ideal row sources. Initialize all8rows through decoder, overwrite only row7, stress shared DATA at2ms/4ms, hold all64states over5ms and read rows0and7 via native source followers. Record every state and all8columns. External ideal address/command/data/reference/current fixtures; no numeric digital state, ideal output buffer or fitted restore. Typical27C/noise off. Spacious integration routing is not dense macro area. No beta/weight compute, read calibration, full-model accuracy, population timing or fullchip acceptance.')
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);t=w[:,0];r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==74 and np.isfinite(w).all() and abs(t[-1]-5.4e-3)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda k,s:float(np.interp(s,t,w[:,k]));states=[]
   for j in range(64):
    row,col=divmod(j,8);target=1.4-.03*col if row==7 else 1.+.03*row+.01*col;initial=sample(j+1,110e-6);held=sample(j+1,5.11e-3);mask=(t>=110e-6)&(t<=5.11e-3)
    v=dict(state=nodes[j],target_v=target,after_initialization_v=initial,write_error_v=initial-target,after_hold_v=held,max_hold_excursion_v=float(np.max(np.abs(w[mask,j+1]-initial))),final_read_state_change_v=sample(j+1,5.39e-3)-held)
    if row in [0,7]:v['readout_v']=sample(65+col,5.23e-3 if row==0 else 5.34e-3)
    states.append(v)
   r['states']=states;r['cases']=[{'sequence':'actual3to8 decode;8row initialization;row7 overwrite;64state5ms hold;row0and7 read'}];r['max_write_error_v']=max(abs(v['write_error_v']) for v in states);r['max_hold_excursion_v']=max(v['max_hold_excursion_v'] for v in states);r['max_read_disturbance_v']=max(abs(v['final_read_state_change_v']) for v in states)
   r['native_decoded_bank_sequence_observed']=bool(r['max_write_error_v']<.02 and r['max_hold_excursion_v']<.02 and r['max_read_disturbance_v']<.02 and all(states[c]['readout_v']<states[c+1]['readout_v'] for c in range(7)) and all(states[56+c]['readout_v']>states[57+c]['readout_v'] for c in range(7)))
   r['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['sha256','states']},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
