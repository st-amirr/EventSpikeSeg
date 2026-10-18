"""Audit terminal-only auxiliary storage and frozen physical reference correction."""
from pathlib import Path
import hashlib,json,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_resident_beta_nf_terminal_storage_boundary.json';assert not out.exists()
 files={Path(__file__)};cases=[];slopes={}
 specs=[('nf_terminal_storage','20b196b31d91','off',1),('nf_terminal_storage','20b196b31d91','on',1),('nf_terminal_storage','20b196b31d91','on',2)]
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
  if family=='nf_terminal_storage' and mode=='on':slopes[n]=b
  if family=='reference_corrected':
   residual=y-1.65-slopes[n]*(x-1.65)
   case.update({'frozen_uncorrected_slope':slopes[n],'physical_error_against_frozen_slope_v':dict(zip(['low','mid','high'],map(float,residual))),'maximum_absolute_error_against_frozen_slope_v':float(np.max(np.abs(residual)))})
  deck=ROOT/'artifacts/analog_asic/benches'/(stem+'.spice');files.add(deck)
  assert not re.search(r'(?m)^Xauxcap_',deck.read_text())
  cases.append(case)
 layout=ROOT/'artifacts/analog_asic/layout/gf180_fixed_body_nf025_shorttracks';qp=layout/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
 assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and q['gds_roundtrip_drc_count']==0 and not q['extraction_feedback']
 cp=layout/'gf180_fixed_body_nf025_shorttracks_cap.spice';files.add(cp);ct=cp.read_text();assert '.subckt gf180_fixed_body_nf025_shorttracks A B EN VSS' in ct
 devices=re.findall(r'(?m)^X[^\n]+',ct);assert len(devices)==1 and 'nfet_03v3' in devices[0] and 'pfet' not in devices[0]
 ap=layout/'abstract_qualification.json';files.add(ap);aq=json.loads(ap.read_text());assert aq['ports']==['A','B','EN','VSS']
 fit=cases[1];predref=1.65-fit['endpoint_line_offset_about_VCM_v']/(1-fit['endpoint_slope'])
 result={'audit_completed':True,'three_cases_primary_waveforms_completed_and_measures_reproduced':True,'predicted_aux_reference_v':predref,'layout_size_um':aq['size_um'] if 'size_um' in aq else q['bbox_um'],'cases':cases,'conclusion':'Native fully settled NF-only reset/selection reduces auxiliary capacitance and increases useful slope without partial pulses or extra state storage. Common offset and state dependence remain; predict one physical auxiliary-reference correction from1plate endpoints before independent checks. Original learned-beta coverage, real reference generation and scalable service remain unqualified.','scope':'Three nominal three-level cases,25us traces,one local update. Writer still quarterTG, reset/beta singleNF with grounded body, noPF/ENB/VDD ports in selection child. Physical DRC/LVS/GDS/LEF qualified child, parent schematic. No applied correction, learned beta coverage, noise/leakage/5msretention, statistical variation, complete PLIF, model or population service acceptance.','acceptance':{'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':str(out),'audit_completed':True,'predicted_reference_v':result['predicted_aux_reference_v'],'cases':[{k:v for k,v in c.items() if k not in ['phases_v','physical_error_against_frozen_slope_v']} for c in cases]},indent=2))
if __name__=='__main__':main()
