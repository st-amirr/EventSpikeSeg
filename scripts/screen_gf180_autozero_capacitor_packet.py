"""Screen physical input-offset sampling for the switched-capacitor charge candidate."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--polarity',choices=['p','n','control'],default='control');p.add_argument('--az-release-gap-ns',type=int,choices=[0,50,1000],default=0);p.add_argument('--az-banks',type=int,choices=[1,4,12],default=1);p.add_argument('--az-dummy',action='store_true');p.add_argument('--delta-v',type=float,default=.001);p.add_argument('--sequence',choices=['p','n','pp','nn','pn','np','pppp','nnnn','pnpn','npnp'],default='p');p.add_argument('--mismatch-seed',type=int);p.add_argument('--neutral',action='store_true');p.add_argument('--width-us',type=float,choices=[.1,1,4],default=1);p.add_argument('--max-step-ns',type=int,choices=[10,20],default=20);a=p.parse_args();sources=set();texts=[]
 for cell in ['gf180_active_charge_reader_fullroute_guarded','gf180_fixed_body_tg_fullroute_half','gf180_phase_inverter_fullroute']:
  d=BASE/'layout'/cell;qpath=d/'qualification.json';q=json.loads(qpath.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];sources.add(qpath)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert digest(f)==h,str(f);sources.add(f)
  local=(d/(cell+'_cap.spice')).read_text()
  if cell=='gf180_active_charge_reader_fullroute_guarded':
   local=local.replace('+ READB RESET RESETB SUM CMP','+ READB RESET RESETB SUM CMP AZ AZB')
   local=local.replace('Xota VCM SUM OUT','Xota VCM AZIN OUT')
   local=local.replace('Xreset OUT SUM RESET RESETB','Xreset OUT SUM VSS VDD')
   local=local.replace('Xresetdummy SUM SUM RESETB RESET','Xresetdummy SUM SUM VDD VSS')
   insertion=['Xazfeedback OUT AZIN AZ AZB VSS VDD gf180_fixed_body_tg_fullroute_half','Xazclamp SUM VCM RESET RESETB VSS VDD gf180_fixed_body_tg_fullroute_half']
   insertion += [f'Xazcap{i} AZIN SUM VSS gf180_mim_bank_7x7_n9' for i in range(a.az_banks)]
   if a.az_dummy:insertion += ['Xazdummy AZIN AZIN RESETB RESET VSS VDD gf180_fixed_body_tg_fullroute_half','Xazclampdummy SUM SUM RESETB RESET VSS VDD gf180_fixed_body_tg_fullroute_half']
   local=local.replace('Xaccess P SUM', '\n'.join(insertion)+'\nXaccess P SUM')
  for child in re.findall(r'(?m)^\.subckt (\S+)',local):
   if child!=cell:local=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,local)
  texts.extend(local.splitlines())
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';sources.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 stem='gf180_autozero_capacitor_packet_'+hashlib.sha256(json.dumps(vars(a),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());sources.add(snap)
 lines=['Active signed charge accumulation diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Ireference bias 0 1u','Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u','Vncas ncas 0 1.1','Vpcas pcas 0 2.2',f'Vpg pg 0 {3.3 if a.neutral else 2.75}',f'Vng ng 0 {0 if a.neutral else .4}','Vreset reset_command 0 PWL(0 3.3 19.99u 3.3 20u 0 61u 0)','Vread read_command 0 0','Vpgref pgref 0 3.3','Vngref ngref 0 0']
 for tag in ['w','r']:
  lines.extend([f'Vmeter_{tag} inject_{tag} sum_{tag} 0',f'Csum_{tag} sum_{tag} 0 50f',f'Cload_{tag} out_{tag} 0 50f',f'Xacc_{tag} vcm vcm vcm out_{tag} vdd 0 bias read readb reset resetb sum_{tag} cmp_{tag} az azb gf180_active_charge_reader_fullroute_guarded',f'.ic v(out_{tag})=1.65 v(sum_{tag})=1.65'])
 lines.append(f'Vaz az_command 0 PWL(0 3.3 {19.99-a.az_release_gap_ns/1000}u 3.3 {20-a.az_release_gap_ns/1000}u 0 61u 0)')
 for phase in ['reset','read','az']:
  lines.extend([f'Xcb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
 sample=22+6*(len(a.sequence)-1)+a.width_us+3
 for kind in ['p','n']:
  event=['0 0'];idle=['0 3.3']
  for i,k in enumerate(a.sequence):
   if k!=kind:continue
   begin=22+6*i;end=begin+a.width_us
   event.extend([f'{begin-.01}u 0',f'{begin}u 3.3',f'{end-.01}u 3.3',f'{end}u 0'])
   idle.extend([f'{begin-.03}u 3.3',f'{begin-.02}u 0',f'{end+.01}u 0',f'{end+.02}u 3.3'])
  event.append('61u 0');idle.append('61u 3.3')
  lines.extend([f"Vevent_{kind} {kind}_command 0 PWL({' '.join(event)})",f"Vidle_{kind} {kind}_idle_command 0 PWL({' '.join(idle)})"])
  for phase in [kind,kind+'_idle']:
   lines.extend([f'Xb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
  for tag in ['w','r']:
   lines.extend([f'Xsel_{kind}_{tag} {kind}out_{tag} inject_{tag} {kind} {kind}b 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xidle_{kind}_{tag} {kind}out_{tag} vcm {kind}_idle {kind}_idleb 0 vdd gf180_fixed_body_tg_fullroute_half'])
 for kind in ['p','n']:
  for tag in ['w','r']:
   bottom=['0 1.65']
   for i,k in enumerate(a.sequence):
    if k!=kind:continue
    begin=22+6*i;end=begin+a.width_us;voltage=1.65+(a.delta_v*(1 if kind=='p' else -1) if tag=='w' else 0)
    bottom.extend([f'{begin+.03}u 1.65',f'{begin+.04}u {voltage}',f'{end+.04}u {voltage}',f'{end+.05}u 1.65'])
   bottom.append('61u 1.65')
   lines.extend([f"Vbottom_{kind}_{tag} bottom_{kind}_{tag} 0 PWL({' '.join(bottom)})",f'Xpacket_{kind}_{tag} {kind}out_{tag} bottom_{kind}_{tag} 0 gf180_active_charge_reader_fullroute_guarded__gf180_mim_bank_7x7_n9'])
 if a.mismatch_seed is not None:lines=[line.replace('sw_stat_mismatch=0','sw_stat_mismatch=1') for line in lines]
 lines.extend(['.control','set numdgt=15'])
 if a.mismatch_seed is not None:lines.extend([f'setseed {a.mismatch_seed}','reset'])
 lines.extend([f'tran {a.max_step_ns}n 61u 0 {a.max_step_ns}n uic','let output_signal=v(out_r)-v(out_w)'])
 for phase,t in [('before','21u'),('event',f'{sample}u'),('late','58u')]:
  lines.append(f'meas tran signal_{phase} find output_signal at={t}')
  for tag in ['w','r']:
   for node in ['out','sum']:lines.append(f'meas tran {node}_{tag}_{phase} find v({node}_{tag}) at={t}')
 lines.extend(['let dsignal=output_signal-signal_before','let lsignal=output_signal-signal_event',f'meas tran signal_delta find dsignal at={sample}u','meas tran signal_tail find lsignal at=58u'])
 for tag in ['w','r']:lines.append(f'meas tran charge_{tag} integ i(Vmeter_{tag}) from=21u to={sample}u')
 lines.extend(['quit','.endc','.end'])
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');sources.add(deck)
 r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=r.stdout+r.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);sources.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^(signal_(?:before|event|late|delta|tail)|(?:out|sum)_[wr]_(?:before|event|late)|charge_[wr])\s*=\s*([-+0-9.eE]+)',log)}
 complete=r.returncode==0 and len(values)==19 and 'timestep too small' not in log.lower()
 report={'simulation_completed':complete,'settings':vars(a),'measurements':values,'differential_pair_physically_assembled':False,'scope':'Autozero topology diagnostic built from independently extracted native modules. Original qualified reader NETLIST IS MODIFIED: OTA negative input is AZIN, original reset/dummy disabled; actual TG closes OUT to AZIN and clamps SUM to VCM during calibration; feedback release can precede SUM-clamp release20us by selected gap. Positive/negative event labels drive opposite ideal bottom steps. Native nine-7um MIM bank(s) AZIN-SUM sample amplifier offset; after release only charge retained on actual capacitors adjusts negative-input voltage. Optional opposite-clock actual half-TG dummies on AZIN/SUM. This modified integrator/pair/calibration interconnect has NO combined layout qualification; original extracted parasitics retained are provisional after topology change. No behavioral amplifier or numerical zero-packet correction. Packet weight bottom is still ideal waveform, not physical weight DAC. Signal is physical voltage across reference and weighted outputs; baseline subtraction measures increment but does not cancel baseline in circuit. Shared MIM resources, not per-state banks. Seed enables per-instance mismatch, no noise/global PVT/model/full5ms service qualification; no full PLIF/chip acceptance.','weighted_charge_accepted':False,'complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in sorted(sources)}}
 rp=BASE/'results'/(stem+'.json');rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),'simulation_completed':complete,'measurements':values},indent=2))
 if not complete:raise RuntimeError(log[-2500:])
if __name__=='__main__':main()
