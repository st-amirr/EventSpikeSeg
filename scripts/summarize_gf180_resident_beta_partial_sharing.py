"""Audit partial-sharing native gate pulses; reject a simple duration-to-beta assumption."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_resident_beta_partial_sharing_boundary.json';assert not out.exists()
 files={Path(__file__)};cases=[]
 for width,src in [(.1,'30b5c833963e'),(.2,'1385e7a35471'),(.5,'30b5c833963e')]:
  rp=R/f'gf180_resident_beta_partial_sharing_width{width:g}ns_on_plates1_src{src}.json';d=json.loads(rp.read_text());files.add(rp)
  assert d['simulation_completed'] and d['simulator_returncode']==0
  for name,h in d['sha256'].items():assert sha(ROOT/name)==h,name
  dp=rp.with_suffix('.dat');files.add(dp);w=np.loadtxt(dp,skiprows=1)
  assert w.shape[1]==9 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-25e-6)<1e-12
  for tag,i in [('low',1),('mid',3),('high',5)]:
   for node,j in [('state',i),('aux',i+1)]:
    for label,t in [('acquired',9.5),('held',19),('sharing',20.45),('after',21.5),('final',24.5)]:assert abs(np.interp(t*1e-6,w[:,0],w[:,j])-d['measurements'][f'{tag}_{node}_{label}'])<6e-6
  mask=(w[:,0]>=19.99e-6)&(w[:,0]<=20.02e-6)
  assert abs(w[mask,7].max()-d['measurements']['beta_peak'])<6e-6 and abs(w[mask,8].min()-d['measurements']['betab_min'])<6e-6
  x=np.array([np.interp(19e-6,w[:,0],w[:,i]) for i in [1,3,5]]);y=np.array([np.interp(21.5e-6,w[:,0],w[:,i]) for i in [1,3,5]]);b=float((y[2]-y[0])/(x[2]-x[0]));off=float(y[0]-1.65-b*(x[0]-1.65))
  cases.append({'report':rp.relative_to(ROOT).as_posix(),'command_hold_ns':width,'endpoint_slope':b,'offset_about1p65_v':off,'midpoint_nonlinearity_v':float(y[1]-y[0]-b*(x[1]-x[0])),'native_beta_gate_peak_v':float(w[mask,7].max()),'native_betab_gate_minimum_v':float(w[mask,8].min())})
 result={'audit_completed':True,'cases':cases,'scope':'Three nominal cases, one state MIM, identical native gate chain and TG/terminal storage.0.1ns command edges, varying command hold; full-sharing reference reused without refitting. Primary finite waveforms/gates and all32 measures checked. Three state levels only; peak excursions and filtered pulses are measured, not qualified driver timing/oxide/noise/mismatch.','conclusion':'Short commands are filtered by native inverter chain; intermediate partial sharing is voltage dependent and has multi-mV midpoint nonlinearity. Do not treat command width as a linear or accepted learned-beta programmer. Stop this direct-TG duration sweep and evaluate lower-capacitance fully settled selection or another physical attenuation mechanism.','acceptance':{'duration_beta_programmer':False,'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'cases':cases},indent=2))
if __name__=='__main__':main()
