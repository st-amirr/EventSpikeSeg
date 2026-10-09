"""Audit buffered readout and identity read/restore circuit evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def deck(v):
 paths=[ROOT/n for n in v['sha256'] if '/benches/' in n and n.endswith('.spice')];assert len(paths)==1
 return re.sub(r'(?m)^tran .*$', 'TRAN_NORMALIZED',paths[0].read_text())
def main():
 rows=[];reports=[];convergence=[]
 for pattern in ['gf180_buffered_capture_inverse*.json','gf180_analog_read_restore_inverse*.json']:
  for p in sorted(BASE.glob(pattern)):
   v=json.loads(p.read_text())
   for n,x in v['sha256'].items():
    if digest(ROOT/n)!=x:raise ValueError('Changed evidence: '+n)
   reports.append((p,v));rows.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'settings':v['settings'],'simulation_completed':v['simulation_completed'],'held_time_s':v['held_measurement_time_s'],'post_restore_hold_completed':v.get('post_restore_hold_completed',False),'cases':v['cases']})
 for p,v in reports:
  if not p.name.startswith('gf180_analog_read_restore_') or not v['simulation_completed'] or v['settings']['max_step_ns']!=10:continue
  desired=dict(v['settings']);desired['max_step_ns']=20
  for q,w in reports:
   if w['settings']!=desired or not w['simulation_completed'] or digest(ROOT/w['source_snapshot'])!=digest(ROOT/v['source_snapshot']):continue
   if deck(v)!=deck(w):raise ValueError('Convergence differs beyond tran')
   convergence.append({'fine':p.name,'coarse':q.name,'exact_decks_match_except_tran':True,'max_voltage_endpoint_difference_uv':max(abs(c['measurements_v'][key]-d['measurements_v'][key])*1e6 for c,d in zip(v['cases'],w['cases']) for key in c['measurements_v']),'round_trip_error_difference_uv':[1000*(c['round_trip_error_mv']-d['round_trip_error_mv']) for c,d in zip(v['cases'],w['cases'])]})
 output={'reports':rows,'convergence':convergence,'calibrated_inverse_accepted':False,'complete_PLIF_accepted':False,'model_accuracy_accepted':False,'population_5ms_service_accepted':False,'full_chip_accepted':False,'scope':'All component/native model/deck/log/source snapshot hashes checked. Nominal identity storage-cycle fixture, not trained nonlinear encoding/complete neuron. Inverse resistor network remains schematic native model. Separately qualified physical macros interconnected schematically. Postrestore5ms native-card hold is not silicon leakage/noise/PVT qualification or population5ms service. No numerical state/offset correction applied.'}
 p=BASE/'gf180_buffered_read_restore_boundary.json';p.write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({'report':str(p),'reports':len(rows),'complete':sum(x['simulation_completed'] for x in rows),'convergence':convergence,'restore_cases':[{'report':p.name,'cases':[{k:c.get(k) for k in ['target_v','round_trip_error_mv','restore_acquired_error_mv','restore_release_step_mv','post_restore_hold_drift_uv']} for c in v['cases']]} for p,v in reports if p.name.startswith('gf180_analog_read_restore_')]},indent=2))
if __name__=='__main__':main()
