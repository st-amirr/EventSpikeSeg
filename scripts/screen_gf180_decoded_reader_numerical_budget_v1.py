"""Native physical bank/replica-reader sequence; one column recovers two held rows."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_decoded_bank_shared_reader_v3';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_full_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'];files={Path(__file__),qp,fp};src=d/(f['flat_subcircuit']+'_fullcap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);text=src.read_text();orders=re.search(r'(?m)^\.subckt\s+'+f['flat_subcircuit']+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert orders==q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_three_site_recovery_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Actual physical bank and analog replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-4 abstol=1e-16 vntol=1e-7 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','In 0 BIAS 1u','Ip PBIAS 0 1u']
 # Initialize every native state by selecting each row and writing all eight columns.
 def wave(name,points):lines.append('V'+name+' '+name+' 0 PWL('+' '.join(f'{t}u {v}' for t,v in points)+')')
 for bit in range(3):
  pts=[(0,0)]
  for row in range(1,8):pts.extend([(4*row-.05,3.3 if (row-1)&(1<<bit) else 0),(4*row,3.3 if row&(1<<bit) else 0)])
  pts.extend([(39.9,3.3),(40,0),(79.9,0),(80,3.3),(100,3.3)]);wave('A'+str(bit),pts)
 pts=[(0,3.3),(2.9,3.3),(3,0)]
 for row in range(1,8):pts.extend([(4*row+.1,0),(4*row+.2,3.3),(4*row+2.9,3.3),(4*row+3,0)])
 pts.append((100,0));wave('WRITE_CMD',pts)
 read=[(0,0),(40.9,0),(41,3.3),(54.9,3.3),(55,0),(60.9,0),(61,3.3),(74.9,3.3),(75,0),(80.9,0),(81,3.3),(94.9,3.3),(95,0),(100,0)]
 wave('READ_CMD',read);wave('READ_ENABLE',read)
 for col in range(8):
  start={0:41,3:61,7:81}.get(col)
  if start is None:lines.append(f'Vsel{col} SEL{col} 0 0')
  else:wave('SEL'+str(col),[(0,0),(start-.1,0),(start,3.3),(start+13.9,3.3),(start+14,0),(100,0)])
  pts=[(0,1+.005*col)]
  for row in range(1,8):pts.extend([(4*row-.1,1+.05*(row-1)+.005*col),(4*row,1+.05*row+.005*col)])
  pts.append((100,1.35+.005*col));wave('DATA'+str(col),pts)
 lines.append('Xbank '+' '.join(orders)+' '+f['flat_subcircuit']);nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+['RECOV']
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 100u 0 1u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);sp=B/'tools/source_snapshots'/(stem+'.py');sp.write_bytes(Path(__file__).read_bytes());files.add(sp)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 out=dict(numerical_setting_comparison_only=True,numerical_change='reltol1e-6to1e-4,vntol1e-10to1e-7;abstol1e-16andgmin1e-18unchanged;nodevice/calibration/stimuluschanges.',comparison_basis='Active-switching numerical accuracy check vs completedstrict100usreader.0.1uV absolute voltage tolerance;relative1e-4 corresponds0.33mVat3.3Vlogic. Thisisnotanalogueprecisionacceptance;independentstablepointdeltas mustbemeasured.',module_simulation_completed=False,simulator_returncode=p.returncode,native_bank_mux_three_site_recovery_observed=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,scope='One100us actual411MOS69MIM physical bank/mux/replica-reader. All64 analog states written through native decoded rows before reading;actual traces reviewed for achieved startup; row0column0,row0column3,row7column7 sequentially recovered through same native TG column mux and same replica feedback reader. All3917 verified native substrate/coupling-C branches and actual physical interconnect retained; source/GDS DRC0,LVS and LEF. Bank native mirror supplies actual column sinks and replica sink bias. No ideal buffer,fitted inverse,ADC,QAT or digital membrane. External analog DATA,categorical row/one-hot column commands,READ_ENABLE and1uA NF/PF references. Typical27C/noise-off/mismatch disabled;3sites do not establish full precision,PVT/matching,5ms retention/global service,compute or full chip. Spaced fixture is not dense capacity geometry.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];out['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==67 and np.isfinite(w).all() and abs(t[-1]-100e-6)<1e-12 and 'aborted' not in log.lower())
  if out['module_simulation_completed']:
   at=lambda c,s:float(np.interp(s,t,w[:,c]));cases=[]
   for row,col,when in [(0,0,54e-6),(0,3,74e-6),(7,7,94e-6)]:
    actual=at(1+8*row+col,when);rec=at(65,when);cases.append(dict(row=row,column=col,state_v=actual,recovered_v=rec,reconstruction_error_v=rec-actual))
   out['cases']=cases;out['max_reconstruction_error_v']=max(abs(c['reconstruction_error_v']) for c in cases);out['max_final_state_change_v']=max(abs(at(j+1,99.8e-6)-at(j+1,35e-6)) for j in range(64));out['native_bank_mux_three_site_recovery_observed']=bool(out['max_reconstruction_error_v']<.01 and out['max_final_state_change_v']<.03);out['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))
 except Exception as e:out['postprocess_error']=str(e)
 out['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='sha256'},indent=2));assert out['module_simulation_completed']
if __name__=='__main__':main()

