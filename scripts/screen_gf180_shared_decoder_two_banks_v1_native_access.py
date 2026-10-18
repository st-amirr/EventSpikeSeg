"""One native decoded64-state initialization/overwrite/5ms retention/read sequence."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pwl(points):return 'PWL('+' '.join(f'{t:.12g} {v:.12g}' for t,v in points)+')'
def main():
 cell='gf180_shared_decoder_two_banks_v1';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['mos_count']==568 and q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and f['flat_lvs_unique'] and not f['negative_aggregate_branches']
 files={Path(__file__),qp,fp};src=d/(cell+'_cap.spice');text=src.read_text()
 for n,h in f['sha256'].items():assert sha(R/n)==h,n;files.add(R/n)
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_decoded_sequence_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();data=rp.with_suffix('.dat')
 lines=['Native addressed analog memory bank',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcom VCM 0 1.2']
 for bit in range(3):
  points=[(0,0)]
  for row in range(1,8):points.extend([(row*10e-6-1e-7,3.3*((row-1)>>bit&1)),(row*10e-6,3.3*(row>>bit&1))])
  points.extend([(104.9e-6,3.3),(105e-6,0),(164.9e-6,0),(165e-6,3.3),(200e-6,3.3)]);lines.append(f'Va{bit} A{bit} 0 '+pwl(points))
 points=[(0,3.3),(7.9e-6,3.3),(8e-6,0)]
 for row in range(1,8):points.extend([(row*10e-6+1.9e-6,0),(row*10e-6+2e-6,3.3),(row*10e-6+7.9e-6,3.3),(row*10e-6+8e-6,0)])
 points.extend([(91.9e-6,0),(92e-6,3.3),(97.9e-6,3.3),(98e-6,0),(200e-6,0)]);lines.append('Vwrite WRITE_CMD 0 '+pwl(points))
 lines.append('Vread READ_CMD 0 PWL(0 0 109.9u 0 110u 3.3 159.9u 3.3 160u 0 169.9u 0 170u 3.3 198.9u 3.3 199u 0 200u 0)')
 for bank in range(2):
  prefix=f'B{bank}_'
  for col in range(8):
   initial=lambda row:(1.+.03*row+.01*col) if bank==0 else (1.4-.03*row-.01*col)
   target=(1.4-.03*col) if bank==0 else (1.+.03*col)
   points=[(0,initial(0))]
   for row in range(1,8):points.extend([(row*10e-6-1e-7,initial(row-1)),(row*10e-6,initial(row))])
   points.extend([(89.9e-6,initial(7)),(90e-6,target),(200e-6,target)]);lines.append(f'Vd{bank}_{col} {prefix}DATA{col} 0 '+pwl(points))
  lines.append(f'Ireference{bank} 0 {prefix}BIAS PWL(0 0 111.9u 0 112u 1u 157.9u 1u 158u 0 171.9u 0 172u 1u 197.9u 1u 198u 0 200u 0)')
 lines +=['Xbank '+' '.join(q['ports'])+' '+cell]
 nodes=[f'B{bank}_STATE{row}{col}' for bank in range(2) for row in range(8) for col in range(8)]+[f'B{bank}_READOUT{col}' for bank in range(2) for col in range(8)]
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 200u 0 10u','wrdata /workspace/'+data.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
 log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_decoded_bank_sequence_observed=False,full_chip_layout_complete=False,full_5ms_population_service_accepted=False,original_float_accuracy_accepted=False,
  scope=f'Actual568MOS128MIM two-bank parent,one166MOS native decoder shared by two201MOS gain-cell banks with16native sinks and2diode masters. All{f["linear_branch_count"]} routing-C branches retained.200us native fixture initializes8rows in both banks with different analog values, overwritesrow7 with opposite column slopes, readsrow0and7 through common row selection. All128states and16readouts recorded. Both banks operate in lockstep; separate analog columns preserve identities. Independent bank inhibit is not implemented. This storage grouping does not select compute-lane allocation or prove5ms parent retention/global service. Native bank5ms/50ms retention is separate child evidence. External address/command/data/master-current/reference fixtures; typical27C/noise-off. No calibrated read, permanent weights, fullmodel precision or chip claim.')
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);t=w[:,0];r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==146 and np.isfinite(w).all() and abs(t[-1]-200e-6)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda k,s:float(np.interp(s,t,w[:,k]));states=[]
   for j in range(128):
    bank,site=divmod(j,64);row,col=divmod(site,8);target=((1.4-.03*col) if bank==0 else (1.+.03*col)) if row==7 else ((1.+.03*row+.01*col) if bank==0 else (1.4-.03*row-.01*col));initial=sample(j+1,103e-6);held=sample(j+1,104e-6);mask=(t>=100e-6)&(t<=104e-6)
    v=dict(state=nodes[j],target_v=target,after_initialization_v=initial,write_error_v=initial-target,after_hold_v=held,max_hold_excursion_v=float(np.max(np.abs(w[mask,j+1]-initial))),final_read_state_change_v=sample(j+1,199.8e-6)-held)
    if row in [0,7]:v['readout_v']=sample(129+bank*8+col,140e-6 if row==0 else 190e-6)
    states.append(v)
   r['states']=states;r['cases']=[{'sequence':'shared decode;128states in2banks;opposite DATA slopes;row0and7 lockstep read;200us'}];r['max_write_error_v']=max(abs(v['write_error_v']) for v in states);r['max_hold_excursion_v']=max(v['max_hold_excursion_v'] for v in states);r['max_read_disturbance_v']=max(abs(v['final_read_state_change_v']) for v in states)
   r['native_decoded_bank_sequence_observed']=bool(r['max_write_error_v']<.03 and r['max_read_disturbance_v']<.03 and all(states[c]['readout_v']<states[c+1]['readout_v'] for c in range(7)) and all(states[56+c]['readout_v']>states[57+c]['readout_v'] for c in range(7)) and all(states[64+c]['readout_v']>states[65+c]['readout_v'] for c in range(7)) and all(states[120+c]['readout_v']<states[121+c]['readout_v'] for c in range(7)))
   r['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['sha256','states']},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
