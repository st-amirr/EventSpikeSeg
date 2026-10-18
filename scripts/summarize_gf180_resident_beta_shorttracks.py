"""Validate matched nominal routed-switch comparison from primary waveforms."""
from pathlib import Path
import hashlib,json,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';R=BASE/'results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_resident_beta_shorttracks_boundary.json';assert not out.exists()
 files={Path(__file__)};cases=[]
 for family,src in [('charge_share_beta','493d42582d19'),('beta_shorttracks','792b8b8aa037')]:
  for mode in ['off','on']:
   stem=f'gf180_resident_{family}_{mode}_plates1_src{src}';rp=R/(stem+'.json');d=json.loads(rp.read_text());files.add(rp)
   assert d['simulation_completed'] and d['simulator_returncode']==0
   for name,h in d['sha256'].items():assert sha(ROOT/name)==h,name
   dp=R/(stem+'.dat');files.add(dp);w=np.loadtxt(dp,skiprows=1)
   assert w.shape[1]==7 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-25e-6)<1e-12
   phases={label:{tag:{node:float(np.interp(t*1e-6,w[:,0],w[:,1+2*i+j])) for j,node in enumerate(['state','aux'])} for i,tag in enumerate(['low','mid','high'])} for label,t in [('held',19),('sharing',20.45),('after',21.5),('final',24.5)]}
   for label,states in phases.items():
    for tag,nodes in states.items():
     for node,val in nodes.items():assert abs(val-d['measurements'][f'{tag}_{node}_{label}'])<6e-6
   x=[phases['held'][t]['state'] for t in ['low','mid','high']];y=[phases['after'][t]['state'] for t in ['low','mid','high']];slope=(y[2]-y[0])/(x[2]-x[0]);intercept=y[0]-slope*x[0]
   cases.append({'report':rp.relative_to(ROOT).as_posix(),'family':family,'mode':mode,'phase_v':phases,'endpoint_slope':slope,'endpoint_line_offset_about1p65_v':intercept+(slope-1)*1.65,'midpoint_offset_about_slope_v':y[1]-1.65-slope*(x[1]-1.65),'midpoint_nonlinearity_v':y[1]-slope*x[1]-intercept,'release_shifts_v':{t:phases['after'][t]['state']-phases['sharing'][t]['state'] for t in ['low','mid','high']}})
 cells=['gf180_fixed_body_tg_fullroute_quarter','gf180_fixed_body_tg_quarter_shorttracks'];layouts=[];devices=[]
 for cell in cells:
  folder=BASE/'layout'/cell;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
  cp=folder/(cell+'_cap.spice');files.add(cp);devices.append(re.findall(r'(?m)^X[^\n]+',cp.read_text()))
  bbox=q['bbox_um'];layouts.append({'cell':cell,'bbox_um':bbox,'bbox_area_um2':(bbox[2]-bbox[0])*(bbox[3]-bbox[1])})
 assert devices[0]==devices[1], 'Native device connections/dimensions must match'
 ap=BASE/'layout'/cells[1]/'abstract_qualification.json';files.add(ap);aq=json.loads(ap.read_text())
 assert aq['ports']==['A','B','EN','ENB','VSS','VDD']
 result={'audit_completed':True,'matched_native_device_lines':True,'comparison_scope':'Nominal only; all three TG instances use the changed routing package. Native device lines identical, target/timing/supply/MIM/aux PF unchanged. Held voltages differ due to physical writer release; compare actual held-to-after transfer. No matched random-variation or total area/precision claim.','layouts':layouts,'cases':cases,'conclusion':'Shorter TG routing raises endpoint slope and reduces switch bbox, but common offset and release nonlinearity persist. Retain qualified primitive; do not accept local beta or grow state capacitors from this result. Review auxiliary charge-storage and cancellation mechanism next.','acceptance':{'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'layouts':layouts,'transfer':[{'family':c['family'],'mode':c['mode'],'slope':c['endpoint_slope'],'midpoint_offset_mV':c['midpoint_offset_about_slope_v']*1000,'midpoint_nonlinearity_mV':c['midpoint_nonlinearity_v']*1000} for c in cases]},indent=2))
if __name__=='__main__':main()
