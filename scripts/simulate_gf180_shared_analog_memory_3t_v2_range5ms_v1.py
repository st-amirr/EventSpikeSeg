"""Three native minimum-MIM memory instances: write, stressed5ms hold and selected read."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_shared_analog_memory_3t_v2';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json'
 q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches']
 files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():assert sha(R/n)==h,n;files.add(R/n)
 src=d/(cell+'_cap.spice');files.add(src);models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix()
 stem=cell+'_three_native_5ms_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();data=B/'results'/(stem+'.dat')
 lines=['Three actual compact analog memory records',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcom VCM 0 1.2',
 'Vwrite WRITE 0 PWL(0 3.3 .99u 3.3 1u 0 5.2m 0)',
 'Vread READ 0 PWL(0 0 5.019m 0 5.02m 3.3 5.149m 3.3 5.15m 0 5.2m 0)']
 levels=[.75,1.65,2.55]
 for i,level in enumerate(levels):
  lines +=[f'Vdata{i} data{i} 0 PWL(0 {level} 1.999m {level} 2m 0 3.999m 0 4m 3.3 5.2m 3.3)',
   f'Iread{i} readout{i} 0 PWL(0 0 5.021m 0 5.022m 1u 5.129m 1u 5.13m 0 5.2m 0)',
   f'Xmemory{i} state{i} data{i} WRITE READ readout{i} VCM VDD VSS {cell}']
 vectors=[f'state{i}' for i in range(3)]+[f'readout{i}' for i in range(3)]
 lines +=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 5.2m 0 10u',
  'wrdata /workspace/'+data.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in vectors)+' i(Vdd)','quit','.endc','.end']
 deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck)
 snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
 log=p.stdout+p.stderr;lp=B/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_compact_memory_write_hold_read_observed=False,
  original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,
  scope='Three independent actual routed3T/50fF-MIM cell instances, all31 nonnegative extracted routing branches per cell retained. Initial DC write through native NFET stores0.75/1.65/2.55V to check the proposed affine float-storage range, then write gate turn off at1us. Unselected ideal DATA sources switch to0V at2ms and3.3V at4ms. Record a full5ms hold from1us to5.001ms before read selection. Native NF source-follower plus read-select drives a separately gated ideal1uA external column sink; selected read sampled5.1ms and release5.19ms. No ideal output buffer, state restore or numerical conversion. Ideal voltage/wordline/reference/column-current fixtures remain external; supply energy excludes their drivers. Typical27C/noise disabled, unchanged1e-6 tolerance. This is an endpoint-range diagnostic outside the previously accepted1.0-1.4V screen; it does not extend that screen without passing all guards. This cell has no trained beta/threshold/inhibition/adaptation logic; array bus loading, decoder, calibrated read offsets, noise/PVT and full-model5ms service remain unfinished. Three memory records do not prove full population behavior.')
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);t=w[:,0]
  r['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==8 and np.isfinite(w).all() and abs(t[-1]-5.2e-3)<1e-12 and 'aborted' not in log.lower())
  if r['module_simulation_completed']:
   sample=lambda k,s:float(np.interp(s,t,w[:,k]));mask=(t>=10e-6)&(t<=5.001e-3)
   r['cases']=[]
   for i,target in enumerate(levels):
    base=sample(i+1,10e-6);held=sample(i+1,5.001e-3);read=sample(i+4,5.1e-3)
    r['cases'].append(dict(target_state_v=target,after_write_release_v=base,write_release_error_v=base-target,
     state_after5ms_hold_v=held,hold_net_change_v=held-base,max_held_state_excursion_v=float(np.max(np.abs(w[mask,i+1]-base))),
     on_read_state_v=sample(i+1,5.1e-3),readout_v=read,source_follower_offset_v=sample(i+1,5.1e-3)-read,
     selected_read_state_change_v=sample(i+1,5.1e-3)-held,read_release_state_change_v=sample(i+1,5.19e-3)-held))
   c=r['cases'];r['native_compact_memory_write_hold_read_observed']=bool(all(abs(x['write_release_error_v'])<.02 and x['max_held_state_excursion_v']<.02 and abs(x['read_release_state_change_v'])<.02 for x in c) and c[0]['readout_v']<c[1]['readout_v']<c[2]['readout_v'])
   r['VDD_supply_energy_j_excludes_ideal_data_and_control_drivers']=float(np.trapezoid(-3.3*w[:,-1],t))
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
