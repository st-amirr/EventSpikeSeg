"""Compose extracted signed-event injection and physical membrane state/update cells."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_signed_charge_state_update_v12'
source_paths=[BASE/'layout/gf180_signed_weight_charge_parent_v2/gf180_signed_weight_charge_parent_v2_cap.spice',BASE/'layout/gf180_nf_state_update_aux_overlap/gf180_nf_state_update_aux_overlap_cap.spice']
models=BASE/'pdk/gf180_primitive_source/models/ngspice';bench=BASE/'benches'/f'{CELL}.spice';logp=BASE/'results'/f'{CELL}.log';out=BASE/'results'/f'{CELL}.json'
assert not out.exists()
def subckts(path):
 text=path.read_text(encoding='utf8',errors='replace');chunks=re.split(r'(?im)(?=^\.subckt\s+)',text);found={}
 for chunk in chunks:
  m=re.match(r'(?im)^\.subckt\s+(\S+)',chunk)
  if not m:continue
  end=re.search(r'(?im)^\.ends(?:\s+\S+)?\s*$',chunk);assert end, f'missing .ends: {path} {m.group(1)}'
  name=m.group(1);body=chunk[:end.end()].strip()
  if name in found:assert re.sub(r'\s+',' ',found[name])==re.sub(r'\s+',' ',body),f'conflicting duplicate subckt {name}'
  found[name]=body
 return found
merged={}
for path_index,path in enumerate(source_paths):
 for name,body in subckts(path).items():
  if path_index==1:
   newname=name+'_composed';body=re.sub(r'\b'+re.escape(name)+r'\b',newname,body);name=newname
  if name in merged:assert re.sub(r'\s+',' ',merged[name])==re.sub(r'\s+',' ',body),f'conflicting duplicate subckt {name}'
  merged[name]=body
cases=[('n45',1.5,1,2.7,.45),('n50',1.5,1,2.7,.50),('n55',1.5,1,2.7,.55),('n60',1.5,1,2.7,.60)]
design=(models/'design.spice').relative_to(ROOT).as_posix();model=(models/'sm141064.spice').relative_to(ROOT).as_posix()
lines=['GF180 extracted signed charge + native state/update cell integration','* Original epoch58 float semantics; analog transistor path only.',f'.include /workspace/{design}',f'.lib /workspace/{model} typical',f'.lib /workspace/{model} mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18','.global VSUBS','Vsub VSUBS 0 0']+list(merged.values())
lines += ['Vdd vdd 0 3.3','Vbias bias 0 .75','Vwrite writecommand 0 PWL(0 3.3 1009.99u 3.3 1010u 0 1300u 0)','Varm armcommand 0 PWL(0 0 1039.99u 0 1040u 3.3 1240u 3.3 1240.01u 0 1300u 0)','Vresetref resetref 0 1.2','Vrampbias rampbias 0 2.6','Vrampcas rampcas 0 2.2','Vvcm vcm 0 1.65','Vpcas pcas 0 2.2','Vncas ncas 0 1.1','Vbeta beta 0 PWL(0 0 1249u 0 1250u 3.3 1300u 3.3 1301u 0 1310u 0)','Vauxreset auxreset 0 PWL(0 3.3 2u 3.3 2.01u 0 1300u 0)','Xb_write writecommand writeb vdd 0 gf180_phase_inverter_fullroute','Xc_write writeb write vdd 0 gf180_phase_inverter_fullroute','Xb_arm armcommand armb vdd 0 gf180_phase_inverter_fullroute','Xc_arm armb arm vdd 0 gf180_phase_inverter_fullroute']
for tag,mag,negative,pbias,nbias in cases:
 sign=3.3 if negative else 0; data=mag
 lines += [f'Vpprogram_{tag} pprogram_{tag} 0 {pbias}',f'Vnprogram_{tag} nprogram_{tag} 0 {nbias}',f'Vsign_{tag} sign_{tag} 0 {sign}',f'Vdata_{tag} data_{tag} 0 PWL(0 {data} 1014.99u {data} 1015u 1.4 1300u 1.4)',f'Xstate_{tag} state_{tag} aux_{tag} vcm write writeb auxreset beta auxref_{tag} vcm 0 vdd gf180_nf_state_update_aux_overlap_composed',f'Vauxref_{tag} auxref_{tag} 0 1.65',f'Vmeter_{tag} state_{tag} tap_{tag} 0',f'Xinject_{tag} data_{tag} write writeb arm armb bias resetref rampbias rampcas vdd 0 sign_{tag} tap_{tag} park_{tag} pprogram_{tag} nprogram_{tag} pcas ncas pulse_{tag} pulseb_{tag} pos_{tag} neg_{tag} gf180_signed_weight_charge_parent_v2',f'Vpark_{tag} park_{tag} 0 1.65',f'.ic v(state_{tag})=1.65 v(aux_{tag})=1.65']
lines += ['.control','set numdgt=15','tran .02u 1310u 0 .2u uic']
for tag,_,_,_,_ in cases:lines += [f'meas tran state_before_{tag} find v(state_{tag}) at=1030u',f'meas tran state_after_event_{tag} find v(state_{tag}) at=1245u',f'meas tran aux_after_event_{tag} find v(aux_{tag}) at=1245u',f'meas tran state_after_beta_{tag} find v(state_{tag}) at=1300u',f'meas tran state_at_1p3ms_{tag} find v(state_{tag}) at=1.3m',f'meas tran event_charge_{tag} integ i(Vmeter_{tag}) from=1040u to=1240u',f'meas tran pulse_hi_{tag} max v(pulse_{tag}) from=1030u to=1250u']
lines += ['quit','.endc','.end',''];bench.write_text('\n'.join(lines),encoding='utf8')
if logp.exists():log=logp.read_text(encoding='utf8');returncode=0
else:
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','150','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=160);log=run.stdout+run.stderr;logp.write_text(log,encoding='utf8');returncode=run.returncode
vals={k:float(v) for k,v in re.findall(r'(?mi)^([a-z][a-z0-9_]+)\s*=\s*([-+0-9.eE]+)',log)}
keys=[f'{what}_{tag}' for tag,_,_,_,_ in cases for what in ('state_before','state_after_event','aux_after_event','state_after_beta','state_at_1p3ms','event_charge','pulse_hi')]
assert returncode==0 and all(k in vals for k in keys) and 'timestep too small' not in log.lower(),log[-2500:]
rows=[]
for tag,mag,negative,pbias,nbias in cases:
 x={k:vals[f'{k}_{tag}'] for k in ('state_before','state_after_event','aux_after_event','state_after_beta','state_at_1p3ms','event_charge','pulse_hi')};x.update({'case':tag,'weight_command_v':mag,'negative_sign':bool(negative),'event_state_step_v':x['state_after_event']-x['state_before'],'beta_state_step_v':x['state_after_beta']-x['state_after_event'],'state_at_1p3ms_delta_mv':(x['state_at_1p3ms']-x['state_after_beta'])*1000});rows.append(x)
r={'simulation_completed':True,'cell':CELL,'cases':rows,'scope':'One routed signed injector parent plus one extracted native state/update cell, connected at the physical STATE node. TT27, fixed external biases/phases, 1.3ms pulse and beta transient. State writer initializes at VCM, signed event deposits charge, then BETA phase exercises the extracted auxiliary-sharing transistor. No calibrated float-weight conversion, PVT/noise/mismatch, multi-event summation, threshold/reset/adaptation, dense array, 5ms population service or full-chip acceptance.','source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'bench_sha256':hashlib.sha256(bench.read_bytes()).hexdigest()}
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))





