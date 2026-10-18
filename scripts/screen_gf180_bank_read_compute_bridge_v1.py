"""Native physical bank/replica-reader sequence; one column recovers two held rows."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bank_read_compute_bridge_v1';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'];files={Path(__file__),qp,fp};src=d/(f['flat_subcircuit']+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);text=src.read_text();orders=re.search(r'(?m)^\.subckt\s+'+f['flat_subcircuit']+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert orders==q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_three_restore_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Actual physical bank and analog replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','In 0 BIAS 1u','Ip PBIAS 0 1u']
 for row in range(8):
  a=row*10;b=a+2;e=a+8
  pulse='PWL(0 3.3 7.9u 3.3 8u 0 180u 0)' if row==0 else f'PWL(0 0 {b-.1}u 0 {b}u 3.3 {e-.1}u 3.3 {e}u 0 180u 0)'
  lines.append(f'Vw{row} WRITE{row} 0 '+pulse)
  read='PWL(0 0 89.9u 0 90u 3.3 134.9u 3.3 135u 0 180u 0)' if row==0 else ('PWL(0 0 144.9u 0 145u 3.3 169.9u 3.3 170u 0 180u 0)' if row==7 else '0')
  lines.append(f'Vr{row} READ{row} 0 '+read)
 lines.append('Ven READ_ENABLE 0 PWL(0 0 89.9u 0 90u 3.3 134.9u 3.3 135u 0 144.9u 0 145u 3.3 169.9u 3.3 170u 0 180u 0)')
 for col in range(8):
  pulses={0:'PWL(0 0 89.9u 0 90u 3.3 109.9u 3.3 110u 0 180u 0)',3:'PWL(0 0 114.9u 0 115u 3.3 134.9u 3.3 135u 0 180u 0)',7:'PWL(0 0 144.9u 0 145u 3.3 169.9u 3.3 170u 0 180u 0)'}
  lines.append(f'Vsel{col} SEL{col} 0 '+pulses.get(col,'0'))
 for col in range(8):
  points=[(0,1+.005*col)]
  for row in range(1,8):points.extend([(row*10-.1,1+.05*(row-1)+.005*col),(row*10,1+.05*row+.005*col)])
  points.append((180,1.35+.005*col));lines.append(f'Vd{col} DATA{col} 0 PWL('+' '.join(f'{t}u {v}' for t,v in points)+')')
 # Only restoration is exercised; compute beta/events/threshold/reset stay idle.
 controls={'C_AUXRESET':3.3,'C_BETA':0,'C_AUXREF':1.2,'C_SENSE_REF':1.2,'C_SENSE_BIAS':.75,'C_OUTPUT_HOLD':0,'C_OUTPUT_HOLDB':3.3,'C_PARK_AZ':3.3,'C_PARK_AZB':0,'C_RESET_PROGRAM':.45,'C_NCAS':1.1,'C_RESET':0,'C_INJ_PPROGRAM':2.5,'C_INJ_NPROGRAM':.45,'C_PCAS':2.2,'C_POS':0,'C_POSB':3.3,'C_NEG':0,'C_NEGB':3.3,'C_SAMPLE':0,'C_SAMPLEB':3.3}
 for n,v in controls.items():lines.append('Vctrl_'+n+' '+n+' 0 '+str(v))
 lines+=['Vcw C_WRITE 0 PWL(0 0 99.9u 0 100u 3.3 103.9u 3.3 104u 0 124.9u 0 125u 3.3 128.9u 3.3 129u 0 159.9u 0 160u 3.3 163.9u 3.3 164u 0 180u 0)','Vcwb C_WRITEB 0 PWL(0 3.3 99.9u 3.3 100u 0 103.9u 0 104u 3.3 124.9u 3.3 125u 0 128.9u 0 129u 3.3 159.9u 3.3 160u 0 163.9u 0 164u 3.3 180u 3.3)','Ipark C_PARK_BIAS 0 1u']
 reference='gf180_pmos_bias_reference_fullroute_v2';rd=B/'layout'/reference;rq=rd/'qualification.json';qref=json.loads(rq.read_text());rnet=rd/(reference+'_cap.spice');assert sha(rnet)==qref['sha256'][rnet.name];files.update([rq,rnet]);lines.extend([rnet.read_text(),'Xparkref C_PARK_BIAS VDD VSS '+reference])
 lines.append('Xbank '+' '.join(orders)+' '+f['flat_subcircuit']);nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+['RECOV','C_STATE','C_AUX']
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 180u 0 2u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);sp=B/'tools/source_snapshots'/(stem+'.py');sp.write_bytes(Path(__file__).read_bytes());files.add(sp)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 out=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_three_compute_restores_observed=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,scope='One180us actual301MOS110MIM physical bank/mux/reader/five-module compute restore bridge,3143 flat C branches,source/GDS DRC0/LVS/LEF. Three stored row/column values are read and transferred by native compute WRITE TG into compute STATE, then released. All beta/injection/decision/reset functions idle; this only qualifies analog restore interface under actual compute loading. Both storage/computeVCM fixed1.2V, external AUXREF/SENSE_REF1.2V diagnostic settings. Earlier v6 compute semantic calibration used1.65V; no transfer of that calibration, learned-beta/threshold accuracy or restored float representation claimed. Native external PF diode parking reference plus1uA current fixture. External phase/voltage references, typical27C/noise-off/mismatch disabled. No row writeback: all8row columns require separate analog staging/parallel lanes before bank row commit. No complete PLIF, original model precision,5ms service or fullchip claim.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];out['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==69 and np.isfinite(w).all() and abs(t[-1]-180e-6)<1e-12 and 'aborted' not in log.lower())
  if out['module_simulation_completed']:
   at=lambda c,s:float(np.interp(s,t,w[:,c]));cases=[]
   for row,col,when in [(0,0,108e-6),(0,3,133e-6),(7,7,168e-6)]:
    actual=at(1+8*row+col,when);rec=at(65,when);comp=at(66,when);cases.append(dict(row=row,column=col,bank_state_v=actual,recovered_v=rec,reconstruction_error_v=rec-actual,compute_state_v=comp,restore_error_v=comp-actual))
   out['cases']=cases;out['max_reconstruction_error_v']=max(abs(c['reconstruction_error_v']) for c in cases);out['max_final_state_change_v']=max(abs(at(j+1,179.8e-6)-at(j+1,85e-6)) for j in range(64));out['max_compute_restore_error_v']=max(abs(c['restore_error_v']) for c in cases);out['native_three_compute_restores_observed']=bool(out['max_reconstruction_error_v']<.01 and out['max_compute_restore_error_v']<.05 and out['max_final_state_change_v']<.03);out['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))
 except Exception as e:out['postprocess_error']=str(e)
 out['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='sha256'},indent=2));assert out['module_simulation_completed']
if __name__=='__main__':main()

