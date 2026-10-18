from __future__ import annotations
import hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';mfile=BASE/'assembly/membrane_voltage_scale_manifest_v2.json';curvefile=BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json';reqfile=BASE/'results/gf180_membrane_scale_hardware_requirements_v1.json';holdfile=BASE/'results/gf180_membrane_scale_v23_bank_map_validate5ms_v2.json'
binfile=BASE/'assembly/gf180_membrane_scale_v23_bank_program_volts_v2_holdcorrected.f64le';outfile=BASE/'results/gf180_membrane_scale_v23_bank_calibration_v2.json';assert not binfile.exists() and not outfile.exists()
m=json.loads(mfile.read_text());curve=json.loads(curvefile.read_text())['curve'];hold=json.loads(holdfile.read_text());assert hold['simulation_completed'];ranges=[float(x) for a in m['actors'] for x in a['range_abs_model_units']];assert len(ranges)==490240;scales=[.9/x for x in ranges];smax=max(scales);smin=min(scales);imax=curve[0]['current_a']
# DC forward/inverse calibration
def iv(v):
 for a,b in zip(curve,curve[1:]):
  if a['command_v']<=v<=b['command_v']:return a['current_a']+(v-a['command_v'])*(b['current_a']-a['current_a'])/(b['command_v']-a['command_v'])
 raise ValueError(v)
def vi(i):
 for a,b in zip(curve,curve[1:]):
  if a['current_a']>=i>=b['current_a']:return a['command_v']+(i-a['current_a'])*(b['command_v']-a['command_v'])/(b['current_a']-a['current_a'])
 raise ValueError(i)
# measured programming-to-held-voltage relation from 7-point extracted transient calibration
h=sorted([(float(x['target_command_v']),float(x['measured_state_5ms_v'])) for x in hold['cases']])
def cmd_for_state(v):
 for (c0,s0),(c1,s1) in zip(h,h[1:]):
  if s0<=v<=s1:return c0+(v-s0)*(c1-c0)/(s1-s0)
 if abs(v-h[0][1])<1e-8:return h[0][0]
 if abs(v-h[-1][1])<1e-8:return h[-1][0]
 raise ValueError(f'held-state target outside calibration nodes {v}')
commands=[]
for scale in scales:
 target_current=imax*scale/smax;target_state=vi(target_current);commands.append(cmd_for_state(target_state))
binfile.write_bytes(struct.pack('<'+'d'*len(commands),*commands))
sorted_sc=sorted(scales)
def quant(a,q):
 x=(len(a)-1)*q;lo=math.floor(x);hi=math.ceil(x);return a[lo]*(hi-x)+a[hi]*(x-lo)
qpoints={}
for name,q in [('p01',.01),('p10',.10),('p50',.50),('p90',.90),('p99',.99)]:
 sc=quant(sorted_sc,q);cur=imax*sc/smax;state=vi(cur);command=cmd_for_state(state);qpoints[name]={'scale_v_per_model_unit':sc,'target_current_a':cur,'target_held_state_v':state,'program_command_v':command}
report={'mapping_generated':True,'model_checkpoint_sha256':m['checkpoint_sha256'],'bank_count':len(commands),'source_calibration':'v23 extracted 441-point DC transfer plus 7-point extracted 5ms write/hold command-to-state correction','mapping':'target_current proportional to original continuous per-bank scale 0.9/range; DC inverse gives target held state; inverse measured 5ms hold curve compensates program-command bias. No QAT or fixed-point model conversion.','bank_scale_dynamic_ratio':smax/smin,'required_ratio':json.loads(reqfile.read_text())['all_bank_scale_v_per_model_unit']['dynamic_ratio'],'target_current_range_a':[imax*smin/smax,imax],'target_held_state_voltage_range_v':[vi(imax*smin/smax),vi(imax)],'program_command_voltage_range_v':[min(commands),max(commands)],'quantile_targets':qpoints,'hold_compensation_mv_range':[min((cmd_for_state(vi(imax*s/smax))-vi(imax*s/smax))*1000 for s in (smin,smax)),max((cmd_for_state(vi(imax*s/smax))-vi(imax*s/smax))*1000 for s in (smin,smax))],'source_hold_residuals_mv':[round((state-cmd)*1000,4) for cmd,state in h],'physical_accuracy_claim':False,'scope':'Float-derived continuous bank calibration targets. The seven-point held-state bias correction is interpolated; representative-point independent transient replay is next. This does not prove PVT/noise/mismatch or recurrent model accuracy.','artifacts':{'commands_f64le':binfile.relative_to(ROOT).as_posix(),'dc_transfer':curvefile.relative_to(ROOT).as_posix(),'hold_validation':holdfile.relative_to(ROOT).as_posix(),'manifest':mfile.relative_to(ROOT).as_posix()},'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (mfile,curvefile,reqfile,holdfile,binfile)}}
outfile.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'bank_count':len(commands),'dynamic_ratio':smax/smin,'target_current_range_a':report['target_current_range_a'],'target_state_v_range':report['target_held_state_voltage_range_v'],'program_command_v_range':report['program_command_voltage_range_v'],'quantiles':qpoints},indent=2))
