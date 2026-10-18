"""One bounded connected-page native write/isolation sequence; no accuracy gate."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';cell='gf180_selected_page1024_v1';d=B/'layout'/cell;q=json.loads((d/'qualification.json').read_text());fq=json.loads((d/'flat_cap_full_qualification.json').read_text());src=d/(cell+'_fullcap.spice');assert hashlib.sha256(src.read_bytes()).hexdigest()==fq['sha256'][src.relative_to(R).as_posix()]
stem=cell+'_native_two_page_write_v1';rp=B/'results'/(stem+'.json');assert not rp.exists();data=rp.with_suffix('.dat');models=B/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+models.relative_to(R).as_posix()
lines=['Connected1024state selected page',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','Vread READ_CMD 0 0']
def wave(n,pts):lines.append('V'+n+' '+n+' 0 PWL('+' '.join(f'{t}u {v}' for t,v in pts)+')')
for n in [f'LOW{i}' for i in range(4)]+[f'HIGH{i}' for i in range(3)]:wave(n,[(0,0),(.99,0),(1,3.3),(2,3.3)])
wave('WRITE_CMD',[(0,0),(.19,0),(.2,3.3),(.69,3.3),(.7,0),(1.19,0),(1.2,3.3),(1.69,3.3),(1.7,0),(2,0)])
for col in range(8):wave('DATA'+str(col),[(0,1.4-.01*col),(.99,1.4-.01*col),(1,.95+.01*col),(2,.95+.01*col)])
for i in range(8):
 for j in range(2):lines.append(f'Imaster{i}_{j} 0 P{i}_B{j}_BIAS 0')
states=[f'P{i}_B{j}_STATE{r}{c}' for i in range(8) for j in range(2) for r in range(8) for c in range(8)]
lines+=['.ic '+' '.join('v('+n+')=1.2' for n in states),'Xpage '+' '.join(q['ports'])+' '+cell,'.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .01u 2u 0 .02u uic','wrdata /workspace/'+data.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in states)+' i(Vdd)','quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');lp.write_text(run.stdout+run.stderr)
o=dict(module_simulation_completed=False,returncode=run.returncode,native_state_count=1024,mos_count=6326,native_cap_branches=60175,native_initialization_validated=False,full_chip_layout_complete=False,scope='One2us typical27C connected1024-state page write sequence. Page0bank0row0 thenpage7bank1row7;8shared analog DATA buses,actualnative higher selector. All1024states monitored. UIC1.2V seeds are fixtures,not qualifiednative init. Short.5us writes are observations,not20mV/model acceptance. No shared reader,compute,retention or5ms population-service proof.')
if data.exists():
 w=np.loadtxt(data,skiprows=1);t=w[:,0];o['module_simulation_completed']=bool(run.returncode==0 and w.shape[1]==1026 and np.isfinite(w).all() and abs(t[-1]-2e-6)<1e-12)
 if o['module_simulation_completed']:
  sample=lambda us:np.array([np.interp(us*1e-6,t,w[:,j+1]) for j in range(1024)])
  pre=sample(.15);after0=sample(.9);pre1=sample(1.1);after1=sample(1.9);selected0=np.arange(8);selected1=np.arange(1016,1024);mask0=np.ones(1024,dtype=bool);mask0[selected0]=False;mask1=np.ones(1024,dtype=bool);mask1[selected1]=False
  o.update(prewrite_state_range_v=[float(pre.min()),float(pre.max())],page0_written_v=after0[selected0].tolist(),page7_written_v=after1[selected1].tolist(),page0_write_max_error_v=float(np.max(abs(after0[selected0]-np.array([1.4-.01*c for c in range(8)])))),page7_write_max_error_v=float(np.max(abs(after1[selected1]-np.array([.95+.01*c for c in range(8)])))),unselected_final_change_during_first_write_v=float(np.max(abs((after0-pre)[mask0]))),unselected_final_change_during_second_write_v=float(np.max(abs((after1-pre1)[mask1]))))
o['sha256']={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),src,deck,lp,d/'qualification.json',d/'flat_cap_full_qualification.json']};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
