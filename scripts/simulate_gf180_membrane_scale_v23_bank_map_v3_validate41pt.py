import json,re,subprocess,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_membrane_scale_compact_v23';models=BASE/'pdk/gf180_primitive_source/models/ngspice';cell=BASE/'layout'/CELL
manifest=json.loads((BASE/'assembly/membrane_voltage_scale_manifest_v2.json').read_text());scales=sorted(.9/float(x) for a in manifest['actors'] for x in a['range_abs_model_units']);smax=scales[-1];transfer=json.loads((BASE/'results/gf180_membrane_scale_v23_bank_map_validate21pt_v1.json').read_text());points=sorted((x['command_v'],x['measured_current_5ms_a']) for x in transfer['cases']);dc=json.loads((BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json').read_text())['curve'];imax=dc[0]['current_a']
def quant(a,q):
 x=(len(a)-1)*q;lo=math.floor(x);hi=math.ceil(x);return a[lo] if lo==hi else a[lo]*(hi-x)+a[hi]*(x-lo)
def cmd(target):
 for (v0,i0),(v1,i1) in zip(points,points[1:]):
  if i0>=target>=i1:return v0+(target-i0)*(v1-v0)/(i1-i0)
 raise ValueError(target)
def state_for_current(i):
 for a,b in zip(dc,dc[1:]):
  if a['current_a']>=i>=b['current_a']:return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
 raise ValueError(i)
qvalues=[i/40 for i in range(41)];allcases=[]
for group,qs in enumerate((qvalues[:21],qvalues[20:])):
 cases=[]
 for j,q in enumerate(qs):
  scale=quant(scales,q);target=imax*scale/smax;cases.append({'tag':f'q{int(round(q*1000)):03d}','q':q,'scale':scale,'target_current_a':target,'target_state_v':state_for_current(target),'command_v':cmd(target)})
 name=f'gf180_membrane_scale_v23_bank_map_v3_validate41_group{group}';lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 PWL(0 0 1u 0 1.01u 3.3 3u 3.3 3.01u 0 5.1m 0)','Vwriteb WRITEB 0 PWL(0 3.3 1u 3.3 1.01u 0 3u 0 3.01u 3.3 5.1m 3.3)']
 for c in cases:lines += [f"Vprogram_{c['tag']} PROGRAM_{c['tag']} 0 {c['command_v']:.12f}",f"Vmeter_{c['tag']} OUT_{c['tag']} 0 0",f"Xdut_{c['tag']} PROGRAM_{c['tag']} WRITE WRITEB VCM OUT_{c['tag']} VDD VSS STATE_{c['tag']} {CELL}",f".ic v(STATE_{c['tag']})=1.65"]
 lines += ['.control','set numdgt=15','tran 1u 5.1m 0 1u uic']
 for c in cases:lines += [f"meas tran state_{c['tag']} find v(STATE_{c['tag']}) at=5m",f"meas tran current_{c['tag']} avg i(Vmeter_{c['tag']}) from=4.999m to=5.001m"]
 lines += ['quit','.endc','.end',''];bench=BASE/'benches'/f'{name}.spice';logp=BASE/'results'/f'{name}.log';assert not any(x.exists() for x in (bench,logp));bench.write_text('\n'.join(lines),encoding='utf8')
 r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;logp.write_text(log,encoding='utf8');vals={k:float(v) for k,v in re.findall(r'(?mi)^((?:state|current)_q\d{3})\s*=\s*([-+0-9.eE]+)',log)};assert r.returncode==0 and len(vals)==42 and 'timestep too small' not in log.lower(),log[-1600:]
 for c in cases:c['measured_state_5ms_v']=vals['state_'+c['tag']];c['measured_current_5ms_a']=vals['current_'+c['tag']];c['hold_error_mv']=(c['measured_state_5ms_v']-c['target_state_v'])*1000;c['relative_current_error']=(c['measured_current_5ms_a']-c['target_current_a'])/c['target_current_a']
 allcases.extend(cases)
out=BASE/'results/gf180_membrane_scale_v23_bank_map_v3_validate41pt.json';assert not out.exists();summary={'simulation_completed':True,'cell':CELL,'points':len(allcases),'hold_s':.005,'curve_used_for_map':'21 measured transient 5ms transfer points','quantiles':allcases,'summary':{'max_abs_relative_current_error':max(abs(c['relative_current_error']) for c in allcases),'mean_abs_relative_current_error':sum(abs(c['relative_current_error']) for c in allcases)/len(allcases),'max_abs_hold_error_mv':max(abs(c['hold_error_mv']) for c in allcases),'mean_abs_hold_error_mv':sum(abs(c['hold_error_mv']) for c in allcases)/len(allcases)},'scope':'41-point held-transient validation at 2.5% bank-scale quantiles, with endpoints and midpoints independent of the 21-point calibration nodes. Nominal GF180 typical only; no PVT/noise/mismatch or original-float recurrence.','bench_logs':[f'artifacts/analog_asic/results/gf180_membrane_scale_v23_bank_map_v3_validate41_group{i}.log' for i in range(2)]};out.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['summary'],indent=2))
