"""Screen signed current steering into a qualified active charge integrator."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--polarity',choices=['p','n','control'],default='control');p.add_argument('--neutral',action='store_true');p.add_argument('--width-us',type=float,choices=[.1,1,4],default=1);p.add_argument('--max-step-ns',type=int,choices=[10,20],default=20);a=p.parse_args();sources=set();texts=[]
 for cell in ['gf180_active_charge_reader_fullroute_guarded','gf180_fixed_body_tg_fullroute_half','gf180_phase_inverter_fullroute']:
  d=BASE/'layout'/cell;qpath=d/'qualification.json';q=json.loads(qpath.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];sources.add(qpath)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert digest(f)==h,str(f);sources.add(f)
  local=(d/(cell+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',local):
   if child!=cell:local=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,local)
  texts.extend(local.splitlines())
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';sources.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 stem='gf180_differential_weighted_charge_'+hashlib.sha256(json.dumps(vars(a),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());sources.add(snap)
 lines=['Active signed charge accumulation diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Ireference bias 0 1u','Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u','Vncas ncas 0 1.1','Vpcas pcas 0 2.2',f'Vpg pg 0 {3.3 if a.neutral else 2.75}',f'Vng ng 0 {0 if a.neutral else .4}','Vreset reset_command 0 PWL(0 3.3 19.99u 3.3 20u 0 61u 0)','Vread read_command 0 0','Vpgref pgref 0 3.3','Vngref ngref 0 0']
 for tag in ['w','r']:
  lines.extend([f'Vmeter_{tag} inject_{tag} sum_{tag} 0',f'Csum_{tag} sum_{tag} 0 50f',f'Cload_{tag} out_{tag} 0 50f',f'Xacc_{tag} vcm vcm vcm out_{tag} vdd 0 bias read readb reset resetb sum_{tag} cmp_{tag} gf180_active_charge_reader_fullroute_guarded',f'.ic v(out_{tag})=1.65 v(sum_{tag})=1.65'])
 for phase in ['reset','read']:
  lines.extend([f'Xcb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
 end=22+a.width_us
 for kind in ['p','n']:
  active=a.polarity==kind
  lines.extend([f'Vevent_{kind} {kind}_command 0 PWL(0 0 21.99u 0 22u {3.3 if active else 0} {end-.01}u {3.3 if active else 0} {end}u 0 61u 0)',f'Vidle_{kind} {kind}_idle_command 0 PWL(0 3.3 21.97u 3.3 21.98u {0 if active else 3.3} {end+.01}u {0 if active else 3.3} {end+.02}u 3.3 61u 3.3)'])
  for phase in [kind,kind+'_idle']:
   lines.extend([f'Xb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
  for tag in ['w','r']:
   lines.extend([f'Xsel_{kind}_{tag} {kind}out_{tag} inject_{tag} {kind} {kind}b 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xidle_{kind}_{tag} {kind}out_{tag} vcm {kind}_idle {kind}_idleb 0 vdd gf180_fixed_body_tg_fullroute_half'])
 for tag in ['w','r']:
  pg='pg' if tag=='w' else 'pgref';ng='ng' if tag=='w' else 'ngref'
  lines.extend([f'Xip_{tag} pi_{tag} {pg} vdd vdd pfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',f'Xpc_{tag} pout_{tag} pcas pi_{tag} vdd pfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',f'Xin_{tag} ni_{tag} {ng} 0 0 nfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',f'Xnc_{tag} nout_{tag} ncas ni_{tag} 0 nfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u'])
 lines.extend(['.control','set numdgt=15',f'tran {a.max_step_ns}n 61u 0 {a.max_step_ns}n uic','let output_signal=v(out_r)-v(out_w)'])
 for phase,t in [('before','21u'),('event','28u'),('late','50u')]:
  lines.append(f'meas tran signal_{phase} find output_signal at={t}')
  for tag in ['w','r']:
   for node in ['out','sum']:lines.append(f'meas tran {node}_{tag}_{phase} find v({node}_{tag}) at={t}')
 lines.extend(['let dsignal=output_signal-signal_before','let lsignal=output_signal-signal_event','meas tran signal_delta find dsignal at=28u','meas tran signal_tail find lsignal at=50u'])
 for tag in ['w','r']:lines.append(f'meas tran charge_{tag} integ i(Vmeter_{tag}) from=21u to=28u')
 lines.extend(['quit','.endc','.end'])
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');sources.add(deck)
 r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=r.stdout+r.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);sources.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^(signal_(?:before|event|late|delta|tail)|(?:out|sum)_[wr]_(?:before|event|late)|charge_[wr])\s*=\s*([-+0-9.eE]+)',log)}
 complete=r.returncode==0 and len(values)==19 and 'timestep too small' not in log.lower()
 report={'simulation_completed':complete,'settings':vars(a),'measurements':values,'differential_pair_physically_assembled':False,'scope':'Physical signal definition is voltage across two actual outputs OUT_reference minus OUT_weighted; SPICE subtraction measures that differential voltage and does not force/correct either node. Two independently instantiated extracted charge integrators, mirrored switch loads/common clock paths and native schematic biased versus off-current reference branches. Exact nominal matched geometry/no mismatch/no noise is an optimistic cancellation screen; reference realization/bias/pair interconnect/readout not physically assembled. Qualified extracted active charge-reader used as integrator: native OTA, feedback9x7um MIM, reset/access/dummy and routing. External native schematic4MOS continuously biased cascode source, extracted half TG steer/idle and inverter paths with20ns commanded gaps; ideal analog bias/VCM, schematic inter-macro links and zero-volt current meter. Reset release20us, weighted event22us, output28us and50us; sign follows inverting charge-amplifier physics and is not yet bound to model membrane sign. No source routing/bias qualification, learned weights/beta/threshold/reset/adaptation/state-writeback, noise/PVT/mismatch/qualified leakage/5ms service/model/chip acceptance. Neutral subtraction is diagnostic only, never applied to state.','weighted_charge_accepted':False,'complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in sorted(sources)}}
 rp=BASE/'results'/(stem+'.json');rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),'simulation_completed':complete,'measurements':values},indent=2))
 if not complete:raise RuntimeError(log[-2500:])
if __name__=='__main__':main()
