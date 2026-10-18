from __future__ import annotations
import hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';mfile=BASE/'assembly/membrane_voltage_scale_manifest_v2.json';curvefile=BASE/'results/gf180_membrane_scale_v23_transfer_replay_summary_v1.json';report21=BASE/'results/gf180_membrane_scale_v23_bank_map_validate21pt_v1.json';rawcurve=BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json'
binfile=BASE/'assembly/gf180_membrane_scale_v23_bank_program_volts_v3_21pt_transient.f64le';outfile=BASE/'results/gf180_membrane_scale_v23_bank_calibration_v3.json';assert not binfile.exists() and not outfile.exists()
m=json.loads(mfile.read_text());cal=json.loads(report21.read_text());cases=cal['cases'];mpoints=sorted((float(c['command_v']),float(c['measured_current_5ms_a'])) for c in cases);assert all(mpoints[i][1]>mpoints[i+1][1] for i in range(len(mpoints)-1))
ranges=[float(x) for a in m['actors'] for x in a['range_abs_model_units']];scales=[.9/r for r in ranges];smin=min(scales);smax=max(scales);imax=json.loads(rawcurve.read_text())['curve'][0]['current_a']
def command_for_current(target):
 for (v0,i0),(v1,i1) in zip(mpoints,mpoints[1:]):
  if i0>=target>=i1:return v0+(target-i0)*(v1-v0)/(i1-i0)
 if abs(target-mpoints[-1][1])<1e-15:return mpoints[-1][0]
 raise ValueError(f'current outside transient calibration range: {target}')
commands=[command_for_current(imax*s/smax) for s in scales];assert len(commands)==490240;binfile.write_bytes(struct.pack('<'+'d'*len(commands),*commands))
sorted_sc=sorted(scales)
def quant(a,q):
 x=(len(a)-1)*q;lo=math.floor(x);hi=math.ceil(x);return a[lo] if lo==hi else a[lo]*(hi-x)+a[hi]*(x-lo)
qs={}
for name,q in [('p01',.01),('p10',.1),('p50',.5),('p90',.9),('p99',.99)]:
 s=quant(sorted_sc,q);target=imax*s/smax;cmd=command_for_current(target);qs[name]={'scale':s,'target_current_a':target,'program_command_v':cmd}
report={'mapping_generated':True,'model_checkpoint_sha256':m['checkpoint_sha256'],'bank_count':len(commands),'mapping':'For each original-float bank scale 0.9/range, target current is proportional to that scale. Command voltage is the piecewise-linear inverse of the extracted-cell 5ms transient measured-current curve at 21 bank-scale percentiles; preserves full float values and uses no QAT.','bank_scale_dynamic_ratio':smax/smin,'target_current_range_a':[imax*smin/smax,imax],'program_command_voltage_range_v':[min(commands),max(commands)],'program_command_quantiles_v':{k:v['program_command_v'] for k,v in qs.items()},'quantile_targets':qs,'physical_accuracy_claim':False,'scope':'Calibrated bank programming commands derived from measured transient current residuals at 21 quantiles. Between-quantile error requires validation; no PVT/noise/mismatch or original-float recurrence accepted.','sources':{'manifest':mfile.relative_to(ROOT).as_posix(),'transient_transfer_validation':report21.relative_to(ROOT).as_posix(),'summary':curvefile.relative_to(ROOT).as_posix(),'dc_transfer':rawcurve.relative_to(ROOT).as_posix()},'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (mfile,report21,curvefile,rawcurve,binfile)}}
outfile.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'banks':len(commands),'current_range':report['target_current_range_a'],'command_range':report['program_command_voltage_range_v'],'quantiles':report['program_command_quantiles_v']},indent=2))
