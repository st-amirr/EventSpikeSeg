from __future__ import annotations
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'; CELL='gf180_membrane_scale_compact_v23'; NAME='gf180_membrane_scale_compact_v23_transfer69'
models=BASE/'pdk/gf180_primitive_source/models/ngspice'; cell=BASE/'layout'/CELL; q=json.loads((cell/'qualification.json').read_text()); assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
points=[.75+i*.025 for i in range(69)]
lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 PWL(0 0 1u 0 1.01u 3.3 3u 3.3 3.01u 0 5.1m 0)','Vwriteb WRITEB 0 PWL(0 3.3 1u 3.3 1.01u 0 3u 0 3.01u 3.3 5.1m 3.3)']
for i,v in enumerate(points):
 tag=f'p{i:02d}'; lines += [f'Vprogram_{tag} PROGRAM_{tag} 0 {v:.4f}',f'Vmeter_{tag} out_{tag} 0 0',f'Xdut_{tag} PROGRAM_{tag} WRITE WRITEB VCM out_{tag} VDD VSS STATE_{tag} {CELL}',f'.ic v(STATE_{tag})=1.65']
lines += ['.control','set numdgt=15','tran 1u 5.1m 0 1u uic']
for i in range(len(points)):
 tag=f'p{i:02d}'; lines += [f'meas tran state_{tag} find v(STATE_{tag}) at=5m',f'meas tran current_{tag} avg i(Vmeter_{tag}) from=4.999m to=5.001m']
lines += ['quit','.endc','.end','']
bench=BASE/'benches'/f'{NAME}.spice'; logp=BASE/'results'/f'{NAME}.log'; out=BASE/'results'/f'{NAME}.json'; assert not any(p.exists() for p in (bench,logp,out)); bench.write_text('\n'.join(lines),encoding='utf-8')
r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135); log=r.stdout+r.stderr; logp.write_text(log,encoding='utf-8'); vals={k:float(v) for k,v in re.findall(r'(?mi)^((?:state|current)_p\d+)\s*=\s*([-+0-9.eE]+)',log)}; complete=r.returncode==0 and len(vals)==138 and 'timestep too small' not in log.lower()
curve=[{'command_v':v,'state_v':vals.get(f'state_p{i:02d}'),'current_a':vals.get(f'current_p{i:02d}')} for i,v in enumerate(points)]
report={'simulation_completed':complete,'returncode':r.returncode,'cell':CELL,'model':'GF180 typical, 27C, extracted compact cell including routed parasitics','write_pulse':'1.01us to 3.00us; hold observed at 5ms','curve':curve,'scope':'Nominal monotonicity/transfer characterization only; not PVT/noise/mismatch, signed-event accumulation, full-float inference, or 5ms population service.','bench':bench.relative_to(ROOT).as_posix(),'log':logp.relative_to(ROOT).as_posix()}; out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'complete':complete,'points':len(curve),'curve':curve},indent=2));
if not complete: raise RuntimeError(log[-2000:])


