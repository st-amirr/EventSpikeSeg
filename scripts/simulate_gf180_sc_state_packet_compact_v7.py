import hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'; CELL='gf180_sc_state_packet_compact_v7'
layout=BASE/'layout'/CELL; netlist=layout/f'{CELL}_cap.spice'
SIM=CELL+'_center_signed_charge_5ms_v1'
bench=BASE/'benches'/f'{SIM}.spice'; logp=BASE/'results'/f'{SIM}.log'; report=BASE/'results'/f'{SIM}.json'
assert all(not p.exists() for p in (bench,logp,report))
lines=[
 'Routed switched-capacitor state packet: signed center updates and 5ms hold',
 '.include /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/design.spice',
 '.lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice typical',
 '.lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice mimcap_typical',
 '.temp 27', '.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',
 '.global VSUBS', 'Vsub VSUBS 0 0', f'.include /workspace/{netlist.relative_to(ROOT).as_posix()}',
]
for tag, init, delta in [('pos',1.5,0.016),('neg',1.5,-0.016)]:
 lines += [
  f'Vdd_{tag} vdd_{tag} 0 3.3',f'Vss_{tag} vss_{tag} 0 0',f'Vcm_{tag} vcm_{tag} 0 1.65',f'Vauxref_{tag} auxref_{tag} 0 1.65',f'Vdata_{tag} data_{tag} 0 {init}',
  f'Vweight_{tag} weight_{tag} 0 PWL(0 1.65 19.999u 1.65 20u {1.65+delta:.6f} 60u {1.65+delta:.6f} 60.001u 1.65 5100u 1.65)',
  f'Vwrite_{tag} write_{tag} 0 PWL(0 3.3 1.999u 3.3 2u 0 5100u 0)',f'Vwriteb_{tag} writeb_{tag} 0 PWL(0 0 1.999u 0 2u 3.3 5100u 3.3)',
  f'Vreset_{tag} reset_{tag} 0 PWL(0 3.3 1.999u 3.3 2u 0 5100u 0)',f'Vbeta_{tag} beta_{tag} 0 0',
  f'Vtop_{tag} top_{tag} 0 PWL(0 0 4.999u 0 5u 3.3 59.999u 3.3 60u 0 5100u 0)',f'Vtopb_{tag} topb_{tag} 0 PWL(0 3.3 4.999u 3.3 5u 0 59.999u 0 60u 3.3 5100u 3.3)',
  f'Vdrive_{tag} drive_{tag} 0 PWL(0 0 9.999u 0 10u 3.3 49.999u 3.3 50u 0 5100u 0)',f'Vdriveb_{tag} driveb_{tag} 0 PWL(0 3.3 9.999u 3.3 10u 0 49.999u 0 50u 3.3 5100u 3.3)',
  f'Vsample_{tag} sample_{tag} 0 0',f'Vsampleb_{tag} sampleb_{tag} 0 3.3',
  f'Xdut_{tag} state_{tag} aux_{tag} data_{tag} write_{tag} writeb_{tag} reset_{tag} beta_{tag} auxref_{tag} vcm_{tag} weight_{tag} top_{tag} topb_{tag} sample_{tag} sampleb_{tag} drive_{tag} driveb_{tag} pkt_top_{tag} pkt_bottom_{tag} vdd_{tag} vss_{tag} {CELL}',
  f'.ic v(aux_{tag})=1.65',
 ]
lines += ['.control','set numdgt=15','tran 20n 5100u 0 20n uic']
for tag in ('pos','neg'):
 for name, at in [('before',19e-6),('connected',45e-6),('released',70e-6),('hold',5.1e-3)]:
  lines.append(f'meas tran {tag}_{name} find v(state_{tag}) at={at}')
lines += ['quit','.endc','.end','']
bench.write_text('\n'.join(lines),encoding='utf8')
run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','240','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=250)
log=run.stdout+run.stderr; logp.write_text(log,encoding='utf8')
vals={k.lower():float(v) for k,v in re.findall(r'(?mi)^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)',log)}
keys=[f'{tag}_{n}' for tag in ('pos','neg') for n in ('before','connected','released','hold')]
assert run.returncode==0 and 'ngspice-47 done' in log.lower() and all(k in vals for k in keys),log[-2500:]
cases=[]
for tag in ('pos','neg'):
 b,c,r,h=[vals[f'{tag}_{n}'] for n in ('before','connected','released','hold')]
 cases.append({'polarity':tag,'initial_state_v':b,'state_with_packet_connected_v':c,'connected_change_mv':(c-b)*1000,'after_top_release_v':r,'release_change_mv':(r-c)*1000,'state_after_5ms_v':h,'postrelease_hold_drift_mv':(h-r)*1000})
result={'simulation_completed':True,'cell':CELL,'corner':'GF180 typical, 27C','weight_step_mv':16,'cases':cases,'scope':'Routed extracted switched-capacitor parent with native transistor switches and MIM packet; one nominal center-state charge screen, external ideal timing/weight voltage, no calibration, PVT/noise/mismatch, range limiter, threshold/reset/adaptation, full model replay or service qualification.','sha256':{'netlist':hashlib.sha256(netlist.read_bytes()).hexdigest(),'qualification':hashlib.sha256((layout/'qualification.json').read_bytes()).hexdigest(),'bench':hashlib.sha256(bench.read_bytes()).hexdigest()}}
report.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
