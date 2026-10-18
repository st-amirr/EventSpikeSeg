"""Native physical bank/replica-reader sequence; one column recovers two held rows."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_row_staged_writeback_v1';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'];files={Path(__file__),qp,fp};src=d/(f['flat_subcircuit']+'_cap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()];files.add(src);text=src.read_text();orders=re.search(r'(?m)^\.subckt\s+'+f['flat_subcircuit']+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert orders==q['ports']
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(R).as_posix();stem=cell+'_native_complete_row_commit_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists();dp=rp.with_suffix('.dat')
 lines=['Actual physical bank and analog replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',text,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','In 0 BIAS 1u','Iio IO_BIAS 0 9u']
 for row in range(8):
  pulse='PWL(0 3.3 7.9u 3.3 8u 0 180u 0)' if row!=7 else 'PWL(0 3.3 7.9u 3.3 8u 0 149.9u 0 150u 3.3 157.9u 3.3 158u 0 180u 0)'
  lines.extend([f'Vw{row} WRITE{row} 0 '+pulse,f'Vr{row} READ{row} 0 0'])
 points=[(0,1.2)]
 for col in range(8):
  start=20+15*col;target=1+.05*col;points.extend([(start-.1,1.2 if col==0 else 1+.05*(col-1)),(start,target)])
  on=start+6;off=start+12
  for suffix,hi,lo in [('',3.3,0),('B',0,3.3)]:lines.append(f'Vcap{suffix}{col} CAP{suffix}{col} 0 PWL(0 {hi} 4.9u {hi} 5u {lo} {on-.1}u {lo} {on}u {hi} {off-.1}u {hi} {off}u {lo} 180u {lo})')
 points.extend([(139.9,1.35),(140,0),(180,0)]);lines.append('Vcompute COMPUTE_OUT 0 PWL('+' '.join(f'{t}u {v}' for t,v in points)+')')
 lines.append('Xbank '+' '.join(orders)+' '+f['flat_subcircuit']);nodes=[f'STATE{r}{c}' for r in range(8) for c in range(8)]+[f'DATA{i}' for i in range(8)]+['COMPUTE_OUT']
 lines+=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .02u 180u 0 2u','wrdata /workspace/'+dp.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);sp=B/'tools/source_snapshots'/(stem+'.py');sp.write_bytes(Path(__file__).read_bytes());files.add(sp)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log);files.add(lp)
 out=dict(module_simulation_completed=False,simulator_returncode=p.returncode,native_staged_row_commit_observed=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,full_chip_layout_complete=False,scope='One180us actual physical289MOS108MIM staged-writeback parent. All64analog bank states initialized through actual8row controls and eight real buffered analog DATA outputs. One shared native isolation amplifier buffers external COMPUTE_OUT; eight native TG/MIM output holders capture serial1.0..1.35V values, COMPUTE_OUT then changes0V, only row7writes all8held outputs. Every native flat parent routing capacitor retained,source/GDS DRC0/LVS/LEF. No ideal internal holding voltage,ideal switches,ADC,QAT or numerical digital state. External master IO9uA for9PF references,NF1uA,VCM1.2V and categorical phases. Typical27C/noise-off/mismatch disabled. This tests complete row commit and preservation of56unselected cells; not compute operation,full5ms parent hold,calibrated model precision,service or full chip. Spacious characterization footprint not dense capacity area.')
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);t=w[:,0];out['module_simulation_completed']=bool(p.returncode==0 and w.shape[1]==75 and np.isfinite(w).all() and abs(t[-1]-180e-6)<1e-12 and 'aborted' not in log.lower())
  if out['module_simulation_completed']:
   at=lambda c,s:float(np.interp(s,t,w[:,c]));states=[];outputs=[]
   for col in range(8):
    target=1+.05*col;held=at(65+col,149e-6);final=at(57+col,179e-6);outputs.append(dict(column=col,target_v=target,held_column_v=held,holding_error_v=held-target,final_bank_state_v=final,final_error_v=final-target,write_release_error_vs_actual_column_v=final-held))
   for j in range(56):states.append(dict(state=nodes[j],before_capture_v=at(j+1,15e-6),before_commit_v=at(j+1,149e-6),after_commit_v=at(j+1,179e-6),total_change_v=at(j+1,179e-6)-at(j+1,15e-6),commit_change_v=at(j+1,179e-6)-at(j+1,149e-6)))
   out['cases']=[dict(sequence='8serial analog captures,one8column row7commit,56unselected states preserved')];out['columns']=outputs;out['unselected_states']=states;out['max_holding_error_v']=max(abs(c['holding_error_v']) for c in outputs);out['max_final_writeback_error_v']=max(abs(c['final_error_v']) for c in outputs);out['max_unselected_state_change_v']=max(abs(c['total_change_v']) for c in states);out['max_unselected_commit_change_v']=max(abs(c['commit_change_v']) for c in states);out['native_staged_row_commit_observed']=bool(out['max_final_writeback_error_v']<.06 and out['max_unselected_state_change_v']<.03);out['VDD_supply_energy_j_excludes_external_fixtures']=float(np.trapezoid(-3.3*w[:,-1],t))

 except Exception as e:out['postprocess_error']=str(e)
 out['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['sha256','columns','unselected_states']},indent=2));assert out['module_simulation_completed']
if __name__=='__main__':main()

