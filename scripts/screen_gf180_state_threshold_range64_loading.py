"""Resident state/beta with startup autozero comparison near proposed range64 threshold."""
import hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files={Path(__file__)};texts=[];state='gf180_state_update_detailstem_ch3_pad06_v2';cmp='gf180_compact_nf_threshold_shielded';inv='gf180_phase_inverter_fullroute';nf='gf180_fixed_body_nf025_shorttracks'
 for name in [state,cmp,inv,nf,'gf180_fixed_body_tg_quarter_shorttracks','gf180_mim_5x5_ports_routed']:
  d=BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback']
  if name!='gf180_mim_5x5_ports_routed':assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique']
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
 stem='gf180_state_threshold_range64_loading_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat');models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Resident state threshold loading',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65',f"Vauxref auxref 0 {cal['frozen_auxiliary_reference_v']:.16g}",'Vthreshold threshold 0 1.656875','Vbias bias 0 .75']
 phases={'write':'PWL(0 3.3 9.99u 3.3 10u 0 50u 0)','auxreset':'PWL(0 3.3 19.97u 3.3 19.98u 0 29.99u 0 30u 3.3 50u 3.3)','beta':'PWL(0 0 19.99u 0 20u 3.3 20.49u 3.3 20.5u 0 50u 0)','az':'PWL(0 3.3 4.99u 3.3 5u 0 50u 0)'}
 for phase,wave in phases.items():lines +=[f'V{phase} {phase}_command 0 {wave}',f'Xb_{phase} {phase}_command {phase}b vdd 0 {inv}',f'Xc_{phase} {phase}b {phase} vdd 0 {inv}']
 for tag,v in [('low',1.652),('mid',1.658),('high',1.664)]:
  lines.append(f'Vtarget_{tag} target_{tag} 0 PWL(0 1.656875 7.99u 1.656875 8u {v} 50u {v})')
  for arm in ['bare','loaded']:
   lines +=[f'Xstate_{arm}_{tag} state_{arm}_{tag} aux_{arm}_{tag} target_{tag} write writeb auxreset beta auxref vcm 0 vdd {state}',f'.ic v(state_{arm}_{tag})=1.656875 v(aux_{arm}_{tag})=1.65']
  lines +=[f'Xcompare_{tag} state_loaded_{tag} azin_{tag} out_{tag} vdd 0 bias cmp_{tag} {cmp}',f'Xaz_{tag} out_{tag} azin_{tag} az azb 0 vdd gf180_fixed_body_tg_quarter_shorttracks',f'Xdummy_{tag} azin_{tag} azin_{tag} azb 0 {nf}',f'Xcomp_{tag} out_{tag} cmp_{tag} 0 gf180_mim_5x5_ports_routed',f'.ic v(azin_{tag})=1.656875 v(out_{tag})=1.656875',f'Xbuf1_{tag} out_{tag} spikeb_{tag} vdd 0 {inv}',f'Xbuf2_{tag} spikeb_{tag} spike_{tag} vdd 0 {inv}']
  for i in range(9):lines.append(f'Xstore{i}_{tag} azin_{tag} vcm 0 gf180_mim_5x5_ports_routed')
 lines +=['.control','set numdgt=15','tran .005u 50u 0 .05u uic'];times={'held':19,'commit':31.5,'pre':38.5,'sensing':41.5,'off':42.5,'final':49.5};valuespec={}
 for tag in ['low','mid','high']:
  for arm in ['bare','loaded']:
   for label,t in times.items():key=f'{arm}_{tag}_{label}';node=f'state_{arm}_{tag}';valuespec[key]=(node,t*1e-6);lines.append(f'meas tran {key} find v({node}) at={t}u')
  for label,t in [('sensing',41.5),('final',49.5)]:key=f'spike_{tag}_{label}';node=f'spike_{tag}';valuespec[key]=(node,t*1e-6);lines.append(f'meas tran {key} find v({node}) at={t}u')
 nodes=[n for tag in ['low','mid','high'] for n in [f'state_bare_{tag}',f'state_loaded_{tag}',f'out_{tag}',f'spike_{tag}',f'azin_{tag}']]+['beta','auxreset','bias','az']
 lines +=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(f'v({n})' for n in nodes),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 w=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,20));printed={k:float(v) for k,v in re.findall(r'(?m)^((?:bare|loaded|spike)_[a-z_]+)\s*=\s*([-+0-9.eE]+)',log)};complete=run.returncode==0 and len(printed)==len(valuespec) and w.ndim==2 and w.shape[1]==20 and len(w)>1 and np.isfinite(w).all() and abs(w[-1,0]-50e-6)<1e-12 and 'aborted' not in log.lower();metrics={}
 if data.exists():files.add(data)
 if complete:
  measures={k:float(np.interp(t,w[:,0],w[:,1+nodes.index(n)])) for k,(n,t) in valuespec.items()};assert max(abs(measures[k]-printed[k]) for k in measures)<6e-6
  metrics={'primary_measures':measures,'loaded_minus_bare_by_phase_v':{tag:{label:measures[f'loaded_{tag}_{label}']-measures[f'bare_{tag}_{label}'] for label in times} for tag in ['low','mid','high']},'late_sensing_state_shift_v':{tag:measures[f'loaded_{tag}_off']-measures[f'loaded_{tag}_pre'] for tag in ['low','mid','high']},'sensing_logic_v':{tag:measures[f'spike_{tag}_sensing'] for tag in ['low','mid','high']}}
 result={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,**metrics,'scope':'Matched resident state with/without shielded comparator and native startup autozero, nine physical minimum MIM reference units, real compensation MIM, native quarterTG plus minimumNF dummy. State writer supplies threshold1.656875V during calibration then near-threshold targets1.652/1.658/1.664V at8us before release10us; no destructive calibration after state retention begins. Comparator continuously biased .75V, native output buffers; no bias power-saving/service claim. Frozen resident reference is diagnostic under new loading. Proposed range64 remains an unaccepted state saturation approximation; this compares sensing after actual beta, with no physical range limiting/conversion or threshold adaptation. Parent schematic with qualified extracted children, nominal only. Initial UIC reference overshoot is an unqualified startup artifact; valid settled operation scoped after1us. No RPEX/native noise,50ms reference retention/PVT/yield, subtraction/reset/model/fullpopulation/combined layout acceptance','acceptance':{'threshold_interface':False,'complete_PLIF':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),**{k:v for k,v in metrics.items() if k!='primary_measures'}},indent=2))
 if not complete:raise RuntimeError(log[-2200:])
if __name__=='__main__':main()
