"""Three-address nominal native full-C higher bank command simulation."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';cell='gf180_bank_page_decoder8_v1';d=B/'layout'/cell
q=json.loads((d/'qualification.json').read_text());fq=json.loads((d/'flat_cap_full_qualification.json').read_text());src=d/(cell+'_fullcap.spice');assert hashlib.sha256(src.read_bytes()).hexdigest()==fq['sha256'][src.relative_to(R).as_posix()]
stem=cell+'_three_address_loaded_v1';rp=B/'results'/(stem+'.json');assert not rp.exists();data=rp.with_suffix('.dat');models=B/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+models.relative_to(R).as_posix()
lines=['Native8way higher bank selector three addresses',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0']
def wave(n,pts):lines.append('V'+n+' '+n+' 0 PWL('+' '.join(f'{t}u {v}' for t,v in pts)+')')
for bit in range(3):wave('A'+str(bit),[(0,0),(2.9,0),(3,3.3 if 3&(1<<bit) else 0),(5.9,3.3 if 3&(1<<bit) else 0),(6,3.3),(9,3.3)])
for mode,delay in [('WRITE',0),('READ',1)]:wave(mode+'_CMD',[(0,0)]+[(t+delay,v) for t,v in [(.49,0),(.5,3.3),(.99,3.3),(1,0),(3.49,0),(3.5,3.3),(3.99,3.3),(4,0),(6.49,0),(6.5,3.3),(6.99,3.3),(7,0)]]+[(9,0)])
outputs=[f'{m}{i}' for i in range(8) for m in ['WRITE','READ']]
for i,n in enumerate(outputs):lines.append(f'Cload{i} {n} 0 100f')
lines+=['Xdecoder '+' '.join(q['ports'])+' '+cell,'.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .002u 9u','wrdata /workspace/'+data.relative_to(R).as_posix()+' '+' '.join('v('+n+')' for n in outputs),'quit','.endc','.end']
deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()];run=subprocess.run(cmd,capture_output=True,text=True,timeout=135);rp.with_suffix('.log').write_text(run.stdout+run.stderr)
o=dict(module_simulation_completed=False,loaded_command_selection_pass=False,scope='Three addresses0,3,7,both READ and WRITE,actual166MOS1242native capacitance branches.100fF external output loads are engineering fixture,not measured full-array fanout. No storage or5ms/full-chip acceptance.',returncode=run.returncode)
if data.exists():
 w=np.loadtxt(data,skiprows=1);o['module_simulation_completed']=bool(run.returncode==0 and w.shape[1]==17 and np.isfinite(w).all() and abs(w[-1,0]-9e-6)<1e-12);cases=[]
 for phase,addr in enumerate([0,3,7]):
  for mode,dt in [('WRITE',.8),('READ',1.8)]:
   values={n:float(np.interp((3*phase+dt)*1e-6,w[:,0],w[:,j+1])) for j,n in enumerate(outputs)};expected=mode+str(addr);cases.append(dict(address=addr,command=mode,selected_v=values[expected],unselected_max_v=max(v for n,v in values.items() if n!=expected),pass_nominal=values[expected]>3 and max(v for n,v in values.items() if n!=expected)<.3))
 o['cases']=cases;o['loaded_command_selection_pass']=bool(o['module_simulation_completed'] and all(c['pass_nominal'] for c in cases))
o['sha256']={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),src,deck,d/'qualification.json',d/'flat_cap_full_qualification.json']};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
