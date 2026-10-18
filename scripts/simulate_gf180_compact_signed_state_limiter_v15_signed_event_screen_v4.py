import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'
CELL='gf180_compact_signed_state_limiter_v15'; SIM=CELL+'_signed_event_screen_v4'
layout=BASE/'layout'/CELL; netlist=layout/f'{CELL}_cap.spice'; bench=BASE/'benches'/f'{SIM}.spice'; logp=BASE/'results'/f'{SIM}.log'; report=BASE/'results'/f'{SIM}.json'
assert not any(p.exists() for p in (bench,logp,report))
lines=['Compact GF180 signed injector + membrane + limiter extracted transient','* TT 27C; two independent 1us signed events then 5ms hold.',' .include /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/design.spice'.strip(),' .lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice typical'.strip(),' .lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice mimcap_typical'.strip(),'.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18','.global VSUBS','Vsub VSUBS 0 0',f'.include /workspace/{netlist.relative_to(ROOT).as_posix()}','Vdd vdd 0 3.3','Vss vss 0 0','Vpprogram pprogram 0 2.6','Vnprogram nprogram 0 0.613','Vpcas pcas 0 2.2','Vncas ncas 0 1.1','Vvcm vcm 0 1.65','Vdata data 0 1.5','Vaux aux 0 1.65','Vauxreset auxreset 0 0','Vbeta beta 0 0','Vauxref auxref 0 1.65','Vlo rail_lo 0 0.75','Vhi rail_hi 0 2.55','Vlimlo limlo 0 0','Vlimlob limlob 0 3.3','Vlimhi limhi 0 0','Vlimhib limhib 0 3.3']
def en_pulse(on):
 if not on: return 'PWL(0 0 6m 0)'
 return 'PWL(0 0 999.999u 0 1000u 3.3 1001u 3.3 1001.001u 0 6m 0)'
def enb_pulse(on):
 if not on: return 'PWL(0 3.3 6m 3.3)'
 return 'PWL(0 3.3 999.999u 3.3 1000u 0 1001u 0 1001.001u 3.3 6m 3.3)'
for tag,initial,pol in [('pos',1.5,'pos'),('neg',1.8,'neg')]:
 lines += [f'Vwrite_{tag} write_{tag} 0 PWL(0 3.3 1u 3.3 1.001u 0 6m 0)',f'Vwriteb_{tag} writeb_{tag} 0 PWL(0 0 1u 0 1.001u 3.3 6m 3.3)',f'Vpos_{tag} pos_{tag} 0 '+en_pulse(pol=='pos'),f'Vposb_{tag} posb_{tag} 0 '+enb_pulse(pol=='pos'),f'Vneg_{tag} neg_{tag} 0 '+en_pulse(pol=='neg'),f'Vnegb_{tag} negb_{tag} 0 '+enb_pulse(pol=='neg'),f'Xdut_{tag} pos_{tag} posb_{tag} neg_{tag} negb_{tag} pprogram nprogram pcas ncas state_{tag} data write_{tag} writeb_{tag} auxreset beta auxref vcm vdd vss rail_lo rail_hi limlo limlob limhi limhib {CELL}',f'.ic v(aux)=1.65']
lines += ['.control','set numdgt=15','tran .05u 6m 0 .05u uic']
for tag,_,_ in [('pos',0,''),('neg',0,'')]:
 lines += [f'meas tran {tag}_restored find v(state_{tag}) at=2u',f'meas tran {tag}_before find v(state_{tag}) at=999u',f'meas tran {tag}_after find v(state_{tag}) at=1002u',f'meas tran {tag}_hold find v(state_{tag}) at=6m']
lines += ['quit','.endc','.end',''];bench.write_text('\n'.join(lines),encoding='utf8')
run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','240','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=250)
log=run.stdout+run.stderr;logp.write_text(log,encoding='utf8');vals={k.lower():float(v) for k,v in re.findall(r'(?mi)^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)',log)}
keys=[f'{tag}_{k}' for tag in ('pos','neg') for k in ('restored','before','after','hold')]
assert run.returncode==0 and 'ngspice-47 done' in log.lower() and all(k in vals for k in keys),log[-2500:]
cases=[]
for tag in ('pos','neg'):
 r,b,a,h=(vals[f'{tag}_{k}'] for k in ('restored','before','after','hold'));cases.append({'polarity':tag,'after_restore_v':r,'before_event_v':b,'restore_to_event_drift_mv':(b-r)*1000,'after_1us_event_v':a,'state_change_mv':(a-b)*1000,'after_5ms_v':h,'hold_drift_mv':(h-a)*1000})
r={'simulation_completed':True,'cell':CELL,'corner':'GF180 typical, 27C','event_pulse_width_us':1.0,'cases':cases,'scope':'One routed compact physical injector/state/limiter parent with extracted parasitics; real transistor-level positive and negative injector gates are driven directly. External bias values are fixed, no calibrated analog weight mapper or sequencer, no threshold/reset/adaptation recurrence, no PVT/noise/mismatch or model accuracy. Clamp gates are held off for center-state event/hold screen.','source_sha256':{netlist.relative_to(ROOT).as_posix():hashlib.sha256(netlist.read_bytes()).hexdigest(),'layout_qualification.json':hashlib.sha256((layout/'qualification.json').read_bytes()).hexdigest(),'bench':hashlib.sha256(bench.read_bytes()).hexdigest()}}
report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))



