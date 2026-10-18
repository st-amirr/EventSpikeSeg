import json,struct,hashlib,math
from pathlib import Path
BASE=Path('artifacts/analog_asic');manifestp=BASE/'assembly/membrane_voltage_scale_manifest_v2.json';dcp=BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json';holdp=BASE/'results/gf180_membrane_scale_v23_bank_map_validate21pt_v1.json';binp=BASE/'assembly/gf180_membrane_scale_v23_bank_program_volts_v4_21pt_holdcurve.f64le';outp=BASE/'results/gf180_membrane_scale_v23_bank_calibration_v4.json';assert not binp.exists() and not outp.exists()
m=json.loads(manifestp.read_text());dc=json.loads(dcp.read_text())['curve'];hold=json.loads(holdp.read_text())['cases'];ranges=[float(x) for a in m['actors'] for x in a['range_abs_model_units']];scales=[.9/r for r in ranges];smax=max(scales);smin=min(scales);imax=dc[0]['current_a']
def state_for_current(i):
 for a,b in zip(dc,dc[1:]):
  if a['current_a']>=i>=b['current_a']:return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
 raise ValueError(i)
h=sorted((float(c['measured_state_5ms_v']),float(c['command_v'])) for c in hold);assert all(h[i][0]<h[i+1][0] for i in range(len(h)-1))
def command_for_state(v):
 for (s0,c0),(s1,c1) in zip(h,h[1:]):
  if s0<=v<=s1:return c0+(v-s0)*(c1-c0)/(s1-s0)
 if abs(v-h[0][0])<1e-9:return h[0][1]
 if abs(v-h[-1][0])<1e-9:return h[-1][1]
 if v<h[0][0]:
  (s0,c0),(s1,c1)=h[0],h[1];return c0+(v-s0)*(c1-c0)/(s1-s0)
 if v>h[-1][0]:
  (s0,c0),(s1,c1)=h[-2],h[-1];return c0+(v-s0)*(c1-c0)/(s1-s0)
 raise ValueError(v)
commands=[]
for s in scales:commands.append(command_for_state(state_for_current(imax*s/smax)))
binp.write_bytes(struct.pack('<'+'d'*len(commands),*commands));ss=sorted(scales)
def quant(a,q):
 x=(len(a)-1)*q;lo=math.floor(x);hi=math.ceil(x);return a[lo] if lo==hi else a[lo]*(hi-x)+a[hi]*(x-lo)
qpoints={}
for name,q in [('p01',.01),('p10',.1),('p50',.5),('p90',.9),('p99',.99)]:
 s=quant(ss,q);it=imax*s/smax;st=state_for_current(it);qpoints[name]={'scale':s,'target_current_a':it,'target_held_state_v':st,'program_command_v':command_for_state(st)}
report={'mapping_generated':True,'model_checkpoint_sha256':m['checkpoint_sha256'],'bank_count':len(commands),'mapping':'For each original float bank scale 0.9/range, set target current proportional to scale; use the dense extracted DC PFET transfer to convert target current to held voltage, then invert the 21-point measured 5ms command-to-held-voltage relationship to obtain the program command. This preserves the nonlinear current curve; no QAT or model quantization.','bank_scale_dynamic_ratio':smax/smin,'target_current_range_a':[imax*smin/smax,imax],'target_held_state_voltage_range_v':[state_for_current(imax*smin/smax),state_for_current(imax)],'program_command_voltage_range_v':[min(commands),max(commands)],'quantile_targets':qpoints,'source_hold_curve_residual_mv':[round((c['measured_state_5ms_v']-c['command_v'])*1000,4) for c in hold],'physical_accuracy_claim':False,'scope':'Generated voltage commands for all 490,240 float-derived banks. State-to-command calibration uses 21 measured transient nodes, but unsampled interpolation error and full float recurrence still require validation. Nominal typical only.','sha256':{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (manifestp,dcp,holdp,binp)}};outp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'range_v':report['program_command_voltage_range_v'],'quantiles':qpoints},indent=2))

