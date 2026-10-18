import hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'; CELL='gf180_sc_state_packet_compact_v11'
layout=BASE/'layout'/CELL; netlist=layout/f'{CELL}_cap.spice'
SIM=CELL+'_center_signed_compensated_5ms_v2'
bench=BASE/'benches'/f'{SIM}.spice'; logp=BASE/'results'/f'{SIM}.log'; report=BASE/'results'/f'{SIM}.json'
assert all(not p.exists() for p in (bench,logp,report))
lines=['Routed switched-capacitor center-state signed packet, handoff compensation and 5ms hold',
 '.include /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/design.spice',
 '.lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice typical',
 '.lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice mimcap_typical',
 '.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18','.global VSUBS','Vsub VSUBS 0 0',f'.include /workspace/{netlist.relative_to(ROOT).as_posix()}']
for tag, packet_step in [('pos',0.108),('neg',0.064)]:
 base=1.697545
 lines += [
 f'Vdd_{tag} vdd_{tag} 0 3.3',f'Vss_{tag} vss_{tag} 0 0',f'Vcm_{tag} vcm_{tag} 0 1.65',f'Vauxref_{tag} auxref_{tag} 0 1.65',f'Vdata_{tag} data_{tag} 0 1.65',
 f'Vweight_{tag} weight_{tag} 0 PWL(0 {base} 99.999u {base} 100u {base+packet_step:.6f} 116.999u {base+packet_step:.6f} 117u {base} 5200u {base})',
 f'Vwrite_{tag} write_{tag} 0 PWL(0 3.3 9.999u 3.3 10u 0 5200u 0)',f'Vwriteb_{tag} writeb_{tag} 0 PWL(0 0 9.999u 0 10u 3.3 5200u 3.3)',
 f'Vreset_{tag} reset_{tag} 0 PWL(0 3.3 1.999u 3.3 2u 0 5200u 0)',
 f'Vbeta_{tag} beta_{tag} 0 PWL(0 0 19.999u 0 20u 3.3 29.999u 3.3 30u 0 5200u 0)',
 f'Vtop_{tag} top_{tag} 0 PWL(0 3.3 115.999u 3.3 116u 0 5200u 0)',f'Vtopb_{tag} topb_{tag} 0 PWL(0 0 115.999u 0 116u 3.3 5200u 3.3)',
 f'Vsample_{tag} sample_{tag} 0 PWL(0 3.3 59u 3.3 60u 0 5200u 0)',f'Vsampleb_{tag} sampleb_{tag} 0 PWL(0 0 59u 0 60u 3.3 5200u 3.3)',
 f'Vdrive_{tag} drive_{tag} 0 PWL(0 0 60.999u 0 61u 3.3 116.999u 3.3 117u 0 5200u 0)',f'Vdriveb_{tag} driveb_{tag} 0 PWL(0 3.3 60.999u 3.3 61u 0 116.999u 0 117u 3.3 5200u 3.3)',
 f'Xdut_{tag} state_{tag} aux_{tag} data_{tag} write_{tag} writeb_{tag} reset_{tag} beta_{tag} auxref_{tag} vcm_{tag} weight_{tag} top_{tag} topb_{tag} sample_{tag} sampleb_{tag} drive_{tag} driveb_{tag} pkt_top_{tag} pkt_bottom_{tag} vdd_{tag} vss_{tag} {CELL}',
 f'.ic v(state_{tag})=1.65 v(aux_{tag})=1.65 v(pkt_top_{tag})=1.65 v(pkt_bottom_{tag})=1.65']
lines += ['.control','set numdgt=15','tran 20n 5200u 0 20n uic']
for tag in ('pos','neg'):
 for name,at in [('pre_beta',19e-6),('post_beta',32e-6),('pre_event',99e-6),('during_event',110e-6),('post_release',120e-6),('hold_5ms',5.117e-3)]:
  lines.append(f'meas tran {tag}_{name} find v(state_{tag}) at={at}')
lines += ['quit','.endc','.end','']
bench.write_text('\n'.join(lines),encoding='utf8')
run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','240','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=250)
log=run.stdout+run.stderr;logp.write_text(log,encoding='utf8')
vals={k.lower():float(v) for k,v in re.findall(r'(?mi)^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)',log)}
keys=[f'{tag}_{n}' for tag in ('pos','neg') for n in ('pre_beta','post_beta','pre_event','during_event','post_release','hold_5ms')]
assert run.returncode==0 and 'ngspice-47 done' in log.lower() and all(k in vals for k in keys),log[-2500:]
cases=[]
for tag in ('pos','neg'):
 pre,post,basev,during,released,hold=[vals[f'{tag}_{n}'] for n in ('pre_beta','post_beta','pre_event','during_event','post_release','hold_5ms')]
 cases.append({'polarity':tag,'pre_beta_v':pre,'post_beta_v':post,'pre_event_v':basev,'during_packet_v':during,'during_packet_change_mv':(during-basev)*1000,'post_release_v':released,'net_update_mv':(released-basev)*1000,'state_after_5ms_v':hold,'postrelease_hold_drift_mv':(hold-released)*1000})
result={'simulation_completed':True,'cell':CELL,'corner':'GF180 typical, 27C','center_state_compensating_bottom_baseline_v':base,'packet_step_mv':{'positive':108,'negative':64},'cases':cases,'scope':'Routed extracted switched-capacitor parent with native quarter-size TGs and MIM packet. Phase timing, baseline and packet amplitudes are ideal external sources based on prior sparse schematic calibration; this is a transfer/hold screen only, not an autonomous weight mapper, PVT/noise/mismatch, model replay or full service qualification.','sha256':{'netlist':hashlib.sha256(netlist.read_bytes()).hexdigest(),'qualification':hashlib.sha256((layout/'qualification.json').read_bytes()).hexdigest(),'bench':hashlib.sha256(bench.read_bytes()).hexdigest()}}
report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
