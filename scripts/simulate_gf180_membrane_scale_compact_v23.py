from __future__ import annotations
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
CELL='gf180_membrane_scale_compact_v23'
NAME='gf180_membrane_scale_compact_v23_hold5ms'
models=BASE/'pdk/gf180_primitive_source/models/ngspice'
cell=BASE/'layout'/CELL
q=json.loads((cell/'qualification.json').read_text())
assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 PWL(0 0 1u 0 1.01u 3.3 3u 3.3 3.01u 0 5.1m 0)','Vwriteb WRITEB 0 PWL(0 3.3 1u 3.3 1.01u 0 3u 0 3.01u 3.3 5.1m 3.3)']
for tag,v in [('lo',.75),('mid',1.65),('hi',2.55)]:
 lines += [f'Vprogram_{tag} PROGRAM_{tag} 0 {v}',f'Vmeter_{tag} out_{tag} 0 0',f'Xdut_{tag} PROGRAM_{tag} WRITE WRITEB VCM out_{tag} VDD VSS STATE_{tag} {CELL}',f'.ic v(STATE_{tag})=1.65']
lines += ['.control','set numdgt=15','tran 1u 5.1m 0 1u uic']
for tag in ('lo','mid','hi'):
 lines += [f'meas tran state_{tag}_early find v(STATE_{tag}) at=4u',f'meas tran state_{tag}_5ms find v(STATE_{tag}) at=5m',f'meas tran current_{tag}_5ms avg i(Vmeter_{tag}) from=4.999m to=5.001m']
lines += ['quit','.endc','.end','']
bench=BASE/'benches'/f'{NAME}.spice'; out=BASE/'results'/f'{NAME}.json'; logp=BASE/'results'/f'{NAME}.log'
assert not any(p.exists() for p in (bench,out,logp))
bench.write_text('\n'.join(lines),encoding='utf-8')
r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
log=r.stdout+r.stderr;logp.write_text(log,encoding='utf-8')
values={k:float(v) for k,v in re.findall(r'(?mi)^((?:state_(?:lo|mid|hi)_(?:early|5ms))|(?:current_(?:lo|mid|hi)_5ms))\s*=\s*([-+0-9.eE]+)',log)}
complete=r.returncode==0 and len(values)==9 and 'timestep too small' not in log.lower()
report={'simulation_completed':complete,'returncode':r.returncode,'cell':CELL,'hold_s':0.005,'models':'GF180 primitive typical, 27C; extracted compact cell netlist and child hierarchy','values':values,'scope':'Single-cell write-and-hold electrical smoke across three gate-command voltages. This is not scale linearity, PVT/noise, full-float recurrence accuracy, full population service, or full-chip qualification.','outputs':{'bench':bench.relative_to(ROOT).as_posix(),'log':logp.relative_to(ROOT).as_posix()}}
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if not complete: raise RuntimeError(log[-2500:])

