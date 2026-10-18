"""Bounded complete-cycle characterization of the physical GF180 state/update parent."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--seed',type=int,choices=[0,29],default=0); p.add_argument('--calibration',type=Path); a=p.parse_args()
 files={Path(__file__)}; texts=[]
 cell='gf180_nf_state_update_aux_three_mim'; inv='gf180_phase_inverter_fullroute'
 for name in [cell,inv]:
  d=BASE/'layout'/name; qp=d/'qualification.json'; q=json.loads(qp.read_text()); files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n; assert sha(f)==h,n; files.add(f)
  texts.append((d/(name+'_cap.spice')).read_text())
 ref=1.4588666507852013; calibration=None
 if a.calibration:
  cp=a.calibration.resolve(); calibration=json.loads(cp.read_text()); assert calibration['simulation_completed'] and calibration['settings']['seed']==0 and not calibration['settings']['calibration']; files.add(cp)
  for n,h in calibration['sha256'].items(): assert sha(ROOT/n)==h,n; files.add(ROOT/n)
  ref=calibration['predicted_common_aux_reference_v']
 mode='check' if calibration else 'baseline'; stem=f'gf180_extracted_state_update_aux_three_mim_{mode}_seed{a.seed}_src{sha(Path(__file__))[:12]}'
 rp=BASE/'results'/(stem+'.json'); assert not rp.exists()
 models=BASE/'pdk/gf180_primitive_source/models/ngspice'; files.update(models.rglob('*.spice')); prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Extracted physical state update',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.param sw_stat_global=0 sw_stat_mismatch={int(bool(a.seed))}', '.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65',f'Vauxref auxref 0 {ref:.16g}']
 phases={'write':[(0,3.3),(9.99,3.3),(10,0)],'auxreset':[(0,3.3)],'beta':[(0,0)]}
 for k in range(3):
  off=100*k; phases['auxreset'] +=[(off+19.97,3.3),(off+19.98,0),(off+29.99,0),(off+30,3.3)]; phases['beta'] +=[(off+19.99,0),(off+20,3.3),(off+20.49,3.3),(off+20.5,0)]
 for phase,edges in phases.items():
  edges.append((315,edges[-1][1])); assert all(y[0]>x[0] for x,y in zip(edges,edges[1:])); wave='PWL('+' '.join(f'{t:.8g}u {v}' for t,v in edges)+')'
  lines +=[f'V{phase} {phase}_command 0 {wave}',f'Xb_{phase} {phase}_command {phase}b vdd 0 {inv}',f'Xc_{phase} {phase}b {phase} vdd 0 {inv}']
 targets=[1.2,1.65,2.1] if calibration else [1.05,1.65,2.25]
 for tag,v in zip(['low','mid','high'],targets):
  lines +=[f'Vtarget_{tag} target_{tag} 0 {v}',f'Xmodule_{tag} state_{tag} aux_{tag} target_{tag} write writeb auxreset beta auxref vcm 0 vdd {cell}',f'.ic v(state_{tag})=1.65 v(aux_{tag})=1.65']
 lines +=['.control','set numdgt=15']
 if a.seed: lines +=[f'setseed {a.seed}','reset']
 lines +=['tran .01u 315u 0 .1u uic']; measure_times={}
 for tag in ['low','mid','high']:
  for k in range(3):
   for node in ['state','aux']:
    for label,t in [('before',19),('sharing',20.45),('after',21.5),('rearmed',31.5),('late',99.5)]:
     key=f'{tag}_c{k}_{node}_{label}'; measure_times[key]=(f'{node}_{tag}',(100*k+t)*1e-6); lines.append(f'meas tran {key} find v({node}_{tag}) at={100*k+t}u')
 data=BASE/'results'/(stem+'.dat'); nodes=[f'{node}_{tag}' for tag in ['low','mid','high'] for node in ['state','aux']]+['beta','auxreset']; lines +=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(f'v({n})' for n in nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice'); deck.write_text('\n'.join(lines)+'\n',encoding='utf-8'); files.add(deck); snap=BASE/'tools/source_snapshots'/(stem+'.py'); snap.write_bytes(Path(__file__).read_bytes()); files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr; lp=BASE/'results'/(stem+'.log'); lp.write_text(log,encoding='utf-8'); files.add(lp); values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_c[0-9]+_[a-z_]+)\s*=\s*([-+0-9.eE]+)',log)}
 rows=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,9)); complete=run.returncode==0 and len(values)==90 and rows.ndim==2 and rows.shape[1]==9 and len(rows)>1 and np.isfinite(rows).all() and rows[-1,0]>=315e-6-1e-12 and 'aborted' not in log.lower(); result={}
 if data.exists(): files.add(data)
 if complete:
  disagreement=max(abs(values[key]-np.interp(t,rows[:,0],rows[:,1+nodes.index(node)])) for key,(node,t) in measure_times.items()); assert disagreement<6e-6
  before=lambda tag:values[f'{tag}_c0_state_before']; after=lambda tag:values[f'{tag}_c0_state_rearmed']
  slope=(after('high')-after('low'))/(before('high')-before('low')); offset=after('low')-1.65-slope*(before('low')-1.65); comparison=calibration['first_complete_cycle_slope'] if calibration else slope
  residuals={tag:[values[f'{tag}_c{k}_state_rearmed']-(1.65+comparison**(k+1)*(before(tag)-1.65)) for k in range(3)] for tag in ['low','mid','high']}
  result={'primary_measure_max_disagreement_v':disagreement,'first_complete_cycle_slope':slope,'endpoint_offset_v':offset,'midpoint_nonlinearity_v':after('mid')-1.65-slope*(before('mid')-1.65)-offset,'comparison_slope':comparison,'cumulative_residuals_v':residuals,'worst_cumulative_residual_v':max(abs(v) for vs in residuals.values() for v in vs),'predicted_common_aux_reference_v':ref-offset/(1-slope)}
 report={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,'settings':{'seed':a.seed,'calibration':str(a.calibration) if a.calibration else None},'frozen_auxiliary_reference_v':ref,'measurements':values,**result,'scope':'Actual capacitively extracted physical state/update parent; native external inverter clocks, ideal reference/data voltage fixtures. Three accelerated100us updates, state initialized through writer only once, auxiliary rearmed each cycle. Calibration uses nominal endpoints only; check uses independent targets and frozen comparator/reference. No learned-beta coverage, RPEX, sampled noise, physical dielectric retention, PVT/yield, complete PLIF/model/service/chip acceptance.','acceptance':{'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),**result},indent=2))
 if not complete: raise RuntimeError(log[-2000:])
if __name__=='__main__': main()
