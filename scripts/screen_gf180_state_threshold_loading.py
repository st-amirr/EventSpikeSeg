"""Matched resident-state loading and gated threshold comparison, native extracted children."""
import hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files={Path(__file__)};texts=[];state='gf180_state_update_detailstem_ch3_pad06_v2';cmp='gf180_compact_nf_threshold_fullroute';inv='gf180_phase_inverter_fullroute';nf='gf180_fixed_body_nf025_shorttracks'
 for name in [state,cmp,inv,nf]:
  d=BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert sha(f)==h,n;files.add(f)
  txt=(d/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 cp=BASE/'results/gf180_trained_beta_detailstem_ch3_secant_reference.json';cal=json.loads(cp.read_text());assert cal['reference_calibration_completed'];files.add(cp)
 for n,h in cal['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 stem='gf180_state_threshold_loading_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat');models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Resident state threshold loading',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65',f"Vauxref auxref 0 {cal['frozen_auxiliary_reference_v']:.16g}",'Vthreshold threshold 0 1.85','Vbias bias 0 PWL(0 0 39.99u 0 40u .75 41.99u .75 42u 0 50u 0)']
 phases={'write':'PWL(0 3.3 9.99u 3.3 10u 0 50u 0)','auxreset':'PWL(0 3.3 19.97u 3.3 19.98u 0 29.99u 0 30u 3.3 50u 3.3)','beta':'PWL(0 0 19.99u 0 20u 3.3 20.49u 3.3 20.5u 0 50u 0)','idle':'PWL(0 3.3 38.99u 3.3 39u 0 42.09u 0 42.1u 3.3 50u 3.3)'}
 for phase,wave in phases.items():lines +=[f'V{phase} {phase}_command 0 {wave}',f'Xb_{phase} {phase}_command {phase}b vdd 0 {inv}',f'Xc_{phase} {phase}b {phase} vdd 0 {inv}']
 for tag,v in [('low',1.2),('mid',1.65),('high',2.1)]:
  lines.append(f'Vtarget_{tag} target_{tag} 0 {v}')
  for arm in ['bare','loaded']:
   lines +=[f'Xstate_{arm}_{tag} state_{arm}_{tag} aux_{arm}_{tag} target_{tag} write writeb auxreset beta auxref vcm 0 vdd {state}',f'.ic v(state_{arm}_{tag})=1.65 v(aux_{arm}_{tag})=1.65']
  lines +=[f'Xcompare_{tag} state_loaded_{tag} threshold out_{tag} vdd 0 bias cmp_{tag} {cmp}',f'Xclamp_{tag} out_{tag} 0 idle 0 {nf}',f'Xbuf1_{tag} out_{tag} spikeb_{tag} vdd 0 {inv}',f'Xbuf2_{tag} spikeb_{tag} spike_{tag} vdd 0 {inv}']
 lines +=['.control','set numdgt=15','tran .005u 50u 0 .05u uic'];times={'held':19,'commit':31.5,'pre':38.5,'sensing':41.5,'off':42.5,'final':49.5};valuespec={}
 for tag in ['low','mid','high']:
  for arm in ['bare','loaded']:
   for label,t in times.items():key=f'{arm}_{tag}_{label}';node=f'state_{arm}_{tag}';valuespec[key]=(node,t*1e-6);lines.append(f'meas tran {key} find v({node}) at={t}u')
  for label,t in [('sensing',41.5),('final',49.5)]:key=f'spike_{tag}_{label}';node=f'spike_{tag}';valuespec[key]=(node,t*1e-6);lines.append(f'meas tran {key} find v({node}) at={t}u')
 nodes=[n for tag in ['low','mid','high'] for n in [f'state_bare_{tag}',f'state_loaded_{tag}',f'out_{tag}',f'spike_{tag}']]+['beta','auxreset','bias','idle']
 lines +=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(f'v({n})' for n in nodes),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 w=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,17));printed={k:float(v) for k,v in re.findall(r'(?m)^((?:bare|loaded|spike)_[a-z_]+)\s*=\s*([-+0-9.eE]+)',log)};complete=run.returncode==0 and len(printed)==len(valuespec) and w.ndim==2 and w.shape[1]==17 and len(w)>1 and np.isfinite(w).all() and abs(w[-1,0]-50e-6)<1e-12 and 'aborted' not in log.lower();metrics={}
 if data.exists():files.add(data)
 if complete:
  measures={k:float(np.interp(t,w[:,0],w[:,1+nodes.index(n)])) for k,(n,t) in valuespec.items()};assert max(abs(measures[k]-printed[k]) for k in measures)<6e-6
  metrics={'primary_measures':measures,'loaded_minus_bare_by_phase_v':{tag:{label:measures[f'loaded_{tag}_{label}']-measures[f'bare_{tag}_{label}'] for label in times} for tag in ['low','mid','high']},'bias_cycle_state_shift_v':{tag:measures[f'loaded_{tag}_off']-measures[f'loaded_{tag}_pre'] for tag in ['low','mid','high']},'sensing_logic_v':{tag:measures[f'spike_{tag}_sensing'] for tag in ['low','mid','high']}}
 result={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,**metrics,'scope':'Matched three-level resident state with/without small native comparator input. All children fully qualified/extracted; assembled parent remains schematic. Frozen resident reference is diagnostic only under new load. Ideal threshold1.85V and gated .75V bias; native inverter clocks/output buffers and NF output clamp. No offset cancellation, RPEX/noise/PVT/yield, subtraction/reset/model/population service or combined layout acceptance.','acceptance':{'threshold_interface':False,'complete_PLIF':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),**{k:v for k,v in metrics.items() if k!='primary_measures'}},indent=2))
 if not complete:raise RuntimeError(log[-2200:])
if __name__=='__main__':main()
