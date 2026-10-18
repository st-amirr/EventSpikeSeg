"""Native physical bank/replica-reader sequence; one column recovers two held rows."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_decoded_shared_compute_tile_v1';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_full_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'];files={Path(__file__),qp,fp};src=d/(f['flat_subcircuit']+'_fullcap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);text=src.read_text();orders=re.search(r'(?m)^\.subckt\s+'+f['flat_subcircuit']+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert orders==q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_closed_loop_cycle_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Actual physical bank and analog replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vsref SREF 0 1.2','Vcref CREF 0 1.65','In 0 BIAS 1u','Iio IO_BIAS 0 9u','Ir READER_BIAS 0 1u','Iu UP_BIAS 0 1u','Id DOWN_BIAS 0 1u','Ip PARK_BIAS 0 1u']
 invd=B/'layout/gf180_dense_inverter_v1';invq=invd/'flat_cap_full_qualification.json';iq=json.loads(invq.read_text());invsrc=invd/(iq['flat_subcircuit']+'_fullcap.spice');assert sha(invsrc)==iq['sha256'][invsrc.relative_to(R).as_posix()];files.update([invq,invsrc]);lines.append(invsrc.read_text());inv=iq['flat_subcircuit']
 calp=B/'results/gf180_combined_v6_joint_reference_reset_calibration.json';cal=json.loads(calp.read_text());files.add(calp);width=cal['frozen_reset_width_us']
 def wave(n,initial,edges):
  points=[(0,initial)];prev=initial
  for at,value in edges:
   at-=980;points.extend([(at-.1,prev),(at,value)]);prev=value
  points.append((230,prev));raw=n+'_CMD_DRIVER';mid=n+'_DRIVERB';lines.append('Vctrl_'+n+' '+raw+' 0 PWL('+' '.join(f'{at}u {value}' for at,value in points)+')');lines.extend([f'XdrvB_{n} {raw} {mid} VDD VSS {inv}',f'Xdrv_{n} {mid} {n} VDD VSS {inv}'])
 def pulse(n,a,b):wave(n,0,[(a,3.3),(b,0)])
 def pair(n,nb,initial,edges):wave(n,initial,edges);wave(nb,3.3-initial,[(a,3.3-v) for a,v in edges])
 # Commands are low while the native row address changes;all64states receive real writes.
 for bit in range(3):
  edges=[]
  for row in range(1,8):edges.append((1008+4*row,3.3 if row&(1<<bit) else 0))
  wave('A'+str(bit),0,edges)
 edges=[(1011,0)]
 for row in range(1,8):edges +=[(1008+4*row+.2,3.3),(1008+4*row+3,0)]
 edges +=[(1120,3.3),(1128,0)];wave('WRITE_CMD',3.3,edges);pulse('READ_CMD',1040,1160)
 for col in range(8):
  pair(f'CAP{col}',f'CAPB{col}',3.3,[(1020,0)]+([(1100,3.3),(1108,0)] if col==0 else []));lines.append(f'Vsel{col} SEL{col} 0 '+str(3.3 if col==0 else 0))
 wave('READ_ENABLE',0,[(1040,3.3),(1160,0)]);pair('INIT','INITB',3.3,[(1030,0)]);pair('RESTORE','RESTOREB',0,[(1050,3.3),(1060,0)]);pair('C_WRITE','C_WRITEB',3.3,[(1010,0),(1052,3.3),(1058,0)])
 wave('C_AUXRESET',3.3,[(1064.98,0),(1075,3.3)]);pulse('C_BETA',1065,1065.5);pair('C_PARK_AZ','C_PARK_AZB',3.3,[(1005,0)]);pair('C_SAMPLE','C_SAMPLEB',0,[(1088,3.3),(1088.5,0)]);pair('C_OUTPUT_HOLD','C_OUTPUT_HOLDB',0,[(1089,3.3)]);pulse('C_RESET',1090,1090+width);pair('C_POS','C_POSB',0,[(1077,3.3),(1082,0)]);pair('C_NEG','C_NEGB',0,[])
 lines+=['Vinit INIT_DATA 0 PWL(0 1.656875 27.9u 1.656875 28u 1.8 230u 1.8)',f"Vaux C_AUXREF 0 {cal['frozen_auxiliary_reference_v']}",'Vsb C_SENSE_BIAS 0 .75','Vrp C_RESET_PROGRAM 0 .45','Vnc C_NCAS 0 1.1','Vip C_INJ_PPROGRAM 0 2.5','Vin C_INJ_NPROGRAM 0 .45','Vpc C_PCAS 0 2.2']
 lines.append('Xtile '+' '.join(orders)+' '+f['flat_subcircuit']);nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+[f'DATA{i}' for i in range(8)]+['C_STATE','C_AUX','C_SENSE_OUT','C_SPIKE','C_PARK','C_SENSE_REF','C_SENSE_COMP']
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 230u 0 10u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);sp=B/'tools/source_snapshots'/(stem+'.py');sp.write_bytes(Path(__file__).read_bytes());files.add(sp)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 out=dict(native_driver_fixture=True,driver_fixture_is_routed_into_tile=False,diagnostic_basis='Previous fullcapideal controlsabort25usAZrelease;existingnativeinverterdriverfixtureonoldtilepassedAZandallphasesuntilpositiveinjection1082usbeforetimeout. Applysameverifiedfiniteoutputstage toallchangingcategoricalcommands,newdecodedtile geometry/C/calibration unchanged.',module_simulation_completed=False,simulator_returncode=p.returncode,native_closed_loop_update_observed=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,scope='Native5337branch hierarchy-off230us native closed-loop trial of actual physical579MOS8R172MIM shared64state tile. Analog init mux programs1.656875V autozero baseline then1.8V compute target; eight real analog output holders initialize bank, row7column0 reads through native mux/replica/up-shifter, actual compute WRITE restores state, one frozen-beta auxiliary cycle and5us positive injection precede sampled decision and gated subtractive reset. Compute output passes native isolation/down-shift into holder0; all8held outputs commit onlyrow7. Other holders retain initialized values. Exact source/flat/GDS primitive connectivity proofs and all native flat C retained with everynative substrate node checked. Previous hierarchical-PCAP cycles underload critical nodes. ActualnativefullCtwo-inverter stages drive changingcategoricalcommands;theirportwiresaretestfixtureconnections,notroutedtile. NoidealRdriveror solverrelaxation. Existing frozen v6 auxiliary reference/reset duration reused without new fit, preserving errors from new loading. External categorical scheduler,analog programming/current/parameter references; typical27C/noise/mismatch off. DC plus20us prebias replaces1ms idle fixture interval;all64states initialized through native decoded row writes,one selected update only, not all64updates,adaptation/RMS/inhibition,trained-weight mapping,original model accuracy,5ms population service,dense tile or full chip. Native Netgen is not rerun; v2 failures retained; exact complete graph bijections qualify connectivity, no false Netgen pass.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];out['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==81 and np.isfinite(w).all() and abs(t[-1]-230e-6)<1e-12 and 'aborted' not in log.lower())
  if out['module_simulation_completed']:
   at=lambda c,us:float(np.interp((us-980)*1e-6,t,w[:,c]));before=at(73,1064);after=at(73,1076);inj=at(73,1086)-after;spike=at(76,1089.5);resetstep=at(73,1096)-at(73,1089.5);held=at(65,1119);final=at(57,1209)
   out['cases']=[dict(sequence='init,read-row7col0,restore,beta,positive-event,detect,reset,capture0,commitrow7',bank_before_update_v=at(57,1039.5),compute_before_beta_v=before,compute_after_beta_v=after,trained_beta_residual_v=after-1.65-cal['original_trained_beta']*(before-1.65),positive_event_step_v=inj,spike_before_reset_v=spike,reset_step_v=resetstep,held_write_column0_v=held,final_bank_state70_v=final,writeback_error_vs_actual_column_v=final-held)]
   out['max_unselected_rows_change_v']=max(abs(at(j+1,1209)-at(j+1,1035)) for j in range(56));out['max_other_columns_row7_change_v']=max(abs(at(57+c,1209)-at(57+c,1035)) for c in range(1,8));out['native_closed_loop_update_observed']=bool(inj>0 and abs(final-held)<.06 and out['max_unselected_rows_change_v']<.03 and (spike<1 or resetstep<0));out['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))

 except Exception as e:out['postprocess_error']=str(e)
 out['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['sha256','columns','unselected_states']},indent=2));assert out['module_simulation_completed']
if __name__=='__main__':main()

