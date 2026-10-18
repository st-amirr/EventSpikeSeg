"""Continuous original-float programming targets and physical parameter storage atlas.

Targets are mathematical voltage requests, not calibrated achieved circuit values.
No quantization, QAT, integer DAC code or parameter-to-device calibration is used.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
from assemble_gf180_full_capacity_storage_gds_v1 import records,rec,begin,reference
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=B/'model_reference/eventspikeseg140k_float_parameters.npz';meta=B/'model_reference/eventspikeseg140k_float_reference.json';m=json.loads(meta.read_text());assert m['checkpoint_sha256']=='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
 atlas=B/'assembly/full_capacity_storage_gds_v1/capacity_assembly.json';a=json.loads(atlas.read_text());assert a['logical_active_analog_nodes']==54630400
 cell='gf180_compact_memory_bank8x8_v1';d=B/'layout'/cell;native=d/(cell+'.gds');q=json.loads((d/'qualification.json').read_text());assert sha(native)==q['sha256'][native.name]
 raw=list(records(native.read_bytes()));first=next(i for i,(t,dt,v,b) in enumerate(raw) if t==5);last=max(i for i,(t,dt,v,b) in enumerate(raw) if t==7);prefix=b''.join(b for t,dt,v,b in raw[:first]);body=b''.join(b for t,dt,v,b in raw[first:last+1])
 data=np.load(source);targets={};entries=[];generated=[];px=151420;py=114400;gap=100000;x=y=shelf=0;total=bankcount=0;max_error=0.
 for i,key in enumerate(k for k in data.files if not k.startswith('affine_gain__')):
  values=data[key].astype(np.float64);assert np.isfinite(values).all();low=float(values.min());high=float(values.max());scale=max(abs(low),abs(high))
  volts=np.full(values.shape,1.2,dtype=np.float64) if scale==0 else 1.2+.2*values/scale
  reconstructed=np.zeros_like(values) if scale==0 else (volts-1.2)*scale/.2;err=float(np.max(np.abs(values-reconstructed)));assert err<1e-12;max_error=max(max_error,err);targets[key]=volts
  n=int(values.size);banks=math.ceil(n/64);cols=min(16,banks);rows=math.ceil(banks/cols);width=cols*px;height=rows*py
  if x+width>20000000:x=0;y+=shelf+gap;shelf=0
  name=f'PARAM_ARRAY_{i:03d}';b=begin(name);full=banks//cols;remaining=banks%cols
  if full:b+=reference(cell,13200,4700,cols,full,px,py)
  if remaining:b+=reference(cell,13200,4700+full*py,remaining,1,px,py)
  generated.append(b+rec(7,0));entries.append(dict(array=key,original_shape=list(values.shape),float_value_count=n,original_min=low,original_max=high,voltage_scale=scale,voltage_expression='1.2 + 0.2 * original_float / voltage_scale; all zero arrays use1.2V',inverse_expression='(V-1.2)*voltage_scale/0.2',requested_min_v=float(volts.min()),requested_max_v=float(volts.max()),mathematical_reconstruction_max_abs_error=err,gds_cell=name,origin_dbu=[x,y],bank_columns=cols,bank_rows=rows,physical_bank_count=banks,inactive_final_bank_slots=banks*64-n,selector='flat=C-order array index; bank=flat//64; local_row=(flat%64)//8; local_column=flat%8',device_control_calibration_complete=False))
  total+=n;bankcount+=banks;x+=width+gap;shelf=max(shelf,height)
 assert sum(int(data[k].size) for k in data.files if k.startswith('weight__'))==143824
 top=begin('FLOAT_PARAMETER_CAPACITY_TOP')
 for e in entries:top+=reference(e['gds_cell'],*e['origin_dbu'])
 generated.append(top+rec(7,0));out=B/'assembly/float_parameter_capacity_v1';assert not out.exists();out.mkdir();gds=out/'float_parameter_capacity_v1.gds';gds.write_bytes(prefix+body+b''.join(generated)+rec(4,0));list(records(gds.read_bytes()))
 targetsfile=out/'continuous_programming_targets_v1.npz';np.savez_compressed(targetsfile,**targets)
 r=dict(continuous_float_target_export_complete=True,physical_parameter_capacity_GDS_written=True,checkpoint_sha256=m['checkpoint_sha256'],synaptic_weights=143824,beta_channels=1856,stored_parameter_values=total,stored_parameter_arrays=len(entries),physical_bank_count=bankcount,physical_slots=bankcount*64,physical_bank_geometry_mm2=bankcount*149.42*112.4/1e6,mathematical_inverse_max_abs_error=max_error,parameters_quantized=False,achieved_analog_precision_accepted=False,programming_and_refresh_circuit_complete=False,full_chip_layout_complete=False,arrays=entries,
  scope='Original float32 values mapped continuously to requested1.0-1.4V programming targets and real qualified bank GDS. Affine gains excluded because already folded into deployed weights. Mathematical inverse checked on every value; this does not establish achievable analog precision. Voltage targets have no QAT/bit-depth/integer DAC code. Stored beta/threshold/adaptation requests are not calibrated transistor controls; they require analog decoding/calibration. Bank retention is only the measured5ms nominal state fixture, not permanent parameter retention. External programming/refresh, routing to compute, weight-to-charge gain/sign/duration calibration, mismatch/noise/PVT and full-chip interconnect remain incomplete. This separate capacity atlas is not a selected chip/die or manufactured parameter memory.',
  sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),R/'scripts/assemble_gf180_full_capacity_storage_gds_v1.py',source,meta,atlas,native,d/'qualification.json',gds,targetsfile]})
 rp=out/'parameter_capacity_assembly.json';rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['arrays','sha256']},indent=2))
if __name__=='__main__':main()
