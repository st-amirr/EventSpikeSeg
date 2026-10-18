import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';CELL='gf180_sc_state_packet_compact_v12';layout=BASE/'layout'/CELL;netlist=layout/f'{CELL}_cap.spice';SIM=CELL+'_beta_aux_cap_sweep_v3';bench=BASE/'benches'/f'{SIM}.spice';logp=BASE/'results'/f'{SIM}.log';report=BASE/'results'/f'{SIM}.json';assert all(not p.exists() for p in (bench,logp,report))
L=['Extracted beta auxiliary-capacitance sweep; control pins otherwise inactive','.include /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/design.spice','.lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice typical','.lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice mimcap_typical','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18','.global VSUBS','Vsub VSUBS 0 0',f'.include /workspace/{netlist.relative_to(ROOT).as_posix()}']
cases=[]
for state,init in [('low',.75),('high',2.55)]:
 for cap_f in [0,4]:
  tag=f'{state}_c{cap_f}'
  L += [f'Vdd_{tag} vdd_{tag} 0 3.3',f'Vss_{tag} vss_{tag} 0 0',f'Vcm_{tag} vcm_{tag} 0 1.65',f'Vauxref_{tag} auxref_{tag} 0 1.65',f'Vdata_{tag} data_{tag} 0 {init}',f'Vwrite_{tag} write_{tag} 0 0',f'Vwriteb_{tag} writeb_{tag} 0 3.3',f'Vreset_{tag} reset_{tag} 0 PWL(0 3.3 1.999u 3.3 2u 0 60u 0)',f'Vbeta_{tag} beta_{tag} 0 PWL(0 0 19.999u 0 20u 3.3 34.999u 3.3 35u 0 60u 0)',f'Vtop_{tag} top_{tag} 0 0',f'Vtopb_{tag} topb_{tag} 0 3.3',f'Vsample_{tag} sample_{tag} 0 0',f'Vsampleb_{tag} sampleb_{tag} 0 3.3',f'Vdrive_{tag} drive_{tag} 0 0',f'Vdriveb_{tag} driveb_{tag} 0 3.3']
  if cap_f: L.append(f'Caux_{tag} aux_{tag} vcm_{tag} {cap_f}f')
  L += [f'Xdut_{tag} state_{tag} aux_{tag} data_{tag} write_{tag} writeb_{tag} reset_{tag} beta_{tag} auxref_{tag} vcm_{tag} vcm_{tag} top_{tag} topb_{tag} sample_{tag} sampleb_{tag} drive_{tag} driveb_{tag} pkt_top_{tag} pkt_bottom_{tag} vdd_{tag} vss_{tag} {CELL}',f'.ic v(state_{tag})={init} v(aux_{tag})=1.65 v(pkt_top_{tag})={init} v(pkt_bottom_{tag})={init}']
  cases.append((tag,state,init,cap_f))
L += ['.control','set numdgt=15','tran 10n 60u 0 10n uic']
for tag,*_ in cases:L += [f'meas tran {tag}_pre find v(state_{tag}) at=19u',f'meas tran {tag}_post find v(state_{tag}) at=40u']
L += ['quit','.endc','.end',''];bench.write_text('\n'.join(L),encoding='utf8')
run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=130);log=run.stdout+run.stderr;logp.write_text(log,encoding='utf8');vals={k.lower():float(v) for k,v in re.findall(r'(?mi)^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)',log)};keys=[f'{tag}_{n}' for tag,*_ in cases for n in ('pre','post')];assert run.returncode==0 and 'ngspice-47 done' in log.lower() and all(k in vals for k in keys),log[-2000:]
results=[]
for tag,state,init,cap_f in cases:
 pre=vals[f'{tag}_pre'];post=vals[f'{tag}_post'];dist=abs(init-1.65);frac=abs(post-pre)/dist;results.append({'state':state,'extra_aux_cap_ff':cap_f,'pre_beta_v':pre,'post_beta_v':post,'beta_transfer_fraction':frac,'effective_beta':1-frac})
r={'simulation_completed':True,'cell':CELL,'corner':'GF180 typical,27C','beta_pulse_us':15,'cases':results,'scope':'Extracted parent with ideal added capacitance from AUX to VCM. The added capacitors are not present in the physical layout; this screens whether auxiliary charge storage can tune endpoint beta before implementing it. Other controls are inactive and packet update is not exercised.','sha256':{'netlist':hashlib.sha256(netlist.read_bytes()).hexdigest(),'qualification':hashlib.sha256((layout/'qualification.json').read_bytes()).hexdigest(),'bench':hashlib.sha256(bench.read_bytes()).hexdigest()}};report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

