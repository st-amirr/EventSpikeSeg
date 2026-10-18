import json,re,math
from pathlib import Path
ROOT=Path('.');BASE=Path('artifacts/analog_asic');m=json.loads((BASE/'assembly/membrane_voltage_scale_manifest_v2.json').read_text());scales=sorted(.9/float(x) for a in m['actors'] for x in a['range_abs_model_units']);dc=json.loads((BASE/'results/gf180_membrane_scale_compact_v23_transfer_dc441.json').read_text())['curve'];hold=json.loads((BASE/'results/gf180_membrane_scale_v23_bank_map_validate21pt_v1.json').read_text());points=sorted((c['command_v'],c['measured_current_5ms_a']) for c in hold['cases']);imax=dc[0]['current_a']
def quant(a,q):
 x=(len(a)-1)*q;lo=math.floor(x);hi=math.ceil(x);return a[lo] if lo==hi else a[lo]*(hi-x)+a[hi]*(x-lo)
def command(i):
 for (v0,i0),(v1,i1) in zip(points,points[1:]):
  if i0>=i>=i1:return v0+(i-i0)*(v1-v0)/(i1-i0)
def state(i):
 for a,b in zip(dc,dc[1:]):
  if a['current_a']>=i>=b['current_a']:return a['state_v']+(i-a['current_a'])*(b['state_v']-a['state_v'])/(b['current_a']-a['current_a'])
logs=[BASE/'results/gf180_membrane_scale_v23_bank_map_v3_validate41_group0.log',BASE/'results/gf180_membrane_scale_v23_bank_map_v3_validate41_group1.log'];vals={}
for p in logs:
 s=p.read_text(); assert 'ngspice-47 done' in s and 'timestep too small' not in s.lower()
 vals.update({k:float(v) for k,v in re.findall(r'(?mi)^((?:state|current)_q\d{3,4})\s*=\s*([-+0-9.eE]+)',s)})
qvalues=[i/40 for i in range(41)];results=[]
for qi,q in enumerate(qvalues):
 tag=f'q{int(round(q*1000)):03d}';sc=quant(scales,q);target=imax*sc/max(scales);vcmd=command(target);targetv=state(target);ms=vals[f'state_{tag}'];mi=vals[f'current_{tag}'];results.append({'quantile':q,'target_current_a':target,'command_v':vcmd,'target_state_v':targetv,'measured_state_5ms_v':ms,'hold_error_mv':(ms-targetv)*1000,'measured_current_5ms_a':mi,'relative_current_error':(mi-target)/target})
summary={'simulation_completed':len(vals)==82,'cell':'gf180_membrane_scale_compact_v23','points':len(results),'hold_s':.005,'curve_used_for_map':'21 measured transient 5ms calibration nodes','cases':results,'summary':{'max_abs_relative_current_error':max(abs(x['relative_current_error']) for x in results),'mean_abs_relative_current_error':sum(abs(x['relative_current_error']) for x in results)/len(results),'max_abs_hold_error_mv':max(abs(x['hold_error_mv']) for x in results),'mean_abs_hold_error_mv':sum(abs(x['hold_error_mv']) for x in results)/len(results)},'scope':'41-point held-transient validation at 2.5% bank-scale quantiles, endpoints and 21-point calibration nodes. Nominal typical only; no PVT/noise/mismatch or model recurrence.','logs':[x.as_posix() for x in logs]};out=BASE/'results/gf180_membrane_scale_v23_bank_map_v3_validate41pt.json';assert not out.exists();out.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['summary'],indent=2))
