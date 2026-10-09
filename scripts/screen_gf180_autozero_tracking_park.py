"""Tracking idle-parking buffer diagnostic with actual preloaded analog integrators."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('settle_us',type=int,choices=[0,5,10],nargs='?',default=5);p.add_argument('--preload-differential-v',type=float,default=0);p.add_argument('--load-ff',type=float,choices=[50,500],default=50);p.add_argument('--baseline-trim-v',type=float,default=0);p.add_argument('--no-events',action='store_true');p.add_argument('--baseline-banks',type=int,choices=[1],default=1);p.add_argument('--pf-reference-levels',default='3.3,3.3,3.3,3.3');p.add_argument('--precharge-v',type=float,choices=[0,2.9,3.0,3.1],default=0);p.add_argument('--warmup-us',type=int,choices=[0,100,1000],default=0);p.add_argument('--cell-order',default='0,1,2,3');p.add_argument('--pf-program-levels',default='2.75,2.65,2.55,2.5');p.add_argument('--nf-gate-v',type=float,choices=[.4,.45,.5,.6,.65],default=.4);p.add_argument('--pf-gate-v',type=float,choices=[2.75,2.7,2.65,2.55,2.5,2.4],default=2.75);p.add_argument('--polarity',choices=['p','n','control'],default='control');p.add_argument('--sequence',choices=['p','n','pp','nn','pn','np','pppp','nnnn','pnpn','npnp'],default='p');p.add_argument('--mismatch-seed',type=int);p.add_argument('--neutral',action='store_true');p.add_argument('--duration-offset-ns',type=float,default=0);p.add_argument('--base-widths-us',default='');p.add_argument('--local-gain',type=int,choices=[1,2,4,8,16],default=1);p.add_argument('--width-us',type=float,default=.1);p.add_argument('--max-step-ns',type=int,choices=[2,5,10,20],default=20);a=p.parse_args();a.base_width_us=a.width_us;a.width_us*=a.local_gain;widths=[float(x) for x in a.base_widths_us.split(',')] if a.base_widths_us else [a.base_width_us]*4;assert len(widths)==4; widths=[x*a.local_gain+(a.local_gain-1)*a.duration_offset_ns*.001 for x in widths];assert all(.05<=x<=3 for x in widths);a.actual_widths_us=widths;a.width_us=max(widths);levels=[float(v) for v in a.pf_program_levels.split(',')];assert a.sequence=='pppp' and len(levels)==4 and all(2.4<=v<=2.75 for v in levels) ;order=[int(v) for v in a.cell_order.split(',')];assert len(order)==4 and all(0<=v<4 for v in order);reference_levels=[float(v) for v in a.pf_reference_levels.split(',')];assert len(reference_levels)==4 and all(2.4<=v<=3.3 for v in reference_levels);sources=set();texts=[]
 for cell in ['gf180_autozero_charge_integrator_fullroute_guarded','gf180_fixed_body_tg_fullroute_half','gf180_phase_inverter_fullroute','gf180_precharged_weight_current_cell_fullroute_guarded','gf180_shared_ota_core_pmos_input_fullroute','gf180_pmos_follower_baseline_readout_fullroute_guarded']:
  d=BASE/'layout'/cell;qpath=d/'qualification.json';q=json.loads(qpath.read_text(encoding='utf-8'));assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];sources.add(qpath)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert digest(f)==h,str(f);sources.add(f)
  local=(d/(cell+'_cap.spice')).read_text(encoding='utf-8')
  for child in re.findall(r'(?m)^\.subckt (\S+)',local):
   if child!=cell:local=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,local)
  texts.extend(local.splitlines())
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';sources.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 stem='gf180_autozero_tracking_park_'+hashlib.sha256(json.dumps(vars(a),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());sources.add(snap)
 lines=['Active signed charge accumulation diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Ireference bias 0 1u','Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u','Vncas ncas 0 1.1','Vpcas pcas 0 2.2',f'Vpg pg 0 {3.3 if a.neutral else a.pf_gate_v}',f'Vng ng 0 {0 if a.neutral else a.nf_gate_v}','Vreset reset_command 0 PWL(0 3.3 19.99u 3.3 20u 0 61u 0)','Vread read_command 0 0','Vpgref pgref 0 3.3','Vngref ngref 0 0']
 lines=[line for line in lines if not line.startswith(('Vpg ','Vng '))]
 for tag in ['w','r']:
  lines.extend([f'Vmeter_{tag} inject_{tag} sum_{tag} 0',f'Csum_{tag} sum_{tag} 0 50f',f'Cload_{tag} out_{tag} 0 50f',f'Xacc_{tag} vcm out_{tag} vdd 0 bias reset resetb az azb sum_{tag} cmp_{tag} azin_{tag} gf180_autozero_charge_integrator_fullroute_guarded',f'.ic v(out_{tag})=1.65 v(sum_{tag})=1.65'])
 # A separate stable unity follower per arm supplies the idle source current.
 # Its high-impedance input senses SUM; it does not force the stored membrane.
 lines.extend(['Iparkref parkbias 0 1u','Xparkref parkbias parkbias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u'])
 for tag in ['w','r']:
  lines.extend([f'Xparkbuffer_{tag} sum_{tag} parkazin_{tag} parkdrive_{tag} vdd 0 parkbias parkcmp_{tag} gf180_shared_ota_core_pmos_input_fullroute',f'Xparkcomp_{tag} parkdrive_{tag} parkcmp_{tag} cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u',f'Cparkload_{tag} park_{tag} 0 50f',f'Xparkaz_{tag} parkdrive_{tag} parkazin_{tag} az azb 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xparkclamp_{tag} park_{tag} vcm az azb 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xparkactive_{tag} parkdrive_{tag} park_{tag} azb az 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xparkstore_{tag} parkazin_{tag} park_{tag} 0 gf180_autozero_charge_integrator_fullroute_guarded__gf180_mim_bank_7x7_n9',f'.ic v(park_{tag})=1.65 v(parkdrive_{tag})=1.65 v(parkazin_{tag})=1.65'])
 lines.append(f'Vbaseline_reference baseline_ref 0 {1.65+a.baseline_trim_v}')
 lines.extend(['Isfref pbias 0 10u',f'Xsfref pbias pbias vdd vdd 0 {cell}__gf180_read_pf10_l1'])
 for tag in ['w','r']:
  ref='vcm' if tag=='w' else 'baseline_ref'
  lines.extend([f'Xbaseline_{tag} out_{tag} capture_{tag} {ref} baseline baselineb vdd 0 pbias drive_{tag} gf180_pmos_follower_baseline_readout_fullroute_guarded',f'Creadload_{tag} drive_{tag} 0 {a.load_ff}f'])
 lines.append('Vbaseline baseline_command 0 PWL(0 3.3 20.99u 3.3 21u 0 61u 0)')
 lines.append('Vaz az_command 0 PWL(0 3.3 19.99u 3.3 20u 0 61u 0)')
 lines.append('Vwrite write_command 0 PWL(0 3.3 9.99u 3.3 10u 0 6000u 0)')
 lines.extend([f'Vprecharge precharge_reference 0 {a.precharge_v if a.precharge_v else 3.0}',f'Vprechargeclock precharge_command 0 '+('PWL(0 3.3 9.99u 3.3 10u 0 6000u 0)' if a.precharge_v else '0')])
 for phase in ['reset','read','az','write','precharge','baseline']:
  lines.extend([f'Xcb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
 sample=22+6*(len(a.sequence)-1)+a.width_us+3
 for i,level in enumerate(levels):
  phase=f'cell{i}';event=['0 0'];idle=['0 3.3']
  for j,selected in enumerate(order):
   if selected!=i:continue
   begin=22+6*j;end=begin+widths[i]
   event.extend([f'{begin-.01}u 0',f'{begin}u 3.3',f'{end-.01}u 3.3',f'{end}u 0'])
   idle.extend([f'{begin-.03}u 3.3',f'{begin-.02}u 0',f'{end+.01}u 0',f'{end+.02}u 3.3'])
  event.append('61u 0');idle.append('61u 3.3')
  if a.no_events:event=['0 0','61u 0'];idle=['0 3.3','61u 3.3']
  lines.extend([f"Vevent_{i} {phase}_command 0 PWL({' '.join(event)})",f"Vidle_{i} {phase}_idle_command 0 PWL({' '.join(idle)})",f'Vpg_{i} program_{i} 0 {3.3 if a.neutral else level}'])
  for ph in [phase,phase+'_idle']:
   lines.extend([f'Xb_{ph} {ph}_command {ph}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{ph} {ph}b {ph} vdd 0 gf180_phase_inverter_fullroute'])
  lines.append(f'Vreference_{i} reference_program_{i} 0 {reference_levels[i]}')
  for tag in ['w','r']:
   pg=f'program_{i}' if tag=='w' else f'reference_program_{i}'
   lines.extend([f'Xsource_{i}_{tag} {pg} write writeb vcm pout_{i}_{tag} ncas pcas vdd 0 gate_{i}_{tag} ni_{i}_{tag} pi_{i}_{tag} precharge_reference precharge prechargeb gf180_precharged_weight_current_cell_fullroute_guarded',f'Xsel_{i}_{tag} pout_{i}_{tag} inject_{tag} {phase} {phase}b 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xidle_{i}_{tag} pout_{i}_{tag} park_{tag} {phase}_idle {phase}_idleb 0 vdd gf180_fixed_body_tg_fullroute_half'])
 assert abs(a.preload_differential_v)<=.3
 # Initialize feedback charge through actual OUT and SUM writers; release SUM first.
 for tag,sign in [('w',-1),('r',1)]:
  lines.extend([f'Vstate_{tag} state_program_{tag} 0 {1.65+sign*a.preload_differential_v/2}',f'Xstateout_{tag} out_{tag} state_program_{tag} stateout stateoutb 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xstatesum_{tag} sum_{tag} vcm statesum statesumb 0 vdd gf180_fixed_body_tg_fullroute_half'])
 for phase,end in [('statesum',20.5),('stateout',20.55)]:
  lines.extend([f'V{phase} {phase}_command 0 PWL(0 0 20.09u 0 20.10u 3.3 {end-.01}u 3.3 {end}u 0 61u 0)',f'Xb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
 if a.mismatch_seed is not None:lines=[line.replace('sw_stat_mismatch=0','sw_stat_mismatch=1') for line in lines]
 lines.extend(['.control','set numdgt=15'])
 if a.mismatch_seed is not None:lines.extend([f'setseed {a.mismatch_seed}','reset'])
 lines.extend([f'tran {a.max_step_ns}n 61u 0 {a.max_step_ns}n uic','let output_signal=v(out_r)-v(out_w)','let captured_signal=v(capture_r)-v(capture_w)','let buffered_signal=v(drive_r)-v(drive_w)'])
 for phase,t in [('before','21.75u'),('event',f'{sample}u'),('late','58u')]:
  lines.extend([f'meas tran buffered_{phase} find buffered_signal at={t}',f'meas tran drive_w_{phase} find v(drive_w) at={t}',f'meas tran drive_r_{phase} find v(drive_r) at={t}'])
  lines.extend([f'meas tran signal_{phase} find output_signal at={t}',f'meas tran captured_{phase} find captured_signal at={t}',f'meas tran capture_w_{phase} find v(capture_w) at={t}',f'meas tran capture_r_{phase} find v(capture_r) at={t}'])
  for tag in ['w','r']:
   for node in ['out','sum','park']:lines.append(f'meas tran {node}_{tag}_{phase} find v({node}_{tag}) at={t}')
 lines.extend(['let dsignal=output_signal-signal_before','let lsignal=output_signal-signal_event',f'meas tran signal_delta find dsignal at={sample}u','meas tran signal_tail find lsignal at=58u'])
 for tag in ['w','r']:lines.append(f'meas tran charge_{tag} integ i(Vmeter_{tag}) from=21.75u to={sample}u')
 for i in range(4):
  begin=22+6*i;pre=21.75 if i==0 else begin-1.75
  lines.extend([f'meas tran captured_step_{i} find captured_signal at={begin+4}u',f'meas tran buffered_step_{i} find buffered_signal at={begin+4}u'])
  lines.extend([f'meas tran preprogram_{i} find output_signal at={pre}u',f'meas tran prepulse_{i} find output_signal at={begin-.25}u',f'meas tran postpulse_{i} find output_signal at={begin+4}u',f'let delta_{i}=output_signal-preprogram_{i}',f'meas tran eventstep_{i} find delta_{i} at={begin+4}u'])
 for i in range(4):lines.extend([f'meas tran gate_before_{i} find v(gate_{i}_w) at=21u',f'meas tran gate_late_{i} find v(gate_{i}_w) at=58u'])
 for i in range(4):lines.extend([f'meas tran pi_before_{i} find v(pi_{i}_w) at=21u',f'meas tran pi_late_{i} find v(pi_{i}_w) at=58u'])
 lines.extend(['quit','.endc','.end'])
 # Give state writers/capture release a separate physical settling interval.
 # Only event/idle clocks and measurement windows move; state itself is unforced.
 if a.settle_us:
  shifted=[]
  for line in lines:
   if line.startswith(('Vevent_','Vidle_','tran ','meas tran ')):
    line=re.sub(r'(?<![A-Za-z0-9_.])([0-9]+(?:\.[0-9]+)?)u\b',lambda m:f'{float(m[1])+a.settle_us:g}u' if float(m[1])>=21.75 else m[0],line)
   shifted.append(line)
  lines=shifted
 if a.warmup_us:
  shifted=[]
  for line in lines:
   if (line.startswith('V') and not line.startswith(('Vwrite ','Vprechargeclock ')) and 'PWL(' in line) or line.startswith(('tran ','meas tran ')):
    line=re.sub(r'(?<![A-Za-z0-9_.])([0-9]+(?:\.[0-9]+)?)u\b',lambda m:f'{float(m[1])+a.warmup_us:g}u',line)
   shifted.append(line)
  lines=shifted
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');sources.add(deck)
 r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=r.stdout+r.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');sources.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^(buffered_(?:before|event|late|step_[0-3])|drive_[wr]_(?:before|event|late)|captured_(?:before|event|late|step_[0-3])|capture_[wr]_(?:before|event|late)|signal_(?:before|event|late|delta|tail)|(?:out|sum|park)_[wr]_(?:before|event|late)|charge_[wr]|(?:preprogram|prepulse|postpulse|eventstep|pi_before|pi_late|gate_before|gate_late)_[0-3])\s*=\s*([-+0-9.eE]+)',log)}
 complete=r.returncode==0 and len(values)==83 and 'timestep too small' not in log.lower()
 report={'simulation_completed':complete,'simulator_returncode':r.returncode,'settings':vars(a),'measurements':values,'differential_pair_physically_assembled':False,'source_module_physically_qualified':True,'initial_state_method':'Actual halfTG writers connect both integrator OUTs to opposite external bench state references and both SUMs toVCM after integrator reset release; SUM writers release before OUT writers; all writers off before baseline capture release/events. No retained node forced during events; actual initial OUT/SUM are measured. State programming/reference generator and combined preload layout unqualified. Capture stores baseline, so readout increments do not expose an absolute stored-state threshold interface.', 'local_gain_implemented_by':'Actual event selection and idle parking timing scaled by fixed gain; native weight cells, MIM geometry and transistor cards unchanged. No arithmetic gain applied to simulated signals. Calibrated duration offset changes real command edges; no corrected output voltage is forced. Different per-cell base widths can represent selected original float weights. Base pulse is shared bench command, not a qualified autonomous duration generator. Scale must be maintained consistently in other PLIF operations; this diagnostic implements injection only.', 'settling_method':'Event/idle edges and measurement windows delayed by settle_us after state writers and baseline capture release. No numerical state correction, extra model spike, or forced membrane node. External timing stimulus, not an autonomous sequencer.', 'idle_parking_method':'Each arm has a native seven-MOS OTA with inputSUM, capacitively coupled negative-feedback nodePARKAZIN and outputPARKDRIVE. DuringAZ, nativeTGs connect DRIVE-to-AZIN and PARK-to-VCM while DRIVE-to-PARK is off, storing the offset on a native9MIM bank between AZIN and PARK. During active operation, DRIVE-to-PARK closes and the offset capacitor supplies feedback; PARK supplies all idle-source switches, with native7um MIM compensation and ideal external1uA bias reference. Unlike originalVCM parking this aims to avoid charging source-output capacitance across a state-dependent voltage step. New connected autozero buffer schematic has no combined layout, stability/noise/PVT qualification; feedback is capacitive, so hold droop and sampled noise are unresolved. Native mismatch hierarchy differs; priorseed29 gate calibration does not automatically transfer.', 'scope':'Actual physical4MOS/9MIM follower/capture/clamp macro imported whole with internal wiring and cap extraction,500fF output loads when selected. PF80 source-body-tied follower/PF10 current source with schematic-connected extracted PF10 diode reference and ideal10uA supply. Output common mode/body effect/nonunity gain require new calibration. Original integrator/weight/startup/clock modules extracted; full bank/pair/bias/programmer/interface assembly still schematic. Noise disabled in transient; sampled-noise/PVT/RPEX/gate leakage/float accuracy/5ms/fullPLIF/chip qualification absent.','weighted_charge_accepted':False,'complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in sorted(sources)}}
 rp=BASE/'results'/(stem+'.json');rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':complete,'measurements':values},indent=2))
 if not complete:raise RuntimeError(log[-2500:])
if __name__=='__main__':main()
