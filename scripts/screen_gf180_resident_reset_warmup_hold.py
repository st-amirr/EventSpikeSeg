"""Independent resident reset target and 5ms hold with extended startup; native extracted children."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--width-us',type=float,default=1);p.add_argument('--gate-v',type=float,default=.45);p.add_argument('--seed',type=int,choices=[0,29],default=0);a=p.parse_args();assert .05<=a.width_us<=2 and .3<=a.gate_v<=.6
 files={Path(__file__)};texts=[]
 cpwidth=BASE/'results/gf180_resident_reset_width_prediction.json';cw=json.loads(cpwidth.read_text());assert cw['calibration_completed'];files.add(cpwidth)
 for n,h in cw['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 a.width_us=cw['predicted_common_width_us']
 state='gf180_state_update_detailstem_ch3_pad06_v2';cmp='gf180_compact_nf_threshold_shielded';inv='gf180_phase_inverter_fullroute';nf='gf180_fixed_body_nf025_shorttracks';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed';source='gf180_source_nf05_l1_compact'
 for name in [state,cmp,inv,nf,tg,mim,source]:
  d=BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback']
  if name!=mim:assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique']
  else:
   ap=BASE/'results/gf180_minimum_mim_routed_gds_integrity.json';au=json.loads(ap.read_text());assert au['audit_completed'] and au['cases'][0]['physical_layout_accepted'];files.add(ap)
   for n,h in au['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert sha(f)==h,n;files.add(f)
  txt=(d/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 cp=BASE/'results/gf180_trained_beta_detailstem_ch3_secant_reference.json';cal=json.loads(cp.read_text());assert cal['reference_calibration_completed'];files.add(cp)
 for n,h in cal['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 settings=json.dumps(vars(a),sort_keys=True);stem='gf180_resident_reset_warmup_hold_'+hashlib.sha256(settings.encode()).hexdigest()[:10]+'_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat');models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Resident beta threshold and native subtractive current reset',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.param sw_stat_global=0 sw_stat_mismatch={int(bool(a.seed))}','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65',f"Vauxref auxref 0 {cal['frozen_auxiliary_reference_v']:.16g}",'Vbias bias 0 .75','Vncas ncas 0 1.1',f'Vprogram program 0 {a.gate_v:.16g}']
 phases={'write':'PWL(0 3.3 9.99u 3.3 10u 0 50u 0)','auxreset':'PWL(0 3.3 19.97u 3.3 19.98u 0 29.99u 0 30u 3.3 50u 3.3)','beta':'PWL(0 0 19.99u 0 20u 3.3 20.49u 3.3 20.5u 0 50u 0)','az':'PWL(0 3.3 4.99u 3.3 5u 0 50u 0)','sample':'PWL(0 0 41.99u 0 42u 3.3 42.49u 3.3 42.5u 0 50u 0)','reset':f'PWL(0 0 43.99u 0 44u 3.3 {44+a.width_us-.01:.16g}u 3.3 {44+a.width_us:.16g}u 0 50u 0)'}
 for ph,wave in phases.items():lines +=[f'V{ph} {ph}_command 0 {wave}',f'Xb_{ph} {ph}_command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 nodes=[];targets={'fresh':1.68};arms=['idle','neutral','active']
 for tag,v in targets.items():
  lines.append(f'Vtarget_{tag} target_{tag} 0 PWL(0 1.656875 7.99u 1.656875 8u {v} 50u {v})')
  for arm in arms:
   n=arm+'_'+tag;s='state_'+n;azn='azin_'+n;out='out_'+n;sp='spike_'+n;lat='latch_'+n;held='held_'+n;heldb='heldb_'+n;ng='ng_'+n;ni='ni_'+n;phase='reset' if arm!='idle' else '0';phaseb='resetb' if arm!='idle' else 'vdd';pg='program' if arm!='neutral' else '0'
   lines +=[f'Xstate_{n} {s} aux_{n} target_{tag} write writeb auxreset beta auxref vcm 0 vdd {state}',f'Xcompare_{n} {s} {azn} {out} vdd 0 bias cmp_{n} {cmp}',f'Xaz_{n} {out} {azn} az azb 0 vdd {tg}',f'Xdummy_{n} {azn} {azn} azb 0 {nf}',f'Xcomp_{n} {out} cmp_{n} 0 {mim}',f'Xbuf1_{n} {out} spikeb_{n} vdd 0 {inv}',f'Xbuf2_{n} spikeb_{n} {sp} vdd 0 {inv}']
   for i in range(9):lines.append(f'Xstore{i}_{n} {azn} vcm 0 {mim}')
   # Sample and hold the decision before reset; reset cannot truncate its own command.
   lines +=[f'Xsample_{n} {sp} {lat} sample sampleb 0 vdd {tg}',f'Xlatchcap_{n} {lat} 0 0 {mim}',f'Xlatb_{n} {lat} {heldb} vdd 0 {inv}',f'Xlat_{n} {heldb} {held} vdd 0 {inv}',f'Xselect_{n} {pg} selected_{n} {held} {heldb} 0 vdd {tg}',f'Xwindow_{n} selected_{n} {ng} {phase} {phaseb} 0 vdd {tg}',f'Xoffphase_{n} {ng} 0 {phaseb} 0 {nf}',f'Xoffspike_{n} {ng} 0 {heldb} 0 {nf}',f'Xsink_{n} {ni} {ng} 0 0 {source}',f'Xcas_{n} drain_{n} ncas {ni} 0 {source}',f'Vmeter_{n} {s} drain_{n} 0',f'.ic v({s})=1.656875 v(aux_{n})=1.65 v({azn})=1.656875 v({out})=1.656875 v({lat})=0 v({ng})=0']
   nodes +=[s,sp,held,ng,lat,f'i(Vmeter_{n})']
 lines +=['.control','set numdgt=15']
 if a.seed:lines +=[f'setseed {a.seed}','reset']
 # Extend initialization through actual writers/calibration before state retention.
 shifted=[]
 for line in lines:
  if line.startswith('V') and 'PWL(' in line:
   line=re.sub(r'(?<![A-Za-z0-9_.])([0-9]+(?:\.[0-9]+)?)u\b',lambda m:f'{float(m[1])+1000:.16g}u',line)
   line=line.replace('1050u','6050u')
  shifted.append(line)
 lines=shifted
 lines +=['tran .005u 6050u 0 .25u uic','set wr_singlescale','set wr_vecnames']
 columns=[n if n.startswith('i(') else f'v({n})' for n in nodes];lines +=['wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(columns),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 w=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,1+len(nodes)));complete=run.returncode==0 and w.ndim==2 and w.shape[1]==1+len(nodes) and len(w)>1 and np.isfinite(w).all() and abs(w[-1,0]-6050e-6)<1e-12 and 'aborted' not in log.lower();metrics={}
 if data.exists():files.add(data)
 if complete:
  sample=lambda n,t:float(np.interp((t+1000)*1e-6,w[:,0],w[:,1+nodes.index(n)]));mask=(w[:,0]>=1043.5e-6)&(w[:,0]<=1049.5e-6);cases=[]
  for tag in targets:
   case={'target_v':targets[tag],'arms':{}}
   for arm in arms:
    n=arm+'_'+tag;before=sample('state_'+n,43.5);after=sample('state_'+n,49.5);curr=w[:,1+nodes.index('i(Vmeter_'+n+')')];charge=float(np.trapezoid(curr[mask],w[mask,0]));case['arms'][arm]={'state_before_v':before,'state_after_v':after,'state_step_v':after-before,'latched_spike_before_v':sample('held_'+n,43.5),'latched_spike_after_v':sample('held_'+n,49.5),'gate_midpulse_v':sample('ng_'+n,44+a.width_us/2),'integrated_sink_charge_c':charge,'state_after_5ms_hold_v':sample('state_'+n,5049.5),'hold_drift_v':sample('state_'+n,5049.5)-after,'sink_current_after_5ms_a':sample('i(Vmeter_'+n+')',5049.5)}
   ref=case['arms']['idle'];active=case['arms']['active'];neutral=case['arms']['neutral'];case.update(active_minus_idle_step_v=active['state_step_v']-ref['state_step_v'],neutral_minus_idle_step_v=neutral['state_step_v']-ref['state_step_v'],active_minus_neutral_step_v=active['state_step_v']-neutral['state_step_v']);cases.append(case)
  metrics={'cases':cases,'requested_base_reset_v':.006875,'target_model_base_threshold_v':1.656875,'note':'Actual pulse uncalibrated; no per-case numerical state correction. Idle controls include identical sink/cascode/load. Neutral pulses switch selectors at zero source program to diagnose switching. Static native seeds are not matched per-device statistics across arms.'}
 result={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,'settings':vars(a),**metrics,'scope':'Native extracted state/beta, startup autozero comparator, decision sampler and pulsed two-NF cascode current sink. Original trained targeted beta geometry/reference carried unchanged under new loading. One independent1.68V writer target; idle, neutral and active arms. Frozen common pulse width predicted from earlier2.1V target. Startup extended1000us through native writers/autozero, then5ms post-reset retention. This changes initialization timing and target together and is not a single-variable causal comparison to the earlier short startup. Real minimum MIM decision hold and native buffer/switch paths; external phase duration, gate/cascode/reference supplies. Single reset after beta and sensing; pulse-width prediction from one earlier transfer, no accepted reset transfer calibration, adaptive threshold reset, repeated cycles, native sampled noise/PVT/yield, physical combined parent, float accuracy/population service/full-chip acceptance. Proposed range64 remains unaccepted; no physical range saturation/conversion implementation.','acceptance':{'subtractive_reset':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in sorted(files)}}
 rp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),**metrics},indent=2))
 if not complete:raise RuntimeError(log[-2500:])
if __name__=='__main__':main()
