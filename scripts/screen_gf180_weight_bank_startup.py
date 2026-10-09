"""Screen signed current steering into a qualified active charge integrator."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--warmup-us',type=int,choices=[0,100,1000],default=0);p.add_argument('--cell-order',default='0,1,2,3');p.add_argument('--pf-program-levels',default='2.75,2.65,2.55,2.5');p.add_argument('--nf-gate-v',type=float,choices=[.4,.45,.5,.6,.65],default=.4);p.add_argument('--pf-gate-v',type=float,choices=[2.75,2.7,2.65,2.55,2.5,2.4],default=2.75);p.add_argument('--polarity',choices=['p','n','control'],default='control');p.add_argument('--sequence',choices=['p','n','pp','nn','pn','np','pppp','nnnn','pnpn','npnp'],default='p');p.add_argument('--mismatch-seed',type=int);p.add_argument('--neutral',action='store_true');p.add_argument('--width-us',type=float,choices=[.02,.05,.1,.25,.5,1,2,4],default=1);p.add_argument('--max-step-ns',type=int,choices=[2,5,10,20],default=20);a=p.parse_args();levels=[float(v) for v in a.pf_program_levels.split(',')];assert a.sequence=='pppp' and a.width_us==1 and len(levels)==4 and all(2.4<=v<=2.75 for v in levels) ;order=[int(v) for v in a.cell_order.split(',')];assert len(order)==4 and all(0<=v<4 for v in order);sources=set();texts=[]
 for cell in ['gf180_autozero_charge_integrator_fullroute_guarded','gf180_fixed_body_tg_fullroute_half','gf180_phase_inverter_fullroute','gf180_signed_cascode_source_compact_guarded']:
  d=BASE/'layout'/cell;qpath=d/'qualification.json';q=json.loads(qpath.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];sources.add(qpath)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert digest(f)==h,str(f);sources.add(f)
  local=(d/(cell+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',local):
   if child!=cell:local=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,local)
  texts.extend(local.splitlines())
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';sources.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 stem='gf180_weight_bank_startup_'+hashlib.sha256(json.dumps(vars(a),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());sources.add(snap)
 lines=['Active signed charge accumulation diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Ireference bias 0 1u','Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u','Vncas ncas 0 1.1','Vpcas pcas 0 2.2',f'Vpg pg 0 {3.3 if a.neutral else a.pf_gate_v}',f'Vng ng 0 {0 if a.neutral else a.nf_gate_v}','Vreset reset_command 0 PWL(0 3.3 19.99u 3.3 20u 0 61u 0)','Vread read_command 0 0','Vpgref pgref 0 3.3','Vngref ngref 0 0']
 lines=[line for line in lines if not line.startswith(('Vpg ','Vng '))]
 for tag in ['w','r']:
  lines.extend([f'Vmeter_{tag} inject_{tag} sum_{tag} 0',f'Csum_{tag} sum_{tag} 0 50f',f'Cload_{tag} out_{tag} 0 50f',f'Xacc_{tag} vcm out_{tag} vdd 0 bias reset resetb az azb sum_{tag} cmp_{tag} azin_{tag} gf180_autozero_charge_integrator_fullroute_guarded',f'.ic v(out_{tag})=1.65 v(sum_{tag})=1.65'])
 lines.append('Vaz az_command 0 PWL(0 3.3 19.99u 3.3 20u 0 61u 0)')
 for phase in ['reset','read','az']:
  lines.extend([f'Xcb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
 sample=22+6*(len(a.sequence)-1)+a.width_us+3
 for i,level in enumerate(levels):
  phase=f'cell{i}';event=['0 0'];idle=['0 3.3']
  for j,selected in enumerate(order):
   if selected!=i:continue
   begin=22+6*j;end=begin+a.width_us
   event.extend([f'{begin-.01}u 0',f'{begin}u 3.3',f'{end-.01}u 3.3',f'{end}u 0'])
   idle.extend([f'{begin-.03}u 3.3',f'{begin-.02}u 0',f'{end+.01}u 0',f'{end+.02}u 3.3'])
  event.append('61u 0');idle.append('61u 3.3')
  lines.extend([f"Vevent_{i} {phase}_command 0 PWL({' '.join(event)})",f"Vidle_{i} {phase}_idle_command 0 PWL({' '.join(idle)})",f'Vpg_{i} pg_{i} 0 {3.3 if a.neutral else level}'])
  for ph in [phase,phase+'_idle']:
   lines.extend([f'Xb_{ph} {ph}_command {ph}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{ph} {ph}b {ph} vdd 0 gf180_phase_inverter_fullroute'])
  for tag in ['w','r']:
   pg=f'pg_{i}' if tag=='w' else 'pgref'
   lines.extend([f'Xsource_{i}_{tag} vcm pout_{i}_{tag} 0 {pg} ncas pcas vdd 0 ni_{i}_{tag} pi_{i}_{tag} gf180_signed_cascode_source_compact_guarded',f'Xsel_{i}_{tag} pout_{i}_{tag} inject_{tag} {phase} {phase}b 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xidle_{i}_{tag} pout_{i}_{tag} vcm {phase}_idle {phase}_idleb 0 vdd gf180_fixed_body_tg_fullroute_half'])
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
 for i in range(4):
  begin=22+6*i;pre=21 if i==0 else begin-1.75
  lines.extend([f'meas tran preprogram_{i} find output_signal at={pre}u',f'meas tran prepulse_{i} find output_signal at={begin-.25}u',f'meas tran postpulse_{i} find output_signal at={begin+4}u',f'let delta_{i}=output_signal-preprogram_{i}',f'meas tran eventstep_{i} find delta_{i} at={begin+4}u'])
 for i in range(4):lines.extend([f'meas tran pi_before_{i} find v(pi_{i}_w) at=21u',f'meas tran pi_late_{i} find v(pi_{i}_w) at=58u'])
 lines.extend(['quit','.endc','.end'])
 if a.warmup_us:
  shifted=[]
  for line in lines:
   if (line.startswith('V') and 'PWL(' in line) or line.startswith(('tran ','meas tran ')):
    line=re.sub(r'(?<![A-Za-z0-9_.])([0-9]+(?:\.[0-9]+)?)u\b',lambda m:f'{float(m[1])+a.warmup_us:g}u',line)
   shifted.append(line)
  lines=shifted
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');sources.add(deck)
 r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=r.stdout+r.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);sources.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^(signal_(?:before|event|late|delta|tail)|(?:out|sum)_[wr]_(?:before|event|late)|charge_[wr]|(?:preprogram|prepulse|postpulse|eventstep|pi_before|pi_late)_[0-3])\s*=\s*([-+0-9.eE]+)',log)}
 complete=r.returncode==0 and len(values)==43 and 'timestep too small' not in log.lower()
 report={'simulation_completed':complete,'settings':vars(a),'measurements':values,'differential_pair_physically_assembled':False,'source_module_physically_qualified':True,'scope':'Four continuously biased positive weight-current cells with independent ideal fixed PF gate voltages held from startup; each actual routed four-MOS source selected by its own extracted TG/idle pair and actual inverter clocks. NF gates off and NOUT parked at externalVCM; negative operation not tested here. Four matched-load off-current reference cells feed a separate real autozero integrator; physical two-output differential measured. Internal PI before/late measured; optional startup warmup holds source gates biased and integrator calibration closed longer before shifted events. Warmup is setup latency, not demonstrated population service. Cell bias is not reprogrammed between spikes; ordered selection can revisit a cell; neutral holds all PF gates3.3V while preserving all switching/load; extra cells/switch/loading/idle power present in circuit. Native source/integrator/clock/switch pieces separately DRC/LVS/GDS-readback qualified, bank/pair interconnect still schematic. Weight memory/calibration/analog reference driver absent, levels are not learned-weight mapping. Eventstep is raw circuit increment, no ideal neutral calibration or baseline cancellation. No noise/globalPVT/RPEX/qualified gateleak/original-float accuracy/5ms population/PLIF/chip acceptance; shared bank, not full144k-weight population or per-state layout.','weighted_charge_accepted':False,'complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in sorted(sources)}}
 rp=BASE/'results'/(stem+'.json');rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),'simulation_completed':complete,'measurements':values},indent=2))
 if not complete:raise RuntimeError(log[-2500:])
if __name__=='__main__':main()
