from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'artifacts/analog_asic/results'
FILES={-31.0:'sky130_ms_mos_state_banked_transfer_ss0_dm31mV.json',
        0.0:'sky130_ms_mos_state_banked_transfer_ss0.json',
       31.0:'sky130_ms_mos_state_banked_transfer_ss0_d31mV.json'}
reports={state:json.loads((RES/name).read_text(encoding='utf-8')) for state,name in FILES.items()}
if any(not r.get('simulation_completed') or r.get('measured_case_count',104)!=104 for r in reports.values()):
    raise RuntimeError('all three 104-point full-bank state maps must complete')
base=reports[0.0]
for state,r in reports.items():
    if r['geometry_factors']!=base['geometry_factors'] or r['gate_fractions']!=base['gate_fractions']:
        raise RuntimeError(f'grid mismatch at state {state:g}mV')
    if abs(r['pulse_width_ns']-base['pulse_width_ns'])>1e-9 or r['mos_corner']!='ss' or r['temperature_c']!=0:
        raise RuntimeError(f'operating point mismatch at state {state:g}mV')
G=base['geometry_factors']; F=np.asarray(base['gate_fractions'],float)
T={s:np.asarray(r['transfer_delta_v_by_polarity_geometry_fraction']['p'],float) for s,r in reports.items()}
rows=[]; pct=[]; slopes=[]
for gi,g in enumerate(G):
  for fi,f in enumerate(F):
    q0=T[0.0][gi,fi]
    row={'geometry':g,'gate_fraction':f,'zero_state_uv':q0*1e6}
    for s in (-31.0,31.0):
      q=T[s][gi,fi]
      row[f'state_{s:+g}mV_uv']=q*1e6
      row[f'state_{s:+g}mV_change_uv']=(q-q0)*1e6
      row[f'state_{s:+g}mV_change_percent']=100*(q/q0-1) if q0 else None
      if q0>0 and np.all(np.diff(T[s][gi])>0):
        curve=T[s][gi]
        ix=np.where(curve>0)[0]
        if len(ix)>=2 and curve[ix[0]]<=q0<=curve[ix[-1]]:
          needed=float(np.interp(q0,curve[ix],F[ix]))
          slope=(needed-f)/(s*1e-3)
          row[f'required_gate_fraction_slope_at_{s:+g}mV_per_v']=slope
          slopes.append({'geometry':g,'gate_fraction':f,'state_diff_mv':s,'required_slope_per_v':slope})
        else: row[f'required_gate_fraction_slope_at_{s:+g}mV_per_v']=None
      else: row[f'required_gate_fraction_slope_at_{s:+g}mV_per_v']=None
      if f>=0.8:
        pct.append(row[f'state_{s:+g}mV_change_percent'])
    rows.append(row)
usable=[x for x in slopes if x['gate_fraction']>=0.8]
vals=np.array([x['required_slope_per_v'] for x in usable])
summary={'test':'sky130_fullbank_MOS_injector_state_transfer_surface',
 'source_reports':list(FILES.values()),'simulation_completed':True,
 'geometry_count':len(G),'bias_count':len(F),'point_count_per_state':104,
 'state_differential_mv':[-31.0,0.0,31.0],'common_mode_v':0.9,
 'maximum_absolute_transfer_change_percent_over_grid':max(abs(r[f'state_{s:+g}mV_change_percent']) for r in rows for s in (-31.0,31.0)),
 'gate_fraction_ge_0p8_point_count':sum(r['gate_fraction']>=0.8 for r in rows),
 'gate_fraction_ge_0p8_transfer_change_percent_p10_median_p90':np.percentile(pct,[10,50,90]).tolist(),
 'gate_fraction_ge_0p8_valid_compensation_slope_count':len(vals),
 'gate_fraction_ge_0p8_required_compensation_slope_per_v_p10_median_p90':np.percentile(vals,[10,50,90]).tolist() if len(vals) else None,
 'rows':rows,
 'scope':'Empirical interpolation of 312 physical full-bank one-event transfer points at -31/0/+31mV. For each zero-state transfer, estimate the gate-fraction shift needed to recover that transfer at the nonzero-state map. This is a control-law diagnostic, not a physical sensor, dynamic feedback, noise/mismatch result, retention test, extraction or layout.'}
out=RES/'sky130_ms_mos_state_banked_transfer_state_surface_summary.json'
out.write_text(json.dumps(summary,indent=2,default=lambda value: value.item() if hasattr(value,'item') else str(value))+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2,default=lambda value: value.item() if hasattr(value,'item') else str(value)))

