"""Three-point native stored-voltage to shared-readout transfer screen."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bank_pair_shared_readout_v3';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_full_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and f['all_flat_extraction_node_ground_caps_verified'];src=d/(f['flat_subcircuit']+'_fullcap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()]
 stem=cell+'_native_three_point_transfer_v1';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice');models=B/'pdk/gf180_primitive_source/models/ngspice';pre='/workspace/'+models.relative_to(R).as_posix()
 lines=['Native shared128-state replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','In0 0 B0_BIAS 1u','In1 0 B1_BIAS 1u','Ip PBIAS 0 1u']
 def wave(n,points):lines.append('V'+n+' '+n+' 0 PWL('+' '.join(f'{t}u {v}' for t,v in points)+')')
 address=[(0,0),(7.9,0),(8,3.3),(25.9,3.3),(26,0),(45.9,0),(46,3.3),(70,3.3)]
 for n in ['A0','A1','A2','BANK_SELECT']:wave(n,address)
 wave('WRITE_CMD',[(0,3.3),(5.9,3.3),(6,0),(9.9,0),(10,3.3),(15.9,3.3),(16,0),(70,0)])
 read=[(0,0),(29.9,0),(30,3.3),(39.9,3.3),(40,0),(49.9,0),(50,3.3),(59.9,3.3),(60,0),(70,0)]
 wave('READ_CMD',read)
 for c in range(8):
  val={0:1.0,1:1.2}.get(c,1.0)
  if c==7: wave('DATA'+str(c),[(0,1.0),(8.9,1.0),(9.0,1.4),(70,1.4)])
  else: wave('DATA'+str(c),[(0,val),(70,val)])
 states=[f'B{b}_STATE{r}{c}' for b in range(2) for r in range(8) for c in range(8)];nodes=states+['SELECTED_BIAS','B0_BIAS','B1_BIAS']+[f'READOUT{c}' for c in range(8)]+['BANK_SELECT','READ_CMD','WRITE_CMD'];lines+=['Xbank '+' '.join(q['ports'])+' '+f['flat_subcircuit'],'.save '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','.tran .02u 70u 0 1u','.end'];deck.write_text('\n'.join(lines)+'\n')
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');lp.write_text(run.stdout+run.stderr)
 o=dict(module_simulation_completed=False,simulator_returncode=run.returncode,three_point_transfer_observed=False,full_chip_layout_complete=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,native_capacitance_branches=f['linear_branch_count'],scope='Actual808MOS/128MIM routed shared-readout parent with extracted native capacitances. Writes 1.0V and 1.2V onto adjacent bank0 row0 cells and 1.4V onto bank1 row7 col7 using native row decoders, then measures the three values via the integrated bank mux/read columns. Categorical controls and ideal voltage DATA writes; actual MIM state, native selectors, shared readout and extracted routing are simulated. Typical 27C, no IC/UIC. Three point read-transfer screen only; no gain stage, array initialization, PVT/mismatch, model accuracy or 5ms acceptance.')
 if raw.exists():
  h,b=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];w=np.frombuffer(b[:len(b)//(8*nv)*(8*nv)],dtype='<f8').reshape(-1,nv);t=w[:,0];assert np.isfinite(w).all() and np.all(np.diff(t)>=0);np.savez_compressed(rp.with_suffix('.npz'),waveforms=w,variables=np.array(names));o['last_saved_time_s']=float(t[-1]);o['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-70e-6)<1e-12 and 'aborted' not in (run.stdout+run.stderr).lower())
  if o['module_simulation_completed']:
   at=lambda n,us:float(np.interp(us*1e-6,t,w[:,names.index('v('+n.lower()+')')]));cases=[]
   for state,signal,us,target in [('B0_STATE00','READOUT0',35,1.0),('B0_STATE01','READOUT1',35,1.2),('B1_STATE77','READOUT7',55,1.4)]:
    actual=at(state,us);rec=at(signal,us);cases.append(dict(selected_state=state,readout=signal,at_us=us,actual_state_v=actual,readout_v=rec,write_error_v=actual-target,selected_bias_v=at('SELECTED_BIAS',us)))
   volts=[c['readout_v'] for c in cases];targets=[c['actual_state_v'] for c in cases];slope=float(np.polyfit(volts,targets,1)[0]);offset=float(np.polyfit(volts,targets,1)[1]);pred=[slope*v+offset for v in volts];res=max(abs(a-b) for a,b in zip(pred,targets));dist=max(abs(at(n,69.9)-at(n,18)) for n in states);o.update(cases=cases,readout_monotonic=bool(volts[0]<volts[1]<volts[2]),linear_restore_gain_v_per_v=slope,linear_restore_offset_v=offset,max_three_point_linear_residual_v=res,max_state_change_after_write_v=dist,three_point_transfer_observed=bool(volts[0]<volts[1]<volts[2] and dist<.03),VDD_energy_j_excludes_external_references=float(np.trapezoid(-3.3*w[:,names.index('i(vdd)')],t)))
 o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),qp,fp,src,deck,lp]+([raw] if raw.exists() else [])};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
