import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_membrane_scale_compact_v23';NAME='gf180_membrane_scale_compact_v23_transfer_dc73';models=BASE/'pdk/gf180_primitive_source/models/ngspice';cell=BASE/'layout'/CELL;report=BASE/'results'/f'{NAME}.json';bench=BASE/'benches'/f'{NAME}.spice';logp=BASE/'results'/f'{NAME}.log';data=BASE/'results'/f'{NAME}.dat'
q=json.loads((cell/'qualification.json').read_text());assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
assert not any(p.exists() for p in (report,bench,logp,data))
lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 3.3','Vwriteb WRITEB 0 0','Vprogram PROGRAM 0 0.75','Vmeter OUT 0 0',f'Xdut PROGRAM WRITE WRITEB VCM OUT VDD VSS STATE {CELL}','.control','set numdgt=15','dc Vprogram 0.75 2.55 0.025',f'wrdata /workspace/{data.relative_to(ROOT).as_posix()} v(PROGRAM) v(STATE) i(Vmeter)','quit','.endc','.end','']
bench.write_text('\n'.join(lines),encoding='utf-8');r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;logp.write_text(log,encoding='utf-8')
rows=[]
if data.exists():
 for line in data.read_text().splitlines():
  vals=re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?',line)
  if len(vals)>=3: rows.append([float(v) for v in vals[-3:]])
curve=[{'command_v':r[0],'state_v':r[1],'current_a':r[2]} for r in rows]
complete=r.returncode==0 and len(curve)==73 and all(curve[i]['current_a']>curve[i+1]['current_a'] for i in range(len(curve)-1))
result={'simulation_completed':complete,'returncode':r.returncode,'cell':CELL,'analysis':'DC steady-state sweep of extracted v23 with write TG continuously enabled; includes routed parasitics but omits 5ms switch-off leakage during transfer sampling','point_count':len(curve),'step_v':0.025,'curve':curve,'scope':'Fine nominal transfer characterization only; the separate transient report covers 5ms hold at three voltages. No PVT/noise/mismatch, signed current, recurrence accuracy or population service.','bench':bench.relative_to(ROOT).as_posix(),'log':logp.relative_to(ROOT).as_posix(),'data':data.relative_to(ROOT).as_posix()};report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'completed':complete,'rows':len(curve),'first':curve[:2],'last':curve[-2:]},indent=2));
if not complete: raise RuntimeError(log[-1800:])
