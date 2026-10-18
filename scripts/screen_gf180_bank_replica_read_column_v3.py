"""Native physical bank/replica-reader sequence; one column recovers two held rows."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bank_replica_read_column_v3';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'];files={Path(__file__),qp,fp};src=d/(f['flat_subcircuit']+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);text=src.read_text();orders=re.search(r'(?m)^\.subckt\s+'+f['flat_subcircuit']+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert orders==q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_two_row_recovery_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Actual physical bank and analog replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','In 0 BIAS 1u','Ip PBIAS 0 1u']
 for row in range(8):
  a=row*10;b=a+2;e=a+8
  pulse='PWL(0 3.3 7.9u 3.3 8u 0 160u 0)' if row==0 else f'PWL(0 0 {b-.1}u 0 {b}u 3.3 {e-.1}u 3.3 {e}u 0 160u 0)'
  lines.append(f'Vw{row} WRITE{row} 0 '+pulse)
  read='PWL(0 0 89.9u 0 90u 3.3 119.9u 3.3 120u 0 160u 0)' if row==0 else ('PWL(0 0 124.9u 0 125u 3.3 154.9u 3.3 155u 0 160u 0)' if row==7 else '0')
  lines.append(f'Vr{row} READ{row} 0 '+read)
 lines.append('Ven READ_ENABLE 0 PWL(0 0 89.9u 0 90u 3.3 119.9u 3.3 120u 0 124.9u 0 125u 3.3 154.9u 3.3 155u 0 160u 0)')
 for col in range(8):
  points=[(0,1+.005*col)]
  for row in range(1,8):points.extend([(row*10-.1,1+.05*(row-1)+.005*col),(row*10,1+.05*row+.005*col)])
  points.append((160,1.35+.005*col));lines.append(f'Vd{col} DATA{col} 0 PWL('+' '.join(f'{t}u {v}' for t,v in points)+')')
 lines.append('Xbank '+' '.join(orders)+' '+f['flat_subcircuit']);nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+['READOUT0','RECOV']
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 160u 0 2u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);sp=B/'tools/source_snapshots'/(stem+'.py');sp.write_bytes(Path(__file__).read_bytes());files.add(sp)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 out=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_bank_replica_two_row_recovery_observed=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,scope='One160us actual213MOS69MIM physical bank plus shared analog column0 replica reader. All64 analog states initialized through independent row controls; row0 and row7 recovered sequentially by same reader; actual2154 flat routing-C branches, full source/GDS DRC0/LVS and LEF. Replica sink shares bank NF mirror BIAS; existing bank actual read sinks remain. No fitted numerical inverse or ideal buffer. External analog DATA,1uA NF/PF references and categorical row/reader-enable commands. Rows serviced sequentially; other seven columns retain raw outputs. Typical27C/noise-off/mismatch disabled. Not5ms parent retention, full8column read support, global scheduling, model accuracy or chip completion.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];out['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==68 and np.isfinite(w).all() and abs(t[-1]-160e-6)<1e-12 and 'aborted' not in log.lower())
  if out['module_simulation_completed']:
   at=lambda c,s:float(np.interp(s,t,w[:,c]));cases=[]
   for row,when in [(0,115e-6),(7,150e-6)]:
    actual=at(1+8*row,when);rec=at(66,when);cases.append(dict(row=row,state_v=actual,recovered_v=rec,reconstruction_error_v=rec-actual,raw_read_v=at(65,when)))
   out['cases']=cases;out['max_reconstruction_error_v']=max(abs(c['reconstruction_error_v']) for c in cases);out['max_final_state_change_v']=max(abs(at(j+1,159.8e-6)-at(j+1,85e-6)) for j in range(64));out['native_bank_replica_two_row_recovery_observed']=bool(out['max_reconstruction_error_v']<.01 and out['max_final_state_change_v']<.03);out['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))
 except Exception as e:out['postprocess_error']=str(e)
 out['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='sha256'},indent=2));assert out['module_simulation_completed']
if __name__=='__main__':main()

