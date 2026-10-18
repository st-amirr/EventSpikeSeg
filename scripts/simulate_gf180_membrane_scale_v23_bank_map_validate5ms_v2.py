import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_membrane_scale_compact_v23';NAME='gf180_membrane_scale_v23_bank_map_validate5ms_v2';models=BASE/'pdk/gf180_primitive_source/models/ngspice';cell=BASE/'layout'/CELL
cal=json.loads((BASE/'results/gf180_membrane_scale_v23_bank_calibration_v1.json').read_text());curve=json.loads((BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json').read_text())['curve']
volts=cal['quantile_program_voltage_v']; vr=cal['predicted_voltage_range_v']; cases=[('maxscale',vr[0]),('p99',volts['p99']),('p90',volts['p90']),('p50',volts['p50']),('p10',volts['p10']),('p01',volts['p01']),('minscale',vr[1])]
def dc_current(v):
 for a,b in zip(curve,curve[1:]):
  if a['command_v']<=v<=b['command_v']:
   return a['current_a']+(v-a['command_v'])*(b['current_a']-a['current_a'])/(b['command_v']-a['command_v'])
 raise ValueError(v)
q=json.loads((cell/'qualification.json').read_text());assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 PWL(0 0 1u 0 1.01u 3.3 3u 3.3 3.01u 0 5.1m 0)','Vwriteb WRITEB 0 PWL(0 3.3 1u 3.3 1.01u 0 3u 0 3.01u 3.3 5.1m 3.3)']
for tag,v in cases:lines += [f'Vprogram_{tag} PROGRAM_{tag} 0 {v:.12f}',f'Vmeter_{tag} OUT_{tag} 0 0',f'Xdut_{tag} PROGRAM_{tag} WRITE WRITEB VCM OUT_{tag} VDD VSS STATE_{tag} {CELL}',f'.ic v(STATE_{tag})=1.65']
lines += ['.control','set numdgt=15','tran 1u 5.1m 0 1u uic']
for tag,v in cases:lines += [f'meas tran state_{tag}_4us find v(STATE_{tag}) at=4u',f'meas tran state_{tag}_5ms find v(STATE_{tag}) at=5m',f'meas tran current_{tag}_5ms avg i(Vmeter_{tag}) from=4.999m to=5.001m']
lines += ['quit','.endc','.end','']
bench=BASE/'benches'/f'{NAME}.spice';logp=BASE/'results'/f'{NAME}.log';out=BASE/'results'/f'{NAME}.json';assert not any(p.exists() for p in (bench,logp,out));bench.write_text('\n'.join(lines),encoding='utf8')
r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;logp.write_text(log,encoding='utf8');vals={k:float(v) for k,v in re.findall(r'(?mi)^((?:state|current)_(?:maxscale|p99|p90|p50|p10|p01|minscale)_(?:4us|5ms))\s*=\s*([-+0-9.eE]+)',log)};complete=r.returncode==0 and len(vals)==21 and 'timestep too small' not in log.lower();results=[]
for tag,v in cases:
 measured=vals.get(f'current_{tag}_5ms');target=dc_current(v);early=vals.get(f'state_{tag}_4us');held=vals.get(f'state_{tag}_5ms');results.append({'bank_scale_percentile_or_endpoint':tag,'target_command_v':v,'measured_state_4us_v':early,'measured_state_5ms_v':held,'hold_error_mv':(held-v)*1000 if held is not None else None,'target_current_from_dc_a':target,'measured_5ms_current_a':measured,'relative_current_error':(measured-target)/target if measured is not None else None})
report={'simulation_completed':complete,'cell':CELL,'hold_s':.005,'model':'GF180 typical 27C, extracted v23 with route parasitics','cases':results,'scope':'Seven representative points from the inverse map were transiently programmed and held for 5ms. Comparison uses same-cell nominal DC transfer interpolation; not independent PVT/noise/mismatch or original-float recurrence acceptance.','calibration_report':(BASE/'results/gf180_membrane_scale_v23_bank_calibration_v1.json').relative_to(ROOT).as_posix(),'bench':bench.relative_to(ROOT).as_posix(),'log':logp.relative_to(ROOT).as_posix()};out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'complete':complete,'cases':results},indent=2));
if not complete:raise RuntimeError(log[-1800:])

