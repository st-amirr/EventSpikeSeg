import json,hashlib,math,struct
from pathlib import Path
BASE=Path('artifacts/analog_asic');mp=BASE/'assembly/membrane_voltage_scale_manifest_v2.json';dcfile=BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json';holdfile=BASE/'results/gf180_membrane_scale_v23_bank_map_v4_validate41pt_batched.json';binfile=BASE/'assembly/gf180_membrane_scale_v23_bank_program_volts_v5_41pt_holdcurve.f64le';outfile=BASE/'results/gf180_membrane_scale_v23_bank_calibration_v5.json';assert not binfile.exists() and not outfile.exists()
m=json.loads(mp.read_text());dc=json.loads(dcfile.read_text())['curve'];hold=json.loads(holdfile.read_text())['cases'];ranges=[float(x) for a in m['actors'] for x in a['range_abs_model_units']];scales=[.9/x for x in ranges];smax=max(scales);smin=min(scales);imax=dc[0]['current_a']
def state_i(i):
 for a,b in zip(dc,dc[1:]):
  if a['current_a']>=i>=b['current_a']:return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
 raise ValueError(i)
h=sorted((float(c['measured_state_5ms_v']),float(c['command_v'])) for c in hold);assert all(h[i][0]<h[i+1][0] for i in range(len(h)-1))
def command(st):
 for (s0,c0),(s1,c1) in zip(h,h[1:]):
  if s0<=st<=s1:return c0+(st-s0)*(c1-c0)/(s1-s0)
 if st<h[0][0]:
  (s0,c0),(s1,c1)=h[0],h[1];return c0+(st-s0)*(c1-c0)/(s1-s0)
 (s0,c0),(s1,c1)=h[-2],h[-1];return c0+(st-s0)*(c1-c0)/(s1-s0)
vs=[command(state_i(imax*x/smax)) for x in scales];binfile.write_bytes(struct.pack('<'+'d'*len(vs),*vs));ss=sorted(scales)
def quant(q):
 x=(len(ss)-1)*q;lo=math.floor(x);hi=math.ceil(x);return ss[lo] if lo==hi else ss[lo]*(hi-x)+ss[hi]*(x-lo)
qmap={}
for name,q in [('p01',.01),('p10',.1),('p50',.5),('p90',.9),('p99',.99)]:
 scale=quant(q);target=imax*scale/smax;state=state_i(target);qmap[name]={'scale':scale,'target_current_a':target,'target_state_v':state,'program_command_v':command(state)}
r={'mapping_generated':True,'checkpoint_sha256':m['checkpoint_sha256'],'bank_count':len(vs),'mapping':'Proportional current targets from original float-derived bank scales; inverse dense DC current-to-state transfer and inverse measured 41-point transient command-to-held-state transfer.','scale_dynamic_ratio':smax/smin,'target_current_range_a':[imax*smin/smax,imax],'command_voltage_range_v':[min(vs),max(vs)],'quantile_targets':qmap,'source_hold_point_count':len(hold),'scope':'Continuous per-bank command table; 41-point transient curve fit by piecewise linear interpolation. Further between-point validation and full-float recurrence remain required. Nominal typical only.','sha256':{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (mp,dcfile,holdfile,binfile)}};outfile.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'count':len(vs),'command_range':r['command_voltage_range_v'],'quantiles':qmap},indent=2))
