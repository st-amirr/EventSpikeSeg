"""Native physical bank/replica-reader sequence; one column recovers two held rows."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_column_mux8_v2';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'];files={Path(__file__),qp,fp};src=d/(f['flat_subcircuit']+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);text=src.read_text();orders=re.search(r'(?m)^\.subckt\s+'+f['flat_subcircuit']+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert orders==q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_eight_column_select_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Actual physical bank and analog replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','Vdummy DUMMY 0 0']
 for i in range(8):
  lines.append(f'Vin{i} IN{i} 0 {0.1+.05*i}')
  pulse='PWL(0 3.3 7.8u 3.3 7.9u 0 64u 0)' if i==0 else f'PWL(0 0 {8*i-.1}u 0 {8*i}u 3.3 {8*i+7.8}u 3.3 {8*i+7.9}u 0 64u 0)'
  lines.append(f'Vs{i} SEL{i} 0 '+pulse)
 lines+=['Cexternal OUT 0 100f','Xmux '+' '.join(orders)+' '+f['flat_subcircuit']];nodes=['OUT']
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 64u 0 .05u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);sp=B/'tools/source_snapshots'/(stem+'.py');sp.write_bytes(Path(__file__).read_bytes());files.add(sp)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 out=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_eight_column_selection_observed=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,scope='One64us native32MOS eight-column analog TG selection sequence. Physical source/GDS DRC0,LVS,LEF and196 flat interconnect C branches retained. Actual eight NF/PF TGs with native inverter complements. External one-hot controls use100ns break before make, ideal analog inputs0.10..0.45V and100fF external output load. Selected output sampled7us after each selection. No ideal switches, numeric conversion, ADC or QAT. Typical27C/noise-off/mismatch disabled; actual bank/reader loading and global service remain to connect.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];out['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==3 and np.isfinite(w).all() and abs(t[-1]-64e-6)<1e-12 and 'aborted' not in log.lower())
  if out['module_simulation_completed']:
   at=lambda c,s:float(np.interp(s,t,w[:,c]));cases=[]
   for i in range(8):
    target=.1+.05*i;v=at(1,(i*8+7)*1e-6);cases.append(dict(column=i,target_v=target,output_v=v,selection_error_v=v-target))
   out['cases']=cases;out['max_selection_error_v']=max(abs(c['selection_error_v']) for c in cases);out['native_eight_column_selection_observed']=bool(out['max_selection_error_v']<.001);out['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))

 except Exception as e:out['postprocess_error']=str(e)
 out['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='sha256'},indent=2));assert out['module_simulation_completed']
if __name__=='__main__':main()

