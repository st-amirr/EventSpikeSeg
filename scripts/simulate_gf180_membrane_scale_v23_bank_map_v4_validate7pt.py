import json,re,subprocess,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_membrane_scale_compact_v23';NAME='gf180_membrane_scale_v23_bank_map_v4_validate7pt';models=BASE/'pdk/gf180_primitive_source/models/ngspice';cell=BASE/'layout'/CELL;manifest=json.loads((BASE/'assembly/membrane_voltage_scale_manifest_v2.json').read_text());scales=sorted(.9/float(x) for a in manifest['actors'] for x in a['range_abs_model_units']);smax=scales[-1];dc=json.loads((BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json').read_text())['curve'];hold=json.loads((BASE/'results/gf180_membrane_scale_v23_bank_map_validate21pt_v1.json').read_text())['cases'];hp=sorted((x['measured_state_5ms_v'],x['command_v']) for x in hold);imax=dc[0]['current_a']
def quant(q):
 x=(len(scales)-1)*q;lo=math.floor(x);hi=math.ceil(x);return scales[lo] if lo==hi else scales[lo]*(hi-x)+scales[hi]*(x-lo)
def st_for_i(i):
 for a,b in zip(dc,dc[1:]):
  if a['current_a']>=i>=b['current_a']:return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
def cmd_for_state(s):
 for (s0,c0),(s1,c1) in zip(hp,hp[1:]):
  if s0<=s<=s1:return c0+(s-s0)*(c1-c0)/(s1-s0)
 if s<hp[0][0]:
  (s0,c0),(s1,c1)=hp[0],hp[1];return c0+(s-s0)*(c1-c0)/(s1-s0)
 (s0,c0),(s1,c1)=hp[-2],hp[-1];return c0+(s-s0)*(c1-c0)/(s1-s0)
qs=[0,.025,.05,.5,.95,.975,1];cases=[]
for j,q in enumerate(qs):
 sc=quant(q);target=imax*sc/smax;st=st_for_i(target);cases.append({'tag':f'p{j}','q':q,'target_current_a':target,'target_state_v':st,'command_v':cmd_for_state(st)})
lines=[f'.include /workspace/{models.relative_to(ROOT).as_posix()}/design.spice',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice typical',f'.lib /workspace/{models.relative_to(ROOT).as_posix()}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',f'.include /workspace/{(cell/f"{CELL}.spice").relative_to(ROOT).as_posix()}','.global VSUBS','Vsub VSUBS 0 0','VDDsrc VDD 0 3.3','VCMsrc VCM 0 1.65','Vwrite WRITE 0 PWL(0 0 1u 0 1.01u 3.3 3u 3.3 3.01u 0 5.1m 0)','Vwriteb WRITEB 0 PWL(0 3.3 1u 3.3 1.01u 0 3u 0 3.01u 3.3 5.1m 3.3)']
for c in cases:lines += [f"Vprogram_{c['tag']} PROGRAM_{c['tag']} 0 {c['command_v']:.12f}",f"Vmeter_{c['tag']} OUT_{c['tag']} 0 0",f"Xdut_{c['tag']} PROGRAM_{c['tag']} WRITE WRITEB VCM OUT_{c['tag']} VDD VSS STATE_{c['tag']} {CELL}",f".ic v(STATE_{c['tag']})=1.65"]
lines+=['.control','set numdgt=15','tran 1u 5.1m 0 1u uic']
for c in cases:lines += [f"meas tran state_{c['tag']} find v(STATE_{c['tag']}) at=5m",f"meas tran current_{c['tag']} avg i(Vmeter_{c['tag']}) from=4.999m to=5.001m"]
lines+=['quit','.endc','.end',''];bench=BASE/'benches'/f'{NAME}.spice';logp=BASE/'results'/f'{NAME}.log';out=BASE/'results'/f'{NAME}.json';assert not any(x.exists() for x in (bench,logp,out));bench.write_text('\n'.join(lines),encoding='utf8');r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;logp.write_text(log,encoding='utf8');vals={k:float(v) for k,v in re.findall(r'(?mi)^((?:state|current)_p\d)\s*=\s*([-+0-9.eE]+)',log)};assert r.returncode==0 and len(vals)==14 and 'timestep too small' not in log.lower(),log[-1000:]
for c in cases:c['state_5ms_v']=vals['state_'+c['tag']];c['current_5ms_a']=vals['current_'+c['tag']];c['hold_error_mv']=(c['state_5ms_v']-c['target_state_v'])*1000;c['relative_current_error']=(c['current_5ms_a']-c['target_current_a'])/c['target_current_a']
report={'simulation_completed':True,'points':len(cases),'hold_s':.005,'cases':cases,'max_abs_relative_current_error':max(abs(c['relative_current_error']) for c in cases),'scope':'Selected-point transient qualification for the v4 state-inverse calibration method. Nominal typical only; full curve and recurrence still open.'};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'max_abs_relative_current_error':report['max_abs_relative_current_error'],'cases':cases},indent=2))
