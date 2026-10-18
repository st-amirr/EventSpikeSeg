"""Correct v5 bank commands using the measured v5 81-point current residual."""
import json,hashlib,math,struct
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]/'artifacts/analog_asic'
mp=BASE/'assembly/membrane_voltage_scale_manifest_v2.json'
dcfile=BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json'
holdfile=BASE/'results/gf180_membrane_scale_v23_bank_map_v4_validate41pt_batched.json'
errfile=BASE/'results/gf180_membrane_scale_v23_bank_map_v5_validate81pt_batched.json'
binfile=BASE/'assembly/gf180_membrane_scale_v23_bank_program_volts_v6_residual_corrected.f64le'
outfile=BASE/'results/gf180_membrane_scale_v23_bank_calibration_v6.json'
assert not binfile.exists() and not outfile.exists()
m=json.loads(mp.read_text());dc=json.loads(dcfile.read_text())['curve'];hold=json.loads(holdfile.read_text())['cases'];err=json.loads(errfile.read_text())['cases']
ranges=[float(x) for a in m['actors'] for x in a['range_abs_model_units']];scales=[.9/x for x in ranges];smax=max(scales);smin=min(scales);imax=dc[0]['current_a']
eq=[float(x['quantile']) for x in err];ee=[float(x['relative_current_error']) for x in err]
ss=sorted(scales)
def quantile(scale):return (math.floor(0) if False else 0) # replaced below
def rank(scale):
 import bisect
 pos=bisect.bisect_left(ss,scale)
 return pos/(len(ss)-1)
def interp(x,xs,ys):
 if x<=xs[0]: i=0
 elif x>=xs[-1]: i=len(xs)-2
 else:
  import bisect
  i=bisect.bisect_right(xs,x)-1
 return ys[i]+(x-xs[i])*(ys[i+1]-ys[i])/(xs[i+1]-xs[i])
def state_i(i):
 for a,b in zip(dc,dc[1:]):
  if a['current_a']>=i>=b['current_a']:return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
 if i>dc[0]['current_a']:
  a,b=dc[0],dc[1];return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
 if i<dc[-1]['current_a']:
  a,b=dc[-2],dc[-1];return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
 raise ValueError(i)
h=sorted((float(c['measured_state_5ms_v']),float(c['command_v'])) for c in hold)
def command(st):
 for (s0,c0),(s1,c1) in zip(h,h[1:]):
  if s0<=st<=s1:return c0+(st-s0)*(c1-c0)/(s1-s0)
 if st<h[0][0]:(s0,c0),(s1,c1)=h[0],h[1]
 else:(s0,c0),(s1,c1)=h[-2],h[-1]
 return c0+(st-s0)*(c1-c0)/(s1-s0)
vs=[]
for scale in scales:
 target=imax*scale/smax;e=interp(rank(scale),eq,ee);corrected=target/(1.0+e);vs.append(command(state_i(corrected)))
binfile.write_bytes(struct.pack('<'+'d'*len(vs),*vs))
r={'mapping_generated':True,'checkpoint_sha256':m['checkpoint_sha256'],'bank_count':len(vs),'mapping':'v5 scale commands corrected by interpolating the measured 81-point v5 residual against bank scale quantile; target DC current divided by (1+residual), then inverted through measured 41-point held-voltage curve.','scale_dynamic_ratio':smax/smin,'target_current_range_a':[imax*smin/smax,imax],'command_voltage_range_v':[min(vs),max(vs)],'source_residual_point_count':len(err),'scope':'Iterative first-order command compensation; requires an independent transistor transient validation and full-float recurrence replay. Nominal typical only.','sha256':{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (mp,dcfile,holdfile,errfile,binfile)}}
outfile.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('bank_count','command_voltage_range_v','scope')},indent=2))
