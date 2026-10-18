"""Validate native5ms hold waveform separately from beta update transfer."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_resident_beta_5ms_hold_boundary.json';assert not out.exists()
 rp=R/'gf180_resident_beta_5ms_hold_on_plates1_src4c917e85a65c.json';d=json.loads(rp.read_text());assert d['simulation_completed'] and d['simulator_returncode']==0
 for name,h in d['sha256'].items():assert sha(ROOT/name)==h,name
 dp=rp.with_suffix('.dat');w=np.loadtxt(dp,skiprows=1);assert w.shape[1]==7 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-5025e-6)<1e-12
 times={'acquired':9.5,'released':10.5,'held':5019,'sharing':5020.45,'after':5021.5,'final':5024.5};phases={label:{tag:{node:float(np.interp(t*1e-6,w[:,0],w[:,1+2*i+j])) for j,node in enumerate(['state','aux'])} for i,tag in enumerate(['low','mid','high'])} for label,t in times.items()}
 for label,states in phases.items():
  for tag,nodes in states.items():
   for node,v in nodes.items():assert abs(v-d['measurements'][f'{tag}_{node}_{label}'])<6e-6
 bp=R/'gf180_resident_beta_terminal_storage_boundary.json';baseline=json.loads(bp.read_text());b=next(c['endpoint_slope'] for c in baseline['cases'] if c['family']=='terminal_storage' and c['mode']=='on' and c['state_plates']==1)
 lanes={t:{'hold_drift_v':phases['held'][t]['state']-phases['released'][t]['state'],'after_update_error_against_frozen_slope_v':phases['after'][t]['state']-1.65-b*(phases['held'][t]['state']-1.65)} for t in ['low','mid','high']}
 files=[Path(__file__),rp,dp,bp]
 result={'audit_completed':True,'simulation_completed':True,'hold_interval_us':[10.5,5019],'nominal_hold_duration_us':5008.5,'lanes':lanes,'maximum_absolute_hold_drift_v':max(abs(v['hold_drift_v']) for v in lanes.values()),'maximum_absolute_update_error_against_frozen_slope_v':max(abs(v['after_update_error_against_frozen_slope_v']) for v in lanes.values()),'frozen_comparison_slope':b,'phases_v':phases,'scope':'One nominal three-level native switch-terminal storage local-update fixture, extracted child capacitances and native junction/leakage model as configured. Static buses, external clocks/reference, no signed events during hold. Does not validate physical MIM dielectric leakage, native sampled noise, statistical/PVT retention, learned beta coverage, complete PLIF or population5ms service. Parent connection schematic.','acceptance':{'qualified_memory_retention':False,'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['phases_v','sha256']},indent=2))
if __name__=='__main__':main()
