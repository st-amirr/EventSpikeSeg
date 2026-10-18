import json,re,subprocess,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_membrane_scale_compact_v23';NAME='gf180_membrane_scale_v23_bank_map_validate21pt_v1';models=BASE/'pdk/gf180_primitive_source/models/ngspice';cell=BASE/'layout'/CELL;m=json.loads((BASE/'assembly/membrane_voltage_scale_manifest_v2.json').read_text());scales=sorted(.9/float(r) for a in m['actors'] for r in a['range_abs_model_units']);curve=json.loads((BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json').read_text())['curve'];hold=json.loads((BASE/'results/gf180_membrane_scale_v23_bank_map_validate5ms_v2.json').read_text())
def quant(a,q):
 x=(len(a)-1)*q;lo=math.floor(x);hi=math.ceil(x);return a[lo] if lo==hi else a[lo]*(hi-x)+a[hi]*(x-lo)
def inverse_current(i):
 for a,b in zip(curve,curve[1:]):
  if a['current_a']>=i>=b['current_a']:return a['command_v']+(i-a['current_a'])*(b['command_v']-a['command_v'])/(b['current_a']-a['current_a'])
 raise ValueError(i)
h=sorted((x['target_command_v'],x['measured_state_5ms_v']) for x in hold['cases'])
def command_for_state(v):
 for (c0,s0),(c1,s1) in zip(h,h[1:]):
  if s0<=v<=s1:return c0+(v-s0)*(c1-c0)/(s1-s0)
 if abs(v-h[0][1])<1e-9:return h[0][0]
 if abs(v-h[-1][1])<1e-9:return h[-1][0]
 raise ValueError(v)
smax=max(scales);imax=curve[0]['current_a'];qvalues=[i/20 for i in range(21)];cases=[]
for idx,q in enumerate(qvalues):
 scale=quant(scales,q);target=imax*scale/smax;state=inverse_current(target);cmd=command_for_state(state);cases.append({'tag':f'q{idx:02d}','quantile':q,'scale':scale,'target_current_a':target,'target_state_v':state,'command_v':cmd})
qual=json.loads((cell/'qualification.json').read_text());assert qual['lvs_unique'] and qual['gds_roundtrip_lvs_unique']
lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 PWL(0 0 1u 0 1.01u 3.3 3u 3.3 3.01u 0 5.1m 0)','Vwriteb WRITEB 0 PWL(0 3.3 1u 3.3 1.01u 0 3u 0 3.01u 3.3 5.1m 3.3)']
for c in cases:lines += [f"Vprogram_{c['tag']} PROGRAM_{c['tag']} 0 {c['command_v']:.12f}",f"Vmeter_{c['tag']} OUT_{c['tag']} 0 0",f"Xdut_{c['tag']} PROGRAM_{c['tag']} WRITE WRITEB VCM OUT_{c['tag']} VDD VSS STATE_{c['tag']} {CELL}",f".ic v(STATE_{c['tag']})=1.65"]
lines += ['.control','set numdgt=15','tran 1u 5.1m 0 1u uic']
for c in cases:lines += [f"meas tran state_{c['tag']}_5ms find v(STATE_{c['tag']}) at=5m",f"meas tran current_{c['tag']}_5ms avg i(Vmeter_{c['tag']}) from=4.999m to=5.001m"]
lines += ['quit','.endc','.end',''];bench=BASE/'benches'/f'{NAME}.spice';logp=BASE/'results'/f'{NAME}.log';out=BASE/'results'/f'{NAME}.json';assert not any(p.exists() for p in (bench,logp,out));bench.write_text('\n'.join(lines),encoding='utf8')
r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;logp.write_text(log,encoding='utf8');vals={k:float(v) for k,v in re.findall(r'(?mi)^((?:state|current)_q\d{2}_5ms)\s*=\s*([-+0-9.eE]+)',log)};complete=r.returncode==0 and len(vals)==42 and 'timestep too small' not in log.lower()
for c in cases:
 tag=c['tag']; c['measured_state_5ms_v']=vals.get(f'state_{tag}_5ms');c['measured_current_5ms_a']=vals.get(f'current_{tag}_5ms');c['hold_error_mv']=(c['measured_state_5ms_v']-c['target_state_v'])*1000 if complete else None;c['relative_current_error']=(c['measured_current_5ms_a']-c['target_current_a'])/c['target_current_a'] if complete else None
report={'simulation_completed':complete,'cell':CELL,'hold_s':.005,'point_count':len(cases),'model':'GF180 typical 27C extracted v23 cell with routed parasitics','cases':cases,'summary':{'max_abs_relative_current_error':max(abs(c['relative_current_error']) for c in cases) if complete else None,'max_abs_hold_error_mv':max(abs(c['hold_error_mv']) for c in cases) if complete else None},'scope':'21-point nominal transient validation over the full float-derived bank-scale distribution. Uses an interpolated 7-point write-bias correction and DC inverse; no PVT/noise/mismatch or end-to-end recurrence accuracy.','sources':['artifacts/analog_asic/results/gf180_membrane_scale_v23_bank_calibration_v2.json','artifacts/analog_asic/results/gf180_membrane_scale_compact_v23_transfer_dc441.json'],'bench':bench.relative_to(ROOT).as_posix(),'log':logp.relative_to(ROOT).as_posix()};out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'complete':complete,'summary':report['summary'],'first':cases[0],'median':cases[10],'last':cases[-1]},indent=2));
if not complete:raise RuntimeError(log[-1600:])

