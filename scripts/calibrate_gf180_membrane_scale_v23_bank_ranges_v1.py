from __future__ import annotations
import hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
manifest=BASE/'assembly/membrane_voltage_scale_manifest_v2.json';curvefile=BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json';reqfile=BASE/'results/gf180_membrane_scale_hardware_requirements_v1.json'
voltagebin=BASE/'assembly/gf180_membrane_scale_v23_bank_program_volts_v1.f64le';reportfile=BASE/'results/gf180_membrane_scale_v23_bank_calibration_v1.json'
assert not voltagebin.exists() and not reportfile.exists()
m=json.loads(manifest.read_text());tr=json.loads(curvefile.read_text());req=json.loads(reqfile.read_text());assert m['checkpoint_sha256']=='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
pts=[(float(x['command_v']),float(x['current_a'])) for x in tr['curve']];assert all(pts[i][1]>pts[i+1][1] for i in range(len(pts)-1))
ranges=[float(r) for a in m['actors'] for r in a['range_abs_model_units']];assert len(ranges)==m['scale_count']==490240
scales=[.9/r for r in ranges];smin=min(scales);smax=max(scales);imax=pts[0][1];imin=imax*smin/smax

def interp_voltage(target):
 for (v0,i0),(v1,i1) in zip(pts,pts[1:]):
  if i0>=target>=i1: return v0+(target-i0)*(v1-v0)/(i1-i0)
 raise ValueError(f'target current out of sweep range: {target}')
def interp_current(v):
 for (v0,i0),(v1,i1) in zip(pts,pts[1:]):
  if v0<=v<=v1:return i0+(v-v0)*(i1-i0)/(v1-v0)
 raise ValueError(v)
volts=[];errs=[]
for scale in scales:
 target=imax*scale/smax; v=interp_voltage(target); volts.append(v); errs.append((interp_current(v)-target)/target)
voltagebin.write_bytes(struct.pack('<'+'d'*len(volts),*volts))
sortedv=sorted(volts)
def quant(q):
 x=(len(sortedv)-1)*q;lo=int(x);hi=min(lo+1,len(sortedv)-1);return sortedv[lo]*(hi-x)+sortedv[hi]*(x-lo)
curve_min=pts[-1][1]; bankratio=smax/smin; required=req['all_bank_scale_v_per_model_unit']['dynamic_ratio'];expected_vhigh=interp_voltage(imin)
report={'mapping_generated':True,'model_checkpoint_sha256':m['checkpoint_sha256'],'bank_count':len(volts),'continuous_formula':'target_current = I_at_0.75V * (0.9V / bank_range) / maximum(0.9V / bank_range); command_voltage is inverse of the measured v23 DC transfer using piecewise-linear interpolation over 5mV samples','bank_scale_dynamic_ratio':bankratio,'hardware_requirements_dynamic_ratio':required,'relative_ratio_match_error':(bankratio-required)/required,'measured_transfer_current_range_a':[pts[0][1],pts[-1][1]],'required_current_range_a':[imin,imax],'predicted_voltage_range_v':[min(volts),max(volts)],'quantile_program_voltage_v':{'p01':quant(.01),'p10':quant(.10),'p50':quant(.50),'p90':quant(.90),'p99':quant(.99)},'lowest_scale_current_margin_over_sweep_floor':imin/curve_min,'piecewise_interpolation_relative_current_error_max':max(abs(x) for x in errs),'physical_accuracy_claim':False,'scope':'Continuous bank-scale programming targets derived from the original float voltage-scale manifest and nominal extracted DC transfer. Interpolation self-consistency is not independent circuit accuracy; no mismatch/noise/PVT, full signed update, output accumulator or model replay is qualified.','artifacts':{'voltage_targets_f64le':voltagebin.relative_to(ROOT).as_posix(),'transfer_curve':curvefile.relative_to(ROOT).as_posix(),'scale_manifest':manifest.relative_to(ROOT).as_posix()},'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (manifest,curvefile,reqfile,voltagebin)}}
reportfile.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ('bank_count','bank_scale_dynamic_ratio','hardware_requirements_dynamic_ratio','required_current_range_a','predicted_voltage_range_v','quantile_program_voltage_v','lowest_scale_current_margin_over_sweep_floor')},indent=2))
