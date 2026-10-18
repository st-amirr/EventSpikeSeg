import json,re,subprocess,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_membrane_scale_compact_v23';models=BASE/'pdk/gf180_primitive_source/models/ngspice';cell=BASE/'layout'/CELL;manifest=json.loads((BASE/'assembly/membrane_voltage_scale_manifest_v2.json').read_text());scales=sorted(.9/float(x) for a in manifest['actors'] for x in a['range_abs_model_units']);smax=scales[-1];dc=json.loads((BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json').read_text())['curve'];hold=json.loads((BASE/'results/gf180_membrane_scale_v23_bank_map_v4_validate41pt_batched.json').read_text())['cases'];hp=sorted((x['measured_state_5ms_v'],x['command_v']) for x in hold);imax=dc[0]['current_a'];raw=(BASE/'assembly/gf180_membrane_scale_v23_bank_program_volts_v6_residual_corrected.f64le').read_bytes();v6=struct.unpack('<'+'d'*(len(raw)//8),raw);pairs=sorted(zip([.9/float(x) for a in manifest['actors'] for x in a['range_abs_model_units']],v6))
def interp_cmd(scale):
 for (s0,c0),(s1,c1) in zip(pairs,pairs[1:]):
  if s0<=scale<=s1:return c0+(scale-s0)*(c1-c0)/(s1-s0)
 return pairs[0][1] if scale<pairs[0][0] else pairs[-1][1]
def quant(q):
 x=(len(scales)-1)*q;lo=math.floor(x);hi=math.ceil(x);return scales[lo] if lo==hi else scales[lo]*(hi-x)+scales[hi]*(x-lo)
def st_for_i(i):
 for a,b in zip(dc,dc[1:]):
  if a['current_a']>=i>=b['current_a']:return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
 raise ValueError(i)
def cmd_for_state(st):
 for (s0,c0),(s1,c1) in zip(hp,hp[1:]):
  if s0<=st<=s1:return c0+(st-s0)*(c1-c0)/(s1-s0)
 if st<hp[0][0]:
  (s0,c0),(s1,c1)=hp[0],hp[1];return c0+(st-s0)*(c1-c0)/(s1-s0)
 (s0,c0),(s1,c1)=hp[-2],hp[-1];return c0+(st-s0)*(c1-c0)/(s1-s0)
qs=[i/80 for i in range(81)];cases=[]
for idx,q in enumerate(qs):
 scale=quant(q);target=imax*scale/smax;state=st_for_i(target);cases.append({'tag':f'q{int(round(q*1000)):03d}','quantile':q,'target_current_a':target,'target_state_v':state,'command_v':interp_cmd(scale)})
allcases=[];logs=[]
for group,start in enumerate(range(0,len(cases),7)):
 groupcases=cases[start:start+7];name=f'gf180_membrane_scale_v23_bank_map_v6_validate81_chunk{group}';lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 PWL(0 0 1u 0 1.01u 3.3 3u 3.3 3.01u 0 5.1m 0)','Vwriteb WRITEB 0 PWL(0 3.3 1u 3.3 1.01u 0 3u 0 3.01u 3.3 5.1m 3.3)']
 for c in groupcases:lines += [f"Vprogram_{c['tag']} PROGRAM_{c['tag']} 0 {c['command_v']:.12f}",f"Vmeter_{c['tag']} OUT_{c['tag']} 0 0",f"Xdut_{c['tag']} PROGRAM_{c['tag']} WRITE WRITEB VCM OUT_{c['tag']} VDD VSS STATE_{c['tag']} {CELL}",f".ic v(STATE_{c['tag']})=1.65"]
 lines+=['.control','set numdgt=15','tran 1u 5.1m 0 1u uic']
 for c in groupcases:lines += [f"meas tran state_{c['tag']} find v(STATE_{c['tag']}) at=5m",f"meas tran current_{c['tag']} avg i(Vmeter_{c['tag']}) from=4.999m to=5.001m"]
 lines+=['quit','.endc','.end',''];bench=BASE/'benches'/f'{name}.spice';logp=BASE/'results'/f'{name}.log'
 if not logp.exists():
  bench.write_text('\n'.join(lines),encoding='utf8');run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;logp.write_text(log,encoding='utf8');assert run.returncode==0 and 'timestep too small' not in log.lower(),log[-1000:]
 else: log=logp.read_text(encoding='utf8')
 vals={k:float(v) for k,v in re.findall(r'(?mi)^((?:state|current)_q\d{3,4})\s*=\s*([-+0-9.eE]+)',log)};assert len(vals)==2*len(groupcases),log[-1000:];logs.append(logp.relative_to(ROOT).as_posix())
 for c in groupcases:c['measured_state_5ms_v']=vals['state_'+c['tag']];c['measured_current_5ms_a']=vals['current_'+c['tag']];c['hold_error_mv']=(c['measured_state_5ms_v']-c['target_state_v'])*1000;c['relative_current_error']=(c['measured_current_5ms_a']-c['target_current_a'])/c['target_current_a'];allcases.append(c)
report={'simulation_completed':True,'cell':CELL,'points':len(allcases),'hold_s':.005,'calibration_method':'DC inverse to target held state, then v5 residual-corrected command table','cases':allcases,'summary':{'max_abs_relative_current_error':max(abs(c['relative_current_error']) for c in allcases),'mean_abs_relative_current_error':sum(abs(c['relative_current_error']) for c in allcases)/len(allcases),'max_abs_hold_error_mv':max(abs(c['hold_error_mv']) for c in allcases),'mean_abs_hold_error_mv':sum(abs(c['hold_error_mv']) for c in allcases)/len(allcases)},'scope':'81-point 5ms transient verification in twelve batches of at most seven cells. Nominal typical only; no mismatch/noise/PVT or full recurrence acceptance.','logs':logs};out=BASE/'results/gf180_membrane_scale_v23_bank_map_v6_validate81pt_batched.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))



