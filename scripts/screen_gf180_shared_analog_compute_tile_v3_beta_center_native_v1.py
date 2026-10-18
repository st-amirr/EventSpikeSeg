"""Native physical bank/replica-reader sequence; one column recovers two held rows."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_shared_analog_compute_tile_v3';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_full_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'];files={Path(__file__),qp,fp};src=d/(f['flat_subcircuit']+'_fullcap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);text=src.read_text();orders=re.search(r'(?m)^\.subckt\s+'+f['flat_subcircuit']+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert orders==q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_closed_loop_cycle_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Actual physical bank and analog replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vsref SREF 0 1.2','Vcref CREF 0 1.65','In 0 BIAS 1u','Iio IO_BIAS 0 9u','Ir READER_BIAS 0 1u','Iu UP_BIAS 0 1u','Id DOWN_BIAS 0 1u','Ip PARK_BIAS 0 1u']
 invd=B/'layout/gf180_dense_inverter_v1';invq=invd/'flat_cap_full_qualification.json';iq=json.loads(invq.read_text());invsrc=invd/(iq['flat_subcircuit']+'_fullcap.spice');assert sha(invsrc)==iq['sha256'][invsrc.relative_to(R).as_posix()];files.update([invq,invsrc]);lines.append(invsrc.read_text());inv=iq['flat_subcircuit']
 calp=B/'results/gf180_combined_v6_joint_reference_reset_calibration.json';cal=json.loads(calp.read_text());files.add(calp);width=cal['frozen_reset_width_us']
 def wave(n,initial,edges):
  points=[(0,initial)];prev=initial
  for at,value in edges:points.extend([(at-.1,prev),(at,value)]);prev=value
  points.append((10,prev));raw=n+'_CMD' if edges else n;lines.append('Vctrl_'+n+' '+raw+' 0 PWL('+' '.join(f'{at}u {value}' for at,value in points)+')')
  if edges:lines.extend([f'XdrvB_{n} {raw} {n}_DRIVERB VDD VSS {inv}',f'Xdrv_{n} {n}_DRIVERB {n} VDD VSS {inv}'])
 def pulse(n,a,b):wave(n,0,[(a,3.3),(b,0)])
 def pair(n,nb,initial,edges):wave(n,initial,edges);wave(nb,3.3-initial,[(a,3.3-v) for a,v in edges])
 for row in range(8):
  wave(f'WRITE{row}',3.3,[]);wave(f'READ{row}',0,[])
 for col in range(8):
  pair(f'CAP{col}',f'CAPB{col}',3.3,[]);wave(f'SEL{col}',0,[])
 for name in ['READ_ENABLE','RESTORE','C_OUTPUT_HOLD','C_SAMPLE','C_RESET','C_POS','C_NEG']:
  if name in ['RESTORE','C_OUTPUT_HOLD','C_SAMPLE','C_POS','C_NEG']:pair(name,name+'B',0,[])
  else:wave(name,0,[])
 pair('INIT','INITB',3.3,[]);pair('C_WRITE','C_WRITEB',3.3,[(2,0)]);pair('C_PARK_AZ','C_PARK_AZB',3.3,[])
 wave('C_AUXRESET',3.3,[(4,0),(7,3.3)]);pulse('C_BETA',5,5.5)
 lines+=['Vinit INIT_DATA 0 1.65',f"Vaux C_AUXREF 0 {cal['frozen_auxiliary_reference_v']}",'Vsb C_SENSE_BIAS 0 .75','Vrp C_RESET_PROGRAM 0 .45','Vnc C_NCAS 0 1.1','Vip C_INJ_PPROGRAM 0 2.5','Vin C_INJ_NPROGRAM 0 .45','Vpc C_PCAS 0 2.2']
 lines.append('Xtile '+' '.join(orders)+' '+f['flat_subcircuit']);nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+[f'DATA{i}' for i in range(8)]+['C_STATE','C_AUX','C_SENSE_OUT','C_SPIKE','C_PARK','C_SENSE_REF','C_SENSE_COMP']
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .002u 10u 0 .05u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);sp=B/'tools/source_snapshots'/(stem+'.py');sp.write_bytes(Path(__file__).read_bytes());files.add(sp)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 out=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_closed_loop_update_observed=False,beta_phase_simulation_completed=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,scope='10us phase-isolated native joined-tile beta characterization with corrected3941branch flat RC. All413MOS8R172MIM retained. Independent initial compute1.65V center-state steady bias, frozen auxiliary reference unchanged; only compute WRITE release,beta/aux phases run. All autozero gates remain high; no comparator autozero release,injection,threshold/reset/read/row-writeback assertion. Method review after ideal Gear/regularized/Trap and finite-driver whole-cycle attempts abort at autozero edge. Only changing WRITE/WRITEB,AUXRESET and BETA commands use two qualified native GF180 inverters each; steady phase inputs remain DC. Whole-cycle native-driver composition timed out120s near1.058ms; do not restart or extend that run. This10us probe reduces changing phases to the beta mechanism; no threshold/row-service claim. This isolates beta with actual joined loading and frozen reference; no numerical tolerance or cap edits. Typical27C/noise/mismatch off; no trained precision or5ms/fullchip acceptance.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];out['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==81 and np.isfinite(w).all() and abs(t[-1]-10e-6)<1e-12 and 'aborted' not in log.lower())
  if out['module_simulation_completed']:
   at=lambda c,us:float(np.interp(us*1e-6,t,w[:,c]));before=at(73,3.5);aftershare=at(73,6.5);after=at(73,9.5)
   out['cases']=[dict(sequence='steady1.65V initialize,WRITE-release,AUXRESET-release,beta,aux-recharge;autozero-held',compute_before_beta_v=before,compute_after_share_v=aftershare,compute_after_aux_recharge_v=after,trained_beta_residual_v=after-1.65-cal['original_trained_beta']*(before-1.65),aux_before_v=at(74,3.5),aux_after_share_v=at(74,6.5))]
   out['beta_phase_simulation_completed']=True

 except Exception as e:out['postprocess_error']=str(e)
 out['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['sha256','columns','unselected_states']},indent=2));assert out['module_simulation_completed']
if __name__=='__main__':main()

