"""Audit terminal-only auxiliary storage and frozen physical reference correction."""
from pathlib import Path
import hashlib,json,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_resident_beta_reference_mismatch_boundary.json';assert not out.exists()
 files={Path(__file__)};cases=[];slopes={}
 specs=[('terminal_storage','c4e4b373ea3a','off',1),('terminal_storage','c4e4b373ea3a','on',1),('terminal_storage','c4e4b373ea3a','on',2),('reference_corrected','de393c6a54dd','on',1),('reference_corrected','de393c6a54dd','on',2),('reference_seed29','af2a30385717','on',1)]
 for family,src,mode,n in specs:
  stem=f'gf180_resident_beta_{family}_{mode}_plates{n}_src{src}';rp=R/(stem+'.json');d=json.loads(rp.read_text());files.add(rp)
  assert d['simulation_completed'] and d['simulator_returncode']==0
  for name,h in d['sha256'].items():assert sha(ROOT/name)==h,name
  dp=rp.with_suffix('.dat');files.add(dp);w=np.loadtxt(dp,skiprows=1)
  assert w.shape[1]==7 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-25e-6)<1e-12
  phases={label:{tag:{node:float(np.interp(t*1e-6,w[:,0],w[:,1+2*i+j])) for j,node in enumerate(['state','aux'])} for i,tag in enumerate(['low','mid','high'])} for label,t in [('held',19),('sharing',20.45),('after',21.5),('final',24.5)]}
  for label,states in phases.items():
   for tag,nodes in states.items():
    for node,v in nodes.items():assert abs(v-d['measurements'][f'{tag}_{node}_{label}'])<6e-6
  x=np.array([phases['held'][t]['state'] for t in ['low','mid','high']]);y=np.array([phases['after'][t]['state'] for t in ['low','mid','high']]);b=float((y[2]-y[0])/(x[2]-x[0]));off=float(y[0]-1.65-b*(x[0]-1.65))
  case={'report':rp.relative_to(ROOT).as_posix(),'family':family,'mode':mode,'state_plates':n,'endpoint_slope':b,'endpoint_line_offset_about_VCM_v':off,'midpoint_offset_about_slope_v':float(y[1]-1.65-b*(x[1]-1.65)),'midpoint_nonlinearity_v':float(y[1]-y[0]-b*(x[1]-x[0])),'phases_v':phases}
  if family=='terminal_storage' and mode=='on':slopes[n]=b
  if family.startswith('reference_'):
   residual=y-1.65-slopes[n]*(x-1.65)
   case.update({'frozen_uncorrected_slope':slopes[n],'physical_error_against_frozen_slope_v':dict(zip(['low','mid','high'],map(float,residual))),'maximum_absolute_error_against_frozen_slope_v':float(np.max(np.abs(residual)))})
  deck=ROOT/'artifacts/analog_asic/benches'/(stem+'.spice');files.add(deck)
  assert not re.search(r'(?m)^Xauxcap_',deck.read_text())
  if family=='reference_seed29':assert '.param sw_stat_global=0 sw_stat_mismatch=1' in deck.read_text() and 'setseed 29' in deck.read_text()
  cases.append(case)
 calp=R/'gf180_resident_beta_terminal_storage_frozen_reference.json';cal=json.loads(calp.read_text());files.add(calp)
 assert cal['prediction_completed']
 for name,h in cal['sha256'].items():assert sha(ROOT/name)==h,name
 result={'audit_completed':True,'six_cases_primary_waveforms_completed_and_measures_reproduced':True,'frozen_aux_reference_v':cal['auxiliary_precharge_reference_v'],'cases':cases,'conclusion':'Removing explicit auxiliary PF raises attenuation slopes without additional state MIM. Frozen common physical precharge prediction reduces common offset on independent levels in both1/2plate cases. Residual nonlinear switching error remains; two slopes do not cover original learned betas. Continue native beta programmability/retention/noise feasibility before complete-neuron layout or full-population replication.','scope':'Five nominal cases plus one configured native local mismatch seed29 case, global variation disabled. Three voltage points/case,25us traces,one local update, actual extracted switch-terminal storage. Common reference predicted only from earlier1plate endpoints. Residual uses earlier measured1/2plate slopes as frozen comparator, not learned beta accuracy or task acceptance. Intermodule parent schematic, external reference/clocks; no native noise, leakage validation,5msretention, mismatch distribution/yield or service.','acceptance':{'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':str(out),'audit_completed':True,'frozen_reference_v':result['frozen_aux_reference_v'],'cases':[{k:v for k,v in c.items() if k not in ['phases_v','physical_error_against_frozen_slope_v']} for c in cases]},indent=2))
if __name__=='__main__':main()
